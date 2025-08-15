import pytest
import numpy as np
import cv2
from pathlib import Path
import os
from typing import Tuple

from src.ocr.arabic import ArabicOCR
from src.ocr.french import FrenchOCR
from src.ocr.hybrid import HybridOCR

# Fixture paths
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
IMAGES_DIR = FIXTURES_DIR / "images"
EXPECTED_DIR = FIXTURES_DIR / "expected"

@pytest.fixture(scope="session")
def setup_test_images():
    """Create test images with known text"""
    # Ensure directories exist
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create test images
    create_text_image(
        "arabic_test.png",
        "المملكة المغربية",
        "Arabic"
    )
    create_text_image(
        "french_test.png",
        "Préfecture de Casablanca",
        "French"
    )
    create_text_image(
        "hybrid_test.png",
        "المملكة المغربية\nPréfecture de Casablanca",
        "Hybrid"
    )
    create_corrupted_image("corrupted_test.png")

def create_text_image(filename: str, text: str, type: str) -> None:
    """Create test image with specified text"""
    image = np.ones((300, 800), dtype=np.uint8) * 255
    
    if type in ["Arabic", "Hybrid"]:
        cv2.putText(
            image,
            text.split('\n')[0],
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 0),
            2
        )
    
    if type in ["French", "Hybrid"]:
        y_pos = 150 if type == "Hybrid" else 50
        cv2.putText(
            image,
            text.split('\n')[-1],
            (50, y_pos),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 0),
            2
        )
    
    cv2.imwrite(str(IMAGES_DIR / filename), image)

def create_corrupted_image(filename: str) -> None:
    """Create a corrupted image file for testing error handling"""
    with open(IMAGES_DIR / filename, 'wb') as f:
        f.write(b'corrupted image data')

@pytest.fixture
def arabic_ocr():
    return ArabicOCR()

@pytest.fixture
def french_ocr():
    return FrenchOCR()

@pytest.fixture
def hybrid_ocr():
    return HybridOCR()

# Test Arabic OCR
def test_arabic_text_recognition(arabic_ocr, setup_test_images):
    image = cv2.imread(str(IMAGES_DIR / "arabic_test.png"))
    results = arabic_ocr.process_document(image)
    
    assert results
    assert any("المملكة المغربية" in result.text for result in results)
    assert all(result.confidence > 0 for result in results)

def test_arabic_preprocessing(arabic_ocr):
    # Create test image with noise
    noisy_image = np.random.normal(128, 50, (300, 800)).astype(np.uint8)
    processed = arabic_ocr.preprocess_image(noisy_image)
    
    # Check if preprocessing maintained basic image properties
    assert processed.shape == noisy_image.shape
    assert processed.dtype == noisy_image.dtype
    assert np.min(processed) >= 0 and np.max(processed) <= 255

# Test French OCR
def test_french_text_recognition(french_ocr, setup_test_images):
    image = cv2.imread(str(IMAGES_DIR / "french_test.png"))
    results = french_ocr.process_document(image)
    
    assert results
    assert any("Prefecture" in result.text for result in results)
    assert all(result.confidence > 0 for result in results)

def test_french_administrative_patterns(french_ocr):
    text = "Préfecture de Casablanca"
    processed = french_ocr.postprocess_text(text)
    
    assert "Prefecture" in processed
    assert processed.strip() == "Prefecture de Casablanca"  # Accent-stripped version

# Test Hybrid OCR
def test_hybrid_document_processing(hybrid_ocr, setup_test_images):
    image = cv2.imread(str(IMAGES_DIR / "hybrid_test.png"))
    results = hybrid_ocr.process_document(image)
    
    assert 'arabic' in results
    assert 'french' in results
    assert len(results['arabic']) > 0
    assert len(results['french']) > 0

def test_hybrid_layout_analysis(hybrid_ocr, setup_test_images):
    image = cv2.imread(str(IMAGES_DIR / "hybrid_test.png"))
    regions = hybrid_ocr.analyze_layout(image)
    
    assert 'arabic' in regions
    assert 'french' in regions
    assert len(regions['arabic']) > 0
    assert len(regions['french']) > 0

# Error Handling Tests
def test_corrupted_image_handling(hybrid_ocr, setup_test_images):
    with pytest.raises(Exception):
        image = cv2.imread(str(IMAGES_DIR / "corrupted_test.png"))
        hybrid_ocr.process_document(image)

def test_empty_image_handling(hybrid_ocr):
    with pytest.raises(ValueError):
        hybrid_ocr.process_document(np.array([]))

# Performance Benchmarks
@pytest.mark.benchmark
def test_processing_performance(benchmark, hybrid_ocr, setup_test_images):
    image = cv2.imread(str(IMAGES_DIR / "hybrid_test.png"))
    
    def process_image():
        return hybrid_ocr.process_document(image)
    
    result = benchmark(process_image)
    assert result  # Ensure processing completed successfully

@pytest.mark.benchmark
def test_layout_analysis_performance(benchmark, hybrid_ocr, setup_test_images):
    image = cv2.imread(str(IMAGES_DIR / "hybrid_test.png"))
    
    def analyze_layout():
        return hybrid_ocr.analyze_layout(image)
    
    result = benchmark(analyze_layout)
    assert result  # Ensure analysis completed successfully
