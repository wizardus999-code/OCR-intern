from __future__ import annotations
from typing import Any, Dict, Iterable, Optional
import re
import unicodedata

from src.ocr.base import OCRResult


class PostProcessor:
    def __init__(self) -> None:
        pass

    @staticmethod
    def _guess_lang(text: str) -> Optional[str]:
        # Arabic block range
        if any("\u0600" <= ch <= "\u06FF" for ch in text):
            return "arabic"
        # crude Latin detection (good enough for FR here)
        if any("a" <= ch.lower() <= "z" for ch in text):
            return "french"
        return None

    @staticmethod
    def _fold(s: str) -> str:
        # remove accents/diacritics for robust matching
        return "".join(
            ch
            for ch in unicodedata.normalize("NFKD", s)
            if not unicodedata.combining(ch)
        )

    def process(self, text_results: Iterable[Any]) -> Dict[str, Any]:
        """Process OCR results to improve accuracy and extract metadata."""
        processed_results: Dict[str, Any] = {
            "text": [],
            "metadata": {
                "document_type": None,
                "languages_detected": set(),
                "confidence": 0.0,
            },
        }

        total_conf = 0.0
        count = 0

        for result in text_results or []:
            if isinstance(result, str):
                text = result
                conf = 0.0
                lang = self._guess_lang(text)
            elif isinstance(result, OCRResult):
                text = result.text or ""
                conf = float(result.confidence or 0.0)
                lang = result.lang or self._guess_lang(text)
            elif isinstance(result, dict):
                text = str(result.get("text") or "")
                conf = float(result.get("confidence") or 0.0)
                lang = result.get("lang") or self._guess_lang(text)
            else:
                continue

            text = text.strip()
            if not text:
                continue

            processed_results["text"].append(text)
            if lang:
                processed_results["metadata"]["languages_detected"].add(lang)
            if conf >= 0:
                total_conf += conf
                count += 1

        processed_results["metadata"]["confidence"] = (
            (total_conf / count) if count else 0.0
        )

        # Simple document-type heuristic (accent-insensitive + noise tolerant)
        txt = " ".join(processed_results["text"])
        txt_lower = txt.lower()
        fold = self._fold(txt_lower)
        # keep only a-z to ignore �, punctuation, etc.
        fold_letters = re.sub(r"[^a-z]+", "", fold)

        doc_type = None
        if ("certificat" in fold) or ("شهادة" in txt_lower):
            doc_type = "certificate"
        elif ("demande" in fold) or ("طلب" in txt_lower):
            doc_type = "application"
        elif ("autorisation" in fold) or ("رخصة" in txt_lower):
            # Only mark as authorization if it's not a demande/application
            if doc_type is None:
                doc_type = "authorization"
        # Match both 'declaration' and 'déclaration', with or without the 'e'
        elif re.search(r"d[ée]?claration", fold_letters) or ("تصريح" in txt_lower):
            doc_type = "declaration"

        processed_results["metadata"]["document_type"] = doc_type

        # Make languages JSON-friendly
        processed_results["metadata"]["languages_detected"] = sorted(
            processed_results["metadata"]["languages_detected"]
        )
        return processed_results
