# Environment Setup Guide - September 8, 2025

## System Requirements

### Windows
- Windows 10/11
- PowerShell 5.1+
- Tesseract 5.x
- Python 3.13+

### Linux
- Ubuntu 22.04 LTS
- Bash 5.x
- Tesseract 5.x
- Python 3.13+

## Installation Steps

### 1. Tesseract Setup

#### Windows
```powershell
# Add Tesseract to PATH
$env:PATH = "C:\Program Files\Tesseract-OCR;$env:PATH"

# Set tessdata directory
$env:TESSDATA_PREFIX = (Resolve-Path .\tessdata).Path

# Verify installation
tesseract --version
```

#### Linux
```bash
# Install Tesseract
sudo apt update
sudo apt install -y tesseract-ocr

# Set tessdata directory
export TESSDATA_PREFIX="./tessdata"

# Verify installation
tesseract --version
```

### 2. Language Packs

#### Required Languages
- Arabic (ara)
- French (fra)

#### Verification
```python
import pytesseract
print(pytesseract.get_languages())  # Should show ['ara', 'fra']
```

### 3. Python Environment

#### Virtual Environment
```powershell
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux
python3 -m venv .venv
source .venv/bin/activate
```

#### Dependencies
```bash
python -m pip install -U pip
pip install -r requirements.txt
pip install -e .
```

## Verification Steps

### 1. Tesseract Check
```powershell
# Check version
tesseract --version

# List languages
tesseract --list-langs
```

### 2. Python Environment
```python
# Check imports
from ocr.base import BaseOCREngine
from ocr.arabic import ArabicOCR
from ocr.hybrid import HybridOCR

# Verify pytesseract
import pytesseract
print(pytesseract.get_languages())
```

### 3. Test Suite
```powershell
# Clear caches
Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force

# Run tests
pytest -vv -x
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
```powershell
# Clear Python cache
Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force

# Reinstall package
pip install -e .
```

#### 2. Tesseract Not Found
```powershell
# Windows: Check PATH
Write-Host $env:PATH

# Check TESSDATA_PREFIX
Write-Host $env:TESSDATA_PREFIX
```

#### 3. Missing Languages
```powershell
# Verify tessdata contents
Get-ChildItem .\tessdata\*.traineddata

# Check language detection
python -c "import pytesseract; print(pytesseract.get_languages())"
```

## Performance Tuning

### Memory Optimization
```python
# Recommended settings
import gc
gc.enable()
```

### Processing Speed
```python
# Optimal thread count
num_threads = min(os.cpu_count(), 4)
```

## Maintenance

### Cache Cleanup
```powershell
# Remove Python cache
Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force

# Clear temp files
Remove-Item .\tmp_*.png
```

### Updates
```powershell
# Update dependencies
pip install -U -r requirements.txt

# Rebuild package
pip install -e .
```

## CI/CD Configuration

### Environment Variables
```yaml
env:
  TESSDATA_PREFIX: ./tessdata
  PYTHONPATH: ./src
  PYTHONUNBUFFERED: 1
```

### Test Configuration
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
```

## Development Tools

### VS Code Extensions
- Python
- Pylance
- Test Explorer UI
- Coverage Gutters

### Git Configuration
```bash
# Ignore patterns
__pycache__/
*.pyc
.coverage
tmp_*.png
```
