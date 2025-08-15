from dataclasses import dataclass
from src.ocr.preproc_pil import median_digit_confidence

@dataclass
class Tok:
    text: str
    confidence: float

def test_median_digit_confidence():
    toks = [Tok("A1",0.9), Tok("B2",0.7), Tok("C",0.2), Tok("9",0.4)]
    # digit confs [0.9,0.7,0.4] -> median 0.7
    assert abs(median_digit_confidence(toks) - 0.7) < 1e-6
