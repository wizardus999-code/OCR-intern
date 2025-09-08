# src/ocr/utils.py
import cv2
import numpy as np

def ensure_3ch(img: np.ndarray) -> np.ndarray:
    """Guarantee BGR 3-channel array for safe pasting/assignment."""
    if img is None:
        return img
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.ndim == 2 else img

# Arabic digit normalization
ARABIC_INDIC = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
EXT_ARABIC_INDIC = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

def arabic_indic_to_ascii(s: str) -> str:
    """Convert Arabic-Indic and Extended Arabic-Indic digits to ASCII."""
    if not s:
        return s
    return s.translate(ARABIC_INDIC).translate(EXT_ARABIC_INDIC)
