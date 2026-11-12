# Demo video script · 01 Ad Brief to Script Pack

**Length:** about 75 seconds · **Format:** screen recording, landscape 1920x1080, with your voice
**Tools:** OBS Studio or Windows Game Bar (Win + Alt + R), Telegram Desktop, a browser

## Before you record

- Run `.\start.ps1` and send `/start` to check the bot answers.
- Use Gemini, not the local model, so the script is good on the first take.
- Open three windows: Telegram Desktop (bot chat, cleared), the Google Sheet (Calendar tab), the n8n workflow canvas.
- Copy the `/ad` line below to the clipboard.
- Hide personal stuff: other chats, bookmarks bar, notifications (turn on Do Not Disturb).

```
/ad Vanilla Oat Cold Brew | smooth, never bitter, 120mg caffeine | students and remote workers | English
```

## Shot list

| # | Time | On screen | You say |
|---|------|-----------|---------|
| 1 | 0:00–0:10 | Title card or your face: "From one message to a full video ad script" | "Small businesses need video ads but don't have time to write them. This automation writes the whole ad from one Telegram message." |
| 2 | 0:10–0:20 | Telegram. Paste the `/ad` line, press Enter | "The owner sends the product, the main benefit and the audience. That's all." |
| 3 | 0:20–0:35 | Messages arrive. Scroll slowly through the overview | "About twenty seconds later they get a three-scene script: hook, benefit and call to action, with on-screen text and voiceover." |
| 4 | 0:35–0:45 | Tap a scene prompt so "copied" appears. Switch to Google Flow, paste it | "Each scene comes with a ready-made prompt for Google Veo. One tap copies it." |
| 5 | 0:45–0:55 | Google Sheet. Show the new row, highlight the status `SCRIPTED` | "Every script is logged in a Google Sheets content calendar automatically." |
| 6 | 0:55–1:10 | n8n canvas. Hover over Ask the AI, Parse Script Pack, Tell Owner It Failed | "Under the hood it's an n8n workflow. The AI model is swappable, the answer is validated before use, and every failure sends the owner a clear message." |
| 7 | 1:10–1:15 | End card: your name, "AI Automation · n8n", contact | "I'm Zali. I build automations like this." |

## Tips

- Record shots 2 to 5 in one take so the timing is real. Speed up the wait in editing if it drags.
- If the script comes out weak, send `/ad` again and use the better take. That is honest: the owner can do the same.
- Export 1080p MP4. Upload to YouTube (unlisted) or Loom and link it in the main README.
