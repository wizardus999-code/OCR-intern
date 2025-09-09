---
name: Cross-Platform Validation
about: Ensure consistent behavior across Windows and Linux
title: 'test: Cross-platform validation and Windows compatibility'
labels: testing, compatibility
assignees: ''
---

## Description
Validate OCR functionality across Windows and Linux platforms with focus on path handling and Tesseract integration.

## Platform Requirements
### Windows
- [ ] Windows 10/11
- [ ] PowerShell environment
- [ ] Tesseract 5.x

### Linux
- [ ] Ubuntu 22.04 LTS
- [ ] Bash environment
- [ ] Tesseract 5.x

## Validation Tasks
### Path Handling
- [ ] TESSDATA_PREFIX resolution:
  ```python
  tessdata_path = os.getenv('TESSDATA_PREFIX', './tessdata')
  tessdata_path = Path(tessdata_path).resolve()
  ```
- [ ] Windows-safe path construction
- [ ] POSIX path compatibility
- [ ] Relative path support

### Environment Setup
Windows:
```powershell
$env:PATH = "C:\Program Files\Tesseract-OCR;$env:PATH"
$env:TESSDATA_PREFIX = (Resolve-Path .\tessdata).Path
```

Linux:
```bash
export TESSDATA_PREFIX="./tessdata"
```

### Test Execution
- [ ] Run identical test set on both platforms
- [ ] Compare results hash for consistency
- [ ] Verify performance metrics

## Test Cases
- [ ] Import resolution
- [ ] Language pack detection
- [ ] Receipt number extraction
- [ ] Arabic text processing
- [ ] ROI extraction

## Acceptance Criteria
- [ ] All tests pass on both platforms
- [ ] Identical results between platforms
- [ ] Performance within 10% variance
- [ ] No platform-specific errors
- [ ] CI logs show:
  - `ara` and `fra` available
  - Correct `TESSDATA_PREFIX` setting
  - Environment variables properly set

## Additional Context
- CI/CD matrix configuration needed
- Environment setup documentation required
- Platform-specific troubleshooting guide
