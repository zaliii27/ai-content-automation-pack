# Loads a Google service account key file into the n8n credential
# "Content Calendar (Google service account)", so you don't have to copy and paste the key.
#
# The key is read from the file and handed straight to n8n, which stores it encrypted.
# It is never printed on screen and never written into this project folder.
#
#   .\scripts\set-google-key.ps1                      (uses the newest key file in Downloads)
#   .\scripts\set-google-key.ps1 -KeyFile C:\path\key.json

param([string]$KeyFile)

$root = Split-Path $PSScriptRoot -Parent
$container = "sprint-n8n"

if (-not $KeyFile) {
    $found = Get-ChildItem "$env:USERPROFILE\Downloads\*.json" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Where-Object { (Get-Content $_.FullName -Raw) -match '"type"\s*:\s*"service_account"' } |
        Select-Object -First 1
    if (-not $found) {
        Write-Host "No service account key file found in Downloads. Pass it with -KeyFile <path>."
        exit 1
    }
    $KeyFile = $found.FullName
}
if (-not (Test-Path $KeyFile)) { Write-Host "File not found: $KeyFile"; exit 1 }

$key = Get-Content $KeyFile -Raw | ConvertFrom-Json
if ($key.type -ne "service_account" -or -not $key.client_email -or -not $key.private_key) {
    Write-Host "That file is not a Google service account key."
    exit 1
}

$credential = @(@{
    id   = "SprintGSheets001"
    name = "Content Calendar (Google service account)"
    type = "googleApi"
    data = @{ region = "us-central1"; email = $key.client_email; privateKey = $key.private_key; inpersonate = $false; httpNode = $false }
})
$tmp = Join-Path $env:TEMP ("n8n-gkey-" + [guid]::NewGuid().ToString("N") + ".json")
[IO.File]::WriteAllText($tmp, (ConvertTo-Json -InputObject $credential -Depth 5), (New-Object Text.UTF8Encoding($false)))

docker cp $tmp "${container}:/tmp/gkey.json" | Out-Null
Remove-Item $tmp -Force
docker exec $container n8n import:credentials --input=/tmp/gkey.json | Select-Object -Last 1
$ok = $LASTEXITCODE -eq 0
docker exec -u root $container rm -f /tmp/gkey.json | Out-Null
if (-not $ok) { Write-Host "n8n did not accept the key. Is the sprint-n8n container running?"; exit 1 }

# The address is not a secret. It is saved so the sheet can be shared with it.
[IO.File]::WriteAllText("$root\files\service-account-email.txt", $key.client_email)

Write-Host ""
Write-Host "Key saved in n8n for: $($key.client_email)"
Write-Host "Key file used:        $KeyFile"
Write-Host ""
Write-Host "Next: share the Google Sheet with that address as Editor."
Write-Host "Keep the key file somewhere safe outside this folder, or delete it. n8n has its own copy now."
