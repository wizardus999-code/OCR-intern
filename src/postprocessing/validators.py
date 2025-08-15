from __future__ import annotations
import re
from typing import Dict, Any

_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
def ar2en_digits(s: str) -> str: return (s or "").translate(_AR_DIGITS)
def squash_spaces(s: str) -> str: return re.sub(r"\s+", " ", s or "").strip()

COMMUNES_CASA = {"Anfa","Sidi Belyout","Maârif","Roches Noires","Aïn Sebaâ","Aïn Chock","Hay Hassani",
"Sidi Othmane","Sidi Bernoussi","Ben M'Sick","Moulay Rachid","Bouskoura","Dar Bouazza","Médiouna"}

def normalize_cin(s):
    raw = ar2en_digits((s or "").upper())
    m = re.search(r"([A-Z]{1,2})\s*[- ]?(\d{5,6})", raw)
    if not m: return {"type":"cin","value":squash_spaces(s),"valid":False}
    return {"type":"cin","value":f"{m.group(1)}{m.group(2)}","valid":True}

def normalize_date_ma(s):
    t = ar2en_digits(s or "").replace(".", "/").replace("-", "/")
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", t)
    if not m: return {"type":"date","value":squash_spaces(s),"valid":False}
    d, mo, y = map(int, m.groups())
    y = (y+2000) if y<100 and y<50 else ((y+1900) if y<100 else y)
    ok = 1<=d<=31 and 1<=mo<=12 and 1900<=y<=2100
    return {"type":"date","value":f"{y:04d}-{mo:02d}-{d:02d}" if ok else squash_spaces(s),"valid":ok}

def normalize_phone_ma(s):
    t = re.sub(r"\D+","", ar2en_digits(s or ""))
    if t.startswith("212"): t = t[3:]
    if t.startswith("0"):   t = t[1:]
    return {"type":"phone","value":f"+212{t}" if len(t)==9 else squash_spaces(s),"valid":len(t)==9}

def normalize_receipt_no(s):
    t = ar2en_digits(s or "")
    m = re.search(r"(\d{1,6}(?:[/-]\d{2,4}){1,3})", t)
    if not m: return {"type":"receipt_no","value":squash_spaces(s),"valid":False}
    return {"type":"receipt_no","value":m.group(1).replace("-", "/"),"valid":True}

def normalize_ice(s):
    t = re.sub(r"\D","", ar2en_digits(s or ""))
    return {"type":"ice","value":t,"valid":len(t)==15}

def normalize_if(s):
    t = re.sub(r"\D","", ar2en_digits(s or ""))
    return {"type":"if","value":t,"valid":7<=len(t)<=8}

def normalize_commune(s):
    base = squash_spaces(s).title()
    for c in COMMUNES_CASA:
        if base.lower() in c.lower() or c.lower() in base.lower():
            return {"type":"commune","value":c,"valid":True}
    return {"type":"commune","value":base,"valid":True}

def normalize_name(s): return {"type":"name","value":squash_spaces(s),"valid":bool(squash_spaces(s))}

def normalize_field(key: str, text: str) -> Dict[str, Any]:
    k = (key or "").lower(); t = text or ""
    if any(x in k for x in ["cin","cnie"]):                           return normalize_cin(t)
    if any(x in k for x in ["date","deliv","délivr","naissance","dob","تاريخ"]):
                                                                      return normalize_date_ma(t)
    if any(x in k for x in ["tel","tél","phone","gsm","هاتف"]):       return normalize_phone_ma(t)
    if any(x in k for x in ["recep","récép","receipt","وصل","رقم الوصل"]):
                                                                      return normalize_receipt_no(t)
    if "ice" in k:                                                    return normalize_ice(t)
    if re.search(r"\bif\b", k):                                       return normalize_if(t)
    if any(x in k for x in ["commune","arrondissement","prefecture","wilaya","province"]):
                                                                      return normalize_commune(t)
    if any(x in k for x in ["président","president","secr","trésor","association","intitul","name","nom","اسم الجمعية"]):
                                                                      return normalize_name(t)
    return {"type":"text","value":squash_spaces(ar2en_digits(t)),"valid":bool(squash_spaces(t))}
