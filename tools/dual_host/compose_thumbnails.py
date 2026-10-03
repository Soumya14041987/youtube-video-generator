#!/usr/bin/env python3
"""Compose episode thumbnails (1280x720) from a small spec file. Text is drawn here, never by an image model,
so spelling and edge margins are always correct.

Usage: compose_thumbnails.py <episode_dir> [<episode_dir> ...]
       compose_thumbnails.py --spec <episode_dir>            (same thing, older spelling)

Reads   <episode_dir>/thumbnail-spec.json
Writes  <episode_dir>/thumbnails/thumb-a.png, thumb-b.png and copies thumb-a.png to <episode_dir>/thumbnail-final.png.
Exactly two options per episode, so the pick stays easy.

Spec (see docs/THUMBNAILS.md):
{
  "series_number": "04",                      shown as the EPISODE tag; use the published number
  "a": { "shot": "thinking",                  presenter shot name from assets/presenter/, or "photo:<cutout.png>", or "none"
         "lines": [["stdio vs", 190, "YELLOW"], ["HTTP", 300, "GREEN"]],
         "banner": "CHANGED IN 2026", "banner_size": 54, "max_w": 590,
         "icons": [["wrench", "Tools"]],      optional emoji row under the banner
         "panels": {"title": [["WHICH ONE?", 130, "YELLOW"]], "items": [["stdio", "memo", "BLUE"]]},   optional panel layout
         "hero": {"left": "64", "right": "1", "size": 270, "banner": "ONE PROTOCOL", "banner_size": 42}   optional big-number layout
       },
  "b": { ... same keys ... }
}
Colors: YELLOW GREEN WHITE RED BLUE ORANGE. If a presenter shot is missing, a face-less navy background is used.
"""
import os, shutil, sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg, data_path, emoji_font, find_font  # noqa: E402

W, H = 1280, 720
YELLOW, GREEN, WHITE, RED, DARK = (255, 213, 0), (46, 204, 64), (255, 255, 255), (200, 16, 30), (6, 10, 22)
BLUE, ORANGE, GREEN_P = (28, 110, 230), (240, 130, 20), (30, 150, 60)
COLORS = {"YELLOW": YELLOW, "GREEN": GREEN, "WHITE": WHITE, "RED": RED, "BLUE": BLUE, "ORANGE": ORANGE}
PANEL_COLORS = {"BLUE": BLUE, "GREEN": GREEN_P, "ORANGE": ORANGE, "RED": RED, "YELLOW": (200, 160, 0)}
EMOJI = {"wrench": "\U0001F527", "folder": "\U0001F4C1", "bulb": "\U0001F4A1", "search": "\U0001F50D", "memo": "\U0001F4DD",
         "globe": "\U0001F310", "lock": "\U0001F512", "gear": "⚙", "rocket": "\U0001F680", "check": "✅"}
LEFT, TOP, BOTTOM = 56, 56, 585  # content must stay inside this box (the badge sits below)
_WARNED = set()


def impact(size):
    return find_font("impact", size)


def black(size):
    return find_font("black", size)


