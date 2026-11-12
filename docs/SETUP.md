# Setup, step by step

Written for a beginner on Windows. Allow about 45 minutes the first time.

You will fill in **three credentials** in n8n. A credential is n8n's locked storage for a key: you paste it once, and workflows use it without showing it.

| Credential in n8n | What you paste | Needed for |
|---|---|---|
| Content Studio Bot (Telegram) | Bot token from BotFather | Everything |
| Content Calendar (Google service account) | Service account email + private key | Saving to Google Sheets |
| LLM API key (Bearer header) | `Bearer <your Gemini key>` | Only if you switch from local Ollama to Gemini |

## 1. Start n8n

1. Install and open **Docker Desktop**.
2. In this folder, copy `.env.example` to `.env`.
3. Run `docker compose up -d`.
4. Open http://localhost:5679 and create the owner account. It is stored only on your laptop.

## 2. Load the workflows

```powershell
.\scripts\import-workflows.ps1 -WithPlaceholders
```

This loads the 4 workflows and creates the 3 credentials above, empty, already connected to the right nodes.

## 3. Telegram bot

1. In Telegram, open **@BotFather** (blue checkmark) and send `/newbot`.
2. Choose a display name, then a username ending in `bot`.
3. BotFather replies with a **token**. Treat it like a password.
4. In n8n: **Credentials** → **Content Studio Bot (Telegram)** → paste the token into **Access Token** → **Save**. You should see "Connection tested successfully".

## 4. Google Sheets content calendar

**Make the sheet**

1. Create a new Google Sheet. Name it anything, for example `Content Calendar`.
2. **File → Import → Upload** `docs/content-calendar-template.csv`, and choose **Replace current sheet**.
3. Rename the tab at the bottom to exactly `Calendar`.
4. Copy the sheet ID from the address bar (the long part between `/d/` and `/edit`) into `.env` as `SHEET_ID=`.

**Make a service account** (a robot Google account that n8n logs in as)

1. Open https://console.cloud.google.com and create a project.
2. **APIs & Services → Library**: enable **Google Sheets API** and **Google Drive API**.
3. **IAM & Admin → Service Accounts → Create service account**. Name it, then **Done**.
4. Open the new service account → **Keys → Add key → Create new key → JSON**. A file downloads. Keep it out of this folder.
5. Open that file in Notepad. You need two values: `client_email` and `private_key`.
6. In n8n: **Credentials** → **Content Calendar (Google service account)** → paste `client_email` into **Service Account Email** and the whole `private_key` (from `-----BEGIN` to `-----END PRIVATE KEY-----\n`) into **Private Key** → **Save**.
7. Back in the Google Sheet: **Share** → paste the `client_email` address → role **Editor** → **Send**.

## 5. AI model

**Option A, local and free (default):** install [Ollama](https://ollama.com) and run `ollama pull qwen3:8b`. Nothing else to do. Quality is fine for testing, weak for Taglish.

**Option B, Gemini (better scripts):**

1. Get an API key at https://aistudio.google.com/apikey.
2. In n8n: **Credentials** → **LLM API key (Bearer header)** → set **Value** to `Bearer ` followed by your key → **Save**.
3. In `.env`, switch the two `LLM_` lines to the Gemini ones shown in the comments.

## 6. Go live

1. Run `.\start.ps1` (or double-click `start.cmd`). It starts everything and gives Telegram a public address to reach your laptop.
2. In n8n, open **00 Telegram Router** and click **Publish**.
3. In Telegram, send `/start` to your bot. It replies with your chat ID.
4. Put that number in `.env` as `OWNER_CHAT_ID=`, then run `.\start.ps1` again. Now the bot only listens to you.

## 7. Try it

1. `/ad Vanilla Oat Cold Brew | smooth, never bitter, 120mg caffeine | students and remote workers | English`
2. Check the new row in your Google Sheet.
3. `/demo` to see a finished ad built from placeholder clips.
4. Tap **Approve**.
5. `/report`

For a real ad: paste each scene prompt into [Google Flow](https://labs.google/flow), set it to portrait 9:16, download the 3 clips and send them to the bot in order.

## Every day after that

Run `.\start.ps1` after each reboot. The free tunnel gets a new public address every time, and the script reconnects Telegram to it.
