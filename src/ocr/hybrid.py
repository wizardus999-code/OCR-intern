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

    def __init__(
        self,
        arabic_engine: Optional[ArabicOCR] = None,
        french_engine: Optional[FrenchOCR] = None,
        config_path: Optional[str] = None,
    ):
        self.logger = logging.getLogger(__name__)
        self.arabic_engine = arabic_engine or ArabicOCR(config_path)
        self.french_engine = french_engine or FrenchOCR(config_path)

    @staticmethod
    def _is_arabic_text(s: str) -> bool:
        return any("\u0600" <= ch <= "\u06FF" for ch in (s or ""))

    @staticmethod
    def _is_latin_text(s: str) -> bool:
        s = s or ""
        return any("a" <= ch.lower() <= "z" for ch in s)

    def _filter_by_script(self, results, lang: str):
        out = []
        for r in results or []:
            t = getattr(r, "text", "") or ""
            if lang == "arabic" and self._is_arabic_text(t):
                out.append(r)
            elif lang == "french" and self._is_latin_text(t):
                out.append(r)
        return out

    def analyze_layout(
        self, image: np.ndarray
    ) -> Dict[str, List[Tuple[int, int, int, int]]]:
        """
        Analyze document layout to identify potential language regions
        Returns dictionary with 'arabic' and 'french' regions as bounding boxes
        """
        regions = {"arabic": [], "french": []}
        gray = (
            cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        )

        # Apply morphological operations to identify text blocks
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
        dilated = cv2.dilate(gray, kernel, iterations=3)

        # Find contours of text regions
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            roi = gray[y : y + h, x : x + w]

            # Simple heuristic: Arabic text typically has more vertical strokes
            vertical_projection = np.sum(roi, axis=0)
            horizontal_projection = np.sum(roi, axis=1)

            if np.std(vertical_projection) > np.std(horizontal_projection):
                regions["arabic"].append((x, y, w, h))
            else:
                regions["french"].append((x, y, w, h))

        return regions

    @staticmethod
    def _overlap(a, b) -> bool:
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        return (ax < bx + bw) and (ax + aw > bx) and (ay < by + bh) and (ay + ah > by)

    def _dedupe_overlaps(self, arabic, french):
        # Drop the lower-confidence item when boxes overlap
        keep_ar = []
        for ar in arabic:
            abox = getattr(ar, "bbox", getattr(ar, "bounding_box", None))
            if not abox:
                keep_ar.append(ar)
                continue
            drop = False
            for fr in french:
                fbox = getattr(fr, "bbox", getattr(fr, "bounding_box", None))
                if not fbox:
                    continue
                if self._overlap(abox, fbox) and (
                    getattr(ar, "confidence", 0.0) <= getattr(fr, "confidence", 0.0)
                ):
                    drop = True
                    break
            if not drop:
                keep_ar.append(ar)

        keep_fr = []
        for fr in french:
            fbox = getattr(fr, "bbox", getattr(fr, "bounding_box", None))
            if not fbox:
                keep_fr.append(fr)
                continue
            drop = False
            for ar in keep_ar:
                abox = getattr(ar, "bbox", getattr(ar, "bounding_box", None))
                if not abox:
                    continue
                if self._overlap(abox, fbox) and (
                    getattr(fr, "confidence", 0.0) < getattr(ar, "confidence", 0.0)
                ):
                    drop = True
                    break
            if not drop:
                keep_fr.append(fr)

        return keep_ar, keep_fr

    def process_document(self, image: np.ndarray) -> Dict[str, List[OCRResult]]:
        """
        Process document using both OCR engines intelligently
        Returns results from both engines, even if empty
        """
        try:
            # Process with both engines unconditionally
            arabic = self.arabic_engine.process_document(image) or []
            french = self.french_engine.process_document(image) or []

            # keep only expected script per language
            arabic = self._filter_by_script(arabic, "arabic")
            french = self._filter_by_script(french, "french")

            # remove bbox overlaps across languages
            arabic, french = self._dedupe_overlaps(arabic, french)

            results = {"arabic": arabic, "french": french}
            self._log_processing_summary(results)
            return results

        except Exception:
            # include traceback automatically
            self.logger.exception("Hybrid OCR processing failed")
            raise

    def _process_regions(
        self,
        image: np.ndarray,
        regions: List[Tuple[int, int, int, int]],
        engine: ArabicOCR | FrenchOCR,
    ) -> List[OCRResult]:
        """
        Process specific regions with given OCR engine
        """
        results = []
        for x, y, w, h in regions:
            # Extract region
            region = image[y : y + h, x : x + w]

            # Process region
            region_results = engine.process_document(region)

            # Adjust bounding boxes to original image coordinates
            for result in region_results:
                bbox = result.bounding_box
                adjusted_bbox = (bbox[0] + x, bbox[1] + y, bbox[2], bbox[3])
                result.bounding_box = adjusted_bbox
                results.append(result)

        return results

    def _log_processing_summary(self, results: Dict[str, List[OCRResult]]) -> None:
        """Log summary of processing results"""
        arabic_conf = (
            np.mean([r.confidence for r in results["arabic"]])
            if results["arabic"]
            else 0
        )
        french_conf = (
            np.mean([r.confidence for r in results["french"]])
            if results["french"]
            else 0
        )

        self.logger.info(
            f"Processing complete:\n"
            f"Arabic text regions: {len(results['arabic'])} (avg conf: {arabic_conf:.2f}%)\n"
            f"French text regions: {len(results['french'])} (avg conf: {french_conf:.2f}%)"
        )
