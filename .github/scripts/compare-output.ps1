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
    [Object[]]$Data,
    [Parameter(Position=1)]
    [string]$Path
  )

  if ($Path) {
    $Data | Set-Content $Path -Encoding UTF8NoBOM
  }
}

function Write-Status {
  param (
      [Parameter(Mandatory = $true, Position=0)]
      [string]$Status
    )

  Write-IfExists "status=${Status}" ${env:GITHUB_OUTPUT}
}

if (-not (Test-Path $Expected)) {
  Write-Host "Reference not found, assuming change"
  Write-Status "changed"
  Exit 0
}

$_today = Get-Date -Format "dd-MM-yyyy"
$_current_month = ($_today -split '-')[1]
$_actual = ((Get-Content $Actual) -replace "{{TODAY}}", $_today) -replace "{{CURRENT MONTH}}", $_current_month
$_expected = ((Get-Content $Expected) -replace "{{TODAY}}", $_today) -replace "{{CURRENT MONTH}}", $_current_month

$_diff = @()

for ($i = 0; $i -lt [Math]::Max($_expected.Count, $_actual.Count); $i++) {
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
  Write-Status "changed"
} else {
  Write-Host "✅ No changes."
  Write-Status "unchanged"
}
