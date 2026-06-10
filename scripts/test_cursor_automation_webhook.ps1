# Smoke-test Cursor Automation webhook trigger (no Linear).
# Set env vars in your shell — do not commit tokens.
#
#   $env:CURSOR_AUTOMATION_WEBHOOK_URL = "https://api2.cursor.sh/automations/webhook/<id>"
#   $env:CURSOR_AUTOMATION_WEBHOOK_TOKEN = "crsr_..."
#   powershell -File scripts/test_cursor_automation_webhook.ps1

$ErrorActionPreference = "Stop"

$url = $env:CURSOR_AUTOMATION_WEBHOOK_URL
$token = $env:CURSOR_AUTOMATION_WEBHOOK_TOKEN

if (-not $url -or -not $token) {
    Write-Error "Set CURSOR_AUTOMATION_WEBHOOK_URL and CURSOR_AUTOMATION_WEBHOOK_TOKEN"
}

$body = @{
    event      = "issue.status_changed"
    issue_id   = "SHA-TEST"
    issue_url  = "https://linear.app/zkaufman/issue/SHA-16"
    team       = "Shapez2Factory"
    state      = "Todo"
    labels     = @("question")
    test       = $true
} | ConvertTo-Json -Compress

$headers = @{
    Authorization = "Bearer $token"
    "Content-Type" = "application/json"
}

Write-Host "POST $url"
try {
    $resp = Invoke-WebRequest -Uri $url -Method POST -Headers $headers -Body $body -UseBasicParsing
    Write-Host "Status:" $resp.StatusCode
    Write-Host $resp.Content
}
catch {
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $text = $reader.ReadToEnd()
        Write-Host "HTTP error:" $_.Exception.Response.StatusCode.value__
        Write-Host $text
    }
    else {
        throw
    }
}
