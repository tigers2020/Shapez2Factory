# Run RTTP solver for one Lab project slug (wraps manage.py run_solver).
# PR-4 ops: -DeferredRetryExecute -> manage.py --deferred-retry-execute
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Slug,

    [string]$RunKey,
    [switch]$MacroOnly,
    [switch]$NoReplay,
    [switch]$Json,
    [switch]$DeferredRetryExecute
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
if ($DeferredRetryExecute) {
    $argsList += "--deferred-retry-execute"
}

python @argsList
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
