---
name: generate
description: Free creative studio — turns a brief ("/generate 10 ads for a juice, cinematic style, max 10 images") into ad concepts, detailed image prompts, AI images (Pollinations.ai, free, no API key) and vertical 9:16 promo videos (ffmpeg Ken Burns + text). Saves every asset next to the exact prompt used. Use when the user asks to generate images, videos, ads or visual content.
---

# /generate — free image & video studio

Free alternative to paid generation skills (Higgsfield etc.). No account, no API key.

- **Images:** Pollinations.ai (`image.pollinations.ai`, models `flux`, `turbo`, `kontext`…). Free.
- **Videos:** each image is animated locally with ffmpeg (zoom/pan, headline, CTA, fades) into a 1080x1920 MP4.
  Optionally all clips are joined into one reel.

## Workflow

1. **Clarify only what's missing** (max 3 quick questions, otherwise pick sensible defaults):
   product / subject, number of pieces, visual style, tone, format (`9:16` default, `1:1`, `16:9`),
   budget = max number of images to generate (default = number of pieces).
2. **Plan.** Think as a creative director: give each piece a distinct concept (angle, setting,
   lighting, camera, mood). Write a rich English image prompt per piece:
   subject + action, setting, lighting, lens/camera, color grade, style, "no text, no logos"
   (text is added later by the overlay, AI-rendered text looks bad).
   Headline/CTA in the user's language, short (≤ 6 words headline, ≤ 3 words CTA).
3. **Write the plan** to `generated/<slug>/plan.json` (schema below). Respect the budget:
   never more items than the budget allows.
4. **Run** (from the repo root):
   ```bash
   python3 .claude/skills/generate/generate.py generated/<slug>/plan.json            # images + videos
   python3 .claude/skills/generate/generate.py generated/<slug>/plan.json --no-video # images only
   python3 .claude/skills/generate/generate.py generated/<slug>/plan.json --reel     # + one joined reel
   ```
   If Pollinations is unreachable (blocked network), the script stops and says so. Only use
   `--offline` (designed gradient cards instead of AI images) when the user accepts that,
   and say clearly the visuals are not AI-generated.
5. **Report**: list the files, show 1–2 images, and point to `manifest.json` / `prompt.txt`
   so the user can re-run any piece by tweaking its prompt or seed.

## plan.json schema

```json
{
  "title": "Gulpo mango smoothie ads",
  "format": "9:16",
  "model": "flux",
  "style": "cinematic, warm Mediterranean summer, 35mm film grain",
  "brand": {"name": "GULPO", "color": "#FF7A00"},
  "items": [
    {
      "id": "ad01",
      "concept": "Beach bar morning — hand grabs the bottle",
      "image_prompt": "close-up of a hand grabbing a cold orange smoothie bottle ...",
      "headline": "El verano en una botella",
      "cta": "Pruébalo hoy",
      "seed": 101,
      "motion": "zoom-in",
      "duration": 6
    }
  ]
}
```

`motion`: `zoom-in` | `zoom-out` | `pan-left` | `pan-right` | `pan-up`. `style` is appended to every
prompt so the series stays consistent. `seed` makes a piece reproducible; change it for variations.

## Output

```
generated/<slug>/
  plan.json  manifest.json  reel.mp4 (with --reel)
  ad01/ image.jpg  video.mp4  prompt.txt
```
