from __future__ import annotations
from typing import Optional, Dict, List
import numpy as np
import re
from pytesseract import pytesseract, Output

from .hybrid import HybridOCR
from .base import OCRResult
from .utils import arabic_indic_to_ascii

class ReceiptOCR:
    def __init__(self, config_path: Optional[str] = None):
        # Keep existing initialization if needed; ensure Hybrid is available.
        self.hybrid = HybridOCR(config_path)

    def process_document(
        self,
        image: np.ndarray,
        config: Optional[dict] = None,
    ) -> Dict[str, List[OCRResult]]:
        """Process document with receipt number detection."""
        # First get standard hybrid results
        result = self.hybrid.process_document(image)

        # Extract receipt number ROI
        roi = None
        if "regions" in result:
            roi = result["regions"].get("receipt_no") or result["regions"].get("association_receipt")
        
        if roi is None:
            roi = image  # Fallback to full image if no ROI found

        # Configure OCR for digit-focused receipt number extraction
        digit_config = "--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789/"
        
        # Get raw text and detailed data for confidence
        raw = pytesseract.image_to_string(roi, lang="fra", config=digit_config) or ""
        data = pytesseract.image_to_data(roi, lang="fra", config=digit_config, output_type=Output.DICT)
        
        # Clean and normalize text
        raw = raw.strip()
        raw_norm = arabic_indic_to_ascii(raw)
        
        # Initialize fields if not present
        if "fields" not in result:
            result["fields"] = {}
        if "body" not in result["fields"]:
            result["fields"]["body"] = {}
            
        # Extract receipt number and calculate confidence
        m = re.search(r"(20\d{2})/(\d{3,5})", raw_norm)
        receipt_field = {
            "value": raw,
            "norm": raw_norm,
            "valid": False,
            "type": "receipt_no",
            "conf": 40,  # Minimum confidence
            "lang": "receipt"
        }
        
        if m:
            norm = f"{m.group(1)}/{m.group(2)}"
            receipt_field["norm"] = norm
            receipt_field["valid"] = True
            
            # Base confidence calculation
            conf = 85.0  # Base confidence for pattern match
            
            # Check if raw matches normalized exactly
            if raw_norm == norm:
                conf = 95.0
                
            # Consider token confidences if available
            token_confs = [float(c) for c in data["conf"] if c != -1]  # Filter valid confidences
            if token_confs:
                max_token_conf = max(token_confs)
                conf = max(conf, max_token_conf)
                
            # Clamp final confidence
            conf = min(max(conf, 40), 99)
            receipt_field["conf"] = int(conf)
            
        result["fields"]["body"]["receipt_no"] = receipt_field
        return result

    # Optional call aliases if other callers use different names:
    # def run(self, image: np.ndarray, config: Optional[dict] = None):
    #     return self.process_document(image, config)
    # def process(self, image: np.ndarray, config: Optional[dict] = None):
    #     return self.process_document(image, config)
