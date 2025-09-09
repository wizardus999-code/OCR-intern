# Detailed Validation Guide - September 8, 2025

## 1. Import Resolution

### Clear Caches
```powershell
# PowerShell
Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
```

```bash
# Bash
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
```

### Sanity Import Checks
```python
import importlib
import sys
print(sys.path)
import ocr.base
print('OK')
```

### Package Setup
- Editable install: `pip install -e .`
- Verify imports work:
  ```python
  from ocr.base import BaseOCREngine  # Should load without ImportError
  ```

### Import Chain Verification
```
src/ocr/
├── __init__.py
├── base.py (BaseOCREngine, OCRResult)
├── arabic.py (imports BaseOCREngine)
├── hybrid.py (imports ArabicOCR)
└── receipt.py (imports HybridOCR)
```

## 2. Environment Validation

### Tesseract Setup (Windows)
```powershell
$env:PATH = "C:\Program Files\Tesseract-OCR;$env:PATH"
$env:TESSDATA_PREFIX = (Resolve-Path .\tessdata).Path
tesseract --version
```

### Language Pack Verification
```python
import pytesseract
print(pytesseract.get_languages())  # Should show ['ara', 'fra']
```

### Path Resolution Test
```python
from pathlib import Path
print(Path(os.getenv('TESSDATA_PREFIX', './tessdata')).resolve())
```

## 3. Test Suite Execution

### Quick Unit Tests
```powershell
pytest -q tests/unit
```

### Full Test Suite
```powershell
python -m pytest -vv -x  # Stop on first failure
```

### Coverage & Performance
```powershell
pytest --cov=src tests/  # Coverage goal: ≥80%
pytest --benchmark-only  # Performance baseline
```

### Test Gates
- All unit/integration tests must pass
- Coverage must be ≥80%
- No regressions in benchmarks

## 4. Receipt Number Validation

### Pattern Requirements
- Format: `20YY/NNNN`
  - Year bounds: 2020–2025
  - Digits: 3-5 numbers after slash
- Confidence thresholds:
  - ≥85 for pattern match
  - ≥95 for exact normalization

### OCR Configuration
```python
config = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789/.'
```

### Preprocessing
- Normalize Arabic-Indic digits
- Strip whitespace and normalize slashes
- Validate year and number format

### Edge Cases
- Arabic-Indic digits
- Wrong year (2019/1234)
- Out-of-range (2026/1234)
- Digit count (2025/12, 2025/123456)
- Separator variants (2025-1234)
- Mixed spaces (2025 / 1234)
- Unicode slash variants

## 5. ROI Extraction Check

### Reference ROI Parameters
- Top area location
- ~12% from left edge
- 30% width span
- 10% height from top

### Validation Requirements
- Test with synthetic crops
- Verify with real samples
- Edge case handling:
  - Rotated documents (slight tilt)
  - Low DPI (150)
  - Overlapping stamps
  - Partial crops

### ROI Fallback Chain
1. Try `regions["receipt_no"]`
2. Fall back to `regions["association_receipt"]`
3. Last resort: use full image

## 6. Arabic Processing Verification

### Core Configuration
- Force PSM=6 for block text
- Enable reshaping + bidi handling
- Verify proper character forms

### Test Cases
- Dense paragraphs
- Text with diacritics
- Bidi punctuation
- Column layouts
- Mixed numeric content

### Configuration Verification
```python
# Check in arabic.py
assert config_dict['psm'] == 6, "PSM must be 6 for Arabic blocks"
assert '--oem 1' in config, "LSTM mode required"
```

## 7. Cross-Platform Compatibility

### Tessdata Resolution (Windows-safe)
1. Check env var: `TESSDATA_PREFIX`
2. Fall back: repo `./tessdata`
3. Verify both Windows & Linux paths

### Path Construction
```python
tessdata_path = os.getenv('TESSDATA_PREFIX', './tessdata')
tessdata_path = Path(tessdata_path).resolve()
```

### Cross-Platform Verification
- Run same test batch on:
  - Windows 10/11
  - Ubuntu 22.04
  - Verify results match

## 8. Performance Benchmarks

### Target Metrics
- Total processing: <4s per doc
  - OCR phase: <2s
  - Analysis: <1s
  - Post-processing: <0.5s

### Accuracy Targets
- Overall: ~96.5%
  - Arabic text: ~95%
  - Receipt numbers: ~98%

### Memory Profiling
- Base footprint: ~100MB
- Peak usage: <200MB
- Batch overhead: +50MB/doc

### GitHub Issue Templates

See `RELEASE_CHECKLIST.md` for complete templates for:
1. Import Resolution
2. Test Suite Completion
3. Receipt Pattern Validation
4. Cross-Platform Validation
5. Performance Optimization

### Validation Commands

Windows (PowerShell):
```powershell
# 1. Environment check
tesseract --version
python -c "import pytesseract; print(pytesseract.get_languages())"

# 2. Clear cache & reinstall
Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
pip install -e .

# 3. Test suite
python -m pytest -vv -x
pytest --cov=src tests/
pytest --benchmark-only
```

Linux (Bash):
```bash
tesseract --version
python - <<'PY'
import pytesseract; print(pytesseract.get_languages())
PY

find . -name "__pycache__" -type d -prune -exec rm -rf {} +
pip install -e .
pytest -q tests/unit
pytest -vv -x
pytest --cov=src tests/
```
