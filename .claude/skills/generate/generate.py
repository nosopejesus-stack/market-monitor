#!/usr/bin/env python3
"""Free image + video generator for the /generate skill.

Images come from Pollinations.ai (free, no API key); videos are built locally
with ffmpeg from each image (zoom/pan, headline, CTA, fades).
"""
import argparse
import json
import random
import shutil
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FORMATS = {"9:16": (1080, 1920), "1:1": (1080, 1080), "16:9": (1920, 1080), "4:5": (1080, 1350)}
POLLINATIONS = "https://image.pollinations.ai/prompt/{prompt}"
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/inter/Inter-Black.otf",
    "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
FPS = 30


def font(size):
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def full_prompt(plan, item):
    style = plan.get("style")
    return f"{item['image_prompt']}, {style}" if style else item["image_prompt"]


def fetch_image(prompt, size, seed, model, dest, retries=3):
    w, h = size
    url = POLLINATIONS.format(prompt=urllib.parse.quote(prompt))
    params = {"width": w, "height": h, "seed": seed, "model": model, "nologo": "true", "enhance": "false"}
    last = None
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=180)
            if r.ok and r.headers.get("content-type", "").startswith("image/"):
                dest.write_bytes(r.content)
                Image.open(dest).convert("RGB").resize(size, Image.LANCZOS).save(dest, quality=95)
                return
            last = f"HTTP {r.status_code}: {r.text[:200]}"
        except requests.RequestException as e:
            last = str(e)
        time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"Pollinations failed: {last}")


