import pytesseract
from pytesseract import Output
import numpy as np
import cv2
from typing import List, Optional
import re

from .base import BaseOCREngine, OCRResult


class FrenchOCR(BaseOCREngine):
    """Specialized OCR engine for French text in Moroccan administrative documents"""

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        self.last_results: List[OCRResult] = []
        self.lang_code = "fra"

        # Morocco-specific French patterns
        self.common_patterns = {
            "prefecture": re.compile(r"pr[Ã©e]fecture\s+d[e']\s+\w+", re.IGNORECASE),
            "province": re.compile(r"province\s+d[e']\s+\w+", re.IGNORECASE),
            "commune": re.compile(
                r"commune\s+(?:urbaine|rurale)?\s+d[e']\s+\w+", re.IGNORECASE
            ),
        }

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for optimal French text recognition
        Specialized for Moroccan administrative documents
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)

        # Use Otsu's thresholding for better text separation
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return binary

    def postprocess_text(self, text: str) -> str:
        """
        Post-process French OCR results
        Applies Morocco-specific corrections and formatting
        """
        if not text.strip():
            return text

        # Fix common OCR errors in French text
        text = text.replace("|", "I")  # Common confusion
        text = text.replace("1", "l")  # Number 1 vs letter l

        # Check for administrative patterns
        for pattern_name, pattern in self.common_patterns.items():
            if pattern.search(text):
                self.logger.info(f"Found administrative pattern: {pattern_name}")

        return text.strip()

    def process_document(self, image: np.ndarray) -> List[OCRResult]:
        """
        Process document using French OCR
        """
        # Validate language support
        if not self.validate_language("fra"):
            raise RuntimeError("French language support not installed in Tesseract")

        # Process the image
        d = pytesseract.image_to_data(
            image, lang="fra", config="--psm 6 --oem 1", output_type=Output.DICT
        )

        # Parse and return results
        return self._parse_data_dict_to_results(d, "fra") or []
