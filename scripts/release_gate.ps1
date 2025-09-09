Param(
  [string]$ImagePath = ".\samples\assoc_fake.png",
  [string]$Template = "assoc_receipt"
)

$ErrorActionPreference = "Stop"

# Env sanity
$env:PATH = "C:\Program Files\Tesseract-OCR;$env:PATH"
$env:TESSDATA_PREFIX = (Resolve-Path .\tessdata).Path

Write-Host "== Sanity =="
tesseract --list-langs
$py = ".\.venv\Scripts\python.exe"
& $py -c "import sys,pytesseract; print('PY:', sys.executable); print('LANGS:', pytesseract.get_languages())"

# Sample regen if missing
if (-not (Test-Path $ImagePath)) {
  & $py .\scripts\gen_fake_assoc.py -o $ImagePath | Out-Host
}

# Extractor smoke
Write-Host "== Extractor =="
$json = & $py .\scripts\test_extractor_assoc.py --image $ImagePath --template $Template
$json | Out-Host

# Parse receipt number from JSON
try {
  $obj = $json | ConvertFrom-Json
  $rcpt = $obj.fields.'body.receipt_no'
  $norm = $rcpt.norm
  $conf = [int]([math]::Round([double]$rcpt.conf))
  $valid = [bool]$rcpt.valid
} catch {
  $norm = ""
  $conf = 0
  $valid = $false
}

# Pattern + threshold
$pattern = '^\d{4}/\d{3,6}$'
$rcpt_ok = $valid -and ($norm -match $pattern) -and ($conf -ge 40)

# Run tests quietly
Write-Host "== Pytest =="
$pytest = & $py -m pytest -q 2>&1
$pytest | Out-Host
$hasFail = $pytest -match 'FAILED|ERROR'

# Gate
if (-not $hasFail -and $rcpt_ok) {
  Write-Host "`nGATE: GO ✅" -ForegroundColor Green
  Write-Host "receipt_no: $norm (conf=$conf) — tests clean"
  exit 0
} else {
  Write-Host "`nGATE: NO-GO ❌" -ForegroundColor Red
  Write-Host "receipt_ok=$rcpt_ok norm='$norm' conf=$conf ; tests_fail=$hasFail"
  exit 1
}
