param (
  [Parameter(Position = 0, Mandatory = $true)]
  [string]$Sufficies,
  [Parameter(Position = 1)]
  [string]$EnvVariables = $null
)

function Get-ValuesToMask {
  param (
    [Parameter(Position=0)]
    [string]$EnvVariablesString
  )
  if ($EnvVariablesString) {
    $dict = @{}
    foreach ($line in $EnvVariablesString.Trim().Split("`n")) {
        $key, $value = $line.Split("=")
        $dict[$key] = $value
    }
    $dict
  } else {
    [System.Environment]::GetEnvironmentVariables()
  }
}

$dict = Get-ValuesToMask $EnvVariables

$SufficiesList = $Sufficies -split ","

foreach ($key in $dict.Keys) {
  foreach ($suffix in $SufficiesList) {
    if ($key.EndsWith($suffix)) {
      $val = $dict[$key]
      if ($val) {
        Write-Output "::add-mask::$val"
        Write-Output "Masked $key"
      }
    }
  }
}
