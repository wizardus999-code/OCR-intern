---
name: ROI Extraction Validation
about: Validate receipt/field ROIs with visual overlays & assertions
title: "[ROI] Validate & harden ROI extraction"
labels: "area:roi, type:test, priority:medium"
assignees: ""
---

## Goal
Ensure ROIs consistently isolate intended text (especially `body.receipt_no`) across synthetic and real samples.

## Tasks
- [ ] Add debug overlay script to draw ROIs over documents (saved to `artifacts/roi_debug/`)
- [ ] Add unit tests:
  - Non-empty ROI verification
  - Minimum area > 0 check
  - Mean contrast threshold validation
- [ ] For receipt:
  - Test optional ~12% left-crop (to skip "Reçu Nº" label)
  - Verify template bbox excludes label
- [ ] Add integration tests with:
  - Slight shifts/rotation
  - Low DPI (150)
  - Stamp overlap scenarios

## Commands
```bash
pytest -q tests/roi
python scripts/roi_overlay.py --image samples/assoc_fake.png --out artifacts/roi_debug/overlay.png
```

## Acceptance Criteria
- [ ] No "empty ROI" failures on test fixtures
- [ ] No "low contrast" failures on test fixtures
- [ ] Visual overlays show digits-only inside receipt ROI
- [ ] Tests pass on:
  - Windows
  - Ubuntu
  - CI environment
