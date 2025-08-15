import os
from pathlib import Path

# Set tessdata path if local copy exists
repo_tessdata = Path(__file__).resolve().parents[2] / "tessdata"
if repo_tessdata.exists():
    os.environ.setdefault("TESSDATA_PREFIX", str(repo_tessdata))

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QLabel, QFileDialog, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import cv2
import numpy as np

from src.ocr.arabic import ArabicOCR
from src.ocr.french import FrenchOCR
from src.preprocessing.preprocess import PreprocessingPipeline
from src.postprocessing.postprocess import PostProcessor
from src.types.document import Document

class OCRWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)

    def __init__(self, image_paths):
        super().__init__()
        self.image_paths = image_paths
        self.arabic_ocr = ArabicOCR()
        self.french_ocr = FrenchOCR()
        self.preprocessor = PreprocessingPipeline()
        self.postprocessor = PostProcessor()

    def run(self):
        results = {}
        total = len(self.image_paths)
        
        for idx, path in enumerate(self.image_paths):
            doc = Document(path)
            self._perform_document_analysis(doc)
            results[path] = doc
            self.progress.emit(int((idx + 1) / total * 100))
            
        self.finished.emit(results)

    def _perform_document_analysis(self, document):
        """Analyze document for text content and layout"""
        # Preprocess the image
        preprocessed = self.preprocessor.process_document(document.image)
        
        # Detect handwriting regions
        handwriting_regions = self._perform_handwriting_detection(preprocessed)
        
        # Compare different OCR engines
        engine_results = self._perform_engine_comparison(preprocessed)
        
        # Store results in document object
        document.handwriting_regions = handwriting_regions
        document.ocr_results = engine_results
        
    def _perform_handwriting_detection(self, image):
        """Detect handwritten regions in the document"""
        # Convert to grayscale if not already
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Find contours
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter contours based on characteristics of handwriting
        handwriting_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # Minimum area threshold
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w)/h
                # Handwriting typically has specific aspect ratios
                if 0.2 < aspect_ratio < 15:
                    handwriting_regions.append((x, y, w, h))
                    
        return handwriting_regions
        
    def _perform_engine_comparison(self, image):
        """Compare results from different OCR engines"""
        # Get results from both Arabic and French OCR using process_document
        arabic_results = self.arabic_ocr.process_document(image)
        french_results = self.french_ocr.process_document(image)
        
        # Combine and validate results
        combined_results = {
            'arabic': arabic_results,
            'french': french_results,
            'confidence_scores': {
                'arabic': self.arabic_ocr.get_confidence(),
                'french': self.french_ocr.get_confidence()
            }
        }
        
        return combined_results

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Morocco Prefecture OCR")
        self.setMinimumSize(800, 600)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Add widgets
        self.setup_ui(layout)
        
        # Initialize variables
        self.current_results = {}
        self.image_paths = []
        
    def setup_ui(self, layout):
        # Add buttons
        self.select_btn = QPushButton("Select Documents")
        self.select_btn.clicked.connect(self.select_documents)
        layout.addWidget(self.select_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Results label
        self.results_label = QLabel()
        self.results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.results_label)
        
    def select_documents(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Documents",
            "",
            "Images (*.png *.jpg *.jpeg *.tiff *.bmp)"
        )
        
        if files:
            self.image_paths = files
            self.process_documents()
            
    def process_documents(self):
        self.progress_bar.setValue(0)
        self.worker = OCRWorker(self.image_paths)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self._display_batch_results)
        self.worker.start()
        
    def update_progress(self, value):
        self.progress_bar.setValue(value)
        
    def _display_batch_results(self, results):
        """Display the results of batch processing"""
        self.current_results = results
        
        # Create summary text
        summary = []
        for path, doc in results.items():
            file_name = Path(path).name
            summary.append(f"File: {file_name}")
            
            # Add language detection results
            for lang, conf in doc.ocr_results['confidence_scores'].items():
                summary.append(f"  {lang.capitalize()} confidence: {conf:.2f}")
            
            # Add handwriting detection results
            hw_regions = len(doc.handwriting_regions)
            summary.append(f"  Handwritten regions detected: {hw_regions}")
            summary.append("")
            
        # Update the results label
        self.results_label.setText("\n".join(summary))

