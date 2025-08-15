import os, re, sys, json, io
from pathlib import Path
from typing import Dict, Any

ROOT = Path(".").resolve()

def info(msg):
    print(f"[info] {msg}")

def warn(msg):
    print(f"[warn] {msg}")

def write_if_changed(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    old = None
    if path.exists():
        old = path.read_text(encoding="utf-8", errors="replace")
    if old != content:
        path.write_text(content, encoding="utf-8")
        info(f"wrote: {path}")
    else:
        info(f"unchanged: {path}")

def replace_in_file(path: Path, pattern: re.Pattern, repl: str) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    new = pattern.sub(repl, text)
    if new != text:
        path.write_text(new, encoding="utf-8")
        return True
    return False

def update_gui_process_calls():
    changed = 0
    gui_dir = ROOT / "gui"
    if not gui_dir.exists():
        warn("gui/ not found; skipping GUI refactor")
        return changed
    pat = re.compile(r"\.process\s*\(")
    for p in gui_dir.rglob("*.py"):
        if replace_in_file(p, pat, ".process_document("):
            changed += 1
            info(f"refactored .process( -> .process_document( in {p}")
    return changed

def make_preproc_module():
    content = r'''from typing import List, Dict, Any
from statistics import median
from PIL import Image, ImageOps, ImageFilter

def otsu_threshold(gray: "Image.Image") -> int:
    hist = gray.histogram()
    total = sum(hist)
    sum_total = sum(i*h for i, h in enumerate(hist))
    sum_bg = 0
    w_bg = 0
    var_max = -1.0
    threshold = 127
    for t in range(256):
        w_bg += hist[t]
        if w_bg == 0:
            continue
        w_fg = total - w_bg
        if w_fg == 0:
            break
        sum_bg += t * hist[t]
        mean_bg = sum_bg / w_bg
        mean_fg = (sum_total - sum_bg) / w_fg
        var_between = w_bg * w_fg * (mean_bg - mean_fg) ** 2
        if var_between > var_max:
            var_max = var_between
            threshold = t
    return threshold

def apply_preproc(img: "Image.Image", cfg: Dict[str, Any]) -> "Image.Image":
    g = img.convert("L")
    scale = float(cfg.get("resize", 1.0))
    if scale and abs(scale - 1.0) > 1e-3:
        w = max(1, int(g.width * scale))
        h = max(1, int(g.height * scale))
        g = g.resize((w, h), Image.LANCZOS)
    if cfg.get("binarize", "none") == "otsu":
        thr = otsu_threshold(g)
        g = g.point(lambda p, t=thr: 255 if p >= t else 0)
    if bool(cfg.get("invert", False)):
        g = ImageOps.invert(g)
    dilate_n = int(cfg.get("dilate", 0))
    for _ in range(max(0, dilate_n)):
        g = g.filter(ImageFilter.MaxFilter(3))
    return g

def median_digit_confidence(tokens: List) -> float:
    vals = []
    for t in tokens:
        # support dict- and object-like tokens
        txt = getattr(t, "text", None)
        if txt is None and isinstance(t, dict):
            txt = t.get("text", "")
        txt = txt or ""
        if any(ch.isdigit() for ch in txt):
            conf = getattr(t, "confidence", None)
            if conf is None and isinstance(t, dict):
                conf = t.get("confidence", t.get("conf", 0.0))
            try:
                vals.append(float(conf))
            except Exception:
                pass
    if not vals:
        return 0.0
    return float(median(vals))
'''
    target = ROOT / "src" / "ocr" / "preproc_pil.py"
    write_if_changed(target, content)

def soft_update_templates():
    # only add "preproc" to likely numeric fields — be conservative
    path = ROOT / "assets" / "templates" / "morocco_templates.json"
    if not path.exists():
        warn("assets/templates/morocco_templates.json not found; skipping template touch")
        return False
    raw = path.read_bytes()
    # handle utf-8-sig
    try:
        text = raw.decode("utf-8-sig")
    except Exception:
        text = raw.decode("utf-8", errors="replace")
    try:
        data = json.loads(text)
    except Exception as e:
        warn(f"cannot parse JSON ({e}); abort template changes")
        return False
    changed = False
    def is_numeric_field(fd: Dict[str, Any]) -> bool:
        wl = (fd.get("whitelist") or "")
        sel = fd.get("select")
        return any(ch.isdigit() for ch in wl) or sel in {"digits"} or fd.get("validator",{}).get("pattern","").startswith("^[0-9")
    def add_preproc(fd: Dict[str, Any]) -> bool:
        if "preproc" in fd:
            return False
        fd["preproc"] = {"binarize":"otsu","dilate":1,"invert":False,"resize":1.3}
        return True
    # support either a list under "templates" or a dict of templates
    container = data.get("templates", data)
    if isinstance(container, dict):
        templates_iter = container.values()
    else:
        templates_iter = container
    for t in templates_iter:
        fields = None
        if "fields" in t:  # flat fields
            fields = t["fields"]
        elif "regions" in t:  # nested regions/fields
            # flatten all dicts under regions
            fields = {}
            def collect(d):
                for k, v in d.items():
                    if isinstance(v, dict) and {"roi","psm"} & set(v.keys()):
                        fields[k] = v
                    elif isinstance(v, dict):
                        collect(v)
            collect(t["regions"])
        if not isinstance(fields, dict):
            continue
        for name, fd in fields.items():
            if isinstance(fd, dict) and is_numeric_field(fd):
                if add_preproc(fd):
                    changed = True
                    info(f"added preproc to field: {t.get('id', '?')}::{name}")
    if changed:
        # write back with utf-8-sig preserved
        out = json.dumps(data, ensure_ascii=False, indent=2)
        path.write_bytes(("\ufeff"+out).encode("utf-8"))
        info(f"updated templates with preproc: {path}")
    else:
        info("no numeric fields found to update (or already updated)")
    return changed

def add_tests_and_tools():
    tests = ROOT / "tests"
    tests.mkdir(exist_ok=True)
    test_conf = r'''from dataclasses import dataclass
from src.ocr.preproc_pil import median_digit_confidence

@dataclass
class Tok:
    text: str
    confidence: float

def test_median_digit_confidence():
    toks = [Tok("A1",0.9), Tok("B2",0.7), Tok("C",0.2), Tok("9",0.4)]
    # digit confs [0.9,0.7,0.4] -> median 0.7
    assert abs(median_digit_confidence(toks) - 0.7) < 1e-6
'''
    write_if_changed(tests / "test_confidence_median.py", test_conf)

    test_health = r'''import os, re, io
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
'''
    write_if_changed(tests / "test_static_health.py", test_health)

    test_accent = r'''import unicodedata

def normalize_field(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.lower().strip()

def test_accent_agnostic_declaration():
    assert normalize_field("déclaration") == normalize_field("declaration")
'''
    write_if_changed(tests / "test_accent_normalization.py", test_accent)

    makefile = r'''.PHONY: format lint test fetch-tessdata precommit

format:
	python -m black .
	python -m ruff --fix .

lint:
	python -m ruff .

test:
	python -m pytest -q

fetch-tessdata:
	powershell -ExecutionPolicy Bypass -File scripts/fetch_tessdata.ps1

precommit: format lint test
'''
    write_if_changed(ROOT / "Makefile", makefile)

    tasks = r'''import platform
from invoke import task

@task
def format(c):
    c.run("python -m black .")
    c.run("python -m ruff --fix .")

@task
def lint(c):
    c.run("python -m ruff .")

@task
def test(c):
    c.run("python -m pytest -q")

@task
def fetch_tessdata(c):
    if platform.system() == "Windows":
        c.run("powershell -ExecutionPolicy Bypass -File scripts/fetch_tessdata.ps1")
    else:
        print("Install tesseract + ara/fra via your package manager.")
'''
    write_if_changed(ROOT / "tasks.py", tasks)

def main():
    info(f"repo root: {ROOT}")
    g = update_gui_process_calls()
    if g == 0:
        info("GUI refactor: no files changed (maybe already ok)")
    make_preproc_module()
    soft_update_templates()
    add_tests_and_tools()
    info("Done. Next: run 'python -m pip install -U pytest pillow black ruff invoke' then 'python -m pytest -q'")

if __name__ == "__main__":
    main()
