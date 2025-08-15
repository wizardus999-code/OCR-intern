# Idempotent Tesseract setup script
# Run from repo root to install Tesseract and configure the environment

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Join-Path $here ".."

# 1) Install Tesseract if not already on PATH
if (-not (Get-Command tesseract.exe -ErrorAction SilentlyContinue)) {
  if (Get-Command winget -ErrorAction SilentlyContinue) {
    $isInstalled = winget list --id UB-Mannheim.TesseractOCR | Select-String -Quiet 'UB-Mannheim\.TesseractOCR'
    if (-not $isInstalled) {
      Write-Host "Installing Tesseract via winget..." -ForegroundColor Green
      winget install -e --id UB-Mannheim.TesseractOCR --accept-package-agreements --accept-source-agreements
    } else {
      Write-Host "Tesseract already installed via winget" -ForegroundColor Green
    }
  } else {
    Write-Host "winget not found. Use Chocolatey (admin) or the portable fallback below." -ForegroundColor Yellow
  }
}

# 2) Ensure this shell can find tesseract.exe (no need to reopen shell)
$paths = @(
  'C:\Program Files\Tesseract-OCR',
  'C:\Program Files (x86)\Tesseract-OCR'
)
foreach ($p in $paths) {
  $exe = Join-Path $p 'tesseract.exe'
  if (Test-Path $exe) {
    if (-not (($env:PATH -split ';') -contains $p)) {
      Write-Host "Adding $p to PATH" -ForegroundColor Green
      $env:PATH = "$env:PATH;$p"
    }
  }
}

# 3) Repo-local tessdata (preferred): download models if missing
$tessdata = Join-Path $root "tessdata"
if (-not (Test-Path $tessdata)) { 
    Write-Host "Creating tessdata directory..." -ForegroundColor Green
    New-Item -ItemType Directory -Force $tessdata | Out-Null 
}

if (Test-Path (Join-Path $root "scripts\fetch_tessdata.ps1")) {
  Write-Host "Fetching language models via fetch_tessdata.ps1..." -ForegroundColor Green
  $fetchScript = Join-Path $root "scripts\fetch_tessdata.ps1"
  if (Get-Command pwsh -ErrorAction SilentlyContinue) {
    pwsh $fetchScript
  } else {
    powershell.exe -File $fetchScript
  }
} else {
  # Minimal inline fetch if the script is absent
  Write-Host "Fetching language models directly..." -ForegroundColor Green
  $base = 'https://github.com/tesseract-ocr/tessdata_best/raw/main'
  foreach ($lang in 'ara','fra') {
    $out = Join-Path $tessdata "$lang.traineddata"
    if (-not (Test-Path $out)) {
      Write-Host "Downloading $lang.traineddata..." -ForegroundColor Green
      Invoke-WebRequest -Uri "$base/$lang.traineddata" -OutFile $out
    } else {
      Write-Host "$lang.traineddata already present" -ForegroundColor Green
    }
  }
}

# 4) Point Tesseract to repo tessdata for this session
$env:TESSDATA_PREFIX = $tessdata

# 5) Verify setup
Write-Host "`nVerifying Tesseract installation:" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

Write-Host "`nTesseract version:"
tesseract --version

Write-Host "`nTesseract location:"
Get-Command tesseract.exe

Write-Host "`nLanguage files in $env:TESSDATA_PREFIX:"
Get-ChildItem $tessdata\*.traineddata

Write-Host "`nSetup complete! Run tests with:" -ForegroundColor Green
Write-Host "pytest -v" -ForegroundColor Yellow
