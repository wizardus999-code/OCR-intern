---
name: Release Gate Checklist
about: Enforce quality bars before tagging & packaging
title: "[REL] Gate: quality, performance, docs"
labels: "area:release, type:process, priority:medium"
assignees: ""
---

## Gate Items
- [ ] Test Quality
  - All unit tests green
  - All integration tests green
  - Coverage ≥ 80%
  - No skipped tests

- [ ] Receipt Extraction
  - ≥98% valid on sample set
  - Confidence ≥85 when pattern matched
  - Confidence ≥95 when exact normalized match
  - Correct handling of edge cases

- [ ] Arabic Processing
  - Quality checks pass
  - Hybrid fallback working
  - PSM=6 enforced
  - No Latin confusion

- [ ] Performance
  - Total processing: < 4s/doc
  - OCR phase: < 2s/doc on CI slab
  - Memory usage: < 500MB peak per doc
  - Stable under batch processing

- [ ] Cross-Platform
  - Windows tests green
  - Ubuntu tests green
  - Environment validation complete
  - Path handling correct

- [ ] Documentation
  - RELEASE_CHECKLIST.md updated
  - DETAILED_VALIDATION.md current
  - INSTALLATION.md verified
  - All TODOs addressed

- [ ] Release Package
  - ZIP archive assembled
  - Required files included
  - Version tagged (e.g., v0.3.0)
  - Release notes prepared

## Commands
```powershell
# Full test suite
pytest -vv -x

# Coverage check
pytest --cov=src tests/

# Performance validation
pytest --benchmark-only
```

## Acceptance Criteria
- [ ] All checkboxes ticked with:
  - Links to passing CI runs
  - Test coverage report
  - Performance metrics
  - Artifact links
- [ ] Tagged release created
- [ ] Release package available for download

## Notes
- Performance numbers must be reproducible on CI
- Memory usage should be stable in long-running tests
- Document any known limitations or edge cases
