# 🇲🇦 Morocco Prefecture OCR

[![CI](https://github.com/wizardus999-code/OCR-intern/actions/wor## 🌍 Translations
<details><summary><strong>🇫🇷 Français (cliquez pour développer)</strong></summary>

### Démarrage rapide

Définir TESSDATA_PREFIX vers tessdata

Forcer l'arabe en psm=6

Pas de repli forcé vers le français

### Windows (PowerShell)
```powershell
$env:PATH = "C:\Program Files\Tesseract-OCR;$env:PATH"
$env:TESSDATA_PREFIX = (Resolve-Path .\tessdata).Path
tesseract --list-langs
.\.venv\Scripts\python.exe -c "import pytesseract; print(pytesseract.get_languages())"
```

### Linux/macOS (bash)
```bash
export TESSDATA_PREFIX="$(pwd)/tessdata"
tesseract --list-langs
python -c "import pytesseract; print(pytesseract.get_languages())"
```

### Stabilisation

tessdata Windows-safe : on privilégie TESSDATA_PREFIX, sinon --tessdata-dir "<chemin posix>".

Arabe PSM=6 (bloc de texte).

Fallback arabe : si aucune région n'est détectée, on tente l'arabe sur toute la page.

### Dépannage

Si l'arabe ressort en latin : activer LSTM-only dans src/ocr/base.py (commentaire dans le code).

</details>

<details><summary><strong>🇸🇦 العربية (انقر للتوسيع)</strong></summary><div dir="rtl">

### البدء السريع

تعيين TESSDATA_PREFIX إلى مجلد tessdata

إجبار العربية على psm=6

لا يوجد تراجع افتراضي إلى الفرنسية

### ويندوز (PowerShell)
```powershell
$env:PATH = "C:\Program Files\Tesseract-OCR;$env:PATH"
$env:TESSDATA_PREFIX = (Resolve-Path .\tessdata).Path
tesseract --list-langs
.\.venv\Scripts\python.exe -c "import pytesseract; print(pytesseract.get_languages())"
```

### لينكس/ماك (bash)
```bash
export TESSDATA_PREFIX="$(pwd)/tessdata"
tesseract --list-langs
python -c "import pytesseract; print(pytesseract.get_languages())"
```

### الاستقرار

مسار tessdata متوافق مع ويندوز: أولوية لـ TESSDATA_PREFIX وإلا --tessdata-dir "<مسار posix>".

العربية PSM=6.

تشغيل العربية على الصفحة كاملة عند عدم اكتشاف مناطق عربية.

### استكشاف الأخطاء

إن ظهرت العربية بحروف لاتينية: فعّل نمط LSTM-only في src/ocr/base.py (مذكور داخل الكود).

</div></details>i.yml/badge.svg?branch=main)](https://github.com/wizardus999-code/OCR-intern/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-informational)
![License](https://img.shields.io/github/license/wizardus999-code/OCR-intern)
![Status](https://img.shields.io/badge/status-Alpha-blue)

End-to-end OCR system optimized for Moroccan administrative documents with bilingual (FR+AR) processing, multi-format export (PDF/Word/Excel/JSON), performance analytics, and a GUI dashboard. Includes automated testing and CI/CD integration.

> 🌍 Translations: **[Français](#-français-cliquez-pour-développer)** • **[العربية](#-العربية-انقر-للتوسيع)**

---

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
