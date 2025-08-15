# Idempotent Tesseract setup for this shell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Add-PathOnce([string]$dir) {
  if ([string]::IsNullOrWhiteSpace($dir)) { return }
  if (-not (Test-Path $dir)) { return }
  $items = $env:PATH -split ';'
  if ($items -notcontains $dir) { $env:PATH = ($env:PATH.TrimEnd(';') + ';' + $dir) }
}

Write-Host "==> Checking Tesseract..." -ForegroundColor Cyan

# 1) Install via winget if not already available on PATH
if (-not (Get-Command tesseract.exe -ErrorAction SilentlyContinue)) {
  if (Get-Command winget -ErrorAction SilentlyContinue) {
    $exists = winget list --id UB-Mannheim.TesseractOCR | Select-String -Quiet 'UB-Mannheim\.TesseractOCR'
    if (-not $exists) {
      Write-Host "   Installing UB-Mannheim.TesseractOCR via winget..." -ForegroundColor Cyan
      winget install -e --id UB-Mannheim.TesseractOCR --accept-package-agreements --accept-source-agreements | Out-Host
    } else {
      Write-Host "   Winget shows UB-Mannheim.TesseractOCR is installed." -ForegroundColor DarkGray
    }
  } else {
    Write-Warning "winget not found. Install Tesseract manually or use a portable build in .\tools\tesseract"
  }
}

# 2) Ensure current session can find tesseract.exe (no restart)
$likely = @(
  'C:\Program Files\Tesseract-OCR',
  'C:\Program Files (x86)\Tesseract-OCR',
  (Join-Path (Resolve-Path .).Path 'tools\tesseract')  # optional portable fallback
)
foreach ($d in $likely) {
  if (Test-Path (Join-Path $d 'tesseract.exe')) { Add-PathOnce $d }
}

# 3) Point tessdata to the repo copy if present (works without admin)
$repoTess = Join-Path (Resolve-Path .).Path 'tessdata'
if (Test-Path $repoTess) {
  $env:TESSDATA_PREFIX = $repoTess
  Write-Host "   TESSDATA_PREFIX -> $repoTess" -ForegroundColor DarkGray
}

# 4) Ensure language files exist (ara/fra); use your fetch script if needed
$need = @('ara.traineddata','fra.traineddata')
$missing = @()
foreach ($f in $need) {
  if (-not (Test-Path (Join-Path $env:TESSDATA_PREFIX $f))) { $missing += $f }
}
if ($missing.Count -gt 0) {
  if (Test-Path .\scripts\fetch_tessdata.ps1) {
    Write-Host "   Downloading tessdata: $($missing -join ', ')..." -ForegroundColor Cyan
    & pwsh .\scripts\fetch_tessdata.ps1
  } else {
    Write-Warning "Missing tessdata ($($missing -join ', ')) and scripts\fetch_tessdata.ps1 not found."
  }
}

# 5) Verify
$tess = Get-Command tesseract.exe -ErrorAction SilentlyContinue
if ($tess) {
  Write-Host "==> Tesseract path: $($tess.Source)" -ForegroundColor Green
  tesseract --version | Select-Object -First 1 | Out-Host
} else {
  Write-Error "tesseract.exe not found on PATH after setup. Add the install dir to PATH or use a portable build in .\tools\tesseract."
}

Write-Host "==> TESSDATA_PREFIX: $env:TESSDATA_PREFIX" -ForegroundColor DarkGray
if (Test-Path $env:TESSDATA_PREFIX) {
  Get-ChildItem (Join-Path $env:TESSDATA_PREFIX '*.traineddata') | ForEach-Object { "   - $($_.Name)" } | Out-Host
}
