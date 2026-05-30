# Thin Windows wrapper for the pure-core asteroid_solve CLI (PR-CLI-3a).
# Forwards all arguments to the Python module and propagates its exit code.
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

python -m shapez2_factory.interfaces.cli.asteroid_solve @Args
exit $LASTEXITCODE
