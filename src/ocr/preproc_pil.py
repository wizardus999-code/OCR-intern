from typing import List, Dict, Any
from statistics import median
from PIL import Image, ImageOps, ImageFilter

def otsu_threshold(gray: "Image.Image") -> int:
    hist = gray.histogram()
    total = sum(hist)
    sum_total = sum(i*h for i, h in enumerate(hist))
    sum_bg = 0
    w_bg = 0
    var_max = -1.0
    threshold = 127
    for t in range(256):
        w_bg += hist[t]
        if w_bg == 0:
            continue
        w_fg = total - w_bg
        if w_fg == 0:
            break
        sum_bg += t * hist[t]
        mean_bg = sum_bg / w_bg
        mean_fg = (sum_total - sum_bg) / w_fg
        var_between = w_bg * w_fg * (mean_bg - mean_fg) ** 2
        if var_between > var_max:
            var_max = var_between
            threshold = t
    return threshold

def apply_preproc(img: "Image.Image", cfg: Dict[str, Any]) -> "Image.Image":
    g = img.convert("L")
    scale = float(cfg.get("resize", 1.0))
    if scale and abs(scale - 1.0) > 1e-3:
        w = max(1, int(g.width * scale))
        h = max(1, int(g.height * scale))
        g = g.resize((w, h), Image.LANCZOS)
    if cfg.get("binarize", "none") == "otsu":
        thr = otsu_threshold(g)
        g = g.point(lambda p, t=thr: 255 if p >= t else 0)
    if bool(cfg.get("invert", False)):
        g = ImageOps.invert(g)
    dilate_n = int(cfg.get("dilate", 0))
    for _ in range(max(0, dilate_n)):
        g = g.filter(ImageFilter.MaxFilter(3))
    return g

def median_digit_confidence(tokens: List) -> float:
    vals = []
    for t in tokens:
        # support dict- and object-like tokens
        txt = getattr(t, "text", None)
        if txt is None and isinstance(t, dict):
            txt = t.get("text", "")
        txt = txt or ""
        if any(ch.isdigit() for ch in txt):
            conf = getattr(t, "confidence", None)
            if conf is None and isinstance(t, dict):
                conf = t.get("confidence", t.get("conf", 0.0))
            try:
                vals.append(float(conf))
            except Exception:
                pass
    if not vals:
        return 0.0
    return float(median(vals))
