---
name: CI/CD Matrix & Caching
about: Windows + Ubuntu CI with Tesseract & tessdata, pip cache, artifacts
title: "[CI] Add Windows/Ubuntu matrix + caching + artifacts"
labels: "area:ci, type:infra, priority:medium"
assignees: ""
---

## Goal
Run tests in GitHub Actions on Windows & Ubuntu with Tesseract installed, `ara/fra` models, and cached deps.

## Tasks
- [ ] Add matrix jobs:
  - `windows-latest`
  - `ubuntu-latest`
- [ ] Install requirements:
  - Tesseract OCR
  - Download `ara` and `fra` traineddata
  - Configure tessdata path
- [ ] Environment setup:
  - Export `TESSDATA_PREFIX`
  - Verify languages in CI logs
  - Configure Python environment
- [ ] Implement caching:
  - Use `actions/setup-python@v5` with caching
  - Cache pip dependencies
  - Cache tessdata models
- [ ] Configure artifacts:
  - Logs on failure
  - ROI overlay images
  - Sample outputs
  - Test reports

## Example Workflow
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        os: [windows-latest, ubuntu-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
          cache: 'pip'
      # ... Tesseract install steps ...
      - run: |
          tesseract --version
          tesseract --list-langs
```

## Acceptance Criteria
- [ ] Both Windows and Ubuntu jobs pass:
  - Unit tests green
  - Integration tests green
  - Performance benchmarks within spec
- [ ] CI logs show:
  - `ara` and `fra` available
  - Correct `TESSDATA_PREFIX`
  - Python environment ready
- [ ] Artifacts uploaded on failure:
  - Test logs preserved
  - Debug images available
  - Performance reports included
