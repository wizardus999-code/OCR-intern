# Development Requirements

## Core Dependencies
```txt
pytesseract==0.3.10
opencv-python>=4.12,<5
numpy>=2.1
Pillow>=10.3
python-dotenv==1.0.0
tqdm==4.65.0
reportlab>=4.2
```

## Text Processing
```txt
arabic-reshaper==3.0.0
python-bidi==0.4.2
langdetect==1.0.9
```

## GUI and Document Processing
```txt
PyQt6>=6.7
pdf2image==1.16.3
python-docx==0.8.11
openpyxl==3.1.2
```

## Data Analysis
```txt
pandas>=2.2
matplotlib>=3.9
seaborn>=0.13
```

## Testing Tools
```txt
pytest==7.4.0
pytest-benchmark==4.0.0
pytest-cov==4.1.0
```

## Development Tools
```txt
black==23.7.0
mypy==1.4.1
pylint==2.17.5
```

## System Requirements

### Tesseract OCR
- Version: 5.0.0 or higher
- Languages: Arabic (ara) and French (fra)
- Installation:
  - Windows: Use installer from https://github.com/UB-Mannheim/tesseract/wiki
  - Linux: `apt install tesseract-ocr tesseract-ocr-ara tesseract-ocr-fra`

### Python
- Version: 3.10 or higher
- Virtual Environment recommended

### System Libraries
- poppler-utils (for pdf2image)
- qt6 (for GUI components)

## Installation Steps

1. System Setup
```powershell
# Windows (using chocolatey)
choco install tesseract
choco install poppler

# Set environment variables
$env:PATH = "C:\Program Files\Tesseract-OCR;$env:PATH"
$env:TESSDATA_PREFIX = "C:\Program Files\Tesseract-OCR\tessdata"
```

2. Python Environment
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

3. Verify Installation
```python
import pytesseract
print(pytesseract.get_languages())  # Should show 'ara' and 'fra'
```

## Development Setup

1. Code Style
```bash
# Format code
black src/ tests/

# Type checking
mypy src/

# Linting
pylint src/
```

2. Testing
```bash
# Run tests with coverage
pytest --cov=src tests/

# Performance benchmarks
pytest --benchmark-only
```

## Common Issues

1. Tesseract Path
- Windows: Ensure TESSDATA_PREFIX is set
- Linux: Check /usr/share/tesseract-ocr/tessdata

2. Arabic Support
- Verify ara.traineddata is present
- Check Arabic reshaper installation

3. Performance
- Use --oem 1 for LSTM only mode
- Configure page segmentation mode (PSM) appropriately
