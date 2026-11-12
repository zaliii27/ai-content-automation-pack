# HANDOFF: continue this project with free models

Written 2026-11-12 (Thursday of the Fable Sprint). Read this first if you are an AI model or a person picking the project up.

**Owner:** Zali, a beginner at AI automation. Explain things briefly, give one step at a time, and never ask them to paste a secret key into a chat.

## 1. What this project is

A portfolio piece: an **AI content automation pack** for small businesses. One Telegram bot turns a product brief into a finished short video ad. Target jobs: part-time remote "n8n developer", "AI automation specialist", "AI content creator" roles, for US and Philippine clients.

Read [README.md](README.md) for the overview and [docs/SETUP.md](docs/SETUP.md) for setup.

## 2. What is done

Updated 2026-11-13 after the first live run.

| Piece | State | How it was checked |
|---|---|---|
| Docker stack: n8n 2.37.7 on port 5679, media-worker on 8090 | Running | Health checks pass |
| media-worker (ffmpeg service) | Working | Rendered sample clips (portrait and landscape) into a 14.5 s ad; frames inspected |
| Tunnel, gateway and `start.ps1` | Working live | Telegram delivers through the tunnel; the editor returns 404 from outside |
| Telegram bot (`/start`, text messages, video preview with buttons) | Working live | Real `/start` from the owner's phone; report and preview arrived |
| Google Sheets (read, append, update) | Working live | A real `/ad` row was written, then updated to `READY`; checked in the sheet |
| Workflow 01 end to end | Working live | Brief → local LLM → sheet row → Telegram messages |
| Workflow 02 demo path | Working live | Placeholder clips → render → preview sent → sheet updated |
| Workflow 03 report path | Working live | Report read from the real sheet and sent to Telegram |
| Error branches | Working (stand-ins) | Each failure path returns the plain-language message |
| Google Cloud | Set up | Project `content-studio`, Sheets API on, service account `n8n-content-studio`, sheet shared with it |
| READMEs, demo scripts, setup guide | Written | |

## 3. What is NOT done or NOT verified

Be honest about these in any status report.

1. **A real clip sent in Telegram has not gone through** (the "Download Clip" node). Only `/demo` placeholder clips.
2. **The Approve and Redo buttons have not been tapped live.** The approve and redo logic ran only through the API with stand-ins.
3. **Auto-posting to a channel (`PUBLISH_CHAT_ID`) has never run.**
4. **Gemini has not been tried.** Only the local model, which is weak.
5. **No real Google Flow clip has gone through the renderer.**
6. **No screenshots, no demo videos, no GitHub push yet.**
7. **"Result" sections** in the READMEs hold test measurements with `TODO` markers, not numbers from real use.

## 4. Exact next steps, in order

### A. Setup (done on 2026-11-13)

Bot token, Google Sheet, service account and chat ID are all in place. To repeat the setup on another machine, follow [docs/SETUP.md](docs/SETUP.md). `scripts/set-google-key.ps1` loads a downloaded service account key file into n8n without copy-pasting.

### B. Finish the live test

In Telegram: tap **Approve** on a preview, send `/report`, then send 3 real video clips, then try **Redo**. For each failure: open n8n → **Executions** → the red run → the red node, and read the error. Likely suspects are listed in section 6 below.

After fixing anything in the editor, save it back to the repo:

```powershell
.\scripts\export-workflows.ps1
git add -A
git commit -m "Fix <what> after live test"
```

### C. Switch to Gemini for demo quality

Setup guide section 5, option B. Then send the same `/ad` line and compare. If Gemini rejects the request, see gotcha 9.

### D. Record and publish

1. Take screenshots into `docs/screenshots/` using the file names the READMEs reference. Remove the `TODO` comments.
2. Record the 3 demo videos from each workflow's `demo-script.md`.
3. Replace the `TODO` "Result" numbers with what you measured.
4. Push to GitHub. The `gh` tool is not installed; use GitHub Desktop, or create an empty repo on github.com and run:

```powershell
git remote add origin https://github.com/<your-username>/ai-content-automation-pack.git
git push -u origin main
```

Before pushing, run `git status` and confirm `.env` and `files/` contents are not listed.

### E. Good first improvements for a free model (each is small and self-contained)

| Task | Where | Notes |
|---|---|---|
| Post approved ads to a Facebook Page | Workflow 03, after **Channel Set?** | Graph API `POST /{page-id}/videos` with a Page access token. Add a `PUBLISH_TARGET` setting. |
| Add voiceover (text to speech) | `worker/app.py`, new `/tts` endpoint; workflow 02 | Each scene already has a `voiceover` line in the script pack. Add `sceneN_voiceover` columns. |
| Background music bed | `worker/app.py` `render()` | Mix a royalty-free track at low volume with ffmpeg `amix`. |
| Web form intake | Workflow 01, add an n8n Form Trigger | Feed it into **Config** like the other two triggers. |
| Per-brand settings in the Sheet | New `Settings` tab | Lets the owner change voice and CTA without touching `.env`. |
| Error alert workflow | New workflow with an Error Trigger | Send any uncaught failure to the owner's chat. |
| Stable public address | `docker-compose.yml`, `start.ps1` | ngrok free static domain or a Cloudflare named tunnel, so the address survives restarts. |

