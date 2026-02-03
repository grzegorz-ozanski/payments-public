param (
  [Parameter(Position=0)][bool]$All = $False
)

$patterns = @(
  'error*',
  'trace*',
  'tests/error*',
  'test/trace*'
)

if ($All) {
  $patterns += 'run/*'
}

cd ..
Get-ChildItem -Force -ErrorAction SilentlyContinue @patterns |
  Remove-Item -Recurse -Force
