param (
  [Parameter(Position=0, Mandatory=$true)][string]$Actual,
  [Parameter(Position=1, Mandatory=$true)][string]$Expected,
  [Parameter(Position=2                 )][string]$ComparedActual,
  [Parameter(Position=3                 )][string]$ComparedExpected,
  [Parameter(Position=4                 )][string]$Diff
)

function Write-IfExists {
  param (
    [Parameter(Mandatory = $true, Position=0)]
    [string[]]$Data,
    [Parameter(Position=1)]
    [string]$Path
  )

  if ($Path) {
    $Data | Set-Content $Path -Encoding UTF8NoBOM
  }
}

if (-not (Test-Path $Expected)) {
  Write-Host "Reference not found, assuming change"
  Write-IfExists "COMPARISON_STATUS=changed" ${env:GITHUB_ENV}
  Exit 0
}

$_today = Get-Date -Format "dd-MM-yyyy"
$_actual = (Get-Content $Actual | Select-Object -Skip 1 -SkipLast 2) -replace "{{TODAY}}", $_today
$_expected = (Get-Content $Expected) -replace "{{TODAY}}", $_today

$_diff = @()

for ($i = 0; $i -lt [Math]::Max($expected.Count, $_actual.Count); $i++) {
  $_expLine = if ($i -lt $_expected.Count) { $_expected[$i] } else { $null }
  $_actLine = if ($i -lt $_actual.Count) { $_actual[$i] } else { $null }

  if ($_expLine -eq $_actLine) {
    $_diff += "✔ $_expLine"
  }
  elseif ($_expLine -ne $null -and $_actLine -ne $null) {
    $_diff += "➖ $_expLine"
    $_diff += "➕ $_actLine"
  }
  elseif ($_expLine -ne $null) {
    $_diff += "➖ $_expLine"
  }
  elseif ($_actLine -ne $null) {
    $_diff += "➕ $_actLine"
  }
}

if ($($_diff -join "") -match "➖|➕") {
  Write-Host "🔍 Differences found:"
  $_diff | Write-Host
  Write-IfExists $_actual $ComparedActual
  Write-IfExists $_expected $ComparedExpected
  Write-IfExists $_diff $Diff
  Write-IfExists "COMPARISON_STATUS=changed" ${env:GITHUB_ENV}
} else {
  Write-Host "✅ No changes."
  Write-IfExists "COMPARISON_STATUS=unchanged" ${env:GITHUB_ENV}
}
