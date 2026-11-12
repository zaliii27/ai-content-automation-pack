"""
media-worker: a tiny video finishing service for the AI Content Automation Pack.

n8n cannot run ffmpeg itself, so it calls this service over HTTP.
The service turns raw AI video clips (for example from Google Flow / Veo)
into one finished vertical ad:

    raw clips  ->  1080x1920, 30 fps  ->  burned-in captions  ->  end card  ->  one MP4

Endpoints
    GET    /health
    POST   /clips/{content_id}          upload one clip (multipart field "file")
    GET    /clips/{content_id}          list stored clips
    DELETE /clips/{content_id}          delete stored clips (used by "Redo")
    POST   /sample-clips/{content_id}   make placeholder clips (demo mode, no AI credits)
    POST   /render                      build the finished ad
    GET    /out/{content_id}.mp4        download the finished ad

All files live under FILES_DIR (the ./files folder of the project):
    inbox/<content_id>/   raw clips, used in file-name order
    out/<content_id>.mp4  finished ads
"""

from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
import threading
import time
import unicodedata
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field

FILES = Path(os.environ.get("FILES_DIR", "/files"))
INBOX = FILES / "inbox"
OUT = FILES / "out"
TMP = FILES / "tmp"

W, H, FPS = 1080, 1920, 30          # vertical 9:16, the TikTok / Reels / Shorts format
MAX_CLIP_SECONDS = 15               # safety cap per clip
MAX_UPLOAD_MB = 200
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")

# Encoding settings shared by every segment, so segments can be joined without re-encoding.
ENCODE = [
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
    "-r", str(FPS), "-video_track_timescale", "15360",
    "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
]

app = FastAPI(title="media-worker", version="1.0.0")
_clip_lock = threading.Lock()       # one upload at a time, so clip counts are exact
_render_lock = threading.Lock()     # one render at a time, to protect a small laptop


# ----------------------------------------------------------------------------- helpers

def check_id(content_id: str) -> str:
    if not ID_RE.match(content_id):
        raise HTTPException(400, "content_id may only contain letters, numbers, - and _")
    return content_id


def run(cmd: list[str]) -> str:
    """Run a command and return stdout. Raise a readable error with ffmpeg's last lines."""
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-8:])
        raise HTTPException(500, f"{cmd[0]} failed:\n{tail}")
    return proc.stdout


def probe(path: Path) -> dict:
    """Width, height (after rotation), duration and whether the clip has sound."""
    data = json.loads(run([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_streams", "-show_format", str(path),
    ]))
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    if video is None:
        raise HTTPException(400, f"{path.name} has no video stream")
    width, height = int(video["width"]), int(video["height"])
    rotation = 0
    for side in video.get("side_data_list", []):
        if "rotation" in side:
            rotation = int(side["rotation"])
    if abs(rotation) in (90, 270):
        width, height = height, width
    return {
        "width": width,
        "height": height,
        "duration": float(data["format"].get("duration", 0) or 0),
        "has_audio": any(s["codec_type"] == "audio" for s in data["streams"]),
    }


def list_clips(content_id: str) -> list[Path]:
    folder = INBOX / content_id
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in VIDEO_EXT)


def find_font(bold: bool = True) -> str:
    wanted = (
        ["Montserrat-ExtraBold", "Montserrat-Bold", "DejaVuSans-Bold"]
        if bold else ["Montserrat-Medium", "Montserrat-Regular", "DejaVuSans"]
    )
    for name in wanted:
        hits = glob.glob(f"/usr/share/fonts/**/{name}.*", recursive=True)
        if hits:
            return hits[0]
    raise HTTPException(500, "No usable font found in the worker image")


def clean_text(text: str) -> str:
    """Drop emoji and other symbols the caption font cannot draw."""
    text = unicodedata.normalize("NFC", text or "")
    kept = [ch for ch in text if unicodedata.category(ch)[0] in "LNPZ" or ch in "$%+&#@₱€£"]
    return re.sub(r"\s+", " ", "".join(kept)).strip()


def wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    line = ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width or not line:
            line = candidate
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def fit_text(draw, text: str, max_width: int, start_size: int, max_lines: int):
    """Shrink the font until the text fits in max_lines lines."""
    size = start_size
    while True:
        font = ImageFont.truetype(find_font(), size)
        lines = wrap(draw, text, font, max_width)
        if len(lines) <= max_lines or size <= 36:
            return font, lines[:max_lines]
        size -= 6


