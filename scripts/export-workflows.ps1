# Saves the workflows FROM n8n into this repo (n8n -> repo).
# Run it after you change a workflow in the editor, then commit the result.
#
# Only the workflow itself is kept. Owner and sharing details (which include your
# n8n account email) are stripped, so the files are safe for a public GitHub repo.
# Credentials are never exported: the files hold a credential's name and ID, not the secret.
#
#   .\scripts\export-workflows.ps1

$root = Split-Path $PSScriptRoot -Parent
$container = "sprint-n8n"
$map = [ordered]@{
    "SprintRouter0000" = "00-telegram-router"
    "SprintAdBrief001" = "01-ad-brief-to-script-pack"
    "SprintRender0002" = "02-clips-to-finished-ad"
    "SprintPublish003" = "03-approve-publish-report"
}

# Runs inside the n8n container (it has Node.js): keep a fixed set of fields, pretty-print.
$tidy = @'
const fs = require("fs");
let wf = JSON.parse(fs.readFileSync("/tmp/export.json", "utf8"));
if (Array.isArray(wf)) wf = wf[0];
const keep = ["id", "name", "nodes", "connections", "settings", "pinData", "meta", "tags"];
const out = {};
for (const k of keep) if (wf[k] !== undefined) out[k] = wf[k];
out.active = false;
out.tags = (out.tags || []).map(t => (typeof t === "string" ? t : { name: t.name }));
fs.writeFileSync("/tmp/tidy.json", JSON.stringify(out, null, 2) + "\n");
'@
$tidyFile = Join-Path $env:TEMP "n8n-tidy.js"
[IO.File]::WriteAllText($tidyFile, $tidy, (New-Object Text.UTF8Encoding($false)))
docker cp $tidyFile "${container}:/tmp/tidy.js" | Out-Null
Remove-Item $tidyFile

foreach ($id in $map.Keys) {
    $folder = $map[$id]
    docker exec $container n8n export:workflow --id=$id --output=/tmp/export.json | Out-Null
    docker exec $container node /tmp/tidy.js
    if ($LASTEXITCODE -ne 0) { Write-Host "Could not export $folder"; continue }
    docker cp "${container}:/tmp/tidy.json" "$root\workflows\$folder\workflow.json" | Out-Null
    Write-Host "Exported $folder"
}
Write-Host "Done. Review the changes with: git diff"