def offline_image(item, size, color, dest):
    """Designed gradient card used only with --offline (not AI-generated)."""
    w, h = size
    rnd = random.Random(item.get("seed", 0))
    base = tuple(int(color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        draw.line([(0, y), (w, y)], fill=tuple(int(c * (1 - t) + 20 * t) for c in base))
    for _ in range(6):
        r = rnd.randint(w // 6, w // 2)
        x, y = rnd.randint(0, w), rnd.randint(0, h)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=tuple(min(255, c + 60) for c in base))
    img = img.filter(ImageFilter.GaussianBlur(80))
    img.save(dest, quality=95)


def wrap(draw, text, fnt, max_w):
    lines, line = [], ""
    for word in text.split():
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=fnt) <= max_w:
            line = test
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return [l for l in lines if l]


def overlay(item, size, brand, dest):
    """Transparent PNG with headline, CTA pill and brand name."""
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # bottom shade for legibility
    shade_h = int(h * 0.45)
    for i in range(shade_h):
        a = int(200 * (i / shade_h) ** 1.5)
        draw.line([(0, h - shade_h + i), (w, h - shade_h + i)], fill=(0, 0, 0, a))
    pad = int(w * 0.08)
    hfont = font(int(w * 0.09))
    lines = wrap(draw, item.get("headline", ""), hfont, w - 2 * pad)
    line_h = int(w * 0.105)
    cta = item.get("cta")
    y = h - pad - (int(w * 0.14) if cta else 0) - line_h * len(lines)
    for line in lines:
        draw.text((pad, y), line, font=hfont, fill="white")
        y += line_h
    color = brand.get("color", "#FF7A00")
    if cta:
        cfont = font(int(w * 0.045))
        tw = draw.textlength(cta, font=cfont)
        bh = int(w * 0.09)
        by = h - pad - bh
        draw.rounded_rectangle([pad, by, pad + tw + 2 * int(w * 0.04), by + bh], radius=bh // 2, fill=color)
        draw.text((pad + int(w * 0.04), by + bh / 2), cta, font=cfont, fill="white", anchor="lm")
    if brand.get("name"):
        draw.text((pad, pad), brand["name"], font=font(int(w * 0.05)), fill="white")
    img.save(dest)


def zoompan_expr(motion, frames, size):
    w, h = size
    zoom_in = f"zoom='1+0.25*on/{frames}'"
    center = "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    return {
        "zoom-in": f"{zoom_in}:{center}",
        "zoom-out": f"zoom='1.25-0.25*on/{frames}':{center}",
        "pan-left": f"zoom=1.2:x='(iw-iw/zoom)*(1-on/{frames})':y='ih/2-(ih/zoom/2)'",
        "pan-right": f"zoom=1.2:x='(iw-iw/zoom)*on/{frames}':y='ih/2-(ih/zoom/2)'",
        "pan-up": f"zoom=1.2:x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*(1-on/{frames})'",
    }.get(motion, f"{zoom_in}:{center}")


def make_video(image, over, size, motion, duration, dest):
    w, h = size
    frames = int(duration * FPS)
    fade_out = max(duration - 0.5, 0)
    filt = (
        f"[0:v]scale={w * 2}:{h * 2},zoompan={zoompan_expr(motion, frames, size)}:d={frames}:s={w}x{h}:fps={FPS}[bg];"
        f"[1:v]format=rgba,fade=t=in:st=0.6:d=0.6:alpha=1[ov];"
        f"[bg][ov]overlay=0:0,fade=t=in:st=0:d=0.4,fade=t=out:st={fade_out}:d=0.5,format=yuv420p[v]"
    )
    cmd = [
        # the still image goes in once: zoompan emits d frames per input frame
        "ffmpeg", "-y", "-v", "error", "-i", str(image),
        "-loop", "1", "-framerate", str(FPS), "-i", str(over), "-filter_complex", filt,
        "-map", "[v]", "-t", str(duration), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-r", str(FPS),
        "-movflags", "+faststart", str(dest),
    ]
    subprocess.run(cmd, check=True)


def make_reel(videos, dest):
    listing = dest.with_suffix(".txt")
    listing.write_text("".join(f"file '{v.resolve()}'\n" for v in videos))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-c", "copy", str(dest)], check=True)
    listing.unlink()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("plan", type=Path)
    ap.add_argument("--no-video", action="store_true", help="images only")
    ap.add_argument("--reel", action="store_true", help="also join all clips into reel.mp4")
    ap.add_argument("--offline", action="store_true", help="gradient cards instead of AI images")
    ap.add_argument("--only", help="comma-separated item ids to (re)generate")
    args = ap.parse_args()

    plan = json.loads(args.plan.read_text())
    out = args.plan.parent
    size = FORMATS[plan.get("format", "9:16")]
    model = plan.get("model", "flux")
    brand = plan.get("brand", {})
    only = set(args.only.split(",")) if args.only else None
    if not args.no_video and not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found: install it or use --no-video")

    manifest, videos = [], []
    for item in plan["items"]:
        if only and item["id"] not in only:
            continue
        d = out / item["id"]
        d.mkdir(parents=True, exist_ok=True)
        prompt = full_prompt(plan, item)
        seed = item.setdefault("seed", random.randint(1, 10**6))
        image = d / "image.jpg"
        print(f"[{item['id']}] image ({'offline' if args.offline else model})...", flush=True)
        try:
            if args.offline:
                offline_image(item, size, brand.get("color", "#FF7A00"), image)
            else:
                fetch_image(prompt, size, seed, model, image)
        except RuntimeError as e:
            sys.exit(f"[{item['id']}] {e}\nCheck network access to image.pollinations.ai "
                     "or re-run with --offline for non-AI placeholder visuals.")
        (d / "prompt.txt").write_text(
            f"model: {'offline-gradient' if args.offline else model}\nseed: {seed}\nsize: {size[0]}x{size[1]}\n\n{prompt}\n")
        entry = {"id": item["id"], "concept": item.get("concept"), "prompt": prompt, "seed": seed,
                 "model": "offline-gradient" if args.offline else model, "image": str(image)}
        if not args.no_video:
            print(f"[{item['id']}] video...", flush=True)
            over = d / "overlay.png"
            overlay(item, size, brand, over)
            video = d / "video.mp4"
            make_video(image, over, size, item.get("motion", "zoom-in"), item.get("duration", 6), video)
            over.unlink()
            entry["video"] = str(video)
            videos.append(video)
        manifest.append(entry)

    if args.reel and len(videos) > 1:
        make_reel(videos, out / "reel.mp4")
        print(f"reel: {out / 'reel.mp4'}")
    (out / "manifest.json").write_text(json.dumps(
        {"title": plan.get("title"), "generated_at": datetime.now(timezone.utc).isoformat(),
         "items": manifest}, indent=2, ensure_ascii=False))
    print(f"done: {len(manifest)} item(s) in {out}")


if __name__ == "__main__":
    main()
