from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QProgressBar,
    QTextEdit,
    QComboBox,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QSplitter,
    QMenu,
    QTabWidget,
    QCheckBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QTimer
from PyQt6.QtGui import QPixmap, QImage, QAction
import sqlite3
from pathlib import Path
import json
import cv2
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Optional
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import threading

from src.utils.document_management import DocumentCache, TemplateManager

from src.ocr.hybrid import HybridOCR
from src.ocr.base import OCRResult
from src.preprocessing.preprocess import PreprocessingPipeline


class OCRWorker(QThread):
    progress = pyqtSignal(int)
    result_ready = pyqtSignal(dict)
    status_update = pyqtSignal(str)
    performance_update = pyqtSignal(dict)

    def __init__(self, cache_dir: str, templates_dir: str):
        super().__init__()
        self.image_paths = []
        self.ocr_engine = HybridOCR()
        self.preprocessor = PreprocessingPipeline()
        self.cache = DocumentCache(cache_dir)
        self.template_manager = TemplateManager(templates_dir)
        self.batch_size = 4  # Number of documents to process in parallel

    def set_images(self, image_paths: List[str]):
        self.image_paths = image_paths

    def process_document(self, path: str) -> Dict:
        """Process a single document with caching"""
        try:
            # Load image
            image = cv2.imread(path)
            if image is None:
                raise ValueError(f"Could not load image: {path}")

            # Check cache first
            cached_results = self.cache.get_cached_results(image)
            if cached_results:
                self.status_update.emit(f"Found cached results for {Path(path).name}")
                return {"path": path, "results": cached_results, "cached": True}

            # Preprocess image
            processed = self.preprocessor.process(image)

            # Process with hybrid OCR
            start_time = time.time()
            ocr_results = self.ocr_engine.process_document(processed)
            processing_time = time.time() - start_time

            # Calculate confidence scores
            confidence = self._calculate_confidence(ocr_results)

            # Detect template type
            template_type = self._detect_template_type(ocr_results)

            # Cache results
            self.cache.cache_results(
                image, ocr_results, template_type, confidence, processing_time
            )

            return {
                "path": path,
                "results": ocr_results,
                "processing_time": processing_time,
                "confidence": confidence,
                "template_type": template_type,
                "image": image,
                "cached": False,
            }

        except Exception as e:
            logging.error(f"Error processing {path}: {str(e)}")
            return {"path": path, "error": str(e)}

    def _calculate_confidence(self, ocr_results: Dict) -> float:
        """Calculate overall confidence score"""
        confidences = []
        for lang in ["arabic", "french"]:
            if lang in ocr_results:
                confidences.extend([r.confidence for r in ocr_results[lang]])
        return np.mean(confidences) if confidences else 0.0

    def _detect_template_type(self, ocr_results: Dict) -> str:
        """Detect document template type from OCR results"""
        templates = self.template_manager.get_template_list()

        # Combine text from both languages
        all_text = []
        for lang in ["arabic", "french"]:
            if lang in ocr_results:
                all_text.extend([r.text for r in ocr_results[lang]])
        text = " ".join(all_text).lower()

        # Check for template matches
        for template in templates:
            if template["name"].lower() in text or template["name_ar"] in text:
                return template["type"]

        return "unknown"

    def run(self):
        """Process documents in parallel with progress tracking"""
        results = {}
        total = len(self.image_paths)
        processed = 0

        # Create thread pool for parallel processing
        with ThreadPoolExecutor(max_workers=self.batch_size) as executor:
            # Submit all tasks
            future_to_path = {
                executor.submit(self.process_document, path): path
                for path in self.image_paths
            }

            # Process completed tasks
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    result = future.result()
                    results[path] = result

                    # Update progress
                    processed += 1
                    self.progress.emit(int(processed / total * 100))

                    # Update status
                    status = (
                        "Processed from cache"
                        if result.get("cached", False)
                        else "Processed"
                    )
                    self.status_update.emit(f"{status}: {Path(path).name}")

                    # Emit performance metrics
                    if "processing_time" in result:
                        self.performance_update.emit(
                            {
                                "path": path,
                                "time": result["processing_time"],
                                "confidence": result.get("confidence", 0),
                                "template_type": result.get("template_type", "unknown"),
                            }
                        )

                except Exception as e:
                    logging.error(f"Error processing {path}: {str(e)}")
                    results[path] = {"error": str(e)}

        self.result_ready.emit(results)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Morocco Prefecture OCR")
        self.setMinimumSize(1200, 800)

        # Initialize components
        self.ocr_worker = OCRWorker()
        self.current_results = {}
        self.image_paths = []

        # Set up UI
        self.setup_ui()

        # Connect signals
        self.connect_signals()

    def setup_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)

        # Left panel for controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Control buttons
        self.select_btn = QPushButton("Select Documents")
        self.process_btn = QPushButton("Process Documents")
        self.process_btn.setEnabled(False)

        left_layout.addWidget(self.select_btn)
        left_layout.addWidget(self.process_btn)

        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        self.progress_bar = QProgressBar()
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        left_layout.addWidget(progress_group)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(
            ["Document", "Arabic Conf.", "French Conf.", "Time (s)"]
        )
        left_layout.addWidget(self.results_table)

        # Right panel for document view
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Document viewer
        self.document_view = QLabel()
        self.document_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.document_view.setMinimumSize(600, 400)
        right_layout.addWidget(self.document_view)

        # Text results
        self.text_results = QTextEdit()
        self.text_results.setReadOnly(True)
        right_layout.addWidget(self.text_results)

        # Add panels to main layout
        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 2)

    def connect_signals(self):
        self.select_btn.clicked.connect(self.select_documents)
        self.process_btn.clicked.connect(self.process_documents)
        self.results_table.itemClicked.connect(self.show_document_results)

        # Worker signals
        self.ocr_worker.progress.connect(self.update_progress)
        self.ocr_worker.result_ready.connect(self._display_batch_results)
        self.ocr_worker.status_update.connect(self.update_status)

    def select_documents(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Documents", "", "Images (*.png *.jpg *.jpeg *.tiff *.bmp)"
        )

        if files:
            self.image_paths = files
            self.process_btn.setEnabled(True)
            self.status_label.setText(f"Selected {len(files)} documents")

    def process_documents(self):
        self.progress_bar.setValue(0)
        self.process_btn.setEnabled(False)
        self.results_table.setRowCount(0)
        self.text_results.clear()

        self.ocr_worker.set_images(self.image_paths)
        self.ocr_worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, message):
        self.status_label.setText(message)

    def _display_batch_results(self, results):
        """Display the results of batch processing"""
        self.current_results = results
        self.results_table.setRowCount(len(results))

        for row, (path, data) in enumerate(results.items()):
            filename = Path(path).name

            # Check for processing errors
            if "error" in data:
                self.results_table.setItem(row, 0, QTableWidgetItem(filename))
                self.results_table.setItem(row, 1, QTableWidgetItem("Error"))
                self.results_table.setItem(row, 2, QTableWidgetItem("Error"))
                self.results_table.setItem(row, 3, QTableWidgetItem("N/A"))
                continue

            # Calculate confidence scores
            arabic_results = data["ocr_results"].get("arabic", [])
            french_results = data["ocr_results"].get("french", [])

            arabic_conf = (
                f"{np.mean([r.confidence for r in arabic_results]):.1f}%"
                if arabic_results
                else "N/A"
            )
            french_conf = (
                f"{np.mean([r.confidence for r in french_results]):.1f}%"
                if french_results
                else "N/A"
            )

            # Add results to table
            self.results_table.setItem(row, 0, QTableWidgetItem(filename))
            self.results_table.setItem(row, 1, QTableWidgetItem(arabic_conf))
            self.results_table.setItem(row, 2, QTableWidgetItem(french_conf))
            self.results_table.setItem(
                row, 3, QTableWidgetItem(f"{data['processing_time']:.2f}")
            )

        self.results_table.resizeColumnsToContents()
        self.status_label.setText("Processing complete")
        self.process_btn.setEnabled(True)

    def show_document_results(self, item):
        """Display detailed results for selected document"""
        row = item.row()
        path = self.image_paths[row]
        data = self.current_results[path]

        # Check for processing errors
        if "error" in data:
            self.text_results.setText(f"Error processing document:\n{data['error']}")
            self.document_view.clear()
            return

        # Display image
        image = data["image"]
        height, width = image.shape[:2]

        # Scale image to fit view while maintaining aspect ratio
        view_width = self.document_view.width()
        view_height = self.document_view.height()
        scale = min(view_width / width, view_height / height)

        new_width = int(width * scale)
        new_height = int(height * scale)

        scaled_image = cv2.resize(image, (new_width, new_height))
        rgb_image = cv2.cvtColor(scaled_image, cv2.COLOR_BGR2RGB)

        q_img = QImage(
            rgb_image.data,
            new_width,
            new_height,
            rgb_image.strides[0],
            QImage.Format.Format_RGB888,
        )
        self.document_view.setPixmap(QPixmap.fromImage(q_img))

        # Display text results
        text_output = []
        for lang in ["arabic", "french"]:
            results = data["ocr_results"].get(lang, [])
            if results:
                text_output.append(f"\n{lang.upper()} TEXT:")
                for result in results:
                    text_output.append(
                        f"{result.text} (conf: {result.confidence:.1f}%)"
                    )

        self.text_results.setText("\n".join(text_output))
