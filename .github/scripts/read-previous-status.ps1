param (
  [Parameter(Position=0, Mandatory=$true)][string]$StatusFile
  [Parameter(Position=1                 )][string]$GitHubOutput,
)

function Write-IfExists {
  param (
    [Parameter(Mandatory = $true, Position=0, ValueFromPipeline=$true)]
    [Object[]]$Data,

    [Parameter(Position=1)]
    [string]$Path
  )

  process {
    if ($Path) {
      $Data | Set-Content $Path -Encoding UTF8NoBOM
    } else {
      Write-Host $Data
    }
  }
}

if (Test-Path $StatusFile) {
  $value = Get-Content $StatusFile -Raw
  if ([string]::IsNullOrWhiteSpace($value)) {
    $value = "failure"
    Write-Warning "Empty data in '$StatusFile', defaulting to $value!"
  }
  Write-Host "Previous run status is: $value"
} else {
  Write-Warning "Previous status file not found in '$StatusFile'!"
  $value = "unknown"
}
Write-IfExists "previous=$value" -Path $GitHubOutput
