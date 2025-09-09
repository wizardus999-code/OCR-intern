---
name: Environment Validation (Windows/Linux)
about: Verify Tesseract + tessdata + Python env are correctly configured
title: "[ENV] Validate Tesseract & Python environment"
labels: "area:env, type:task, priority:high"
assignees: ""
---

## Goal
Ensure consistent local & CI environments (PATH/TESSDATA_PREFIX, ara/fra available, pytesseract functional).

## Tasks
- [ ] Windows: set PATH + TESSDATA_PREFIX; capture `tesseract --version`
- [ ] Verify languages: `tesseract --list-langs` shows `ara` and `fra`
- [ ] Python check: `python -c "import pytesseract; print(pytesseract.get_languages())"`
- [ ] Clear caches (`__pycache__`) and do `pip install -e .`
- [ ] Document steps in INSTALLATION.md / DETAILED_VALIDATION.md

## Commands (Win PowerShell)
```powershell
$env:PATH = "C:\Program Files\Tesseract-OCR;$env:PATH"
$env:TESSDATA_PREFIX = (Resolve-Path .\tessdata).Path
tesseract --version
tesseract --list-langs
python -c "import pytesseract; print(pytesseract.get_languages())"
Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
pip install -e .
```

## Acceptance Criteria
- [ ] `ara` and `fra` present in both `tesseract --list-langs` and `pytesseract.get_languages()`
- [ ] Steps documented and reproducible on:
  - Clean Windows host
  - CI runner
  - Development environment
