import os
import sys
from pathlib import Path

# Configure python path for imports
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

# Configure stdout for UTF-8
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Standard imports
import argparse  # noqa: E402
import json  # noqa: E402
import cv2  # noqa: E402
import numpy as np  # noqa: E402
import pytesseract  # noqa: E402
from pytesseract import Output  # noqa: E402
from src.templates.template_extractor import TemplateExtractor  # noqa: E402

# Make tessdata resilient
repo_tessdata = Path(__file__).resolve().parents[1] / "tessdata"
if repo_tessdata.exists():
    os.environ.setdefault("TESSDATA_PREFIX", str(repo_tessdata))

# Ensure tessdata is found (you already set this, but just in case)
repo_root = Path(__file__).resolve().parents[1]
os.environ.setdefault("TESSDATA_PREFIX", str(repo_root / "tessdata"))

LANG_MAP = {"french": "fra", "arabic": "ara"}


class TesseractEngine:
    def __init__(self, lang_key: str):
        self.lang_key = lang_key
        self.tess_lang = LANG_MAP.get(lang_key, "eng")

    def _ocr(self, image: np.ndarray, config: str = ""):
        d = pytesseract.image_to_data(
            image, lang=self.tess_lang, config=config, output_type=Output.DICT
        )
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
            left = int(d.get("left", [0] * n)[i] or 0)
            top = int(d.get("top", [0] * n)[i] or 0)
            width = int(d.get("width", [1] * n)[i] or 1)
            height = int(d.get("height", [1] * n)[i] or 1)
            out.append(
                {
                    "text": txt,
                    "confidence": conf,
                    "bbox": [left, top, width, height],
                    "language": self.lang_key,
                }
            )
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
    ap.add_argument(
        "--templates-json", default="assets/templates/morocco_templates.json"
    )
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

    result = extractor.run(img, args.template, engines)
    # Output the results as UTF-8 JSON
    out = {"metadata": result.get("metadata"), "fields": result.get("fields")}
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
