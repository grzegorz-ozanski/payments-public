param (
  [Parameter(Position=0)][bool]$All = $False
)

$patterns = @(
  'error*',
  'trace*',
  'tests/error*',
  'test/trace*',
  '../error*',
  '../trace*'
)

if ($All) {
  $patterns += 'run/*'
}

Set-Location ..
Get-ChildItem -Force -ErrorAction SilentlyContinue @patterns |
  Remove-Item -Recurse -Force
