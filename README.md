# 🇲🇦 Morocco Prefecture OCR

[![CI](https://github.com/Trunsoest04/OCR-intern/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Trunsoest04/OCR-intern/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-informational)
![License](https://img.shields.io/github/license/Trunsoest04/OCR-intern)
![Status](https://img.shields.io/badge/status-Alpha-blue)

End-to-end OCR system optimized for Moroccan administrative documents with bilingual (FR+AR) processing, multi-format export (PDF/Word/Excel/JSON), performance analytics, and a GUI dashboard. Includes automated testing and CI/CD integration.

## ✨ Highlights
- **Templates**: Residency Certificate, Administrative Attestation, Construction Permit, Birth Extract.
- **Engines**: Arabic, French, and Hybrid strategies with pre/post-processing.
- **Exports**: PDF, DOCX, XLSX/CSV, JSON (API-ready).
- **Analytics**: SQLite-backed metrics + interactive dashboard (cache hits, throughput, error trends).
- **Ops**: Modular architecture, batch processing, robust error handling.

> ⚠️ Replace example commands/paths below with the actual entrypoints in `src/` (e.g., your CLI or GUI module). If something differs, open an issue and we’ll adjust.

---

## 📁 Repository structure
assets/templates/ # Prefecture document templates
src/
ocr/ # Arabic/French/Hybrid OCR logic
preprocessing/ # Image cleanup, binarization, etc.
postprocessing/ # Parsing, validation, formatting
gui/components/ # Qt GUI + performance dashboard
utils/ # Document export, analytics, helpers
tests/
integration/ # End-to-end scenarios
unit/ # Focused unit tests
requirements.txt

---

## 🧰 Requirements
- **Python** ≥ 3.10
- **Tesseract OCR** (with Arabic + French traineddata)  
  - Windows: install Tesseract, then ensure `tesseract.exe` is on PATH.
- **Poppler** (for some PDF operations, if used)
- **Git** (for versioning)
- System packages used by OpenCV/Qt as needed.

Install Python dependencies:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -U pip
pip install -r requirements.txt
🚀 Usage
1) CLI (batch)
# Detect document type, run OCR, and export to multiple formats
python -m src.cli.process --input path/to/folder --out out/ --formats pdf word excel json
2) GUI
python -m src.gui.components.main_window
# or
python -m src.gui.components.hybrid_ocr_gui
3) Performance dashboard
python -m src.gui.components.performance_dashboard
# Analytics are stored in SQLite (e.g., analytics.db)
📤 Exports
PDF: Arabic/French text rendering supported.

Word (DOCX): bilingual formatting preserved.

Excel (XLSX/CSV): tabular outputs for analysis.

JSON: structured fields for API integrations.

Example:
from src.utils.document_exporter import DocumentExporter

exporter = DocumentExporter("out/")
exporter.batch_export(results, template_info, formats=['pdf','word','excel','json'])
📊 Analytics
Metrics: processing time, template success rate, cache hit rate, error taxonomy.

Storage: SQLite (default analytics.db).

UI: interactive charts via dashboard component.

✅ Testing
pytest -q
# with coverage
pytest -q --maxfail=1 --disable-warnings --cov=src --cov-report=term-missing
🔒 Configuration & secrets
Do not commit API keys or private datasets.

Use a local .env (ignored) if you need credentials.

🛣️ Roadmap / Open items
 Confirm/lock the exact CLI/GUI entrypoints and update README commands.

 Add golden-set tests for each template type (FR/AR).

 Benchmark suite (throughput, latency, accuracy).

 Optional Dockerfile for on-prem deployments.
