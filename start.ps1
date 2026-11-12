# Starts the whole stack and connects Telegram to it.
#
# Telegram needs a public HTTPS address to deliver messages to n8n. The free
# Cloudflare "quick tunnel" gives the laptop one, but the address is NEW every
# time the tunnel starts. This script reads the new address, saves it in .env
# and restarts n8n so the bot's webhook points to it.
#
# Run it after every reboot:   .\start.ps1      (or double-click start.cmd)

Set-Location $PSScriptRoot

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example"
}

Write-Host "1/4 Starting the video service, the gateway and the tunnel..."
docker compose --profile tunnel up -d --build media-worker gateway | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Host "Docker could not start the services. Is Docker Desktop running?"; exit 1 }
# A tunnel that is already running keeps its address. A stopped one is rebuilt from
# scratch, so its log holds only the NEW address (an old log would still show the old one).
$tunnelRunning = docker ps --filter "name=sprint-tunnel" --filter "status=running" -q
if (-not $tunnelRunning) {
    docker compose --profile tunnel up -d --force-recreate tunnel | Out-Null
}

Write-Host "2/4 Waiting for the public address..."
$url = $null
for ($i = 0; $i -lt 30 -and -not $url; $i++) {
    Start-Sleep -Seconds 2
    # cloudflared writes its log to stderr; cmd merges it so PowerShell 5.1 does not treat it as an error.
    $log = (cmd /c "docker logs sprint-tunnel 2>&1") -join "`n"
    $found = [regex]::Matches($log, 'https://[a-z0-9-]+\.trycloudflare\.com')
    if ($found.Count -gt 0) { $url = $found[$found.Count - 1].Value }
}
if (-not $url) {
    Write-Host "No public address after 60 seconds. Check your internet, then run: docker logs sprint-tunnel"
    exit 1
}

Write-Host "3/4 Saving $url to .env..."
$envText = [IO.File]::ReadAllText("$PSScriptRoot\.env")
if ($envText -match '(?m)^WEBHOOK_URL=.*$') {
    $envText = [regex]::Replace($envText, '(?m)^WEBHOOK_URL=.*$', "WEBHOOK_URL=$url/")
} else {
    $envText = $envText.TrimEnd() + "`nWEBHOOK_URL=$url/`n"
}
# Write without a BOM: docker compose cannot read a .env file that starts with one.
[IO.File]::WriteAllText("$PSScriptRoot\.env", $envText, (New-Object Text.UTF8Encoding($false)))

Write-Host "4/4 Starting n8n with the new address..."
docker compose up -d n8n | Out-Null
$ready = $false
for ($i = 0; $i -lt 45 -and -not $ready; $i++) {
    Start-Sleep -Seconds 2
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri http://localhost:5679/healthz/readiness -TimeoutSec 3
        $ready = $r.StatusCode -eq 200
    } catch { }
}
if (-not $ready) { Write-Host "n8n did not become ready. Run: docker logs sprint-n8n"; exit 1 }

Write-Host ""
Write-Host "Ready."
Write-Host "  n8n editor (this laptop only):  http://localhost:5679"
Write-Host "  Public address (Telegram only): $url"
Write-Host "  Finished videos:                $PSScriptRoot\files\out"
Write-Host ""
Write-Host "Open Telegram and send /start to your bot."
