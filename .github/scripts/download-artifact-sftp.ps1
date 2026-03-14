param (
  [Parameter(Mandatory = $true)][string]$SftpHost,
  [Parameter(Mandatory = $true)][int]$SftpPort,
  [Parameter(Mandatory = $true)][string]$SftpUser,
  [Parameter(Mandatory = $true)][string]$SshKeyPath,
  [Parameter(Mandatory = $true)][string]$RemotePath,
  [Parameter(Mandatory = $true)][string]$LocalPath,
  [Parameter(Mandatory = $false)][string]$TempDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Require-Command([string]$name) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if (-not $cmd) { throw "Required command '$name' not found on PATH. Install OpenSSH SFTP client on this runner." }
}

Require-Command sftp

if (-not $TempDir) {
  $TempDir = [System.IO.Path]::GetTempPath()
}

$sessionId = [guid]::NewGuid().ToString('N')
$knownHosts = Join-Path $TempDir "known_hosts_$sessionId"
$batchFile = Join-Path $TempDir "sftp_batch_$sessionId.txt"
$localFullPath = [System.IO.Path]::GetFullPath($LocalPath)
$localDir = Split-Path -Path $localFullPath -Parent

if ($localDir -and -not (Test-Path $localDir)) {
  New-Item -ItemType Directory -Path $localDir -Force | Out-Null
}

$sftpOpts = @(
  '-P', "$SftpPort",
  '-o', 'StrictHostKeyChecking=accept-new',
  '-o', "UserKnownHostsFile=$knownHosts",
  '-i', "$SshKeyPath"
)

$cmds = @(
  "get `"$RemotePath`" `"$localFullPath`"",
  'bye'
)
$cmds | Set-Content -Path $batchFile -Encoding ASCII

Write-Host "Downloading via SFTP from ${SftpUser}@${SftpHost}:${RemotePath}"
sftp @sftpOpts -b "${batchFile}" "${SftpUser}@${SftpHost}"
if ($LASTEXITCODE -ne 0) {
  throw "SFTP download failed (exit code: $LASTEXITCODE)."
}

if (-not (Test-Path $localFullPath)) {
  throw "Downloaded file not found at '$localFullPath'."
}

Write-Host "Download OK: $localFullPath"

try { Remove-Item -Force $batchFile } catch {}
try { Remove-Item -Force $knownHosts } catch {}
