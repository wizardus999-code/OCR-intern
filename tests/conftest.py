import os, pathlib

def pytest_sessionstart(session):
    root = pathlib.Path(__file__).resolve().parents[1]
    td = root / "tessdata"
    if td.exists():
        os.environ["TESSDATA_PREFIX"] = str(td)
    # keep CLI encoding stable on Windows
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")