def caption_overlay(text: str, dest: Path) -> None:
    """Transparent 1080x1920 PNG with one caption, placed above the app buttons area."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    text = clean_text(text)
    if text:
        font, lines = fit_text(draw, text, max_width=880, start_size=72, max_lines=3)
        line_h = int(font.size * 1.25)
        block_h = line_h * len(lines)
        block_w = max(int(draw.textlength(l, font=font)) for l in lines)
        center_y = int(H * 0.68)                      # safe zone: clear of the bottom UI
        top = center_y - block_h // 2
        pad_x, pad_y = 44, 30
        draw.rounded_rectangle(
            [(W - block_w) // 2 - pad_x, top - pad_y, (W + block_w) // 2 + pad_x, top + block_h + pad_y],
            radius=36, fill=(0, 0, 0, 150),
        )
        for i, line in enumerate(lines):
            lw = draw.textlength(line, font=font)
            draw.text(((W - lw) // 2, top + i * line_h), line, font=font, fill=(255, 255, 255, 255),
                      stroke_width=3, stroke_fill=(0, 0, 0, 255))
    img.save(dest)


def hex_to_rgb(color: str, fallback=(31, 58, 46)) -> tuple[int, int, int]:
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", (color or "").strip())
    if not m:
        return fallback
    v = m.group(1)
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


def end_card(brand: str, cta: str, color: str, dest: Path) -> None:
    """Full-screen closing card: brand name on top, call to action below."""
    bg = hex_to_rgb(color)
    light_bg = (0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2]) > 150
    fg = (20, 20, 20) if light_bg else (250, 246, 236)
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)
    brand, cta = clean_text(brand), clean_text(cta)
    y = int(H * 0.40)
    if brand:
        font, lines = fit_text(draw, brand, max_width=900, start_size=110, max_lines=2)
        for line in lines:
            lw = draw.textlength(line, font=font)
            draw.text(((W - lw) // 2, y), line, font=font, fill=fg)
            y += int(font.size * 1.2)
        y += 30
        draw.rectangle([(W // 2 - 90, y), (W // 2 + 90, y + 8)], fill=fg)
        y += 70
    if cta:
        font, lines = fit_text(draw, cta, max_width=860, start_size=64, max_lines=3)
        for line in lines:
            lw = draw.textlength(line, font=font)
            draw.text(((W - lw) // 2, y), line, font=font, fill=fg)
            y += int(font.size * 1.3)
    img.save(dest)


def normalize_clip(src: Path, overlay: Path, dest: Path) -> float:
    """Re-encode one clip to 1080x1920 / 30 fps with its caption burned in."""
    info = probe(src)
    portrait = info["width"] / info["height"] <= 0.80
    if portrait:
        # Already vertical: fill the frame, trim any overflow.
        base = f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[base]"
    else:
        # Landscape or square: keep the whole picture, fill the rest with a blurred copy.
        base = (
            f"[0:v]split=2[bg][fg];"
            f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=24:4[bgb];"
            f"[fg]scale={W}:-2[fgs];"
            f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2[base]"
        )
    graph = f"{base};[base][1:v]overlay=0:0,fps={FPS},setsar=1[v]"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-i", str(overlay)]
    if info["has_audio"]:
        graph += ";[0:a]aresample=48000,aformat=channel_layouts=stereo[a]"
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        graph += ";[2:a]anull[a]"
    duration = min(info["duration"] or MAX_CLIP_SECONDS, MAX_CLIP_SECONDS)
    cmd += ["-filter_complex", graph, "-map", "[v]", "-map", "[a]", "-t", f"{duration:.3f}", *ENCODE, str(dest)]
    run(cmd)
    return duration


def still_segment(image: Path, seconds: float, dest: Path) -> None:
    """A silent video segment that shows one image."""
    run([
        "ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-i", str(image),
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-vf", f"scale={W}:{H},setsar=1", "-t", f"{seconds:.3f}", *ENCODE, str(dest),
    ])


# ----------------------------------------------------------------------------- API

class RenderRequest(BaseModel):
    content_id: str
    texts: list[str] = Field(default_factory=list, description="One on-screen caption per clip, in order")
    brand: str = ""
    cta: str = ""
    brand_color: str = "#1F3A2E"
    end_card_seconds: float = 2.5


@app.get("/health")
def health():
    return {"ok": True, "ffmpeg": run(["ffmpeg", "-version"]).splitlines()[0]}


@app.post("/clips/{content_id}")
def upload_clip(content_id: str, file: UploadFile = File(...), order: str = Form("")):
    check_id(content_id)
    suffix = Path(file.filename or "clip.mp4").suffix.lower()
    if suffix not in VIDEO_EXT:
        suffix = ".mp4"             # unknown name: let ffprobe below decide if it is a video
    # Clips are used in file-name order. "order" is normally the Telegram message id,
    # which always grows, so clips keep the order the owner sent them in.
    prefix = order.zfill(12) if order.isdigit() and int(order) > 0 else str(time.time_ns())
    with _clip_lock:
        folder = INBOX / content_id
        folder.mkdir(parents=True, exist_ok=True)
        dest = folder / f"{prefix}{suffix}"
        if dest.exists():           # never overwrite a clip that is already stored
            dest = folder / f"{prefix}-{time.time_ns()}{suffix}"
        with dest.open("wb") as out:
            shutil.copyfileobj(file.file, out)
        if dest.stat().st_size > MAX_UPLOAD_MB * 1024 * 1024:
            dest.unlink()
            raise HTTPException(413, f"Clip is larger than {MAX_UPLOAD_MB} MB")
        try:
            probe(dest)
        except HTTPException:
            dest.unlink(missing_ok=True)
            raise HTTPException(400, "That file is not a video ffmpeg can read")
        clips = list_clips(content_id)
    return {"content_id": content_id, "count": len(clips), "files": [p.name for p in clips]}


@app.get("/clips/{content_id}")
def get_clips(content_id: str):
    clips = list_clips(check_id(content_id))
    return {"content_id": content_id, "count": len(clips), "files": [p.name for p in clips]}


@app.delete("/clips/{content_id}")
def delete_clips(content_id: str):
    check_id(content_id)
    with _clip_lock:
        removed = len(list_clips(content_id))
        shutil.rmtree(INBOX / content_id, ignore_errors=True)
    return {"content_id": content_id, "removed": removed}


@app.post("/sample-clips/{content_id}")
def sample_clips(content_id: str, n: int = 3, seconds: float = 4.0, replace: bool = True):
    """Demo mode: placeholder clips so the pipeline can be shown without spending AI video credits."""
    check_id(content_id)
    if replace:
        with _clip_lock:
            shutil.rmtree(INBOX / content_id, ignore_errors=True)
    n = max(1, min(n, 6))
    seconds = max(1.0, min(seconds, 8.0))
    palette = [((233, 196, 106), (231, 111, 81)), ((42, 157, 143), (38, 70, 83)), ((168, 218, 220), (69, 123, 157))]
    work = TMP / f"sample-{content_id}-{time.time_ns()}"
    work.mkdir(parents=True, exist_ok=True)
    try:
        with _clip_lock:
            folder = INBOX / content_id
            folder.mkdir(parents=True, exist_ok=True)
            for i in range(n):
                landscape = i == 1                    # one landscape clip, to exercise the blur fill
                size = (1920, 1080) if landscape else (W, H)
                top, bottom = palette[i % len(palette)]
                img = Image.new("RGB", size)
                draw = ImageDraw.Draw(img)
                for y in range(size[1]):
                    t = y / size[1]
                    draw.line([(0, y), (size[0], y)],
                              fill=tuple(int(top[c] + (bottom[c] - top[c]) * t) for c in range(3)))
                font = ImageFont.truetype(find_font(), 90)
                label = f"SAMPLE CLIP {i + 1}"
                lw = draw.textlength(label, font=font)
                draw.text(((size[0] - lw) // 2, size[1] * 0.3), label, font=font, fill=(255, 255, 255))
                png = work / f"{i}.png"
                img.save(png)
                frames = int(seconds * FPS)
                run([
                    "ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-i", str(png),
                    "-vf", f"zoompan=z='min(zoom+0.0006,1.15)':d={frames}:s={size[0]}x{size[1]}:fps={FPS}",
                    "-t", f"{seconds:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                    str(folder / f"{str(i + 1).zfill(12)}.mp4"),
                ])
            clips = list_clips(content_id)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return {"content_id": content_id, "count": len(clips), "files": [p.name for p in clips]}


@app.post("/render")
def render(req: RenderRequest):
    content_id = check_id(req.content_id)
    clips = list_clips(content_id)
    if not clips:
        raise HTTPException(404, f"No clips found for {content_id}. Upload clips first.")
    started = time.time()
    work = TMP / f"render-{content_id}-{time.time_ns()}"
    work.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        with _render_lock:
            segments: list[Path] = []
            total = 0.0
            for i, clip in enumerate(clips):
                overlay = work / f"overlay{i}.png"
                caption_overlay(req.texts[i] if i < len(req.texts) else "", overlay)
                seg = work / f"seg{i:02d}.mp4"
                total += normalize_clip(clip, overlay, seg)
                segments.append(seg)
            if (req.brand or req.cta) and req.end_card_seconds > 0:
                card = work / "endcard.png"
                end_card(req.brand, req.cta, req.brand_color, card)
                seg = work / "seg99.mp4"
                still_segment(card, req.end_card_seconds, seg)
                segments.append(seg)
                total += req.end_card_seconds
            concat = work / "concat.txt"
            concat.write_text("".join(f"file '{s.as_posix()}'\n" for s in segments), encoding="utf-8")
            final = OUT / f"{content_id}.mp4"
            run([
                "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
                "-c", "copy", "-movflags", "+faststart", str(final),
            ])
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return {
        "content_id": content_id,
        "file": f"out/{content_id}.mp4",
        "download_path": f"/out/{content_id}.mp4",
        "clips_used": len(clips),
        "captions_used": min(len(clips), len([t for t in req.texts if t.strip()])),
        "duration_s": round(total, 1),
        "size_mb": round(final.stat().st_size / 1024 / 1024, 2),
        "render_seconds": round(time.time() - started, 1),
    }


@app.get("/out/{name}")
def download(name: str):
    if not name.endswith(".mp4"):
        raise HTTPException(404, "Not found")
    content_id = check_id(name[:-4])
    path = OUT / f"{content_id}.mp4"
    if not path.is_file():
        raise HTTPException(404, f"No finished video for {content_id} yet")
    return FileResponse(path, media_type="video/mp4", filename=path.name)
