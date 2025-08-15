import pytesseract
import numpy as np
import cv2
import unicodedata
from typing import List, Optional, Dict, Pattern
import re

from .base import BaseOCREngine, OCRResult

class FrenchOCR(BaseOCREngine):
    """Specialized OCR engine for French text in Moroccan administrative documents"""
    
    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        self.last_result = None
        self.last_results: List[OCRResult] = []
        
        # Morocco-specific French patterns
        self.common_patterns = {
            'prefecture': re.compile(r"pr[ée]fecture\s+d[e']\s+\w+", re.IGNORECASE),
            'province': re.compile(r"province\s+d[e']\s+\w+", re.IGNORECASE),
            'commune': re.compile(r"commune\s+(?:urbaine|rurale)?\s+d[e']\s+\w+", re.IGNORECASE)
        }
        
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for optimal French text recognition with accent preservation
        Specialized for Moroccan administrative documents
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Scale to higher DPI for better accent detection
        scale_factor = 300 / 72  # Scale to 300 DPI
        scaled = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, 
                          interpolation=cv2.INTER_CUBIC)
            
        # Multi-stage enhancement
        # First CLAHE pass - global enhancement
        clahe1 = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced1 = clahe1.apply(scaled)
        
        # Second CLAHE pass - local detail enhancement
        clahe2 = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4,4))
        enhanced2 = clahe2.apply(enhanced1)
        
        # Denoise while preserving accent marks
        denoised = cv2.fastNlMeansDenoising(enhanced2,
                                           h=10,
                                           templateWindowSize=7,
                                           searchWindowSize=21)
        
        # Adaptive thresholding for better handling of varying text weights
        binary = cv2.adaptiveThreshold(denoised,
                                     255,
                                     cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY,
                                     11,
                                     2)
        
        # Create kernels for morphological operations
        kernel_vert = cv2.getStructuringElement(cv2.MORPH_RECT, (1,2))
        kernel_horz = cv2.getStructuringElement(cv2.MORPH_RECT, (2,1))
        
        # Vertical and horizontal refinement
        vert = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_vert)
        processed = cv2.morphologyEx(vert, cv2.MORPH_CLOSE, kernel_horz)
        
        # Edge enhancement for better character definition
        edge_enhanced = cv2.addWeighted(denoised, 0.7, processed, 0.3, 0)
        
        return edge_enhanced
        
    def postprocess_text(self, text: str) -> str:
        """
        Post-process French OCR results with accent-agnostic normalization
        """
        # accent-agnostic normalization
        nfkd = unicodedata.normalize("NFKD", text)
        no_accents = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
        return no_accents
        
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
        
    def process(self, image) -> List[OCRResult]:
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
        ocr_results: List[OCRResult] = []
        confidences = []
        
        for i in range(len(result["text"])):
            if int(result["conf"][i]) > -1:  # Filter out low confidence results
                text = result["text"][i]
                conf = float(result["conf"][i])
                
                if text.strip():  # Only process non-empty text
                    ocr_result = OCRResult(
                        text=text,
                        confidence=conf,
                        bounding_box=(
                            result["left"][i],
                            result["top"][i],
                            result["width"][i],
                            result["height"][i]
                        ),
                        language='fra',
                        page_number=result.get('page_num', [1])[i]
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
