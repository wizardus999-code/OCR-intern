import os, sys, argparse, json
from pathlib import Path
import cv2
import numpy as np
import pytesseract
from pytesseract import Output

# Allow repo imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Make tessdata resilient
repo_tessdata = Path(__file__).resolve().parents[1] / "tessdata"
if repo_tessdata.exists():
    os.environ.setdefault("TESSDATA_PREFIX", str(repo_tessdata))

from src.templates.template_extractor import TemplateExtractor

# Ensure tessdata is found (you already set this, but just in case)
repo_root = Path(__file__).resolve().parents[1]
os.environ.setdefault("TESSDATA_PREFIX", str(repo_root / "tessdata"))

LANG_MAP = {"french": "fra", "arabic": "ara"}

class TesseractEngine:
    def __init__(self, lang_key: str):
        self.lang_key = lang_key
        self.tess_lang = LANG_MAP.get(lang_key, "eng")

    def _ocr(self, image: np.ndarray, config: str = ""):
        d = pytesseract.image_to_data(image, lang=self.tess_lang, config=config, output_type=Output.DICT)
        out = []
        n = len(d["text"])
        for i in range(n):
            txt = str(d["text"][i] or "").strip()
            if not txt:
                continue
            # conf can be int or "-1"
            try:
                conf = float(d["conf"][i])
            except Exception:
                conf = 0.0
            left = int(d.get("left", [0]*n)[i] or 0)
            top  = int(d.get("top",  [0]*n)[i] or 0)
            width= int(d.get("width",[1]*n)[i] or 1)
            height=int(d.get("height",[1]*n)[i] or 1)
            out.append({
                "text": txt,
                "confidence": conf,
                "bbox": [left, top, width, height],
                "language": self.lang_key
            })
        return out

    # Both signatures supported
    def process_document(self, image: np.ndarray, config: str = ""):
        return self._ocr(image, config=config)

    def process(self, image: np.ndarray, config: str = ""):
        return self._ocr(image, config=config)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True, help="path to scanned receipt/image")
    ap.add_argument("--template", default="assoc_receipt")
    ap.add_argument("--templates-json", default="assets/templates/morocco_templates.json")
    args = ap.parse_args()

    img = cv2.imread(args.image)
    if img is None:
        print(f"Could not read image: {args.image}", file=sys.stderr)
        sys.exit(2)

    extractor = TemplateExtractor(args.templates_json)

    engines = {
        "french": TesseractEngine("french"),
        "arabic": TesseractEngine("arabic"),
        # "hybrid": TesseractEngine("french"),  # optional fallback
    }
    
    # Add receipt OCR for receipt number field
    from src.ocr.receipt import ReceiptOCR
    engines["receipt"] = ReceiptOCR()

    result = extractor.run(img, args.template, engines)
    # Pretty print the normalized fields only
    print(json.dumps({
        "metadata": result.get("metadata"),
        "fields": result.get("fields")
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
