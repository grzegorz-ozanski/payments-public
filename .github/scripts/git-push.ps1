param (
  [Parameter(Position=0, Mandatory=$true)][string]$File,
  [Parameter(Position=1, Mandatory=$true)][string]$Message,
  [Parameter(Position=2, Mandatory=$true)][string]$Username,
  [Parameter(Position=3, Mandatory=$true)][string]$Email
  [Parameter(Position=4)][string]$RepoDir
)

if ($RepoDir) {
    if (-not (Test-Path $RepoDir -PathType Container)) {
        throw "'$RepoDir' does not exist or is not a directory."
    }
    Set-Location $RepoDir
}

git add $File
if (git diff --cached --quiet) {
  echo "No changes to commit"
} else {
  Write-Host "Committing modified '$File' file."
  git config user.name "$Username"
  git config user.email "$Email"
  git commit -m "$Message"
  git pull --rebase
  git push
}
