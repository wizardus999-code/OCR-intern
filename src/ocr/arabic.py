import pytesseract
from pytesseract import Output
import arabic_reshaper
from bidi.algorithm import get_display
import numpy as np
import cv2
from typing import List, Optional

from .base import BaseOCREngine, OCRResult


class ArabicOCR(BaseOCREngine):
    """Specialized OCR engine for Arabic text in Moroccan administrative documents"""

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        self.last_results: List[OCRResult] = []
        self.lang_code = "ara"

    def _tess_config_ar(self, psm: int = 6) -> str:
        # LSTM only, keep spaces, and avoid Latin bleed-through
        return (
            f"--psm {psm} --oem 1 "
            "-c preserve_interword_spaces=1 "
            "-c tessedit_char_blacklist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        )

        # Morocco-specific Arabic patterns
        self.common_phrases = {
            "Ø§Ù„Ù…Ù…Ù„ÙƒØ© Ø§Ù„Ù…ØºØ±Ø¨ÙŠØ©": "royaume du maroc",
            "ÙˆØ²Ø§Ø±Ø©": "ministÃ¨re",
            "Ø¹Ù…Ø§Ù„Ø©": "prÃ©fecture",
        }

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for optimal Arabic text recognition
        Specialized for Moroccan administrative documents
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Apply adaptive thresholding for better text separation
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,  # Block size
            2,  # C constant
        )

        # Remove noise while preserving Arabic text characteristics
        denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)

        # Enhance contrast for better character recognition
        enhanced = cv2.equalizeHist(denoised)

        return enhanced

    def postprocess_text(self, text: str) -> str:
        """
        Post-process Arabic OCR results
        Applies Morocco-specific corrections and formatting
        """
        if not text.strip():
            return text

        # Reshape Arabic text for proper display
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)

        # Apply Morocco-specific corrections
        for arabic, french in self.common_phrases.items():
            if arabic in bidi_text:
                # Log the detection of common administrative terms
                self.logger.info(f"Found common phrase: {arabic} ({french})")

        return bidi_text

    def process_document(self, image: np.ndarray) -> List[OCRResult]:
        """
        Process document using Arabic OCR with retry logic
        """
        # Validate language support
        if not self.validate_language("ara"):
            raise RuntimeError("Arabic language support not installed in Tesseract")

        # Preprocess the image
        processed = self.preprocess_image(image)

        # 1st pass (psm 6)
        d = pytesseract.image_to_data(
            processed,
            lang="ara",
            config=self._tess_config_ar(6),
            output_type=Output.DICT,
        )
        results = self._parse_data_dict_to_results(d, "ara")

        # Fallback: up-scale + psm 7 if nothing recognized
        if not results:
            try:
                bigger = cv2.resize(
                    processed, None, fx=1.3, fy=1.3, interpolation=cv2.INTER_CUBIC
                )
            except Exception:
                bigger = processed
            d2 = pytesseract.image_to_data(
                bigger,
                lang="ara",
                config=self._tess_config_ar(7),
                output_type=Output.DICT,
            )
            results = self._parse_data_dict_to_results(d2, "ara")

        return results or []

    def process(self, image) -> List[OCRResult]:
        """Process image and extract Arabic text with bidirectional text handling"""
        results = super().process(image)

        # Apply Arabic-specific text processing
        for result in results:
            reshaped_text = arabic_reshaper.reshape(result.text)
            result.text = get_display(reshaped_text)

        return results
