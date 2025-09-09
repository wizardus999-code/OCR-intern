# Release Validation Checklist - September 8, 2025

## 1. Import Resolution
- [ ] Clear Python cache files:
  ```powershell
  Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
  ```
- [ ] Verify module structure:
  ```
  src/ocr/
  ├── __init__.py
  ├── base.py (BaseOCREngine, OCRResult)
  ├── arabic.py (imports BaseOCREngine)
  ├── hybrid.py (imports ArabicOCR)
  └── receipt.py (imports HybridOCR)
  ```
- [ ] Test imports in Python REPL:
  ```python
  from src.ocr.base import BaseOCREngine, OCRResult
  from src.ocr.arabic import ArabicOCR
  from src.ocr.hybrid import HybridOCR
  ```

## 2. Environment Validation
- [ ] Verify Tesseract setup:
  ```powershell
  $env:PATH = "C:\Program Files\Tesseract-OCR;$env:PATH"
  $env:TESSDATA_PREFIX = (Resolve-Path .\tessdata).Path
  tesseract --list-langs  # Should show ara,fra
  ```
- [ ] Check Python environment:
  ```powershell
  .\.venv\Scripts\python.exe -c "import sys,pytesseract; print('PY:', sys.executable); print('LANGS:', pytesseract.get_languages())"
  ```

## 3. Test Suite Execution
- [ ] Run full test suite:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest -vv -x
  ```
- [ ] Run receipt OCR test:
  ```powershell
  .\.venv\Scripts\python.exe scripts/test_receipt_ocr.py samples/assoc_fake.png
  ```

## 4. Receipt Number Validation
- [ ] Pattern matching:
  - Format: `20YY/NNNN` where NNNN is 3-5 digits
  - Example valid: "2025/12345", "2024/123"
  - Example invalid: "2026/12", "19999/123"

- [ ] Confidence scoring:
  - Base confidence: 85 for pattern match
  - Boost to 95 if raw == normalized
  - Take max of (base, token confidence)
  - Clamp final to range [40, 99]

## 5. ROI Extraction Check
- [ ] Primary method:
  - Use region from result["regions"]["receipt_no"]
  - Fallback to result["regions"]["association_receipt"]
  - Last resort: use full image

- [ ] ROI heuristic validation:
  - Left margin: 12% of image width
  - Height: top 10% of document
  - Test with sample images of varying sizes

## 6. Arabic Processing Verification
- [ ] Confirm PSM=6 for Arabic blocks:
  ```python
  # in src/ocr/arabic.py
  results = self.process_image(image, lang='ara', psm=6)
  ```
- [ ] Verify hybrid layout fallback:
  - Arabic-only full-page fallback exists
  - No French full-page fallback present

## 7. Cross-Platform Compatibility
- [ ] Windows path handling:
  - TESSDATA_PREFIX takes precedence if exists
  - Fallback to repo ./tessdata with POSIX path
  - Test both absolute and relative paths

## 8. Performance Benchmarks
- [ ] Measure processing times:
  - Document analysis: < 1s
  - OCR processing: < 2s
  - Post-processing: < 0.5s
  - Total per document: < 4s

- [ ] Memory usage:
  - Base process: ~100MB
  - Peak usage: < 200MB
  - Batch processing: +50MB per doc

## GitHub Issues Template

```markdown
### Import Resolution
Fix BaseOCREngine import path and verify module structure
- [ ] Clear Python caches
- [ ] Verify import chain
- [ ] Add explicit exports if needed

### Test Suite Completion
Complete integration test coverage for OCR components
- [ ] Fix existing test failures
- [ ] Add receipt number validation tests
- [ ] Add cross-platform path tests

### Receipt Pattern Validation
Verify receipt number extraction against sample set
- [ ] Test pattern matching
- [ ] Validate confidence scoring
- [ ] Check ROI extraction

### Cross-Platform Validation
Ensure consistent behavior across platforms
- [ ] Test Windows path handling
- [ ] Verify tessdata resolution
- [ ] Check Arabic text processing

### Performance Optimization
Measure and optimize processing performance
- [ ] Benchmark processing times
- [ ] Monitor memory usage
- [ ] Test batch processing
```

## Release Criteria
1. All tests passing (pytest -vv -x)
2. Receipt extraction success rate > 95%
3. Arabic text recognition accuracy > 90%
4. Memory usage within limits
5. Processing time targets met
6. Windows compatibility verified
