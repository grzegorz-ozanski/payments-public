param (
  [Parameter(Position=0, Mandatory=$true)][string]$Actual,
  [Parameter(Position=1, Mandatory=$true)][string]$Expected,
  [Parameter(Position=2                 )][string]$ComparedActual,
  [Parameter(Position=3                 )][string]$ComparedExpected,
  [Parameter(Position=4                 )][string]$Diff,
  [Parameter(Position=5                 )][string]$ResultJson
)

function Write-IfExists {
  param (
    [Parameter(Mandatory = $true, Position=0)]
    [Object[]]$Data,
    [Parameter(Position=1)]
    [string]$Path
  )

  if ($Path) {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllLines($Path, [string[]]$Data, $utf8NoBom)
  }
}

function Write-Status {
  param (
    [Parameter(Mandatory = $true, Position=0)]
    [string]$Status
  )

  Write-IfExists "status=${Status}" ${env:GITHUB_OUTPUT}
}

function Update-ResultJsonStatuses {
  param (
    [Parameter(Mandatory = $true, Position=0)]
    [string]$Path,
    [Parameter(Mandatory = $true, Position=1)]
    [string[]]$Providers
  )

  if (-not $Path -or -not (Test-Path $Path)) {
    return
  }

  $uniqueProviders = $Providers | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique
  if (-not $uniqueProviders) {
    return
  }

  $json = Get-Content $Path -Raw | ConvertFrom-Json
  foreach ($provider in $uniqueProviders) {
    $providerData = $json.PSObject.Properties[$provider]
    if (-not $providerData) {
      continue
    }

    foreach ($payment in $providerData.Value.payments) {
      $payment.status = "failed"
      $reasonProperty = $payment.PSObject.Properties["reason"]
      if ($reasonProperty) {
        $reasonProperty.Value = "diff changed"
      } else {
        $payment | Add-Member -NotePropertyName "reason" -NotePropertyValue "diff changed"
      }
    }
  }

  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, ($json | ConvertTo-Json -Depth 100), $utf8NoBom)
}

function Compare-Lines {
  param (
      [Parameter(Mandatory = $true, Position=0)]
      [AllowEmptyString()]
      [string]$Left,
      [Parameter(Mandatory = $true, Position=1)]
      [AllowEmptyString()]
      [string]$Right,
      [Parameter(Mandatory = $false, Position=2)]
      [bool]$IgnoreWhitespace = $false
    )

    $result = [PSCustomObject]@{
        Left = ""
        Right  = ""
        IsEqual = $false
    }
    $pattern = '^(\S+)\s+(\S+)\s+(\S+)\s+(\S+)(?:\s+(.*))?$'
    $leftMatch = [regex]::Match($Left, $pattern)
    $rightMatch = [regex]::Match($Right, $pattern)
    if ($leftMatch.Success) {
      $result.Left = $leftMatch.Groups[1].Value
    }
    if ($rightMatch.Success) {
      $result.Right = $rightMatch.Groups[1].Value
    }
    if (-not $leftMatch.Success -or
        -not $rightMatch.Success -or
        $leftMatch.Groups.Count -ne $rightMatch.Groups.Count)
    {
      return $result
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
        return $result
      }
    }
    $result.IsEqual = $true
    return $result
}

if (-not (Test-Path $Actual)) {
  Write-Host "Actual not found, assuming change"
  Write-Status "changed"
  Exit 0
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
$_changedProviders = @()

for ($i = 0; $i -lt [Math]::Max($_expected.Count, $_actual.Count); $i++) {
  $_expLine = if ($i -lt $_expected.Count) { $_expected[$i] } else { $null }
  $_actLine = if ($i -lt $_actual.Count) { $_actual[$i] } else { $null }

  $result = Compare-Lines $_expLine $_actLine $_ignore_whitespace
  if ($result.IsEqual) {
    $_diff += "✔ $_expLine"
  }
  elseif ($_expLine -ne $null -and $_actLine -ne $null) {
    $_diff += "➖ $_expLine"
    $_diff += "➕ $_actLine"
    $_changedProviders += $result.Left
    $_changedProviders += $result.Right
  }
  elseif ($_expLine -ne $null) {
    $_diff += "➖ $_expLine"
    $_changedProviders += $result.Left
  }
  elseif ($_actLine -ne $null) {
    $_diff += "➕ $_actLine"
    $_changedProviders += $result.Right
  }
}

if ($($_diff -join "") -match "➖|➕") {
  Write-Host "🔍 Differences found:"
  $_diff | Write-Host
  Update-ResultJsonStatuses $ResultJson $_changedProviders
  Write-IfExists $_actual $ComparedActual
  Write-IfExists $_expected $ComparedExpected
  Write-IfExists $_diff $Diff
  Write-Status "changed"
} else {
  Write-Host "✅ No changes."
  Write-Status "unchanged"
}
