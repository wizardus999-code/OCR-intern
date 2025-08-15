BeforeAll {
    $here = Split-Path -Parent $PSCommandPath
    $repo = Split-Path -Parent $here
    $scriptPath = Join-Path $repo 'scripts\setup_ocr.ps1'
    $script:code = Get-Content $scriptPath -Raw
}

Describe "Tesseract Setup Script" {
    BeforeAll {
        # Basic mocks that should always be in place
        Mock Write-Host { }
        Mock Write-Warning { }
        Mock Write-Error { }
        Mock New-Item { }
        Mock Out-Host { }

        # Mock Resolve-Path to handle . and .\tessdata
        Mock Resolve-Path {
            param($LiteralPath, $Path, $ErrorAction)
            if ($LiteralPath -eq '.\tessdata' -or $Path -eq '.\tessdata') {
                return [PSCustomObject]@{ Path = 'C:\Users\wizar\Desktop\OCR-intern\tessdata' }
            }
            if ($LiteralPath -eq '.' -or $Path -eq '.') {
                return [PSCustomObject]@{ Path = 'C:\Users\wizar\Desktop\OCR-intern' }
            }
            throw "Path not found"
        }
    }

    Context "Fresh Installation Scenario" {
        BeforeAll {
            # Save original state
            $script:originalPath = $env:PATH
            $script:originalTessdata = $env:TESSDATA_PREFIX

            # Mock commands for fresh install scenario
            Mock Get-Command {
                param($Name, $ErrorAction)
                if ($Name -eq 'tesseract.exe') { 
                    if ($script:tesseractInstalled) {
                        return [PSCustomObject]@{ Source = 'C:\Program Files\Tesseract-OCR\tesseract.exe' }
                    }
                    throw [System.Management.Automation.CommandNotFoundException]::new()
                }
                if ($Name -eq 'winget') { return $true }
                if ($Name -eq 'pwsh') { return $true }
            }

            Mock Select-String {
                param($Pattern, $Quiet)
                if ($Pattern -eq 'UB-Mannheim\.TesseractOCR') {
                    return $script:tesseractInWinget
                }
            }

            Mock winget {
                param([Parameter(ValueFromRemainingArguments=$true)]$args)
                if ($args -contains 'install') {
                    $script:wingetInstallCalled = $true
                    $script:tesseractInstalled = $true
                    return "Successfully installed Tesseract"
                }
                return ""
            }

            Mock Test-Path {
                param($Path)
                if ($Path -match 'tessdata$') { return $true }
                if ($Path -match 'tesseract\.exe$') { return $script:tesseractInstalled }
                return $false
            }
        }

        BeforeEach {
            # Reset state for each test
            $script:tesseractInstalled = $false
            $script:tesseractInWinget = $false
            $script:wingetInstallCalled = $false
        }

        It "Should attempt winget installation when Tesseract is not found" {
            # Arrange
            $script:tesseractInstalled = $false
            $script:tesseractInWinget = $false

            # Act
            & ([scriptblock]::Create($script:code)) *>$null

            # Assert
            $script:wingetInstallCalled | Should -Be $true
        }

        It "Should not attempt winget installation when Tesseract is already installed" {
            # Arrange
            $script:tesseractInstalled = $true
            $script:tesseractInWinget = $true

            # Act
            & ([scriptblock]::Create($script:code)) *>$null

            # Assert
            $script:wingetInstallCalled | Should -Be $false
        }

        AfterAll {
            # Restore original state
            $env:PATH = $script:originalPath
            $env:TESSDATA_PREFIX = $script:originalTessdata
        }
    }

    Context "PATH Management" {
        BeforeAll {
            $script:originalPath = $env:PATH
        }

        It "Should add Tesseract directory to PATH only if not already present" {
            # Arrange
            $tessPath = "C:\Program Files\Tesseract-OCR"
            $env:PATH = $env:PATH.Replace($tessPath, '')
            
            Mock Test-Path { 
                param($Path)
                return $Path -eq (Join-Path $tessPath 'tesseract.exe')
            }

            # Act
            & ([scriptblock]::Create($script:code)) *>$null
            $pathContainsTess = $env:PATH -split ';' -contains $tessPath

            # Assert
            $pathContainsTess | Should -Be $true
        }

        AfterAll {
            $env:PATH = $script:originalPath
        }
    }

    Context "TESSDATA_PREFIX Management" {
        BeforeAll {
            $script:originalTessdata = $env:TESSDATA_PREFIX
        }

        It "Should set TESSDATA_PREFIX to repository tessdata when available" {
            # Arrange
            Mock Test-Path { return $true }

            # Act
            & ([scriptblock]::Create($script:code)) *>$null

            # Assert
            $env:TESSDATA_PREFIX | Should -Match 'tessdata$'
        }

        AfterAll {
            $env:TESSDATA_PREFIX = $script:originalTessdata
        }
    }
}
