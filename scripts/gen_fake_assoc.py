from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, argparse
import arabic_reshaper
from bidi.algorithm import get_display


def to_abs(W, H, rel):
    return (int(rel["x"] * W), int(rel["y"] * H), int(rel["w"] * W), int(rel["h"] * H))


def put_text(draw, box, txt, font, rtl=False):
    x, y, w, h = box
    if rtl:
        shaped = arabic_reshaper.reshape(txt)
        txt = get_display(shaped)
        tw, th = draw.textbbox((0, 0), txt, font=font)[2:]
        draw.text((x + w - tw - 8, y + (h - th) // 2), txt, font=font, fill="black")
    else:
        tw, th = draw.textbbox((0, 0), txt, font=font)[2:]
        draw.text((x + 8, y + (h - th) // 2), txt, font=font, fill="black")


def main(out_path):
    W, H = 1600, 1100
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    data = json.load(
        open("assets/templates/morocco_templates.json", "r", encoding="utf-8-sig")
    )
    tpl = data["assoc_receipt"]["regions"]

    fr_font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 46)
    ar_font_path = Path("assets/fonts/NotoNaskhArabic-Regular.ttf")
    ar_font = (
        ImageFont.truetype(str(ar_font_path), 50) if ar_font_path.exists() else fr_font
    )

    title_fr = to_abs(W, H, tpl["title"]["fr"])
    title_ar = to_abs(W, H, tpl["title"]["ar"])
    head_fr = to_abs(W, H, tpl["header"]["commune.fr"])
    head_ar = to_abs(W, H, tpl["header"]["commune.ar"])
    body_fr = to_abs(W, H, tpl["body"]["association_name.fr"])
    body_ar = to_abs(W, H, tpl["body"]["association_name.ar"])
    receipt = to_abs(W, H, tpl["body"]["receipt_no"])
    date_fr = to_abs(W, H, tpl["body"]["date.fr"])

    # light guide boxes (optional)
    for b in [title_fr, title_ar, head_fr, head_ar, body_fr, body_ar, receipt, date_fr]:
        x, y, w, h = b
        draw.rectangle([x, y, x + w, y + h], outline="gray")

    put_text(draw, title_fr, "PRÉFECTURE DE CASABLANCA – ARRONDISSEMENT", fr_font)
    put_text(draw, title_ar, "ولاية الدار البيضاء", ar_font, rtl=True)

    put_text(draw, head_fr, "Commune de Casablanca", fr_font)
    put_text(draw, head_ar, "جماعة الدار البيضاء", ar_font, rtl=True)

    put_text(draw, body_fr, "Association AMAL pour le Développement", fr_font)
    put_text(draw, body_ar, "جمعية الأمل للتنمية", ar_font, rtl=True)

    put_text(draw, receipt, "Reçu Nº 2024/1234", fr_font)
    put_text(draw, date_fr, "12/08/2025", fr_font)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print("Saved:", out_path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="samples/assoc_fake.png")
    args = ap.parse_args()
    main(args.out)
