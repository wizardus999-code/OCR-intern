---
name: Receipt Pattern Validation
about: Verify receipt number extraction against sample set
title: 'feat: Receipt number pattern validation and confidence scoring'
labels: feature, validation
assignees: ''
---

## Description
Implement and validate receipt number extraction with pattern matching and confidence scoring.

## Pattern Requirements
- Format: `20YY/NNNN`
  - Year: 2020-2025
  - Number: 3-5 digits
  - Separator: /
- Normalized Regex: `^(20\d{2})/(\d{3,6})$`

### Confidence Policy
- Base confidence: 85 for pattern match
- Token confidence boost:
  - Max of (base, token confidence)
  - 95 if sanitized raw == normalized
  - Clamp final to range [40, 99]

## Test Cases
### Valid Formats
- [ ] Standard: "2025/1234"
- [ ] Min digits: "2024/123"
- [ ] Max digits: "2023/12345"

### Invalid Formats
- [ ] Wrong year: "2019/1234", "2026/1234"
- [ ] Wrong digits: "2025/12", "2025/123456"
- [ ] Wrong separator: "2025-1234"
- [ ] Mixed spaces: "2025 / 1234"

### Edge Cases
- [ ] Arabic-Indic digits
- [ ] Unicode slash variants
- [ ] Mixed numeral systems
- [ ] Whitespace variations

## OCR Configuration
```python
config = '--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789/.'
```

## Confidence Scoring
- [ ] Base confidence ≥85 for pattern match
- [ ] Boost to ≥95 for exact normalization
- [ ] Take max(base, token_confidence)
- [ ] Clamp to range [40, 99]

## Implementation Tasks
- [ ] Pattern matching function
- [ ] Confidence calculation
- [ ] Arabic numeral normalization
- [ ] Test suite with all cases

## Acceptance Criteria
- [ ] ≥98% valid detection on sample set
- [ ] No false positives on out-of-range values
- [ ] All test cases pass
- [ ] Performance within spec (<2s per extraction)

## Additional Context
- Sample images in tests/fixtures/
- Ground truth in tests/fixtures/expected/
- Performance benchmarks required
