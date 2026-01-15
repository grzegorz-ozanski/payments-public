param (
  [Parameter(Position=0, Mandatory=$true)][string]$PreviousJobStatus,
  [Parameter(Position=1, Mandatory=$true)][string][AllowEmptyString()]$CompareStatus,
  [Parameter(Position=2                 )][string]$ScriptOutput,
  [Parameter(Position=3                 )][string]$DiffFile,
  [Parameter(Position=4                 )][string]$GitHubOutput,
  [Parameter(Position=5                 )][string]$GitHubSummary
)

function Append-IfExists {
  param (
    [Parameter(Mandatory = $true, Position=0, ValueFromPipeline=$true)]
    [Object[]]$Data,

    [Parameter(Position=1)]
    [string]$Path,

    [Parameter(Position=2)]
    [bool]$Blockquote = $false
  )

  process {
    if ($Path) {
      if ($Blockquote) {
        echo '```' >> $Path
      }
      foreach ($line in $Data) {
        echo $line >> $Path
      }
      if ($Blockquote) {
        echo '```' >> $Path
      }
    } else {
      Write-Host $Data
    }
  }
}

function Get-Emoji {
    param (
        [Parameter(Position=0, Mandatory=$true)]
        [hashtable]$Hashtable,

        [Parameter(Position=1, Mandatory=$true)]
        [string]$Key
    )

    return $Hashtable[$Key] ? $Hashtable[$Key] : $Hashtable["default"]
}

if ($CompareStatus -eq "changed") {
  $current = "failure"
} elseif ($CompareStatus -eq "unchanged") {
  $current = "success"
} else {
  $current = "unknown"
}

Write-Host "Previous: $PreviousJobStatus"
Write-Host "Current: $current"

Append-IfExists "current=${current}" $GitHubOutput
Append-IfExists "previous=$PreviousJobStatus" $GitHubOutput
if ($PreviousJobStatus -ne $current) {
  Append-IfExists "changed=true" $GitHubOutput
} else {
  Append-IfExists "changed=false" $GitHubOutput
}
$emojis = @{
  "failure" = "❌"
  "success" = "✅"
  "unknown" = "🆕"
  "default" = "❔"
}

$transition = "NONE"
if ($PreviousJobStatus -eq "failure") {
  if ($current -eq "success") {
    $transition = "FIXED"
  }
} elseif ($PreviousJobStatus -eq "success") {
  if ($current -eq "failure") {
    $transition = "BROKEN"
  }
} elseif ($PreviousJobStatus -eq "unknown") {
  if ($current -eq "success") {
    $transition = "FIXED"
  } elseif ($current -eq "failure") {
    $transition = "BROKEN"
  }
} else {
  if ($current -eq "success") {
    $transition = "FIXED"
  } elseif ($current -eq "failure") {
    $transition = "BROKEN"
  }
}
Append-IfExists "transition=${transition}" $GitHubOutput

@"
# 🛠️ Workflow summary

- **Previous run status**: $(Get-Emoji $emojis $PreviousJobStatus) $PreviousJobStatus
- **Current comparison status**: $(Get-Emoji $emojis $current) $CompareStatus
"@ | Append-IfExists -Path $GitHubSummary
if ($ScriptOutput -and (Test-Path $ScriptOutput)) {
  Append-IfExists "- 📃**Script Output**:" -Path $GitHubSummary
#   Get-Content -Path $ScriptOutput -Raw | Append-IfExists -Path $GitHubSummary -Blockquote $true
  Get-Content -Path $ScriptOutput -Raw | Append-IfExists -Path $GitHubSummary
}
if ($DiffFile -and (Test-Path $DiffFile) -and ($CompareStatus -eq "changed")) {
  Append-IfExists "- 🟥🟩**Diff**:" -Path $GitHubSummary
  Get-Content -Path $DiffFile -Raw | Append-IfExists -Path $GitHubSummary -Blockquote $true
}
