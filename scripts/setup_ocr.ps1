# Idempotent OCR setup script
# Run from repo root to install/detect Tesseract and configure the environment

param (
    [switch]$Persist
)

# Exit codes
$Script:SUCCESS = 0
$Script:ERROR_TESSERACT_NOT_FOUND = 1
$Script:ERROR_LANGUAGE_FILES_MISSING = 2

# --- 0) Repo root + helper ---
$repo = Resolve-Path .

function Add-PathIfMissing([string]$p, [switch]$Persist) {
    if ($null -ne $p -and (Test-Path $p)) {
        $paths = ($env:PATH -split ';') | Where-Object { $_ }
        if (-not ($paths -contains $p)) { 
            Write-Host "Adding to PATH: $p" -ForegroundColor Green
            $env:PATH = "$env:PATH;$p"
            if ($Persist) {
                $newPath = [Environment]::GetEnvironmentVariable('Path', 'User') + ";$p"
                [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
                Write-Host "PATH update persisted to user profile" -ForegroundColor DarkGray
            }
        }
    }
}

# --- 1) Install/detect Tesseract ---
Write-Host "`nChecking Tesseract installation..." -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan

$tessCmd = Get-Command tesseract.exe -ErrorAction SilentlyContinue
if (-not $tessCmd) {
    # Check for and use portable install first
    $portableTess = Join-Path $repo 'tools\tesseract\tesseract.exe'
    if (Test-Path $portableTess) {
        Write-Host "Using portable Tesseract installation" -ForegroundColor Green
        $portableDir = Split-Path $portableTess
        if (-not (($env:PATH -split ';') -contains $portableDir)) {
            $env:PATH = "$env:PATH;$portableDir"
            Write-Host "Added portable tesseract to PATH: $portableDir" -ForegroundColor DarkGray
        }
    }
    # Try winget if no portable
    elseif (Get-Command winget -ErrorAction SilentlyContinue) {
        # More reliable way to check if Tesseract is installed
        $isInstalled = winget list --id UB-Mannheim.TesseractOCR | Select-String -Quiet 'UB-Mannheim\.TesseractOCR'
        if (-not $isInstalled) {
            Write-Host "Installing Tesseract via winget..." -ForegroundColor Cyan
            winget install -e --id UB-Mannheim.TesseractOCR --accept-package-agreements --accept-source-agreements
        } else {
            Write-Host "Tesseract already installed via winget" -ForegroundColor DarkGray
        }
    } else {
        Write-Warning "winget not found. Install Tesseract manually or use Chocolatey: choco install tesseract -y"
    }
}

# --- 2) Ensure PATH can find Tesseract now ---
Write-Host "`nConfiguring PATH..." -ForegroundColor Cyan
Write-Host "=================" -ForegroundColor Cyan

# Add standard install locations to PATH if they exist and contain tesseract.exe
$probable = @(
    'C:\Program Files\Tesseract-OCR',
    'C:\Program Files (x86)\Tesseract-OCR'
)
foreach ($p in $probable) {
    if (Test-Path (Join-Path $p 'tesseract.exe')) {
        if (-not (($env:PATH -split ';') -contains $p)) {
            $env:PATH = "$env:PATH;$p"
            Write-Host "Added to PATH (session): $p" -ForegroundColor DarkGray
        }
    }
}

# --- 3) Set up repo-local tessdata ---
Write-Host "`nSetting up language data..." -ForegroundColor Cyan
Write-Host "=======================" -ForegroundColor Cyan

# Ensure repo-local tessdata exists
$tessdata = Resolve-Path -LiteralPath .\tessdata -ErrorAction SilentlyContinue
if (-not $tessdata) {
    Write-Host "Creating tessdata directory..." -ForegroundColor Green
    New-Item -ItemType Directory -Force .\tessdata | Out-Null
    $tessdata = Resolve-Path -LiteralPath .\tessdata
}
$env:TESSDATA_PREFIX = $tessdata.Path

# --- 4) Ensure language models exist ---
$ara = Join-Path $tessdata 'ara.traineddata'
$fra = Join-Path $tessdata 'fra.traineddata'

if (-not (Test-Path $ara) -or -not (Test-Path $fra)) {
    if (Test-Path '.\scripts\fetch_tessdata.ps1') {
        Write-Host "Fetching language models..." -ForegroundColor Green
        try {
            if (Get-Command pwsh -ErrorAction SilentlyContinue) {
                pwsh .\scripts\fetch_tessdata.ps1
            } else {
                powershell.exe -File .\scripts\fetch_tessdata.ps1
            }
        } catch {
            Write-Error "Failed to fetch language models: $_"
            Write-Warning "Please download ara.traineddata and fra.traineddata manually to .\tessdata"
        }
    } else {
        Write-Warning "Missing scripts\fetch_tessdata.ps1 - please download language models manually."
    }
}

# --- 5) Verify setup ---
Write-Host "`nVerifying installation:" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan
$tess = Get-Command tesseract.exe -ErrorAction SilentlyContinue
if ($tess) {
    tesseract --version
    Write-Host "tesseract.exe: $($tess.Source)" -ForegroundColor DarkGray
    
    Write-Host "`nAvailable languages:"
    tesseract --list-langs
} else {
    Write-Error "tesseract.exe not found on PATH. Ensure install succeeded or add its folder to PATH."
}

Write-Host "`nTESSDATA_PREFIX=$env:TESSDATA_PREFIX" -ForegroundColor DarkGray
Get-ChildItem .\tessdata\*.traineddata -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "Found: $($_.Name)" -ForegroundColor DarkGray
}