## 5. How things fit together

```
Telegram → Cloudflare quick tunnel → gateway (Caddy, allows one path) → n8n :5678
n8n → LLM (Ollama on the laptop, or Gemini)        via LLM_BASE_URL
n8n → media-worker :8000 (ffmpeg)                  via MEDIA_WORKER_URL
n8n → Google Sheets                                via service account
media-worker ↔ ./files (inbox/<ad code>/, out/<ad code>.mp4)
```

- Fixed workflow IDs: `SprintRouter0000`, `SprintAdBrief001`, `SprintRender0002`, `SprintPublish003`.
- Fixed credential IDs: `SprintTelegram01`, `SprintGSheets001`, `SprintLlmKey0001`.
- Every workflow starts with a **Config** node that reads `.env` values through `$env`. Nodes after it read `cfg.*`.
- Ad statuses: `SCRIPTED` → `READY` → `APPROVED` → `POSTED`, or `REDO`.

## 6. Known gotchas

1. **One Telegram bot, one trigger.** Never add a second Telegram Trigger for this bot. Add a route in workflow 00 instead.
2. **The public address changes on every tunnel start.** After a reboot the bot is silent until `.\start.ps1` runs. If the bot stops answering, run it first.
3. **Importing with the CLI switches workflows off, and CLI changes need an n8n restart.** `scripts/import-workflows.ps1` handles both, but the router must be re-published by hand.
4. **Sub-workflows must stay published,** or the router's "Run 0X" nodes fail.
5. **`$env` in expressions is blocked by default in n8n 2.x.** This stack sets `N8N_BLOCK_ENV_ACCESS_IN_NODE=false`. On n8n Cloud, `$env` is not available: replace the expressions in each **Config** node with plain values.
6. **Telegram file limits.** A bot can download 20 MB and upload 50 MB. Bigger clips: send as a normal video (Telegram compresses it), or drop the file in `files/inbox/<ad code>/` and send `/render <ad code>`.
7. **Clips pile up.** Clips are used in the order sent. Sending new clips for an ad that already has 3 gives a 4-clip ad. Tap **Redo** first.
8. **Google Sheet rules.** Tab must be named `Calendar`. Header names must match the template exactly. Don't rename or delete columns. Editing cell values (for example a caption before rendering) is fine.
9. **LLM answer shape.** The request uses `response_format: json_schema`. If a provider rejects it, change it to `{ type: 'json_object' }` in **Build Brief**. If a provider rejects `reasoning_effort`, set `LLM_REASONING_EFFORT=` (empty) in `.env`.
10. **Local model quality.** `qwen3:8b` writes clumsy Taglish and sometimes adds claims that were not in the brief ("no crash"). Use Gemini for anything a client will see, and read every script before generating clips.
11. **Don't put `: ` (colon, space) in a Code node error message.** n8n cuts off everything before it. Use "like this → ..." instead.
12. **Burned-in captions drop emoji.** The caption font has no emoji. They are removed on purpose.
13. **Google Flow has no API** for subscription credits. The clip step is manual by design. Credits are limited, so use `/demo` while testing.
14. **`brain-n8n` on port 5678 is a different project** (Zali's Second Brain). Never stop, restart or edit it. This project is `sprint-n8n` on 5679.
15. **A "Python task runner" warning in the n8n log is harmless.** No workflow uses Python.
16. **Docker Desktop has about 4 GB of RAM** on this laptop. Rendering is light, but don't run heavy containers next to it.
17. **The workflow files are tidied n8n exports.** `scripts/export-workflows.ps1` strips owner and sharing details (they contain the n8n account email). Don't commit a raw export from the n8n editor's "Download" button without checking it for personal details. Edit in the n8n editor, then run the export script.

18. **Type IDs, don't read them off screenshots.** A chat ID misread by one digit made Telegram answer "chat not found" and would have locked the owner out. Copy the number as text.

## 7. Useful commands

```powershell
.\start.ps1                                   # start everything, reconnect Telegram
docker compose --profile tunnel down          # stop everything (data is kept)
docker logs sprint-n8n --tail 50              # n8n log
docker logs sprint-media-worker --tail 50     # video service log
.\scripts\export-workflows.ps1                # n8n → repo
.\scripts\import-workflows.ps1                # repo → n8n
```

Test a workflow without Telegram:

```powershell
curl.exe -X POST http://localhost:5679/webhook/ad-brief -H "Content-Type: application/json" -d '{\"product\":\"Ube Latte\",\"language\":\"Taglish\"}'
curl.exe -X POST http://localhost:5679/webhook/ad-action -H "Content-Type: application/json" -d '{\"action\":\"report\"}'
curl.exe -X POST "http://localhost:8090/sample-clips/AD-TEST?n=3"
```

## 8. Prompt to give a free model

> You are helping Zali, a beginner, continue an n8n project. Read HANDOFF.md, README.md and docs/SETUP.md first. Work on one task from HANDOFF section 4 at a time. Explain each step briefly. Edit workflows in the n8n editor at http://localhost:5679 and then run scripts/export-workflows.ps1. Never ask for API keys or tokens in chat: tell Zali which n8n credential to paste them into. Do not touch the brain-n8n container.
