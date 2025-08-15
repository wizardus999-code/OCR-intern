# src/ocr/utils.py
import cv2
import numpy as np

def ensure_3ch(img: np.ndarray) -> np.ndarray:
    """Guarantee BGR 3-channel array for safe pasting/assignment."""
    if img is None:
        return img
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.ndim == 2 else img