# Show Python architecture for compatibility checking
Write-Host "`nPython architecture = $(if ([Environment]::Is64BitProcess) { 'x64' } else { 'x86' })" -ForegroundColor DarkGray

Write-Host "`nLanguage files in $env:TESSDATA_PREFIX:"
Get-ChildItem "$env:TESSDATA_PREFIX\*.traineddata" -ErrorAction SilentlyContinue | 
    Select-Object Name, Length | Format-Table

# --- 6) Final validation ---
$success = $true

# Check Tesseract is callable
if (-not (Get-Command tesseract.exe -ErrorAction SilentlyContinue)) {
    Write-Error "Tesseract installation failed or not accessible"
    $success = $false
}

# Check language files
if (-not (Test-Path (Join-Path $env:TESSDATA_PREFIX "ara.traineddata")) -or 
    -not (Test-Path (Join-Path $env:TESSDATA_PREFIX "fra.traineddata"))) {
    Write-Error "Required language files are missing"
    $success = $false
}

# --- 7) Ready to test ---
if ($success) {
    Write-Host "`nSetup complete!" -ForegroundColor Green
    Write-Host "`nTo run tests:" -ForegroundColor Yellow
    Write-Host "1. Ensure venv is activated:  .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "2. Run all tests:      pytest -v" -ForegroundColor Yellow
    Write-Host "3. Run specific test:  pytest -k document_type_detection -q" -ForegroundColor Yellow
    
    exit $Script:SUCCESS
} else {
    Write-Host "`nSetup incomplete - please check errors above" -ForegroundColor Red
    
    if (-not (Get-Command tesseract.exe -ErrorAction SilentlyContinue)) {
        exit $Script:ERROR_TESSERACT_NOT_FOUND
    } else {
        exit $Script:ERROR_LANGUAGE_FILES_MISSING
    }
}
# Quick reference for portable Python setup:
$pythonSetupComment = @"

Note: For portable installations in Python code:
-----------------------------------------------
import os
from pathlib import Path
import pytesseract

repo_tessdata = Path(__file__).resolve().parents[1] / "tessdata"
if repo_tessdata.exists():
    os.environ.setdefault("TESSDATA_PREFIX", str(repo_tessdata))

# If using portable exe:
# pytesseract.pytesseract.tesseract_cmd = r".\tools\tesseract\tesseract.exe"
"@

Write-Host $pythonSetupComment -ForegroundColor DarkGray
