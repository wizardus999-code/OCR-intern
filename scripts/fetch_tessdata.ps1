# downloads fra/ara traineddata into repo-local .\tessdata
param()

$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$td = Join-Path $here "..\tessdata"
New-Item -ItemType Directory -Force $td | Out-Null

$base = "https://github.com/tesseract-ocr/tessdata_best/raw/main"
$fra  = Join-Path $td "fra.traineddata"
$ara  = Join-Path $td "ara.traineddata"

Write-Host "Downloading fra.traineddata → $fra"
Invoke-WebRequest "$base/fra.traineddata" -OutFile $fra

Write-Host "Downloading ara.traineddata → $ara"
Invoke-WebRequest "$base/ara.traineddata" -OutFile $ara

Write-Host "Done. Files in $td"
