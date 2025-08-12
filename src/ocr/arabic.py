import pytesseract
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
        
        # Morocco-specific Arabic patterns
        self.common_phrases = {
            'المملكة المغربية': 'royaume du maroc',
            'وزارة': 'ministère',
            'عمالة': 'préfecture'
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
            2    # C constant
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
        Process a Moroccan administrative document with Arabic text
        """
        # Validate language support
        if not self.validate_language('ara'):
            raise RuntimeError("Arabic language support not installed in Tesseract")
            
        # Process with Arabic-specific settings
        results = self.process_image(image, lang='ara')
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
        """Process image and extract Arabic text"""
        # Configure Tesseract for Arabic
        config = r'--oem 3 --psm 3 -l ara'
        
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
                    # Reshape Arabic text for proper display
                    reshaped_text = arabic_reshaper.reshape(text)
                    bidi_text = get_display(reshaped_text)
                    
                    ocr_result = OCRResult(
                        text=bidi_text,
                        confidence=conf,
                        bounding_box=(
                            result["left"][i],
                            result["top"][i],
                            result["width"][i],
                            result["height"][i]
                        ),
                        language='ara',
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
