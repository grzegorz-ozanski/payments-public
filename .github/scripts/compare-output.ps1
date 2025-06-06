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

function Is-Equal {
  param (
      [Parameter(Mandatory = $true, Position=0)]
      [string]$Left,
      [Parameter(Mandatory = $true, Position=1)]
      [string]$Right,
      [Parameter(                 , Position=2)]
      [bool]$IgnoreWhitespace = $false
    )

    $pattern = '^(\S+\s+)(\S+\s+)(\S+\s+)(\S+)$'
    $leftMatch = [regex]::Match($Left, $pattern)
    $rightMatch = [regex]::Match($Right, $pattern)
    if (-not $leftMatch.Success -or
        -not $rightMatch.Success -or
        $leftMatch.Groups.Count -ne $rightMatch.Groups.Count)
    {
      return $false
    }
    for ($i = 1; $i -lt $leftMatch.Groups.Count; $i++) {
      $lval = $leftMatch.Groups[$i].Value
      $rval = $rightMatch.Groups[$i].Value
      if ($lval.Contains('{{IGNORE}}') -or $rval.Contains('{{IGNORE}}')) {
        continue
      }
      if ($IgnoreWhitespace) {
        $lval = $lval.Trim()
        $rval = $rval.Trim()
      }
      if ($lval -ne $rval) {
        return $false
      }
    }
    return $true
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
$_ignore_whitespace = [bool]($_actual -match '<unknown>')

$_diff = @()

for ($i = 0; $i -lt [Math]::Max($_expected.Count, $_actual.Count); $i++) {
  $_expLine = if ($i -lt $_expected.Count) { $_expected[$i] } else { $null }
  $_actLine = if ($i -lt $_actual.Count) { $_actual[$i] } else { $null }

  if (Is-Equal $_expLine $_actLine $_ignore_whitespace) {
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
