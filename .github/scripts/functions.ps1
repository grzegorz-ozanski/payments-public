function Write-IfExists {
  param (
    [Parameter(Mandatory = $true, Position=0)]
    [string[]]$Data,
    [Parameter(Position=1)]
    [string]$Path
  )

  if ($Path) {
    $Data | Set-Content $Path -Encoding UTF8NoBOM
  }
}
