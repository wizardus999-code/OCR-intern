import pytest
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import os
import image_utils
from tests.utils.text_renderer import TextRenderer

from src.ocr.hybrid import HybridOCR
from src.types.document import Document

# Test fixtures path
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
TEMPLATES_DIR = FIXTURES_DIR / "templates"
STAMPS_DIR = FIXTURES_DIR / "stamps"

class MoroccanDocumentGenerator:
    """Generate test documents with realistic Moroccan administrative layouts"""
    
    def __init__(self):
        self.templates_dir = TEMPLATES_DIR
        self.stamps_dir = STAMPS_DIR
        self.text_renderer = TextRenderer()
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Create necessary directories for test assets"""
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.stamps_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample stamp if not exists
        if not list(self.stamps_dir.glob("*.png")):
            self._create_sample_stamp()
    
    def _create_sample_stamp(self):
        """Create a sample official stamp image"""
        stamp = np.ones((200, 200, 3), dtype=np.uint8) * 255
        cv2.circle(stamp, (100, 100), 90, (0, 0, 0), 2)
        cv2.putText(stamp, "MAROC", (60, 100),
                   cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 0), 2)
        cv2.imwrite(str(self.stamps_dir / "official_stamp.png"), stamp)
    
    def create_document(self, doc_type: str, content: dict) -> str:
        """Create a test document with specified type and content"""
        # Create base image as 3-channel
        width, height = 2480, 3508  # A4 size at 300 DPI
        image = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        # Add header
        self._add_header(image, doc_type)
        
        # Add content based on document type
        content_method = getattr(self, f"_add_{doc_type}_content", None)
        if content_method:
            content_method(image, content)
        
        # Add stamp and signature area
        self._add_stamp_and_signature(image)
        
        # Save document
        output_path = self.templates_dir / f"{doc_type}_{datetime.now().strftime('%Y%m%d')}.png"
        cv2.imwrite(str(output_path), image)
        
        return str(output_path)
    
    def _add_header(self, image: np.ndarray, doc_type: str):
        """Add official header to document"""
        # Add Moroccan coat of arms
        cv2.putText(image, "🇲🇦", (1140, 200),
                   cv2.FONT_HERSHEY_COMPLEX, 4, (0, 0, 0), 2)
        
        # Add bilingual headers
        # French header
        image = self.text_renderer.draw_text(
            image,
            (940, 300), 
            "ROYAUME DU MAROC",
            font_size=64,
            arabic=False,
            color=(0, 0, 0)
        )
        
        # Arabic header
        image = self.text_renderer.draw_text(
            image,
            (940, 400),
            "المملكة المغربية",
            font_size=64,
            arabic=True,
            color=(0, 0, 0)
        )
    
    def _add_identity_content(self, image: np.ndarray, content: dict):
        """Add content for identity documents"""
        fields = [
            ("Nom / الاسم العائلي", content.get("name", "")),
            ("Prénom / الاسم الشخصي", content.get("firstname", "")),
            ("Date de naissance / تاريخ الازدياد", content.get("birth_date", "")),
            ("Lieu de naissance / مكان الازدياد", content.get("birth_place", "")),
            ("Adresse / العنوان", content.get("address", ""))
        ]
        
        y_pos = 600
        for label, value in fields:
            # Split label into French and Arabic parts
            fr_part, ar_part = label.split(" / ")
            
            # Add French label
            image = self.text_renderer.draw_text(
                image,
                (200, y_pos), 
                fr_part,
                font_size=40,
                arabic=False,
                color=(0, 0, 0)
            )
            
            # Add Arabic label
            image = self.text_renderer.draw_text(
                image,
                (400, y_pos),
                ar_part,
                font_size=40,
                arabic=True,
                color=(0, 0, 0)
            )
            
            # Add value
            image = self.text_renderer.draw_text(
                image,
                (200, y_pos + 60),
                value,
                font_size=42,
                arabic=any('\u0600' <= ch <= '\u06FF' for ch in value),
                color=(0, 0, 0)
            )
            
            y_pos += 200
    
    def _add_certificate_content(self, image: np.ndarray, content: dict):
        """Add content for certificates"""
        # Add title
        title_fr = content.get("title_fr", "CERTIFICAT")
        title_ar = content.get("title_ar", "شهادة")
        
        image = self.text_renderer.draw_text(
            image,
            (940, 500),
            title_fr,
            font_size=56,
            arabic=False,
            color=(0, 0, 0)
        )
        image = self.text_renderer.draw_text(
            image,
            (940, 600),
            title_ar,
            font_size=56,
            arabic=True,
            color=(0, 0, 0)
        )
        
        # Add certificate body
        body_fr = content.get("body_fr", "")
        body_ar = content.get("body_ar", "")
        
        y_pos = 800
        for text in [body_fr, body_ar]:
            words = text.split()
            line = []
            x_pos = 200
            
            is_arabic = any('\u0600' <= c <= '\u06FF' for c in text)
            joined_text = text  # Keep text intact for Arabic
            if not is_arabic:
                for word in words:
                    line.append(word)
                    if len(" ".join(line)) * 20 > 2080:  # width(2480) - 400
                        joined_text = " ".join(line)
                        line = []
                        image = self.text_renderer.draw_text(
                            image,
                            (x_pos, y_pos),
                            joined_text,
                            font_size=32,
                            arabic=is_arabic,
                            color=(0, 0, 0)
                        )
                        y_pos += 50
            
            if not is_arabic and line:
                joined_text = " ".join(line)
            image = self.text_renderer.draw_text(
                image,
                (x_pos, y_pos),
                joined_text,
                font_size=32,
                arabic=is_arabic,
                color=(0, 0, 0)
            )
            y_pos += 100
    
    def _add_stamp_and_signature(self, image: np.ndarray):
        """Add official stamp and signature area"""
        # Load and add stamp
        stamp_path = self.stamps_dir / "official_stamp.png"
        if stamp_path.exists():
            stamp = cv2.imread(str(stamp_path))
            if stamp is not None:
                h, w = stamp.shape[:2]
                image_region = image[2800:2800+h, 1800:1800+w]
                # Ensure both the image region and stamp have same number of channels
                image_region = image_utils.ensure_3ch(image_region)
                stamp = image_utils.ensure_3ch(stamp)
                image[2800:2800+h, 1800:1800+w] = stamp
        
        # Add signature area
        # Draw signature label with Arabic support
        image = self.text_renderer.draw_text(
            image,
            (400, 2900),
            "Signature / إمضاء",
            font_size=32,
            arabic=True,
            color=(0, 0, 0)
        )
        image = np.ascontiguousarray(image)  # Ensure contiguous array for OpenCV
        cv2.rectangle(image, (400, 2950), (800, 3150), (0, 0, 0), 2)

@pytest.fixture(scope="session")
def document_generator():
    return MoroccanDocumentGenerator()

@pytest.fixture(scope="session")
def sample_documents(document_generator):
    """Create a set of sample documents for testing"""
    documents = {}
    
    # Identity Document
    documents['identity'] = document_generator.create_document(
        'identity',
        {
            'name': 'Alami',
            'firstname': 'Mohammed',
            'birth_date': '01/01/1990',
            'birth_place': 'Casablanca',
            'address': '123 Rue Hassan II, Casablanca'
        }
    )
    
    # Certificate
    documents['certificate'] = document_generator.create_document(
        'certificate',
        {
            'title_fr': 'CERTIFICAT DE RÉSIDENCE',
            'title_ar': 'شهادة السكنى',
            'body_fr': 'Le président de la commune certifie que M. Mohammed Alami réside à...',
            'body_ar': 'يشهد رئيس الجماعة أن السيد محمد علمي يسكن في...'
        }
    )
    
    return documents

def test_identity_document_recognition(sample_documents):
    """Test recognition of identity document fields"""
    ocr = HybridOCR()
    image = cv2.imread(sample_documents['identity'])
    results = ocr.process_document(image)
    
    # Check for key identity fields
    text = " ".join([r.text for r in results['french'] + results['arabic']])
    assert "Nom" in text
    assert "الاسم" in text
    assert "Alami" in text
    
def test_certificate_recognition(sample_documents):
    """Test recognition of official certificates"""
    ocr = HybridOCR()
    image = cv2.imread(sample_documents['certificate'])
    results = ocr.process_document(image)
    
    # Check for certificate-specific elements
    text = " ".join([r.text for r in results['french'] + results['arabic']])
    assert "CERTIFICAT" in text
    assert "شهادة" in text
    assert "commune" in text.lower()
    
def test_stamp_detection(sample_documents):
    """Test detection of official stamps"""
    ocr = HybridOCR()
    image = cv2.imread(sample_documents['certificate'])
    
    # Convert to grayscale for stamp detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        1,
        minDist=100,
        param1=50,
        param2=30,
        minRadius=50,
        maxRadius=100
    )
    
    assert circles is not None, "Official stamp not detected"

@pytest.mark.benchmark
def test_document_processing_performance(benchmark, sample_documents):
    """Benchmark document processing performance"""
    ocr = HybridOCR()
    image = cv2.imread(sample_documents['certificate'])
    
    def process_doc():
        return ocr.process_document(image)
    
    result = benchmark(process_doc)
    assert result, "Document processing failed"
