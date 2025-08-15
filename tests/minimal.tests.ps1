BeforeAll {
    $here = Split-Path -Parent $PSCommandPath
    $repo = Split-Path -Parent $here
}

Describe "A minimal test" {
    It "Should pass" {
        $true | Should -Be $true
    }
}
