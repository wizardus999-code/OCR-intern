from typing import List, Dict, Any
from dataclasses import is_dataclass

def _normalize_item(r: Any) -> Dict[str, Any]:
    if is_dataclass(r):
        bbox = getattr(r, 'bounding_box', None) or getattr(r, 'bbox', None) or (0,0,1,1)
        x, y, w, h = bbox if isinstance(bbox, (list, tuple)) and len(bbox) == 4 else (0,0,1,1)
        return {
            'text': getattr(r, 'text', ''),
            'language': getattr(r, 'language', 'french'),
            'bbox': [int(x), int(y), int(w), int(h)]
        }
    if isinstance(r, dict):
        bbox = r.get('bbox') or r.get('bounding_box') or [0,0,1,1]
        if isinstance(bbox, tuple):
            bbox = list(bbox)
        if not (isinstance(bbox, (list, tuple)) and len(bbox) == 4):
            bbox = [0,0,1,1]
        return {
            'text': r.get('text',''),
            'language': r.get('language', r.get('lang','french')),
            'bbox': [int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])]
        }
    return {'text': str(r), 'language': 'french', 'bbox': [0,0,1,1]}

def flatten_results(results: Any) -> List[Dict[str, Any]]:
    if isinstance(results, dict):
        items: List[Any] = []
        for v in results.values():
            if isinstance(v, list):
                items.extend(v)
        return [_normalize_item(x) for x in items]
    if isinstance(results, list):
        return [_normalize_item(x) for x in results]
    return []

def sort_for_reading(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    lines: Dict[int, List[Dict[str, Any]]] = {}
    for it in items:
        x, y, w, h = it.get('bbox', [0,0,1,1])
        key = int(y // max(1, h))
        lines.setdefault(key, []).append(it)
    ordered: List[Dict[str, Any]] = []
    for key in sorted(lines.keys()):
        line = lines[key]
        arabic_cnt = sum(1 for i in line if str(i.get('language','')).lower().startswith('arab'))
        rtl = arabic_cnt > (len(line) / 2)
        line.sort(key=lambda i: i.get('bbox',[0,0,1,1])[0], reverse=rtl)
        ordered.extend(line)
    return ordered
