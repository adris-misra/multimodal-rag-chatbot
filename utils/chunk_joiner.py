"""
chunk_joiner.py
Layout-aware helper (IoU-based) to attach nearby text context to tables.

In a production system, you might use page-level headings, section numbers,
or learned heuristics. Here we show a simple geometric proximity approach.
"""
from __future__ import annotations
from typing import List, Dict, Any

def iou(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    """Compute Intersection-over-Union between two [0..1] bounding boxes."""
    ax, ay, aw, ah = a['Left'], a['Top'], a['Width'], a['Height']
    bx, by, bw, bh = b['Left'], b['Top'], b['Width'], b['Height']
    ax2, ay2 = ax+aw, ay+ah
    bx2, by2 = bx+bw, by+bh
    inter_w = max(0.0, min(ax2, bx2) - max(ax, bx))
    inter_h = max(0.0, min(ay2, by2) - max(ay, by))
    inter = inter_w * inter_h
    union = aw*ah + bw*bh - inter
    return inter/union if union else 0.0

def attach_context_to_tables(lines: List[dict], tables: List[tuple]) -> List[Dict[str, Any]]:
    """Attach nearby line text to each table as `context` (very simple heuristic)."""
    chunks: List[Dict[str, Any]] = []
    for md, tbl in tables:
        tbox = tbl['Geometry']['BoundingBox']
        nearby = []
        for ln in lines:
            if ln.get('Page') != tbl.get('Page'):
                continue
            lbox = ln['Geometry']['BoundingBox']
            # Either overlapping, or very close above the table
            proximity = iou(tbox, lbox)
            if proximity > 0.0 or abs((lbox['Top'] + lbox['Height']) - tbox['Top']) < 0.05:
                nearby.append(ln.get('Text', ''))
        context = ' '.join(nearby[-5:])  # last few lines often capture captions/lead-in
        chunks.append({
            'modality': 'table',
            'content': md,
            'context': context,
            'metadata': {
                'page': tbl.get('Page'),
                'caption': context[:140],
            }
        })
    return chunks
