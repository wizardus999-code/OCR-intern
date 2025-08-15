"""OCR configuration optimized for receipt numbers."""
from .base import BaseOCREngine
from typing import List
import cv2
import numpy as np

class ReceiptOCR(BaseOCREngine):
    """OCR engine optimized for receipt numbers"""
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Enhanced preprocessing for receipt numbers"""
        processed = super().preprocess_image(image)
        
        # Additional preprocessing specific to receipt numbers
        kernel = np.ones((2,2), np.uint8)
        processed = cv2.erode(processed, kernel, iterations=1)
        processed = cv2.threshold(processed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        return processed

    def postprocess_text(self, text: str) -> str:
        """Clean up receipt number text"""
        # Remove unwanted characters
        text = ''.join(c for c in text if c.isdigit() or c == '/')
        return text

    def process_image(self, image: np.ndarray, lang: str, psm: int = 7) -> List:
        """Process with settings optimized for receipt numbers"""
        # Use --psm 7 (treat as single line) with increased DPI
        dpi = 300
        scaled = cv2.resize(image, None, fx=dpi/72, fy=dpi/72, interpolation=cv2.INTER_CUBIC)
        return super().process_image(scaled, lang, psm=psm)
