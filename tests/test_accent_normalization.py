import unicodedata

def normalize_field(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.lower().strip()

def test_accent_agnostic_declaration():
    assert normalize_field("déclaration") == normalize_field("declaration")
