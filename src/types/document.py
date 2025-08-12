from dataclasses import dataclass, field
from typing import List, Dict, Tuple
import cv2
import numpy as np
from pathlib import Path

@dataclass
class Document:
    """Represents a document with its image and extracted information"""
    path: str
    image: np.ndarray = field(init=False)
    handwriting_regions: List[Tuple[int, int, int, int]] = field(default_factory=list)
    ocr_results: Dict = field(default_factory=dict)
    document_type: str = None
    
    def __post_init__(self):
        """Load image after initialization"""
        self.image = cv2.imread(self.path)
        if self.image is None:
            raise ValueError(f"Could not load image from {self.path}")
            
    @property
    def filename(self) -> str:
        """Return the filename of the document"""
        return Path(self.path).name
        
    def get_handwriting_overlay(self) -> np.ndarray:
        """Return image with handwriting regions highlighted"""
        overlay = self.image.copy()
        for x, y, w, h in self.handwriting_regions:
            cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 0), 2)
        return overlay
