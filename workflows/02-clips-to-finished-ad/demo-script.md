# Demo video script · 02 Clips to Finished Ad

**Length:** about 90 seconds · **Format:** screen recording, landscape 1920x1080, with your voice
**Tools:** OBS Studio or Windows Game Bar, Telegram Desktop, Google Flow, a browser

## Before you record

- Have a script from workflow 01 ready (an ad with status `SCRIPTED`).
- Generate the 3 clips in Google Flow **before** recording (Veo, portrait 9:16) and download them. Generation takes minutes and costs credits, so don't do it live. Record a few seconds of Flow generating for shot 2.
- Name the files `1.mp4`, `2.mp4`, `3.mp4` so you send them in order.
- Open: Telegram Desktop (bot chat), the Google Sheet, the n8n canvas for workflow 02, the `files\out` folder.

## Shot list

| # | Time | On screen | You say |
|---|------|-----------|---------|
| 1 | 0:00–0:10 | Split screen: 3 raw clips on the left, finished ad on the right | "AI video tools give you raw clips. Turning them into a finished ad is the same boring edit every time. This automation does that edit." |
| 2 | 0:10–0:20 | Google Flow with the prompt from workflow 01 pasted in, a clip generating | "I generate the three scenes in Google Flow using the prompts from the first workflow." |
| 3 | 0:20–0:35 | Telegram. Drag in clip 1, then 2, then 3. Show "Clip 1 of 3 saved", "Clip 2 of 3 saved" | "Then I just send the clips to the bot, in order." |
| 4 | 0:35–0:50 | "Building your ad" message, then the finished video arrives with Approve / Redo buttons | "After the third clip it builds the ad: vertical format, captions from the content calendar, and a branded end card." |
| 5 | 0:50–1:05 | Play the finished ad full screen | (Let it play. Say nothing, or: "Here's the result.") |
| 6 | 1:05–1:15 | Google Sheet: the row now says `READY` | "The calendar updates itself." |
| 7 | 1:15–1:27 | n8n canvas: hover Store Clip, Render Ad. Then show `worker/app.py` for two seconds | "n8n can't edit video, so I wrote a small ffmpeg service that the workflow calls. Landscape clips get a blurred background instead of being cropped." |
| 8 | 1:27–1:32 | End card | "I'm Zali. I build automations like this." |

## No Flow credits left?

Send `/demo` instead of clips in shot 3. It builds the ad from placeholder clips. Say so in the voiceover: "Here I'm using placeholder clips to show the pipeline."

## Tips

- If a clip is over 20 MB, send it as a normal video, not as a file, so Telegram compresses it.
- Want to redo a take? Tap **Redo** first. It clears the stored clips so the next 3 start fresh.
