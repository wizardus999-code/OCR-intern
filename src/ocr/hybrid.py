from typing import List, Optional, Dict, Tuple
import numpy as np
import cv2
from concurrent.futures import ThreadPoolExecutor
import logging

from .arabic import ArabicOCR
from .french import FrenchOCR
from .base import OCRResult

class HybridOCR:
    """
    Intelligent hybrid OCR processor for Moroccan administrative documents
    Combines Arabic and French OCR engines with smart language detection
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.arabic_engine = ArabicOCR(config_path)
        self.french_engine = FrenchOCR(config_path)
        
    def analyze_layout(self, image: np.ndarray) -> Dict[str, List[Tuple[int, int, int, int]]]:
        """
        Analyze document layout to identify potential language regions
        Returns dictionary with 'arabic' and 'french' regions as bounding boxes
        """
        regions = {'arabic': [], 'french': []}
        if image is None or image.size == 0:
            return regions  # early

        # Convert to grayscale and threshold
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Create a horizontal kernel
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
        dilated = cv2.dilate(binary, kernel, iterations=2)
        
        # Remove noise
        cleaned = cv2.morphologyEx(dilated, cv2.MORPH_CLOSE, kernel, iterations=1)

        # Find contours of text regions
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        min_area = 500  # Minimum contour area to consider
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue
                
            x, y, w, h = cv2.boundingRect(contour)
            roi = gray[y:y+h, x:x+w]
            
            # Simple heuristic: Arabic text typically has more vertical strokes
            vertical_projection = np.sum(roi, axis=0)
            horizontal_projection = np.sum(roi, axis=1)
            
            if np.std(vertical_projection) > np.std(horizontal_projection):
                regions['arabic'].append((x, y, w, h))
            else:
                regions['french'].append((x, y, w, h))

        # Full-page Arabic fallback if no Arabic regions detected
        h, w = gray.shape[:2]
        if not regions['arabic']:
            regions['arabic'].append((0, 0, w, h))
                
        return regions
        
    def process_document(self, image: np.ndarray) -> Dict[str, List[OCRResult]]:
        """
        Process document using both OCR engines intelligently
        """
        if image is None or image.size == 0:
            raise ValueError("Invalid image input")

        try:
            # Analyze layout first
            regions = self.analyze_layout(image)
            results = {'arabic': [], 'french': []}
            
            # Process regions in parallel
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Submit Arabic processing
                if regions['arabic']:
                    arabic_future = executor.submit(
                        self._process_regions,
                        image,
                        regions['arabic'],
                        self.arabic_engine
                    )
                    
                # Submit French processing
                if regions['french']:
                    french_future = executor.submit(
                        self._process_regions,
                        image,
                        regions['french'],
                        self.french_engine
                    )
                    
                # Collect results
                if regions['arabic']:
                    results['arabic'] = arabic_future.result()
                if regions['french']:
                    results['french'] = french_future.result()
                    
            # Log processing summary
            self._log_processing_summary(results)
            return results
            
        except Exception as e:
            self.logger.error(f"Hybrid OCR processing failed: {str(e)}")
            raise
            
    def _process_regions(self, 
                        image: np.ndarray,
                        regions: List[Tuple[int, int, int, int]],
                        engine: ArabicOCR | FrenchOCR) -> List[OCRResult]:
        """
        Process specific regions with given OCR engine
        """
        results = []
        for x, y, w, h in regions:
            # Extract region
            region = image[y:y+h, x:x+w]
            
            # Process region
            region_results = engine.process_document(region)
            
            # Adjust bounding boxes to original image coordinates
            for result in region_results:
                bbox = result.bounding_box
                adjusted_bbox = (
                    bbox[0] + x,
                    bbox[1] + y,
                    bbox[2],
                    bbox[3]
                )
                result.bounding_box = adjusted_bbox
                results.append(result)
                
        return results
        
    def _log_processing_summary(self, results: Dict[str, List[OCRResult]]) -> None:
        """Log summary of processing results"""
        arabic_conf = np.mean([r.confidence for r in results['arabic']]) if results['arabic'] else 0
        french_conf = np.mean([r.confidence for r in results['french']]) if results['french'] else 0
        
        self.logger.info(
            f"Processing complete:\n"
            f"Arabic text regions: {len(results['arabic'])} (avg conf: {arabic_conf:.2f}%)\n"
            f"French text regions: {len(results['french'])} (avg conf: {french_conf:.2f}%)"
        )
