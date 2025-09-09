---
name: Import Resolution
about: Fix BaseOCREngine import path and verify module structure
title: 'fix: Import resolution for BaseOCREngine and module structure'
labels: bug, high-priority
assignees: ''
---

## Description
Resolve import issues with `BaseOCREngine` and ensure proper module structure.

## Steps to Reproduce
1. Try importing BaseOCREngine:
```python
from ocr.base import BaseOCREngine
```
2. Observe ImportError

## Expected Behavior
- `from ocr.base import BaseOCREngine` loads without ImportError
- All dependent modules load correctly

## Current Behavior
ImportError when trying to import BaseOCREngine

## Tasks
- [ ] Clear Python caches:
  ```powershell
  Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
  ```
- [ ] Verify module structure:
  ```
  src/ocr/
  ├── __init__.py
  ├── base.py
  ├── arabic.py
  ├── hybrid.py
  └── receipt.py
  ```
- [ ] Test import chain:
  ```python
  from src.ocr.base import BaseOCREngine, OCRResult
  from src.ocr.arabic import ArabicOCR
  from src.ocr.hybrid import HybridOCR
  ```
- [ ] Install package in editable mode:
  ```bash
  pip install -e .
  ```

## Acceptance Criteria
- [ ] All imports work without errors
- [ ] Module structure is correct
- [ ] Package installs cleanly
- [ ] No stale cache files present

## Additional Context
- Python version: 3.13
- Project structure follows standard package layout
- Using pip's editable install mode
