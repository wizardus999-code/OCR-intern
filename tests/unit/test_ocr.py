import pytest
import cv2
import numpy as np
from src.ocr.arabic import ArabicOCR
from src.ocr.french import FrenchOCR
from src.types.document import Document

@pytest.fixture
def sample_image():
    # Create a blank image with some text
    img = np.ones((300, 800), dtype=np.uint8) * 255
    cv2.putText(img, "Test Document", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    return img

def test_arabic_ocr_initialization():
    ocr = ArabicOCR()
    assert ocr.confidence == 0.0
    assert ocr.last_result is None

def test_french_ocr_initialization():
    ocr = FrenchOCR()
    assert ocr.confidence == 0.0
    assert ocr.last_result is None

def test_document_initialization(tmp_path):
    # Create a temporary image file
    image_path = tmp_path / "test.png"
    img = np.ones((100, 100), dtype=np.uint8) * 255
    cv2.imwrite(str(image_path), img)
    
    # Create document instance
    doc = Document(str(image_path))
    assert doc.handwriting_regions == []
    assert doc.ocr_results == {}
