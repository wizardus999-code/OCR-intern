# tests/Simple.Tests.ps1
BeforeAll {
    # Helper function we're testing
    function Add-PathOnce {
        param([string]$dir)
        if ([string]::IsNullOrWhiteSpace($dir)) { return }
        if (-not (Test-Path $dir)) { return }
        $items = $env:PATH -split ';'
        if ($items -notcontains $dir) { $env:PATH = ($env:PATH.TrimEnd(';') + ';' + $dir) }
    }

    # Define the mock function for pwsh
    function global:pwsh {
        param([Parameter(ValueFromRemainingArguments=$true)]$args)
        # Mock implementation
    }
}

Describe "Tesseract Setup" {
    BeforeEach {
        # Save original environment
        $script:originalPath = $env:PATH
        $script:originalTessdata = $env:TESSDATA_PREFIX

        # Basic mocks
        Mock Write-Host { }
        Mock Write-Warning { }
        Mock Write-Error { }
        Mock Test-Path { $false }
        Mock Join-Path { 
            param($Path, $ChildPath)
            return [System.IO.Path]::Combine($Path, $ChildPath)
        }
    }

    AfterEach {
        # Restore original environment
        $env:PATH = $script:originalPath
        $env:TESSDATA_PREFIX = $script:originalTessdata
    }

    Context "Installation via winget" {
        It "Attempts winget installation when Tesseract is not found" {
            # Mock commands
            Mock Get-Command { $null } -ParameterFilter { $Name -eq 'tesseract.exe' }
            Mock Get-Command { $true } -ParameterFilter { $Name -eq 'winget' }
            Mock Select-String { $false }
            Mock winget { }
            
            # Run test code
            $testCode = {
                if (-not (Get-Command tesseract.exe -ErrorAction SilentlyContinue)) {
                    if (Get-Command winget -ErrorAction SilentlyContinue) {
                        $exists = winget list --id UB-Mannheim.TesseractOCR | Select-String -Quiet 'UB-Mannheim\.TesseractOCR'
                        if (-not $exists) {
                            Write-Host "Installing Tesseract via winget..."
                            winget install -e --id UB-Mannheim.TesseractOCR --accept-package-agreements --accept-source-agreements
                        }
                    }
                }
            }

            & $testCode

            Should -Invoke winget -Times 2 # Once for list, once for install
            Should -Invoke Write-Host -ParameterFilter { $Object -eq "Installing Tesseract via winget..." }
        }
    }

    Context "PATH management" {
        It "Adds Tesseract directory to PATH if found" {
            # Setup
            Mock Test-Path { $true }
            $env:PATH = "C:\Windows\System32"

            # Test
            Add-PathOnce 'C:\Program Files\Tesseract-OCR'

            # Verify
            $env:PATH | Should -BeLike '*Tesseract-OCR'
        }

        It "Does not add duplicate PATH entries" {
            # Setup
            Mock Test-Path { $true }
            $env:PATH = "C:\Windows\System32;C:\Program Files\Tesseract-OCR"
            $originalPath = $env:PATH

            # Test
            Add-PathOnce 'C:\Program Files\Tesseract-OCR'

            # Verify
            $env:PATH | Should -Be $originalPath
        }
    }

    Context "TESSDATA_PREFIX configuration" {
        It "Sets TESSDATA_PREFIX to repo tessdata if it exists" {
            # Setup
            Mock Test-Path { $true }
            Mock Resolve-Path { 
                param($Path)
                if ($Path -eq '.') {
                    [PSCustomObject]@{ Path = 'C:\repo' }
                } else {
                    [PSCustomObject]@{ Path = 'C:\repo\tessdata' }
                }
            }

            # Test
            $testCode = {
                $repoTess = Join-Path (Resolve-Path .).Path 'tessdata'
                if (Test-Path $repoTess) {
                    $env:TESSDATA_PREFIX = $repoTess
                }
            }

            & $testCode

            # Verify
            $env:TESSDATA_PREFIX | Should -Be 'C:\repo\tessdata'
        }
    }

    Context "Language file management" {
        It "Detects missing language files" {
            # Setup
            Mock Test-Path { 
                param($Path)
                if ($Path -like '*traineddata') { return $false }
                return $true
            }

            $global:pwshCalled = $false
            Mock Get-Command { 
                param($Name)
                if ($Name -eq 'pwsh') { return $true }
                return $null
            }

            $env:TESSDATA_PREFIX = 'C:\repo\tessdata'

            # Test
            $testCode = {
                $need = @('ara.traineddata','fra.traineddata')
                $missing = @()
                foreach ($f in $need) {
                    if (-not (Test-Path (Join-Path $env:TESSDATA_PREFIX $f))) { $missing += $f }
                }
                if ($missing.Count -gt 0) {
                    if (Test-Path '.\scripts\fetch_tessdata.ps1') {
                        Write-Host "Downloading tessdata: $($missing -join ', ')..."
                        $global:pwshCalled = $true
                        & pwsh .\scripts\fetch_tessdata.ps1
                    }
                }
            }

            & $testCode

            # Verify
            Should -Invoke Write-Host -ParameterFilter { 
                $Object -eq "Downloading tessdata: ara.traineddata, fra.traineddata..." 
            }
            $global:pwshCalled | Should -Be $true
        }

        It "Doesn't download language files if they exist" {
            # Setup
            Mock Test-Path { $true }
            $global:pwshCalled = $false
            Mock Get-Command { 
                param($Name)
                if ($Name -eq 'pwsh') { return $true }
                return $null
            }
            $env:TESSDATA_PREFIX = 'C:\repo\tessdata'

            # Test
            $testCode = {
                $need = @('ara.traineddata','fra.traineddata')
                $missing = @()
                foreach ($f in $need) {
                    if (-not (Test-Path (Join-Path $env:TESSDATA_PREFIX $f))) { $missing += $f }
                }
                if ($missing.Count -gt 0) {
                    if (Test-Path '.\scripts\fetch_tessdata.ps1') {
                        Write-Host "Downloading tessdata: $($missing -join ', ')..."
                        $global:pwshCalled = $true
                        & pwsh .\scripts\fetch_tessdata.ps1
                    }
                }
            }

            & $testCode

            # Verify
            Should -Not -Invoke Write-Host -ParameterFilter { 
                $Object -like "Downloading tessdata*" 
            }
            $global:pwshCalled | Should -Be $false
        }
    }
}

AfterAll {
    # Clean up global function
    Remove-Item -Path function:global:pwsh -ErrorAction SilentlyContinue
}
