param (
  [Parameter(Mandatory = $true)][string]$WorkflowName,
  [Parameter(Mandatory = $true)][string]$RunNumber,
  [Parameter(Mandatory = $true)][string]$JobName,

  # Paths (files/dirs) relative to repo root or absolute
  [Parameter(Mandatory = $true)][string[]]$Artifacts,

  # SFTP/SSH connection
  [Parameter(Mandatory = $true)][string]$SftpHost,
  [Parameter(Mandatory = $true)][int]$SftpPort,
  [Parameter(Mandatory = $true)][string]$SftpUser,

  # Remote base directory (POSIX path), e.g. /srv/reports/artifacts
  [Parameter(Mandatory = $true)][string]$RemoteBaseDir,

  # Optional: where to create temp files (default: system temp)
  [Parameter(Mandatory = $false)][string]$TempDir,
  [Parameter(Mandatory = $false)][string]$SummaryBaseUrl
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Sanitize([string]$s) {
  ($s -replace '[^\w\-\.]', '_').ToLower()
}

function Require-Command([string]$name) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if (-not $cmd) { throw "Required command '$name' not found on PATH. Install OpenSSH client (ssh/sftp) on this runner." }
}

Require-Command ssh
Require-Command sftp

$workflow = Sanitize $WorkflowName
$job = Sanitize $JobName

# Remote dir: <base>/<workflow>/<job>/<runNumber>
# (use POSIX separators regardless of platform)
$remoteDir = ($RemoteBaseDir.TrimEnd('/') + "/$workflow/$job/$RunNumber")

if (-not $TempDir) { $TempDir = [System.IO.Path]::GetTempPath() }

$sessionId = [guid]::NewGuid().ToString('N')

# SSH options:
# - accept-new: first connect auto-add host key; later it must match (safer than "no")
$knownHosts = Join-Path $TempDir "known_hosts_$sessionId"
$sshOpts = @(
  '-p', "$SftpPort",
  '-o', 'StrictHostKeyChecking=accept-new',
  '-o', "UserKnownHostsFile=$knownHosts"
)
$sftpOpts = @(
  '-P', "$SftpPort",
  '-o', 'StrictHostKeyChecking=accept-new',
  '-o', "UserKnownHostsFile=$knownHosts"
)

# Ensure remote dir exists (mkdir -p)
Write-Host "Ensuring remote dir exists: $remoteDir"
ssh @sshOpts "$SftpUser@$SftpHost" "mkdir -p '$remoteDir'"
if ($LASTEXITCODE -ne 0) {
  throw "SSH command failed while creating remote directory '$remoteDir' (exit code: $LASTEXITCODE)."
}

# Upload via SFTP in batch mode
$batchFile = Join-Path $TempDir "sftp_batch_$sessionId.txt"

$cmds = @(
  "cd `"$remoteDir`""
)

foreach ($path in $Artifacts) {
  $full = (Resolve-Path $path).Path
  $cmds += "put `"$full`""
}

$cmds += "bye"

$cmds | Set-Content -Path $batchFile -Encoding ASCII

Write-Host "Uploading via SFTP to ${SftpUser}@${SftpHost}:${remoteDir}"
sftp @sftpOpts -b "${batchFile}" "${SftpUser}@${SftpHost}"
if ($LASTEXITCODE -ne 0) {
  throw "SFTP upload failed (exit code: $LASTEXITCODE)."
}

Write-Host "Upload OK: $($Artifacts -join ', ')"

function Add-SummaryLine([string]$line) {
  if ($env:GITHUB_STEP_SUMMARY -and (Test-Path $env:GITHUB_STEP_SUMMARY)) {
    Add-Content -Path $env:GITHUB_STEP_SUMMARY -Value $line
  }
}

if ($SummaryBaseUrl) {
  $baseUrl = $SummaryBaseUrl.TrimEnd('/')
  # remoteRel musi odpowiadać temu co faktycznie tworzysz na serwerze
  $remoteRel = "$workflow/$job/$RunNumber"   # jeśli masz taki układ
  Add-SummaryLine "## Artifacts (self-hosted via Tailscale)"
  foreach ($p in $Artifacts) {
    $leaf = Split-Path -Leaf $p
    $url = "$baseUrl/$remoteRel/$leaf"
    Add-SummaryLine "- [$leaf]($url)"
  }
}

# Cleanup (best-effort)
try { Remove-Item -Force $batchFile } catch {}
# known_hosts zostawiamy do temp, ale możesz też usuwać:
try { Remove-Item -Force $knownHosts } catch {}
