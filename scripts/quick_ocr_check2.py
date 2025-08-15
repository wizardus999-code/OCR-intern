import os, shutil
from pathlib import Path
import numpy as np
import pytesseract
from pytesseract import Output
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

# Make Tesseract + tessdata reliable
repo_root = Path(__file__).resolve().parents[1]
os.environ.setdefault("TESSDATA_PREFIX", str(repo_root / "tessdata"))
tess_exe = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if shutil.which("tesseract") is None and tess_exe.exists():
    pytesseract.pytesseract.tesseract_cmd = str(tess_exe)

print("Tesseract:", pytesseract.get_tesseract_version())
try:
    langs = set(pytesseract.get_languages(config=""))
except Exception:
    langs = set()
print("Installed languages:", sorted(langs))

# --- Synthesize a 300-DPI style canvas with 2 lines (FR + AR) ---
W, H = 1600, 500
img = Image.new("RGB", (W, H), "white")
draw = ImageDraw.Draw(img)

font_fr = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 72)
font_ar_path = repo_root / "assets" / "fonts" / "NotoNaskhArabic-Regular.ttf"
font_ar = (
    ImageFont.truetype(str(font_ar_path), 72) if font_ar_path.exists() else font_fr
)

# French (top)
text_fr = "Bonjour, Préfecture de Casablanca"
y_fr = 120
draw.text((80, y_fr), text_fr, font=font_fr, fill="black")

# Arabic (bottom, proper shaping + RTL, right-aligned)
raw_ar = "ولاية الدار البيضاء"
shaped = arabic_reshaper.reshape(raw_ar)
text_ar = get_display(shaped)
w_ar, h_ar = draw.textbbox((0, 0), text_ar, font=font_ar)[2:]
y_ar = 300
draw.text((W - w_ar - 80, y_ar), text_ar, font=font_ar, fill="black")

np_img = np.array(img)

# --- ROIs for each line (so PSM 7 is valid) ---
fra_roi = np_img[y_fr - 30 : y_fr + 120, 60 : W - 60]  # adjust margins if needed
ara_roi = np_img[y_ar - 30 : y_ar + 120, 60 : W - 60]


def ocr_with_conf(image, lang, config_extra=""):
    # Pretend 300 DPI so Tesseract doesn't guess low DPI
    config = f"--oem 1 --psm 7 -c user_defined_dpi=300 {config_extra}".strip()
    d = pytesseract.image_to_data(
        image, lang=lang, config=config, output_type=Output.DICT
    )
    text = " ".join([str(w) for w in d["text"] if str(w).strip()])
    confs = []
    for c in d["conf"]:
        try:
            v = float(c)
        except Exception:
            continue
        if v >= 0:
            confs.append(v)
    conf = sum(confs) / len(confs) if confs else -1.0
    return text, conf


# French line
txt_fra, conf_fra = ocr_with_conf(fra_roi, "fra")
print(f"[fra single-line] conf={conf_fra:.1f}  text={txt_fra}")

# Arabic line (preserve spaces helps Arabic)
if "ara" in langs:
    txt_ara, conf_ara = ocr_with_conf(
        ara_roi, "ara", config_extra="-c preserve_interword_spaces=1"
    )
    print(f"[ara single-line] conf={conf_ara:.1f}  text={txt_ara}")
else:
    print("[ara] skipped (not installed)")

# Save image to inspect
out_path = Path("tmp_ocr_test2.png")
Image.fromarray(np_img).save(out_path)
print("Saved:", out_path.resolve())
