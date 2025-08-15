import os, pathlib, re

import cv2
import pytest
import pytesseract

from src.ocr.hybrid import HybridOCR

# Repo + fixtures
ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "images"

# Make sure tessdata + tesseract.exe are visible to tests
def pytest_sessionstart(session):
    td = ROOT / "tessdata"
    if td.exists():
        os.environ["TESSDATA_PREFIX"] = str(td)
    tesseract_cli = pathlib.Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if tesseract_cli.exists():
        os.environ["PATH"] = f"{tesseract_cli.parent};" + os.environ.get("PATH", "")

REAL_SAMPLES = [
    ("test_fr.png",        "fra"),
    ("engagement_cert.jpg","ara"),
    ("darpa_arabic.png",   "ara"),
]

def _has_arabic(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text))

def _has_latin(text: str) -> bool:
    return bool(re.search(r"\b[A-Za-z]{4,}\b", text))

def _langs_ok() -> set[str]:
    try:
        return set(pytesseract.get_languages() or [])
    except Exception:
        return set()

@pytest.mark.parametrize("fname, expected", REAL_SAMPLES)
def test_real_images_smoke(fname: str, expected: str):
    langs = _langs_ok()
    if expected not in langs:
        pytest.skip(f"Missing tessdata for '{expected}'. Installed: {sorted(langs)}")

    img_path = FIXTURES / fname
    assert img_path.exists(), f"Missing fixture: {img_path}"

    img = cv2.imread(str(img_path))
    assert img is not None and img.size > 0, "Could not read image"

    ocr = HybridOCR()
    results = ocr.process_document(img)

    # tolerate different dict keys
    french = results.get("french", []) or results.get("fra", [])
    arabic = results.get("arabic", []) or results.get("ara", [])
    text = " ".join([r.text for r in (french + arabic)]).strip()

    assert text, "OCR returned no text"

    if expected == "ara":
        assert _has_arabic(text), f"Expected Arabic characters for {fname}, got: {text[:120]!r}"
    else:
        assert _has_latin(text), f"Expected Latin words for {fname}, got: {text[:120]!r}"