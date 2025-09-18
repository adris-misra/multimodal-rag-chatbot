"""
textract_parser.py
Utilities to call Amazon Textract and convert responses into usable chunks.

Functions:
  • analyze_document(bucket, key)  -> raw Textract response
  • extract_lines(blocks)          -> LINE blocks
  • extract_tables_as_markdown()   -> Markdown tables for quick LLM rendering
  • extract_figures(blocks)        -> FIGURE blocks (if present)
"""
from __future__ import annotations
import boto3
from typing import List, Dict, Tuple

def analyze_document(s3_bucket: str, s3_key: str) -> dict:
    """Run Textract on an S3 object and return raw JSON blocks."""
    textract = boto3.client('textract')
    return textract.analyze_document(
        Document={'S3Object': {'Bucket': s3_bucket, 'Name': s3_key}},
        FeatureTypes=['TABLES', 'FORMS']
    )

def extract_lines(blocks: List[dict]) -> List[dict]:
    """Extract only LINE blocks from a Textract response."""
    return [b for b in blocks if b.get('BlockType') == 'LINE']

def extract_tables_as_markdown(blocks: List[dict]) -> List[Tuple[str, dict]]:
    """
    Convert Textract TABLE blocks into Markdown for easy prompting.

    Returns:
        List[(markdown_table_str, table_block)]
    """
    tables = []
    block_map = {b['Id']: b for b in blocks if 'Id' in b}

    # Iterate all blocks, find TABLEs, then traverse their CELL children
    for b in blocks:
        if b.get('BlockType') != 'TABLE':
            continue

        cell_text = {}
        for r in b.get('Relationships', []) or []:
            if r.get('Type') != 'CHILD':
                continue
            for cid in r.get('Ids', []):
                cell = block_map.get(cid)
                if not cell or cell.get('BlockType') != 'CELL':
                    continue

                row = cell.get('RowIndex', 1)
                col = cell.get('ColumnIndex', 1)

                # Collect all WORD children for this cell
                text = ''
                for rr in cell.get('Relationships', []) or []:
                    if rr.get('Type') != 'CHILD':
                        continue
                    for wid in rr.get('Ids', []):
                        w = block_map.get(wid)
                        if w and w.get('BlockType') == 'WORD':
                            text += (w.get('Text', '') + ' ')
                cell_text[(row, col)] = text.strip()

        # Build a simple Markdown table
        max_row = max((r for r, _ in cell_text.keys()), default=0)
        max_col = max((c for _, c in cell_text.keys()), default=0)
        lines = []
        for r in range(1, max_row + 1):
            row_vals = [cell_text.get((r, c), '') for c in range(1, max_col + 1)]
            lines.append('| ' + ' | '.join(row_vals) + ' |')
            if r == 1:
                lines.append('|' + '|'.join([' --- ']*max_col) + '|')

        md = '\n'.join(lines)
        tables.append((md, b))
    return tables

def extract_figures(blocks: List[dict]) -> List[dict]:
    """Return FIGURE blocks (if the document includes them)."""
    return [b for b in blocks if b.get('BlockType') == 'FIGURE']