def emoji(name_or_char, size):
    char = EMOJI.get(name_or_char, name_or_char)
    found = emoji_font()
    if found:
        f, native = found
        tile = Image.new("RGBA", (native + 100, native + 100), (0, 0, 0, 0))
        try:
            ImageDraw.Draw(tile).text((10, 10), char, font=f, embedded_color=True)
            box = tile.getbbox()
            if box:
                return tile.crop(box).resize((size, size), Image.LANCZOS)
        except Exception:
            pass
    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(tile).ellipse([size * 0.2, size * 0.2, size * 0.8, size * 0.8], outline=WHITE, width=max(3, size // 12))
    return tile


def text_block(d, x, y, s, font, fill, stroke=9):
    b = d.textbbox((0, 0), s, font=font, stroke_width=stroke)
    d.text((x - b[0], y - b[1]), s, font=font, fill=fill, stroke_width=stroke, stroke_fill=DARK)
    return b[2] - b[0], b[3] - b[1]


def measure(d, s, font, stroke=9):
    b = d.textbbox((0, 0), s, font=font, stroke_width=stroke)
    return b[2] - b[0], b[3] - b[1]


def banner(d, x, y, s, size, bg=RED, fg=WHITE, pad=(26, 12)):
    f = black(size)
    w, h = measure(d, s, f, 0)
    d.rounded_rectangle([x, y, x + w + pad[0] * 2, y + h + pad[1] * 2], radius=14, fill=bg)
    d.text((x + pad[0] - d.textbbox((0, 0), s, font=f)[0], y + pad[1] - d.textbbox((0, 0), s, font=f)[1]), s, font=f, fill=fg)
    return w + pad[0] * 2, h + pad[1] * 2


def badge(d, n):
    """Series tag (from 'Series Badge' in channel-config.md) plus EPISODE NN."""
    series = cfg("Series Badge", "")
    f = black(34)
    t2 = f"EPISODE {n}"
    w2, h2 = measure(d, t2, f, 0)
    y, x2 = 616, LEFT
    if series:
        w1, _ = measure(d, series, f, 0)
        d.rounded_rectangle([LEFT, y, LEFT + w1 + 44, y + h2 + 28], radius=10, fill=RED)
        d.text((LEFT + 22 - d.textbbox((0, 0), series, font=f)[0], y + 14 - d.textbbox((0, 0), series, font=f)[1]), series, font=f, fill=WHITE)
        x2 = LEFT + w1 + 44
    d.rounded_rectangle([x2, y, x2 + w2 + 44, y + h2 + 28], radius=10, fill=(245, 245, 245))
    d.text((x2 + 22 - d.textbbox((0, 0), t2, font=f)[0], y + 14 - d.textbbox((0, 0), t2, font=f)[1]), t2, font=f, fill=DARK)


def stack(d, items, max_w, bottom=BOTTOM):
    """Lay out text lines and a banner top to bottom, shrinking to fit the left zone."""
    scale = 1.0
    for _ in range(40):
        y, rows = TOP, []
        for kind, s, size, color in items:
            sz = int(size * scale)
            if kind == "text":
                w, h = measure(d, s, impact(sz))
            else:
                w, h = measure(d, s, black(sz), 0)
                w, h = w + 52, h + 24
            rows.append((kind, s, sz, color, y, w, h))
            y += h + (22 if kind == "text" else 30)
        if max(r[5] for r in rows) <= max_w and rows[-1][4] + rows[-1][6] <= bottom:
            return rows
        scale *= 0.96
    return rows


def draw_stack(d, rows):
    for kind, s, sz, color, y, w, h in rows:
        if kind == "text":
            text_block(d, LEFT, y, s, impact(sz), color)
        else:
            banner(d, LEFT, y, s, sz)
    return rows[-1][4] + rows[-1][6]


# ---------------------------------------------------------------- backgrounds
def navy_background():
    bg = Image.new("RGB", (W, H), (8, 13, 27))
    glow = Image.new("RGB", (W, H), (8, 13, 27))
    ImageDraw.Draw(glow).ellipse([650, -120, 1450, 700], fill=(22, 52, 112))
    return Image.blend(bg, glow.filter(ImageFilter.GaussianBlur(120)), 0.9)


def photo_base(cutout_path, face_center_x=960, scale=1.15, top=-6):
    """Real photo (transparent PNG cutout) on the navy background with a soft blue halo."""
    cut = Image.open(cutout_path).convert("RGBA")
    rgb = cut.convert("RGB")
    rgb = ImageEnhance.Color(ImageEnhance.Contrast(ImageEnhance.Brightness(rgb).enhance(1.08)).enhance(1.08)).enhance(1.05)
    cut = Image.merge("RGBA", (*rgb.split(), cut.split()[3]))
    cut = cut.resize((int(cut.width * scale), int(cut.height * scale)), Image.LANCZOS)
    sharp = cut.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.6, percent=85, threshold=2))
    cut = Image.merge("RGBA", (*sharp.split(), cut.split()[3]))
    bbox = cut.getbbox()
    face_x = bbox[0] + int((bbox[2] - bbox[0]) * 0.40)
    person = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    person.paste(cut, (face_center_x - face_x, top), cut)
    halo = person.split()[3].filter(ImageFilter.MaxFilter(31)).filter(ImageFilter.GaussianBlur(22))
    base = Image.composite(Image.new("RGB", (W, H), (70, 150, 255)), navy_background(), halo.point(lambda v: int(v * 0.55)))
    base = base.convert("RGBA")
    base.alpha_composite(person)
    return base.convert("RGB")


def base(shot, variant):
    if shot.startswith("photo:"):
        path = shot[6:]
        if not os.path.isabs(path):
            path = data_path(path)
        return photo_base(path, int(variant.get("face_x", 960)))
    if shot and shot != "none":
        p = data_path("assets", "presenter", f"{shot}.png")
        if os.path.exists(p):
            return Image.open(p).convert("RGB").resize((W, H))
        if shot not in _WARNED:
            _WARNED.add(shot)
            print(f"note: presenter shot '{shot}' not found in assets/presenter/, using a face-less background")
    return navy_background()


