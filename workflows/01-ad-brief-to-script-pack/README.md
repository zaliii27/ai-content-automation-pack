# 01 · Ad Brief to Script Pack

![Workflow screenshot](../../docs/screenshots/01-ad-brief-to-script-pack.png)
<!-- TODO: screenshot of the workflow canvas, plus one of the Telegram chat showing the script pack -->

## Problem

A small business owner knows the product but not how to write a video ad. Hooks, scene ideas, AI video prompts, captions and hashtags take an hour per ad, so the ads don't get made.

## Solution

The owner sends one line to a Telegram bot:

```
/ad Vanilla Oat Cold Brew | smooth, never bitter, 120mg caffeine | students and remote workers | English
```

An optional fifth part sets the style, and can switch the voiceover off:

```
/ad Ube Cheese Pandesal | soft, baked fresh every morning | pastry lovers | English | luxurious, slow, no voiceover, piano music only
```

About 20 seconds later they have a complete **script pack**:

- the idea of the ad in one sentence
- 3 scenes (hook, benefit, call to action), each with on-screen text and a voiceover line
- a ready-to-paste **Google Veo prompt** per scene, in a tap-to-copy block
- a caption and 5 to 8 hashtags
- an ad code such as `AD-7KQ2M`, and a new row in the Google Sheets content calendar

## How it works

| Step | Node | What it does |
|---|---|---|
| 1 | **From Telegram Router** / **API: POST ad-brief** | Two ways in: the bot, or another app calling `POST /webhook/ad-brief` |
| 2 | **Config** | Reads the brand and model settings from `.env` |
| 3 | **Build Brief** (Code) | Parses the brief, makes the ad code, writes the instructions for the AI |
| 4 | **Ask the AI** (HTTP Request) | Calls any OpenAI-compatible model. A JSON schema forces the answer shape. Retries up to 5 times, because free AI tiers are often briefly overloaded. |
| 5 | **Parse Script Pack** (Code) | Checks the answer really has 3 complete scenes, trims lengths, cleans hashtags |
| 6 | **Save to Calendar** (Google Sheets) | Appends the row with status `SCRIPTED` |
| 7 | **Write Telegram Messages** (Code) | One overview message, one message per Veo prompt, one "next step" message |
| 8 | **Send Script Pack** (Telegram) | Delivers them to the owner |
| ! | **Tell Owner It Failed** | Any failing step sends a plain-language message instead of silence |

### API use

```bash
curl -X POST http://localhost:5679/webhook/ad-brief \
  -H "Content-Type: application/json" \
  -d '{"product":"Vanilla Oat Cold Brew","benefit":"smooth, never bitter","audience":"students","language":"Taglish","style":"playful, fast cuts"}'
```

Returns the script pack as JSON. This is how another system (a chatbot, a form, a CRM) can order an ad.

## Result

- Brief to full script pack: about 20 seconds on Gemini Flash-Lite (free tier), and about the same on a local 8B model.
- The prompts follow a fixed recipe (9:16, 8 seconds, consistent product look, no on-screen text), so clips from different scenes fit together.
- Supports English, Tagalog and Taglish for on-screen text, voiceover and caption. Veo prompts are always English.

## Settings used

`LLM_BASE_URL`, `LLM_MODEL`, `LLM_REASONING_EFFORT`, `BRAND_NAME`, `BRAND_VOICE`, `BRAND_CTA`, `SHEET_ID`, `OWNER_CHAT_ID`

Demo video script: [demo-script.md](demo-script.md)
