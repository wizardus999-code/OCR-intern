import pytesseract
from pytesseract import Output
import arabic_reshaper
from bidi.algorithm import get_display
import numpy as np
import cv2
from typing import List, Optional, Dict, Any

from .base import BaseOCREngine, OCRResult


class ArabicOCR(BaseOCREngine):
    """Specialized OCR engine for Arabic text in Moroccan administrative documents"""

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        self.last_results: List[OCRResult] = []

    def _tess_config_ar(self, psm: int = 6) -> str:
        # LSTM only, keep spaces, and avoid Latin bleed-through
        return (
            f"--psm {psm} --oem 1 "
            "-c preserve_interword_spaces=1 "
            "-c tessedit_char_blacklist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        )

    def _parse_data_dict_to_results(self, d: Dict[str, Any]) -> List[OCRResult]:
        out = []
        n = len(d.get("text", []))
        for i in range(n):
            text = (d["text"][i] or "").strip()
            try:
                conf = float(d["conf"][i])
            except Exception:
                conf = -1.0
            if text and conf >= 0:
                out.append(
                    OCRResult(
                        text=text,
                        confidence=conf,
                        bbox=(d["left"][i], d["top"][i], d["width"][i], d["height"][i]),
                        lang="ara",
                        page=d.get("page_num", [1])[i],
                    )
                )
        return out

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
        results = self._parse_data_dict_to_results(d)

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
            results = self._parse_data_dict_to_results(d2)

        return results or []

    def get_confidence(self) -> float:
        """Return average confidence of last OCR operation"""
        if not self.last_results:
            return 0.0
        return np.mean([r.confidence for r in self.last_results])

    def process(self, image) -> List[OCRResult]:
        """Process image and extract Arabic text"""
        # Configure Tesseract for Arabic
        config = r"--oem 3 --psm 3 -l ara"

        # Perform OCR
        result = pytesseract.image_to_data(
            image, config=config, output_type=pytesseract.Output.DICT
        )

        # Process results
        ocr_results: List[OCRResult] = []
        confidences = []

        for i in range(len(result["text"])):
            if int(result["conf"][i]) > -1:  # Filter out low confidence results
                text = result["text"][i]
                conf = float(result["conf"][i])

                if text.strip():  # Only process non-empty text
                    # Reshape Arabic text for proper display
                    reshaped_text = arabic_reshaper.reshape(text)
                    bidi_text = get_display(reshaped_text)

                    ocr_result = OCRResult(
                        text=bidi_text,
                        confidence=conf,
                        bbox=(
                            result["left"][i],
                            result["top"][i],
                            result["width"][i],
                            result["height"][i],
                        ),
                        lang="ara",
                        page=result.get("page_num", [1])[i],
                    )
                    ocr_results.append(ocr_result)
                    confidences.append(conf)

        # Update confidence score
        self.confidence = np.mean(confidences) if confidences else 0.0
        self.last_results = ocr_results

        return ocr_results

    def get_confidence(self):
        """Return confidence score of last OCR operation"""
        return self.confidence
