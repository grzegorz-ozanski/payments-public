param (
  [Parameter(Position = 0, Mandatory = $true)]
  [string[]]$Patterns
)

foreach ($key in [System.Environment]::GetEnvironmentVariables().Keys) {
  foreach ($suffix in $Patterns) {
    if ($key.EndsWith($suffix)) {
      $val = [System.Environment]::GetEnvironmentVariable($key)
      if ($val) {
        Write-Output "::add-mask::$val"
        Write-Output "Masked $key"
      }
    }
  }
}
