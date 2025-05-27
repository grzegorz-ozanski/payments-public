param (
  [Parameter(Mandatory = $true)][string]$WorkflowName,
  [Parameter(Mandatory = $true)][string]$RunNumber,
  [Parameter(Mandatory = $true)][string]$JobName,
  [Parameter(Mandatory = $true)][string[]]$ArtifactPaths,
  [Parameter(Mandatory = $true)][string[]]$DiffPaths,
  [Parameter(Mandatory = $true)][string]$CompareStatus,
  [Parameter(Mandatory = $true)][string]$LocalDir
)

$workflow = $($WorkflowName -replace '[^\w\-]', '_').ToLower()
$targetDir = "$LocalDir/$workflow/$JobName/$RunNumber"

if (Test-Path $LocalDir -PathType Container) {
  New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
  foreach ($path in $ArtifactPaths) {
    if (Test-Path $path) {
      Write-Host "Storing artifact '$path' locally in '$targetDir'"
      Copy-Item $path $targetDir -Recurse
    }
  }
  if ($CompareStatus -eq 'changed') {
    foreach ($path in $DiffPaths) {
      if (Test-Path $path) {
        Write-Host "Storing artifact '$path' locally in '$targetDir'"
        Copy-Item $path $targetDir -Recurse
      }
    }
  }
} else {
  Write-Warning "LOCAL_ARTIFACTS_DIR '$LocalDir' not found. Skipping artifact save."
}
