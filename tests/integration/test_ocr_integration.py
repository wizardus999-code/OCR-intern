import pytest
import cv2
import numpy as np
from pathlib import Path
import time
from typing import Dict

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
        "certificate": create_sample_document(
            "certificat_residence.png",
            "Certificat de Résidence\nشهادة السكنى",
            "certificate",
        ),
        "declaration": create_sample_document(
            "declaration.png", "Déclaration\nتصريح", "declaration"
        ),
        "application": create_sample_document(
            "demande.png", "Demande d'Autorisation\nطلب الترخيص", "application"
        ),
    }

    return documents


def create_sample_document(filename: str, text: str, doc_type: str) -> Dict:
    """Create a sample document with specified characteristics"""
    # Create base image
    image = np.ones((600, 800), dtype=np.uint8) * 255

    # Add header
    cv2.putText(
        image, "ROYAUME DU MAROC", (300, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2
    )

    cv2.putText(
        image, "المملكة المغربية", (300, 100), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2
    )

    # Add main text
    y_pos = 200
    for line in text.split("\n"):
        cv2.putText(
            image, line, (100, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2
        )
        y_pos += 100

    # Save image
    output_path = IMAGES_DIR / filename
    cv2.imwrite(str(output_path), image)

    return {"path": str(output_path), "type": doc_type, "text": text}


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
            image = cv2.imread(doc_info["path"])
            assert image is not None, f"Failed to load image for {doc_type}"

            # Preprocess
            processed = self.preprocessor.process(image)
            assert processed is not None, "Preprocessing failed"

            # Perform OCR
            start_time = time.time()
            results = self.ocr.process_document(processed)
            processing_time = time.time() - start_time

            # Verify results
            assert "arabic" in results, "Arabic text not detected"
            assert "french" in results, "French text not detected"

            # Check confidence scores
            arabic_conf = np.mean([r.confidence for r in results["arabic"]])
            french_conf = np.mean([r.confidence for r in results["french"]])

            assert arabic_conf > 0, "Arabic confidence too low"
            assert french_conf > 0, "French confidence too low"

            # Verify processing time
            assert (
                processing_time < 10.0
            ), f"Processing too slow: {processing_time:.2f}s"

    def test_document_type_detection(self, sample_documents):
        """Test accurate detection of document types"""
        for doc_type, doc_info in sample_documents.items():
            image = cv2.imread(doc_info["path"])
            results = self.ocr.process_document(image)

            # Combine text from both languages
            all_text = []
            for lang in ["arabic", "french"]:
                all_text.extend([r.text for r in results[lang]])

            # Process combined text
            processed_results = self.postprocessor.process(all_text)

            # Debug print
            print(f"Text for {doc_type}:", all_text)
            print("Processed:", processed_results)

            assert (
                processed_results["metadata"]["document_type"] == doc_type
            ), f"Failed to detect correct document type for {doc_type}"

    def test_bilingual_alignment(self, sample_documents):
        """Test alignment and correspondence of bilingual text"""
        for doc_info in sample_documents.values():
            image = cv2.imread(doc_info["path"])
            results = self.ocr.process_document(image)

            # Check if we have both Arabic and French results
            assert len(results["arabic"]) > 0, "No Arabic text detected"
            assert len(results["french"]) > 0, "No French text detected"

            # Verify spatial relationship (Arabic text should be above or beside French)
            for ar_result in results["arabic"]:
                ar_box = ar_result.bounding_box
                for fr_result in results["french"]:
                    fr_box = fr_result.bounding_box

                    # Check if boxes don't overlap
                    assert not (
                        ar_box[0] < fr_box[0] + fr_box[2]
                        and ar_box[0] + ar_box[2] > fr_box[0]
                        and ar_box[1] < fr_box[1] + fr_box[3]
                        and ar_box[1] + ar_box[3] > fr_box[1]
                    ), "Text regions overlap"

    @pytest.mark.benchmark
    def test_processing_performance(self, benchmark, sample_documents):
        """Benchmark processing performance"""
        doc_path = sample_documents["certificate"]["path"]
        image = cv2.imread(doc_path)

        def process_doc():
            processed = self.preprocessor.process(image)
            return self.ocr.process_document(processed)

        result = benchmark(process_doc)
        assert result, "Processing failed during benchmark"
