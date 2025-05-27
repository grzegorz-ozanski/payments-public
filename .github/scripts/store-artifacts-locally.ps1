param (
  [Parameter(Mandatory = $true)][string]$WorkflowName,
  [Parameter(Mandatory = $true)][string]$RunNumber,
  [Parameter(Mandatory = $true)][string]$JobName,
  [Parameter(Mandatory = $true)][string[]]$Artifacts,
  [Parameter(Mandatory = $true)][string]$TargetDir
)

$workflow = $($WorkflowName -replace '[^\w\-]', '_').ToLower()
$target = "$TargetDir/$workflow/$JobName/$RunNumber"

if (Test-Path $TargetDir -PathType Container) {
  New-Item -ItemType Directory -Path $target -Force | Out-Null
  foreach ($path in $Artifacts) {
    if (Test-Path $path) {
      Write-Host "Storing artifact '$path' locally in '$target'"
      Copy-Item $path $target -Recurse
    }
  }
} else {
  Write-Warning "LOCAL_ARTIFACTS_DIR '$TargetDir' not found. Skipping artifact save."
}
