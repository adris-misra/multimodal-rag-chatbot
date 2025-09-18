"""
query.py
Query pipeline: user question -> embeddings -> KNN retrieval -> prompt -> Claude.

Steps:
  1) Embed the user question using Titan
  2) Retrieve top‑k neighbors from text/table/image indexes
  3) Assemble a structured context string (sections for text/table/image)
  4) Ask Claude 3 Sonnet on Bedrock with a strict, grounded prompt
"""
from __future__ import annotations
import argparse, json, boto3
from typing import List
from config import Config
from embeddings import embed_text
from vector_store import VectorStore

cfg = Config()
bedrock = boto3.client("bedrock-runtime", region_name=cfg.region)

def knn_topk(vs: VectorStore, vector: List[float], k: int = 4) -> list[dict]:
    """Retrieve top‑k for each modality and return a flat list with metadata."""
    hits_all = []
    for index, modality in [
        (cfg.index_text, 'text'),
        (cfg.index_table, 'table'),
        (cfg.index_image, 'image'),
    ]:
        hits = vs.knn(index, vector, k)
        for h in hits:
            src = h.get('_source', {})
            hits_all.append({
                'modality': modality,
                'content': src.get('content', ''),
                'metadata': src.get('metadata', {}),
                'score': h.get('_score', 0.0)
            })
    # Optional: sort by score first, with a slight preference for tables
    hits_all.sort(key=lambda x: (round(x['score'], 4), 1 if x['modality']=='table' else 0), reverse=True)
    return hits_all

def build_context(chunks: list[dict]) -> str:
    """Build a readable, grounded context string for the LLM."""
    parts = []
    for ch in chunks:
        src = ch['metadata'].get('source')
        page = ch['metadata'].get('page')
        if ch['modality'] == 'table':
            parts.append(f"[TABLE]\n{ch['content']}\n(Source: {src} p.{page})\n")
        elif ch['modality'] == 'image':
            parts.append(f"[IMAGE]\nCaption: {ch['content']}\n(Source: {src} p.{page})\n")
        else:
            parts.append(f"[TEXT]\n{ch['content'][:1200]}\n(Source: {src} p.{page})\n")
    return "\n".join(parts)

def load_prompt_template() -> str:
    with open('prompt_templates/claude_prompt.txt', 'r', encoding='utf-8') as f:
        return f.read()

def ask_claude(question: str, context: str) -> str:
    """Send the grounded prompt to Claude via Bedrock and return the answer text."""
    prompt = load_prompt_template().replace("{{CONTEXT}}", context).replace("{{QUESTION}}", question)
    body = json.dumps({
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ],
        "max_tokens": 1200,
        "temperature": 0.1
    })
    resp = bedrock.invoke_model(
        modelId=cfg.bedrock_claude_model,
        body=body,
        contentType="application/json",
        accept="application/json"
    )
    payload = json.loads(resp["body"].read())
    parts = payload.get("content", [])
    return parts[0].get("text", "") if parts else ""

def main():
    parser = argparse.ArgumentParser(description="Ask a multimodal RAG question")
    parser.add_argument("question", type=str)
    parser.add_argument("--k", type=int, default=4)
    args = parser.parse_args()

    vs = VectorStore(cfg)
    qvec = embed_text(args.question)
    chunks = knn_topk(vs, qvec, k=args.k)
    context = build_context(chunks)
    answer = ask_claude(args.question, context)
    print("\n=== ANSWER ===\n")
    print(answer)

if __name__ == "__main__":
    main()
