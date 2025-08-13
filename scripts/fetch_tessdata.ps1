# Create tessdata directory if it doesn't exist
$tessdata = Join-Path $PSScriptRoot ".." "tessdata"
New-Item -ItemType Directory -Force -Path $tessdata | Out-Null

$baseUrl = "https://github.com/tesseract-ocr/tessdata_best/raw/main"
$languages = @("ara", "fra")

Write-Host "Downloading Tesseract language files..."
foreach ($lang in $languages) {
    $url = "$baseUrl/$lang.traineddata"
    $outFile = Join-Path $tessdata "$lang.traineddata"
    
    if (Test-Path $outFile) {
        Write-Host "Skipping $lang.traineddata (already exists)"
        continue
    }
    
    Write-Host "Downloading $lang.traineddata..."
    try {
        Invoke-WebRequest -Uri $url -OutFile $outFile
        Write-Host "Successfully downloaded $lang.traineddata"
    }
    catch {
        Write-Error "Failed to download $lang.traineddata: $_"
    }
}

Write-Host "`nDone! Language files are in ./tessdata/"
