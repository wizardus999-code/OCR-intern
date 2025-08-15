from typing import Dict, Any, Tuple, List
import json
import re
from pathlib import Path
import cv2
import numpy as np
from src.postprocessing.validators import normalize_field

def _build_tess_config(rel: Dict[str, Any]) -> str:
    cfg: List[str] = []
    if (psm := rel.get('psm')) is not None: cfg += ['--psm', str(psm)]
    if (oem := rel.get('oem')) is not None: cfg += ['--oem', str(oem)]
    if (dpi := rel.get('dpi')) is not None: cfg += ['-c', f'user_defined_dpi={int(dpi)}']
    if rel.get('preserve_spaces'): cfg += ['-c', 'preserve_interword_spaces=1']
    if (wl := rel.get('whitelist')): cfg += ['-c', f'tessedit_char_whitelist={wl}']
    if (bl := rel.get('blacklist')): cfg += ['-c', f'tessedit_char_blacklist={bl}']
    
    # Special handling for Arabic to prevent Latin character confusion
    if rel.get('lang') == 'arabic':
        cfg += ['--oem', '1',  # Use LSTM mode
                '-c', 'preserve_interword_spaces=1',
                '-c', 'tessedit_char_blacklist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz']
    return " ".join(cfg)

def _apply_scale(img: np.ndarray, rel: Dict[str, Any]) -> np.ndarray:
    s = rel.get('scale')
    try:
        s = float(s) if s is not None else 1.0
    except Exception:
        s = 1.0
    if s and s != 1.0:
        return cv2.resize(img, dsize=None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
    return img

def _result_to_dict(r: Any) -> Dict[str, Any]:
    if hasattr(r, 'to_dict'):
        return r.to_dict()
    if hasattr(r, '__dict__') and hasattr(r, 'text'):
        bbox = getattr(r, 'bounding_box', (0,0,1,1))
        x, y, w, h = bbox if isinstance(bbox, (list, tuple)) and len(bbox)==4 else (0,0,1,1)
        return {
            "text": getattr(r, "text", ""),
            "confidence": float(getattr(r, "confidence", 0.0)),
            "bbox": [int(x), int(y), int(w), int(h)],
            "language": getattr(r, "language", ""),
            "page_number": int(getattr(r, "page_number", 1)),
        }
    if isinstance(r, dict):
        return r
    return {"text": str(r)}

class TemplateExtractor:
    """Crop ROIs from a known template and run the appropriate OCR engine per ROI."""
    def __init__(self, templates_path: str = 'assets/templates/morocco_templates.json'):
        self.templates_path = Path(templates_path)
        with open(self.templates_path, 'r', encoding='utf-8-sig') as f:
            self.templates: Dict[str, Any] = json.load(f)

    def _abs_box(self, H: int, W: int, rel: Dict[str, float]) -> Tuple[int,int,int,int]:
        x = int(rel['x'] * W); y = int(rel['y'] * H)
        w = int(rel['w'] * W); h = int(rel['h'] * H)
        x = max(0, min(x, W-1)); y = max(0, min(y, H-1))
        w = max(1, min(w, W-x)); h = max(1, min(h, H-y))
        return x, y, w, h

    def _run_engine(self, engine: Any, crop: np.ndarray, config: str):
        try:
            return engine.process_document(crop, config=config)
        except TypeError:
            try:
                return engine.process_document(crop, config=config)
            except TypeError:
                try:
                    return engine.process_document(crop)
                except TypeError:
                    return engine.process_document(crop)

    def run(self, image: np.ndarray, template_key: str, engines: Dict[str, Any]) -> Dict[str, Any]:
        if template_key not in self.templates:
            raise KeyError(f"Unknown template '{template_key}' in {self.templates_path}")
        tpl = self.templates[template_key]
        H, W = image.shape[:2]
        out: Dict[str, Any] = {'fields': {}, 'raw': {}, 'metadata': {}}

        for section, fields in tpl['regions'].items():
            for name, rel in fields.items():
                x, y, w, h = self._abs_box(H, W, rel)
                crop = image[y:y+h, x:x+w]
                crop = _apply_scale(crop, rel)
                config = _build_tess_config(rel)

                # Check if this is a receipt field
                if name == 'receipt_no':
                    lang_key = 'receipt'
                else:
                    lang_key = rel.get('lang')
                    if not lang_key:
                        is_ar = (section == 'title' and name == 'ar') or any('\u0600' <= ch <= '\u06FF' for ch in name)
                        lang_key = 'arabic' if is_ar else 'french'

                engine = engines.get(lang_key) or engines.get('hybrid')
                if engine is None:
                    raise RuntimeError(f"No OCR engine available for {lang_key}")

                results = self._run_engine(engine, crop, config)

                best_text, best_conf, best_area = '', 0.0, 1
                safe_raw: List[Dict[str, Any]] = []
                for r in results:
                    rd = _result_to_dict(r)
                    safe_raw.append(rd)
                    text = rd.get('text', '')
                    conf = float(rd.get('confidence', 0.0))
                    bx = rd.get('bbox', (0,0,1,1))
                    x0, y0, w0, h0 = bx if isinstance(bx, (list, tuple)) and len(bx)==4 else (0,0,1,1)
                    area = max(1, int(w0) * int(h0))
                    if conf*area > best_conf*best_area:
                        best_text, best_conf, best_area = text, conf, area

                # Calculate confidence from digit-containing tokens
                digitish = []
                for rd in safe_raw:
                    t = rd.get("text", "")
                    if any(ch.isdigit() for ch in t) or "/" in t or "-" in t:
                        digitish.append(float(rd.get("confidence", 0.0)))

                # Use median confidence from digit tokens if available
                if digitish:
                    best_conf = sorted(digitish)[len(digitish)//2]  # median is robust

                # Build line-level candidates
                joined = " ".join([rd.get("text","") for rd in safe_raw]).strip()
                digits_only = re.sub(r"[^\d/-]+", "", joined)

                candidates = []
                if joined:
                    candidates.append(("joined", joined, best_conf))
                if digits_only:
                    candidates.append(("digits", digits_only, best_conf + 0.1))  # tiny bias to prefer numeric
                if best_text:
                    candidates.append(("token", best_text, best_conf))

                chosen_text = ""
                chosen_conf = 0.0
                chosen_norm = {"type": "text", "value": "", "valid": False}

                for _, txt, c in candidates:
                    nrm = normalize_field(f"{section}.{name}", txt)
                    # prefer valid, then higher conf, then longer text
                    score = (1 if nrm.get("valid") else 0, c, len(txt))
                    if score > (1 if chosen_norm.get("valid") else 0, chosen_conf, len(chosen_text)):
                        chosen_text, chosen_conf, chosen_norm = txt, c, nrm

                norm = chosen_norm
                best_text = chosen_text
                best_conf = chosen_conf

                out['fields'][f"{section}.{name}"] = {
                    'value': best_text,
                    'norm': norm.get('value'),
                    'valid': bool(norm.get('valid')),
                    'type': norm.get('type'),
                    'conf': best_conf,
                    'lang': lang_key,
                    'bbox': [x, y, w, h],
                }
                out['raw'].setdefault(lang_key, []).extend(safe_raw)

        out['metadata'] = {
            'template_name': tpl.get('name'),
            'template_name_ar': tpl.get('name_ar'),
            'template_version': tpl.get('template_version', '1.0'),
            'required_fields': tpl.get('required_fields', []),
        }
        return out



