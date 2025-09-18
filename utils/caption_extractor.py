"""
caption_extractor.py
Heuristic caption finder for FIGURE blocks using nearest line above/below.
"""
from __future__ import annotations
from typing import List, Dict, Any

def figure_captions(lines: List[dict], figures: List[dict]) -> list[dict]:
    """Return a list of {'modality', 'content', 'metadata'} dicts for images."""
    out = []
    for fig in figures:
        fbox = fig['Geometry']['BoundingBox']
        same_page = [ln for ln in lines if ln.get('Page') == fig.get('Page')]
        best = None
        best_dist = 1e9
        for ln in same_page:
            lbox = ln['Geometry']['BoundingBox']
            # Distance to top or bottom edge of the figure box
            dist = min(abs((lbox['Top']+lbox['Height']) - fbox['Top']),
                       abs(lbox['Top'] - (fbox['Top']+fbox['Height'])))
            if dist < best_dist:
                best, best_dist = ln, dist
        caption = best.get('Text', '') if best else ''
        out.append({
            'modality': 'image',
            'content': caption or 'Figure',
            'metadata': {
                'page': fig.get('Page'),
                'caption': caption[:140]
            }
        })
    return out
