$Dest = ".\tessdata"
New-Item -ItemType Directory -Force -Path $Dest | Out-Null

$base = "https://github.com/tesseract-ocr/tessdata_best/raw/main"
Invoke-WebRequest -Uri "$base/ara.traineddata" -OutFile "$Dest\ara.traineddata" -UseBasicParsing
Invoke-WebRequest -Uri "$base/fra.traineddata" -OutFile "$Dest\fra.traineddata" -UseBasicParsing

Write-Host "Downloaded:" (Get-Item "$Dest\ara.traineddata").FullName
Write-Host "Downloaded:" (Get-Item "$Dest\fra.traineddata").FullName
