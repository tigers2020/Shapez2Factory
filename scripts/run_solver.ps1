# Run RTTP solver for one Lab project slug (wraps manage.py run_solver).
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Slug,

    [string]$RunKey,
    [switch]$MacroOnly,
    [switch]$NoReplay,
    [switch]$Json
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$argsList = @("manage.py", "run_solver", "--slug", $Slug)
if ($RunKey) {
    $argsList += @("--run-key", $RunKey)
}
if ($MacroOnly) {
    $argsList += "--macro-only"
}
if ($NoReplay) {
    $argsList += "--no-replay"
}
if ($Json) {
    $argsList += "--json"
}

python @argsList
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