# ---------------------------------------------------------------- layouts
def icons_row(labels):
    def f(img, d, end):
        x, y = LEFT, end + 22
        lf = black(26)
        for name, label in labels:
            ic = emoji(name, 64)
            img.paste(ic, (x, y), ic)
            lw, _ = measure(d, label, lf, 0)
            d.text((x + 74, y + 18), label, font=lf, fill=WHITE, stroke_width=3, stroke_fill=DARK)
            x += 74 + lw + 36
    return f


def draw_panels(img, d, y, items, pw=190, ph=235, gap=20, icon=96, label_size=60, icon_y=118, label_y=24):
    x = LEFT
    for name, ic_name, color in items:
        d.rounded_rectangle([x, y, x + pw, y + ph], radius=22, fill=PANEL_COLORS.get(color, BLUE), outline=WHITE, width=4)
        f = impact(label_size)
        w, _ = measure(d, name, f, 0)
        d.text((x + (pw - w) / 2, y + label_y), name, font=f, fill=WHITE)
        ic = emoji(ic_name, icon)
        img.paste(ic, (x + (pw - icon) // 2, y + icon_y), ic)
        x += pw + gap


def draw_hero(img, d, hero):
    f = impact(int(hero.get("size", 270)))
    w1, h1 = text_block(d, LEFT, TOP, hero["left"], f, YELLOW)
    s = int(hero.get("size", 270)) / 270.0
    ax, ay = LEFT + w1 + int(22 * s), TOP + h1 // 2
    d.polygon([(ax, ay - 28 * s), (ax + 62 * s, ay - 28 * s), (ax + 62 * s, ay - 60 * s), (ax + 128 * s, ay),
               (ax + 62 * s, ay + 60 * s), (ax + 62 * s, ay + 28 * s), (ax, ay + 28 * s)], fill=GREEN, outline=DARK)
    text_block(d, ax + int(150 * s), TOP, hero["right"], f, GREEN)
    if hero.get("banner"):
        banner(d, LEFT, TOP + h1 + 40, hero["banner"], int(hero.get("banner_size", 42)), RED)


def build_variant(v, n):
    img = base(v.get("shot", "thinking"), v)
    d = ImageDraw.Draw(img)
    if v.get("hero"):
        draw_hero(img, d, v["hero"])
    elif v.get("panels"):
        p = v["panels"]
        items = [("text", t, int(sz), COLORS[c]) for t, sz, c in p["title"]]
        rows = stack(d, items, int(v.get("max_w", 640)), int(v.get("bottom", 330)))
        end = draw_stack(d, rows)
        draw_panels(img, d, end + int(p.get("dy", 14)), p["items"], **{k: p[k] for k in ("pw", "ph", "gap", "icon", "label_size", "icon_y", "label_y") if k in p})
    else:
        items = [("text", t, int(sz), COLORS[c]) for t, sz, c in v["lines"]]
        if v.get("banner"):
            items.append(("banner", v["banner"], int(v.get("banner_size", 54)), RED))
        rows = stack(d, items, int(v.get("max_w", 590)), int(v.get("bottom", BOTTOM)))
        end = draw_stack(d, rows)
        if v.get("icons"):
            icons_row([(a, b) for a, b in v["icons"]])(img, d, end)
        if v.get("outline_banner"):
            for kind, _s, _sz, _c, y, w, h in rows:
                if kind == "banner":
                    d.rounded_rectangle([LEFT, y, LEFT + w, y + h], radius=14, outline=WHITE, width=4)
    badge(d, n)
    return img


def run_spec(ep_dir):
    import json
    spec = json.load(open(os.path.join(ep_dir, "thumbnail-spec.json")))
    n = spec["series_number"]
    out = os.path.join(ep_dir, "thumbnails")
    os.makedirs(out, exist_ok=True)
    for key in ("a", "b"):
        build_variant(spec[key], n).save(os.path.join(out, f"thumb-{key}.png"), optimize=True)
    shutil.copy(os.path.join(out, "thumb-a.png"), os.path.join(ep_dir, "thumbnail-final.png"))
    print(f"{os.path.basename(os.path.abspath(ep_dir))}: two thumbnails written")


def main():
    args = [a for a in sys.argv[1:] if a != "--spec"]
    if not args:
        sys.exit(__doc__)
    for d in args:
        run_spec(os.path.abspath(d))


if __name__ == "__main__":
    main()
