import pytesseract
import numpy as np
import cv2
from typing import List, Optional, Dict, Pattern
import re

from .base import BaseOCREngine, OCRResult

class FrenchOCR(BaseOCREngine):
    """Specialized OCR engine for French text in Moroccan administrative documents"""
    
    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        self.last_results: List[OCRResult] = []
        
        # Morocco-specific French patterns
        self.common_patterns = {
            'prefecture': re.compile(r"pr[ée]fecture\s+d[e']\s+\w+", re.IGNORECASE),
            'province': re.compile(r"province\s+d[e']\s+\w+", re.IGNORECASE),
            'commune': re.compile(r"commune\s+(?:urbaine|rurale)?\s+d[e']\s+\w+", re.IGNORECASE)
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
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (3,3), 0)
        
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
        text = text.replace('|', 'I')  # Common confusion
        text = text.replace('1', 'l')  # Number 1 vs letter l
        
        # Check for administrative patterns
        for pattern_name, pattern in self.common_patterns.items():
            if pattern.search(text):
                self.logger.info(f"Found administrative pattern: {pattern_name}")
                
        return text.strip()
        
    def process_document(self, image: np.ndarray) -> List[OCRResult]:
        """
        Process a Moroccan administrative document with French text
        """
        # Validate language support
        if not self.validate_language('fra'):
            raise RuntimeError("French language support not installed in Tesseract")
            
        # Process with French-specific settings
        results = self.process_image(
            image,
            lang='fra',
            psm=6  # Assume uniform block of text
        )
        self.last_results = results
        
        # Calculate overall confidence
        if results:
            avg_confidence = np.mean([r.confidence for r in results])
            self.logger.info(f"Document processed with average confidence: {avg_confidence:.2f}%")
            
        return results
        
    def get_confidence(self) -> float:
        """Return average confidence of last OCR operation"""
        if not self.last_results:
            return 0.0
        return np.mean([r.confidence for r in self.last_results])
        
    def process(self, image):
        """Process image and extract French text"""
        # Configure Tesseract for French
        config = r'--oem 3 --psm 3 -l fra'
        
        # Perform OCR
        result = pytesseract.image_to_data(
            image,
            config=config,
            output_type=pytesseract.Output.DICT
        )
        
        # Process results
        texts = []
        confidences = []
        
        for i in range(len(result["text"])):
            if int(result["conf"][i]) > -1:  # Filter out low confidence results
                text = result["text"][i]
                conf = float(result["conf"][i])
                
                if text.strip():  # Only process non-empty text
                    texts.append({
                        'text': text,
                        'confidence': conf,
                        'bbox': (
                            result["left"][i],
                            result["top"][i],
                            result["width"][i],
                            result["height"][i]
                        )
                    })
                    confidences.append(conf)
        
        # Update confidence score
        self.confidence = np.mean(confidences) if confidences else 0.0
        self.last_result = texts
        
        return texts
    
    def get_confidence(self):
        """Return confidence score of last OCR operation"""
        return self.confidence
