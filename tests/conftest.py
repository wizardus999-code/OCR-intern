from __future__ import annotations
import os, sys
from pathlib import Path

# Make `src` importable in tests
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Use repo-local tessdata for CI/local runs
repo_tessdata = ROOT / "tessdata"
if repo_tessdata.exists():
    os.environ.setdefault("TESSDATA_PREFIX", str(repo_tessdata))
