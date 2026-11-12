# Loads the workflow files from this repo INTO n8n (repo -> n8n).
# Use it on a fresh n8n, or to undo experiments and go back to the repo version.
# It overwrites workflows that have the same ID.
#
#   .\scripts\import-workflows.ps1
#   .\scripts\import-workflows.ps1 -WithPlaceholders   (first time only: also creates the 3 empty credentials)

param([switch]$WithPlaceholders)

$root = Split-Path $PSScriptRoot -Parent
$container = "sprint-n8n"

docker exec $container sh -c "rm -rf /tmp/wf && mkdir -p /tmp/wf" | Out-Null
Get-ChildItem "$root\workflows" -Directory | ForEach-Object {
    docker cp "$($_.FullName)\workflow.json" "${container}:/tmp/wf/$($_.Name).json" | Out-Null
}

if ($WithPlaceholders) {
    docker cp "$root\scripts\credential-placeholders.json" "${container}:/tmp/creds.json" | Out-Null
    docker exec $container n8n import:credentials --input=/tmp/creds.json
}

docker exec $container n8n import:workflow --separate --input=/tmp/wf

# Importing switches workflows off. Switch the three sub-workflows back on.
# The router (00) is switched on by hand in the editor, once the Telegram token is saved.
foreach ($id in "SprintAdBrief001", "SprintRender0002", "SprintPublish003") {
    docker exec $container n8n publish:workflow --id=$id | Out-Null
}
docker restart $container | Out-Null
Write-Host "Imported. n8n is restarting (about 20 seconds). Then open http://localhost:5679"
Write-Host "If the Telegram router was on before, open it in the editor and publish it again."
