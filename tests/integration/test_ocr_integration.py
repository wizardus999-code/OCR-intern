import pytest
import cv2
import numpy as np
from pathlib import Path
import time
from typing import Dict, List

from src.ocr.hybrid import HybridOCR
from src.preprocessing.preprocess import PreprocessingPipeline
from src.postprocessing.postprocess import PostProcessor

# Test fixtures path
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
IMAGES_DIR = FIXTURES_DIR / "images"

@pytest.fixture(scope="session")
def sample_documents():
    """Create a set of sample Moroccan administrative documents"""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    documents = {
        'certificate': create_sample_document(
            "certificat_residence.png",
            "Certificat de Résidence\nشهادة السكنى",
            "certificate"
        ),
        'declaration': create_sample_document(
            "declaration.png",
            "Déclaration\nتصريح",
            "declaration"
        ),
        'application': create_sample_document(
            "demande.png",
            "Demande d'Autorisation\nطلب الترخيص",
            "application"
        )
    }
    
    return documents

def create_sample_document(filename: str, text: str, doc_type: str) -> Dict:
    """Create a sample document with specified characteristics"""
    # Create base image
    image = np.ones((600, 800), dtype=np.uint8) * 255
    
    # Add header
    cv2.putText(
        image,
        "ROYAUME DU MAROC",
        (300, 50),
        cv2.FONT_HERSHEY_COMPLEX,
        1,
        (0, 0, 0),
        2
    )
    
    cv2.putText(
        image,
        "المملكة المغربية",
        (300, 100),
        cv2.FONT_HERSHEY_COMPLEX,
        1,
        (0, 0, 0),
        2
    )
    
    # Add main text
    y_pos = 200
    for line in text.split('\n'):
        cv2.putText(
            image,
            line,
            (100, y_pos),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 0),
            2
        )
        y_pos += 100
    
    # Save image
    output_path = IMAGES_DIR / filename
    cv2.imwrite(str(output_path), image)
    
    return {
        'path': str(output_path),
        'type': doc_type,
        'text': text
    }

class TestEndToEnd:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.ocr = HybridOCR()
        self.preprocessor = PreprocessingPipeline()
        self.postprocessor = PostProcessor()

    def test_complete_document_processing(self, sample_documents):
        """Test complete processing pipeline with different document types"""
        for doc_type, doc_info in sample_documents.items():
            # Load and process document
            image = cv2.imread(doc_info['path'])
            assert image is not None, f"Failed to load image for {doc_type}"
            
            # Preprocess
            processed = self.preprocessor.process(image)
            assert processed is not None, "Preprocessing failed"
            
            # Perform OCR
            start_time = time.time()
            results = self.ocr.process_document(processed)
            processing_time = time.time() - start_time
            
            # Verify results
            assert 'arabic' in results, "Arabic text not detected"
            assert 'french' in results, "French text not detected"
            
            # Check confidence scores
            arabic_conf = np.mean([r.confidence for r in results['arabic']])
            french_conf = np.mean([r.confidence for r in results['french']])
            
            assert arabic_conf > 0, "Arabic confidence too low"
            assert french_conf > 0, "French confidence too low"
            
            # Verify processing time
            assert processing_time < 10.0, f"Processing too slow: {processing_time:.2f}s"
            
    def test_document_type_detection(self, sample_documents):
        """Test accurate detection of document types"""
        for doc_type, doc_info in sample_documents.items():
            image = cv2.imread(doc_info['path'])
            results = self.ocr.process_document(image)
            
            # Combine text from both languages
            all_text = []
            for lang in ['arabic', 'french']:
                all_text.extend([r.text for r in results[lang]])
            
            # Process combined text
            processed_results = self.postprocessor.process(all_text)
            
            assert processed_results['metadata']['document_type'] == doc_type, \
                f"Failed to detect correct document type for {doc_type}"
                
    def test_bilingual_alignment(self, sample_documents):
        """Test alignment and correspondence of bilingual text"""
        for doc_info in sample_documents.values():
            image = cv2.imread(doc_info['path'])
            results = self.ocr.process_document(image)
            
            # Check if we have both Arabic and French results
            assert len(results['arabic']) > 0, "No Arabic text detected"
            assert len(results['french']) > 0, "No French text detected"
            
            # Verify spatial relationship (Arabic text should be above or beside French)
            for ar_result in results['arabic']:
                ar_box = ar_result.bounding_box
                for fr_result in results['french']:
                    fr_box = fr_result.bounding_box
                    
                    # Calculate overlap percentage
                    def get_overlap_percentage(box1, box2):
                        x1, y1, w1, h1 = box1
                        x2, y2, w2, h2 = box2
                        
                        # Calculate intersection
                        x_left = max(x1, x2)
                        y_top = max(y1, y2)
                        x_right = min(x1 + w1, x2 + w2)
                        y_bottom = min(y1 + h1, y2 + h2)
                        
                        if x_right <= x_left or y_bottom <= y_top:
                            return 0.0
                            
                        intersection_area = (x_right - x_left) * (y_bottom - y_top)
                        box1_area = w1 * h1
                        box2_area = w2 * h2
                        
                        return intersection_area / min(box1_area, box2_area)
                    
                    # Allow up to 20% overlap
                    overlap = get_overlap_percentage(ar_box, fr_box)
                    assert overlap <= 0.2, "Text regions overlap too much"
    
    @pytest.mark.benchmark
    def test_processing_performance(self, benchmark, sample_documents):
        """Benchmark processing performance"""
        doc_path = sample_documents['certificate']['path']
        image = cv2.imread(doc_path)
        
        def process_doc():
            processed = self.preprocessor.process(image)
            return self.ocr.process_document(processed)
        
        result = benchmark(process_doc)
        assert result, "Processing failed during benchmark"
