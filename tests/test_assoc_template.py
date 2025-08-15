from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(cmd, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",  # ensure UTF-8 decoding
        errors="replace",  # safely handle any decode errors
    )


def test_assoc_smoke():
    # 1) Make a synthetic receipt image
    out_img = ROOT / "samples" / "assoc_fake.png"
    out_img.parent.mkdir(parents=True, exist_ok=True)
    run([PY, str(ROOT / "scripts" / "gen_fake_assoc.py"), "-o", str(out_img)])

    # 2) Run template extractor (prints JSON)
    cp = run(
        [
            PY,
            str(ROOT / "scripts" / "test_extractor_assoc.py"),
            "--image",
            str(out_img),
            "--template",
            "assoc_receipt",
        ]
    )
    data = json.loads(cp.stdout)
    f = data["fields"]

    # Title FR exists and has decent confidence
    assert f["title.fr"]["valid"] is True
    assert f["title.fr"]["conf"] >= 50

    # Commune mentions Casablanca
    assert "casablanca" in f["header.commune.fr"]["value"].lower()

    # Date normalized ISO and confident
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", f["body.date.fr"]["norm"])
    assert f["body.date.fr"]["valid"] is True
    assert f["body.date.fr"]["conf"] >= 50

    # Receipt number format like 2024/1234 and decent confidence
    rn = f["body.receipt_no"]
    assert re.fullmatch(r"\d{4}/\d{3,5}", rn["norm"]), rn
    assert rn["valid"] is True
    assert rn["conf"] >= 40
