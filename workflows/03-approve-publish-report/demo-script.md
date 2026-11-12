# Demo video script · 03 Approve, Publish and Report

**Length:** about 70 seconds · **Format:** screen recording, landscape 1920x1080, with your voice
**Tools:** OBS Studio or Windows Game Bar, Telegram Desktop, a browser

## Before you record

- Have one ad at status `READY` with its preview and buttons visible in the bot chat.
- Have 4 or 5 other rows in the calendar at mixed statuses (`SCRIPTED`, `READY`, `APPROVED`, `POSTED`) from the last 7 days, so the report has something to count. Make them with `/ad` and `/demo`.
- For the auto-post shot: create a Telegram channel (for example "Tala Coffee Co."), add the bot as admin, put the channel ID in `.env` as `PUBLISH_CHAT_ID`, run `.\start.ps1`. Skip this and you show the posting kit instead, which is also fine.
- Open: Telegram Desktop, the Google Sheet, the n8n canvas for workflow 03.

## Shot list

| # | Time | On screen | You say |
|---|------|-----------|---------|
| 1 | 0:00–0:08 | Title card: "Approve from your phone. Get a weekly report." | "Making content is half the job. The other half is approving it, posting it and keeping track. This workflow handles that." |
| 2 | 0:08–0:20 | Telegram: the ad preview. Click **Approve** | "The owner reviews the finished ad in Telegram and taps Approve. Nothing gets posted without that tap." |
| 3 | 0:20–0:32 | The channel showing the posted ad (or the posting kit message, tap to copy the caption) | "The ad is posted to the brand's channel with its caption." (or: "They get the caption and hashtags, one tap to copy, ready for TikTok or Instagram.") |
| 4 | 0:32–0:40 | Google Sheet: row changed to `POSTED` with the time | "The content calendar records when it was approved and posted." |
| 5 | 0:40–0:55 | Telegram: send `/report`. The report arrives. Pause on it | "Every Monday morning the owner gets this report: scripts written, ads rendered, approved and posted, plus what's waiting on them." |
| 6 | 0:55–1:05 | n8n canvas: show the three triggers, then the Which Action switch | "One workflow, three ways in: a button tap, a weekly schedule, or an API call." |
| 7 | 1:05–1:10 | End card | "I'm Zali. I build automations like this." |

## Tips

- To show **Redo**: tap it on another `READY` ad and show the "Cleared the clips" reply. Optional, adds about 8 seconds.
- You can't wait for Monday on camera. `/report` runs the same path as the schedule.
