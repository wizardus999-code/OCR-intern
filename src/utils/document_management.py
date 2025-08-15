from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict

from src.ocr.base import OCRResult


class DocumentCache:
    def __init__(self, path: Path):
        self.path = Path(path)

    # ---- helpers ----
    @staticmethod
    def _default(o: Any):
        if isinstance(o, OCRResult):
            return o.to_dict()
        if isinstance(o, tuple):
            return list(o)
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    @staticmethod
    def _hook(d: Dict[str, Any]):
        # Rehydrate OCRResult if it looks like one
        keys = {"text", "confidence", "bbox"}
        if keys.issubset(d.keys()):
            bbox = tuple(d.get("bbox") or ())
            return OCRResult(
                text=d.get("text", ""),
                confidence=float(d.get("confidence", -1.0)),
                bbox=bbox if len(bbox) == 4 else (0, 0, 0, 0),
                page=d.get("page"),
                lang=d.get("lang"),
            )
        return d

    # ---- API ----
    def save(self, data: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=self._default)

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8-sig") as f:
            return json.load(f, object_hook=self._hook)
