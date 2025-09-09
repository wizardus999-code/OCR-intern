---
name: Arabic Processing Verification
about: Enforce PSM=6 and verify quality & fallback behavior
title: "[AR] Verify Arabic OCR stability (PSM=6)"
labels: "area:arabic, type:test, priority:high"
assignees: ""
---

## Goal
Confirm Arabic blocks use PSM=6, respect Windows-safe tessdata, and avoid Latin-like noise.

## Tasks
- [ ] Assert code path:
  ```python
  ArabicOCR.process_document(..., psm=6)
  ```
- [ ] Add Arabic paragraph fixtures:
  - Diacritics
  - Punctuation
  - RTL text
  - Mixed content
- [ ] Add test for LSTM-only flag:
  - Verify flag can be enabled
  - Test with and without LSTM mode
  - Document performance differences
- [ ] Verify hybrid analyzer:
  - Arabic full-page fallback present
  - No French full-page fallback
  - Correct language selection

## Commands
```bash
pytest -q tests/arabic
pytest -vv -k "arabic and psm6"
```

## Acceptance Criteria
- [ ] Tests confirm PSM=6 is in effect
- [ ] Arabic fixtures produce proper Arabic glyphs:
  - No Latin character confusion
  - Correct character shapes
  - Proper diacritic placement
- [ ] Hybrid fallback rules enforced:
  - Arabic-only fallback works
  - No French fallback attempted
- [ ] All tests pass on Windows and Linux
