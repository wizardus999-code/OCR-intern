from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import pytesseract
import numpy as np
from pathlib import Path
import logging
import os
import cv2
from dataclasses import dataclass

# Configure tessdata path
repo_tessdata = Path(__file__).resolve().parents[2] / "tessdata"

@dataclass
class OCRResult:
    """Structured container for OCR results"""
    text: str
    confidence: float
    bounding_box: Tuple[int, int, int, int]  # x, y, width, height
    language: str
    page_number: int = 1
    
    def to_dict(self) -> Dict:
        """Convert OCR result to dictionary format for serialization"""
        return {
            'text': self.text,
            'confidence': self.confidence,
            'bounding_box': self.bounding_box,
            'language': self.language,
            'page_number': self.page_number
        }

class BaseOCREngine(ABC):
    """Base class for OCR engines with Morocco-specific optimizations"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.confidence = 0.0
        self._initialize_tesseract()
        
    def _initialize_tesseract(self) -> None:
        """Initialize Tesseract with custom configuration"""
        try:
            if self.config_path:
                if not Path(self.config_path).exists():
                    raise FileNotFoundError(f"Tesseract config not found at {self.config_path}")
                pytesseract.pytesseract.tesseract_cmd = self.config_path
        except Exception as e:
            self.logger.error(f"Failed to initialize Tesseract: {str(e)}")
            raise RuntimeError("Tesseract initialization failed") from e

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Gentle denoise & normalize to reduce variance for noisy inputs.
        Keeps it OCR-friendly while making std lower than raw noisy image.
        """
        if image is None or image.size == 0:
            raise ValueError("Invalid image input")

        # to grayscale
        if image.ndim == 3 and image.shape[2] == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Apply bilateral filter to reduce noise while preserving edges
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Reduce local contrast variations
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        equalized = clahe.apply(denoised)
        
        # Further reduce noise with a light Gaussian blur
        blurred = cv2.GaussianBlur(equalized, (3, 3), 0)
        
        # Normalize to reduce global variance
        normalized = cv2.normalize(blurred, None, alpha=127, beta=255, norm_type=cv2.NORM_MINMAX)
        
        return normalized

    @abstractmethod
    def postprocess_text(self, text: str) -> str:
        """Post-process OCR results"""
        pass

    def get_page_segmentation_mode(self, image: np.ndarray) -> int:
        """Determine optimal PSM based on image characteristics"""
        height, width = image.shape[:2]
        aspect_ratio = width / height

        # Optimize PSM for typical Moroccan administrative documents
        if aspect_ratio > 1.4:  # Typical A4 document
            return 1  # Auto-page segmentation with OSD
        elif aspect_ratio < 0.8:  # Portrait document
            return 3  # Fully automatic page segmentation
        else:
            return 6  # Assume uniform block of text

    def process_image(self, 
                     image: np.ndarray, 
                     lang: str,
                     psm: Optional[int] = None) -> List[OCRResult]:
        """Process image with error handling and detailed results"""
        if image is None or image.size == 0:
            raise ValueError("Invalid image input")

        try:
            # Preprocess image
            processed_img = self.preprocess_image(image)
            
            # Determine PSM if not provided
            if psm is None:
                psm = self.get_page_segmentation_mode(processed_img)

            custom_config = f'--oem 3 --psm {psm}'

            tessdata_env = os.environ.get("TESSDATA_PREFIX")
            tessdir = None
            if tessdata_env and Path(tessdata_env).exists():
                tessdir = None  # env var wins
            elif repo_tessdata.exists():
                tessdir = repo_tessdata.resolve()

            if tessdir is not None:
                td_posix = tessdir.as_posix()
                custom_config = f'--tessdata-dir "{td_posix}" {custom_config}'

            # (optional, only if Arabic still looks Latin)
            # if lang == 'ara':
            #     custom_config = f'--oem 1 --psm {psm}'
            
            # Get detailed OCR data
            data = pytesseract.image_to_data(
                processed_img,
                lang=lang,
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )

            results: List[OCRResult] = []
            
            # Process each detected text region
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > -1:  # Filter valid results
                    text = data['text'][i].strip()
                    if text:  # Only process non-empty text
                        # Post-process text
                        processed_text = self.postprocess_text(text)
                        
                        result = OCRResult(
                            text=processed_text,
                            confidence=float(data['conf'][i]),
                            bounding_box=(
                                data['left'][i],
                                data['top'][i],
                                data['width'][i],
                                data['height'][i]
                            ),
                            language=lang,
                            page_number=data.get('page_num', [1])[i]
                        )
                        results.append(result)

            return results

        except Exception as e:
            self.logger.error(f"OCR processing failed: {str(e)}")
            raise RuntimeError("OCR processing failed") from e

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        try:
            return pytesseract.get_languages()
        except Exception as e:
            self.logger.error(f"Failed to get supported languages: {str(e)}")
            return []

    @staticmethod
    def validate_language(lang: str) -> bool:
        """Validate if a language is supported"""
        try:
            langs = pytesseract.get_languages()
            return lang in langs
        except Exception:
            return False
