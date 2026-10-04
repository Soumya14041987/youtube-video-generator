#!/usr/bin/env python3
"""Make reusable presenter shots for thumbnails (the man on the right, empty navy on the left).

Usage: gen_presenter.py <reference_photo_of_presenter> [name ...]
Set 'Presenter Look:' in channel-config.md to describe the person (optional).
Writes assets/presenter/<name>.png at 1280x720. Thumbnail text, banners and icons are drawn by
compose_thumbnails.py so spelling and margins are always exact.
"""
import base64, concurrent.futures as cf, json, os, subprocess, sys, tempfile
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg, data_path, env_key  # noqa: E402

OUT = data_path("assets", "presenter")

LOOK = cfg("Presenter Look", "the same person as in the reference image")
BASE = (f"Using {LOOK}, create a new image. "
        "Place him on the RIGHT side of the frame, filling the right 45 percent of the width, from the top of his head to mid-torso, "
        "with the top of his head about 10 percent below the top edge. The entire LEFT 55 percent of the frame must be a plain, "
        "dark navy background (very dark blue, almost flat, with only very faint circuit lines) and completely empty: no text, no objects, no logos. "
        "Studio lighting, sharp photo, same look as the reference. No text anywhere in the image. ")
SHOTS = {
    "thinking": "Expression: surprised and thinking, eyebrows raised, one hand near his chin. A small glowing lightbulb floats above and to the right of his head.",
    "skeptical": "Expression: skeptical and concerned, one eyebrow raised, lips slightly pressed, looking straight at the viewer. No lightbulb.",
    "finger": "Expression: confident friendly smile, holding up one index finger beside his face. A small glowing lightbulb floats above and to the right of his head.",
    "curious": "Expression: curious and calm, one hand near his chin, looking straight at the viewer. No lightbulb.",
}


def one(key, ref, name):
    cfg = tempfile.NamedTemporaryFile("w", suffix=".cfg", delete=False)
    cfg.write(f'header = "Authorization: Bearer {key}"\n'); cfg.close()
    try:
        r = subprocess.run(["curl", "-s", "--max-time", "300", "-K", cfg.name,
                            "-F", "model=gpt-image-1", "--form-string", f"prompt={BASE}{SHOTS[name]}",
                            "-F", "size=1536x1024", "-F", "quality=high", "-F", f"image=@{ref}",
                            "https://api.openai.com/v1/images/edits"], capture_output=True, text=True)
    finally:
        os.unlink(cfg.name)
    resp = json.loads(r.stdout)
    if "data" not in resp:
        sys.exit(f"{name} failed: " + resp.get("error", {}).get("message", "unknown error"))
    raw = os.path.join(tempfile.gettempdir(), f"presenter_{name}.png")
    open(raw, "wb").write(base64.b64decode(resp["data"][0]["b64_json"]))
    im = Image.open(raw).convert("RGB")
    w, h = im.size
    ch = int(w * 9 / 16)
    top = max(0, (h - ch) // 2 - int(h * 0.02))
    im.crop((0, top, w, top + ch)).resize((1280, 720), Image.LANCZOS).save(os.path.join(OUT, f"{name}.png"), optimize=True)


def main():
    ref = sys.argv[1]
    names = sys.argv[2:] or list(SHOTS)
    os.makedirs(OUT, exist_ok=True)
    key = env_key("OPENAI_API_KEY")
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        for f in [ex.submit(one, key, ref, n) for n in names]:
            f.result()
    print("presenter shots:", ", ".join(names))


if __name__ == "__main__":
    main()
