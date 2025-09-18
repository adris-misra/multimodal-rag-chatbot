"""
ingest.py
Ingest pipeline: S3 -> Textract -> Titan Embeddings -> OpenSearch.

What it does:
  1) Lists PDFs under S3_PREFIX in S3_BUCKET
  2) Runs Textract to extract lines, tables, and figures
  3) Generates embeddings for text lines, table+context, and figure captions
  4) Upserts vectors into three OpenSearch indexes (text/table/image)

Tip: For large docs, consider the async Textract API (StartDocumentAnalysis).
"""
from __future__ import annotations
import boto3
from typing import List
from config import Config
from embeddings import embed_text
from vector_store import VectorStore
from utils.textract_parser import analyze_document, extract_lines, extract_tables_as_markdown, extract_figures
from utils.chunk_joiner import attach_context_to_tables
from utils.caption_extractor import figure_captions

cfg = Config()

def list_pdf_keys(bucket: str, prefix: str) -> List[str]:
    """Return all S3 keys under prefix that end with .pdf (case-insensitive)."""
    s3 = boto3.client('s3')
    keys = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            if key.lower().endswith('.pdf'):
                keys.append(key)
    return keys

def ingest_document(vs: VectorStore, bucket: str, key: str) -> None:
    """Analyze one PDF and write text/table/image vectors to OpenSearch."""
    print(f"[INGEST] Analyzing s3://{bucket}/{key}")
    resp = analyze_document(bucket, key)
    blocks = resp['Blocks']

    # --- TEXT: naïve approach, index each LINE (you may group by page/heading) ---
    lines = extract_lines(blocks)
    for i, ln in enumerate(lines):
        text = ln.get('Text', '').strip()
        if not text:
            continue
        emb = embed_text(text)
        doc_id = f"{key}::line::{i}"
        vs.upsert(cfg.index_text, doc_id, text, emb, 'text', {
            'source': key, 'page': ln.get('Page')
        })

    # --- TABLES: convert to Markdown and attach nearby context ---
    tables = extract_tables_as_markdown(blocks)
    table_chunks = attach_context_to_tables(lines, tables)
    for i, ch in enumerate(table_chunks):
        content_for_embed = f"{ch['content']}\nContext: {ch['context']}"
        emb = embed_text(content_for_embed)
        doc_id = f"{key}::table::{i}"
        vs.upsert(cfg.index_table, doc_id, ch['content'], emb, 'table', {
            'source': key, **ch['metadata']
        })

    # --- IMAGES: derive a caption from nearby lines, embed caption ---
    figs = extract_figures(blocks)
    caps = figure_captions(lines, figs)
    for i, ch in enumerate(caps):
        caption = ch['metadata'].get('caption') or 'Figure'
        emb = embed_text(caption)
        doc_id = f"{key}::image::{i}"
        vs.upsert(cfg.index_image, doc_id, caption, emb, 'image', {
            'source': key, **ch['metadata']
        })

def main():
    if not cfg.s3_bucket:
        raise SystemExit("S3_BUCKET not configured")
    vs = VectorStore(cfg)
    keys = list_pdf_keys(cfg.s3_bucket, cfg.s3_prefix)
    if not keys:
        print("No PDFs found to ingest.")
        return
    for key in keys:
        ingest_document(vs, cfg.s3_bucket, key)
    print("Ingestion complete.")

if __name__ == "__main__":
    main()
