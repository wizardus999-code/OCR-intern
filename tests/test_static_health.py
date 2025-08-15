import os, re, io
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "src"

def read_py_files(root: Path):
    for p in root.rglob("*.py"):
        txt = p.read_text(encoding="utf-8", errors="replace")
        yield p, txt

def test_no_lingering_process_calls():
    bad = []
    for p, txt in read_py_files(ROOT):
        safe = txt.replace(".process_document(", "")
        if re.search(r"\.process\s*\(", safe):
            bad.append(str(p))
    assert not bad, f"Lingering .process( in: {bad}"

def test_no_print_in_src():
    bad = []
    for p, txt in read_py_files(ROOT):
        if "print(" in txt:
            bad.append(str(p))
    assert not bad, f"Use logging, not print(): {bad}"
