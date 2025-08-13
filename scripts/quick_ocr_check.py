import os, shutil
from pathlib import Path
import cv2, numpy as np
import pytesseract
from pytesseract import Output

# Make Tesseract + tessdata resilient
repo_tessdata = Path(__file__).resolve().parents[1] / "tessdata"
if repo_tessdata.exists():
    os.environ.setdefault("TESSDATA_PREFIX", str(repo_tessdata))

if shutil.which("tesseract") is None:
    p = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if p.exists():
        pytesseract.pytesseract.tesseract_cmd = str(p)

print("Tesseract:", pytesseract.get_tesseract_version())
try:
    langs = set(pytesseract.get_languages(config=""))
except Exception:
    langs = set()
print("Installed languages:", sorted(langs))

# Build a clean synthetic French image
W, H = 900, 220
img = np.full((H, W, 3), 255, np.uint8)
cv2.putText(img, "Bonjour, Préfecture 123", (30, 120),
            cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0,0,0), 3, cv2.LINE_AA)

# Simple preprocessing (grayscale + Otsu)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

def ocr_with_conf(image, lang):
    d = pytesseract.image_to_data(image, lang=lang, output_type=Output.DICT)
    text = " ".join([str(w) for w in d["text"] if str(w).strip()])
    confs = []
    for c in d["conf"]:
        try:
            v = float(c)  # handles "96", 96, 96.0, "-1"
        except Exception:
            continue
        if v >= 0:
            confs.append(v)
    conf = sum(confs)/len(confs) if confs else -1.0
    return text, conf

# Run FRA
txt_fra, conf_fra = ocr_with_conf(th, "fra")
print(f"[fra] conf={conf_fra:.1f}  text={txt_fra}")

# ENG only if installed
if "eng" in langs:
    txt_eng, conf_eng = ocr_with_conf(th, "eng")
    print(f"[eng] conf={conf_eng:.1f}  text={txt_eng}")
else:
    print("[eng] skipped (not installed)")

# ARA only if installed
if "ara" in langs:
    txt_ara, conf_ara = ocr_with_conf(th, "ara")
    print(f"[ara] conf={conf_ara:.1f}  text={txt_ara}")
else:
    print("[ara] skipped (not installed)")

# Save the test image
out_path = Path("tmp_ocr_test.png")
cv2.imwrite(str(out_path), img)
print("Saved:", out_path.resolve())
