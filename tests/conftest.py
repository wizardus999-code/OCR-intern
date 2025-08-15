"""Test configuration and fixtures."""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

# Make `src` importable in tests
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_sessionstart(session):
    """Set up test environment before session."""
    # Ensure tessdata is present
    repo_tessdata = ROOT / "tessdata"
    if (
        not (repo_tessdata / "fra.traineddata").exists()
        or not (repo_tessdata / "ara.traineddata").exists()
    ):
        print("\nFetching tessdata files...")
        subprocess.run(
            ["powershell", "-File", str(ROOT / "scripts" / "fetch_tessdata.ps1")],
            check=True,
        )

    # Set up Tesseract if not available
    try:
        subprocess.run(["tesseract", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\nSetting up Tesseract...")
        subprocess.run(
            ["powershell", "-File", str(ROOT / "scripts" / "setup_tesseract.ps1")],
            check=True,
        )

    # Ensure environment variables are set
    os.environ.setdefault("TESSDATA_PREFIX", str(repo_tessdata))
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
