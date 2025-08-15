import cv2
import numpy as np

def ensure_3ch(img: np.ndarray) -> np.ndarray:
    """Convert image to 3 channels if it's grayscale."""
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.ndim == 2 else img
