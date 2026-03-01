param (
  [Parameter(Mandatory = $false)][string]$WorkflowName,
  [Parameter(Mandatory = $false)][string]$RunNumber,
  [Parameter(Mandatory = $false)][string]$JobName,

  # Paths (files/dirs) relative to repo root or absolute
  [Parameter(Mandatory = $true)][string[]]$Artifacts,

  # SFTP/SSH connection
  [Parameter(Mandatory = $true)][string]$SftpHost,
  [Parameter(Mandatory = $true)][int]$SftpPort,
  [Parameter(Mandatory = $true)][string]$SftpUser,
  [Parameter(Mandatory = $true)][string]$SshKeyPath,

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
  if (-not $cmd) { throw "Required command '$name' not found on PATH. Install OpenSSH SFTP client on this runner." }
}

function Join-PosixPath([string]$left, [string]$right) {
  $l = ($left -replace '\\', '/')
  $r = ($right -replace '\\', '/')

  if ([string]::IsNullOrWhiteSpace($l)) { return $r.TrimStart('/') }
  if ($l -eq '/') { return '/' + $r.TrimStart('/') }
  return $l.TrimEnd('/') + '/' + $r.TrimStart('/')
}

Require-Command sftp

$hasRunContext = -not [string]::IsNullOrWhiteSpace($WorkflowName) `
  -and -not [string]::IsNullOrWhiteSpace($RunNumber) `
  -and -not [string]::IsNullOrWhiteSpace($JobName)

$remoteBaseRaw = ($RemoteBaseDir -replace '\\', '/')
$remoteBase = if ($remoteBaseRaw -eq '/') { '/' } else { $remoteBaseRaw.TrimEnd('/') }
if ([string]::IsNullOrWhiteSpace($remoteBase)) {
  throw "RemoteBaseDir must not be empty."
}
if ($hasRunContext) {
  $workflow = Sanitize $WorkflowName
  $job = Sanitize $JobName

  # Remote dir: <base>/<workflow>/<job>/<runNumber>
  # (use POSIX separators regardless of platform)
  $remoteRel = "$workflow/$job/$RunNumber"
  $remoteDir = Join-PosixPath $remoteBase $remoteRel
} else {
  # Brak pełnego kontekstu workflow/run/job: upload bezpośrednio do bazy.
  $remoteDir = $remoteBase
  $remoteRel = ""
}

if (-not $TempDir) { $TempDir = [System.IO.Path]::GetTempPath() }

$sessionId = [guid]::NewGuid().ToString('N')

# SFTP options:
# - accept-new: first connect auto-add host key; later it must match (safer than "no")
$knownHosts = Join-Path $TempDir "known_hosts_$sessionId"
$sftpOpts = @(
  '-P', "$SftpPort",
  '-o', 'StrictHostKeyChecking=accept-new',
  '-o', "UserKnownHostsFile=$knownHosts",
  '-i', "$SshKeyPath"
)
# Upload via SFTP in batch mode
$batchFile = Join-Path $TempDir "sftp_batch_$sessionId.txt"

function Get-SftpMkdirCommands([string]$path) {
  $normalized = $path -replace '\\', '/'
  $isAbsolute = $normalized.StartsWith('/')
  $parts = $normalized.Trim('/') -split '/' | Where-Object { $_ -ne '' }
  $current = if ($isAbsolute) { '/' } else { '' }
  $commands = @()
  foreach ($part in $parts) {
    if ($current -eq '/' -or $current -eq '') {
      $current = "$current$part"
    } else {
      $current = "$current/$part"
    }
    # Prefix "-" ignores "already exists" errors in batch mode.
    $commands += "-mkdir `"$current`""
  }
  return $commands
}

$cmds = @()
$cmds += Get-SftpMkdirCommands $remoteDir
$cmds += "cd `"$remoteDir`""

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
  Add-SummaryLine "## Artifacts (self-hosted via Tailscale)"
  foreach ($p in $Artifacts) {
    $leaf = Split-Path -Leaf $p
    if ($remoteRel) {
      $url = "$baseUrl/$remoteRel/$leaf"
    } else {
      $url = "$baseUrl/$leaf"
    }
    Add-SummaryLine "- [$leaf]($url)"
  }
}

# Cleanup (best-effort)
try { Remove-Item -Force $batchFile } catch {}
# known_hosts zostawiamy do temp, ale możesz też usuwać:
try { Remove-Item -Force $knownHosts } catch {}
