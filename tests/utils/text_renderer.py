import numpy as np
import cv2
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
from typing import Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTO_NASKH_FONT_PATH = REPO_ROOT / "assets" / "fonts" / "NotoNaskhArabic-Regular.ttf"

class TextRenderer:
    """Helper class for rendering text in different languages"""
    
    def __init__(self, size_scale: float = 1.0):
        self.size_scale = size_scale
        self.ar_font_path = str(NOTO_NASKH_FONT_PATH)
        self.la_font_path = r"C:\Windows\Fonts\arial.ttf"

    def _font(self, size: int, arabic: bool) -> ImageFont.FreeTypeFont|ImageFont.ImageFont:
        path = self.ar_font_path if arabic else self.la_font_path
        size = max(10, int(size * self.size_scale))
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            # fallback bitmap font (no Arabic shaping, but better than nothing)
            return ImageFont.load_default()

    def draw_text(
        self,
        image_bgr: np.ndarray,
        xy: Tuple[int, int],
        text: str,
        font_size: int = 32,
        arabic: bool = False,
        color: Tuple[int, int, int] = (0, 0, 0)
    ) -> np.ndarray:
        """Draws text onto a BGR image, handling Arabic shaping+RTL when requested."""
        if arabic and text.strip():
            text = get_display(arabic_reshaper.reshape(text))

        # Convert BGR -> RGB for Pillow
        rgb = image_bgr[..., ::-1]
        pil_img = Image.fromarray(rgb)
        draw = ImageDraw.Draw(pil_img)
        font = self._font(font_size, arabic=arabic)
        draw.text(xy, text, fill=(color[2], color[1], color[0]), font=font)

        # Back to BGR
        out = np.array(pil_img)[..., ::-1]
        return out
