# image_utils.py (repo root)
try:
    from src.ocr.utils import ensure_3ch  # preferred
except Exception:  # ultra-safe fallback (shouldn't happen if pythonpath=src)
    import cv2
    import numpy as np
    def ensure_3ch(img: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.ndim == 2 else img

__all__ = ["ensure_3ch"]
