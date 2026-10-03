# Thumbnails

Every episode gets exactly two thumbnails, so the pick stays easy. All text, banners, icons and the episode tag are drawn by code,
never by an image model, so spelling and edge margins are always right. An image model is used only for the presenter photo, and only if you want one.

## Make two thumbnails (no face, no keys needed)

Create `episodes/<folder>/thumbnail-spec.json`:

```json
{
  "series_number": "1",
  "a": { "shot": "none",
         "lines": [["WHAT IS", 190, "YELLOW"], ["MCP?", 300, "GREEN"]],
         "banner": "2026 UPDATE", "banner_size": 58, "max_w": 590 },
  "b": { "shot": "none",
         "lines": [["MCP", 230, "YELLOW"], ["TUTORIALS", 150, "YELLOW"]],
         "banner": "OUTDATED?", "banner_size": 64, "max_w": 610 }
}
```

Then run:

```bash
python3 tools/dual_host/compose_thumbnails.py episodes/<folder>
```

This writes `thumbnails/thumb-a.png`, `thumbnails/thumb-b.png` and copies option a to `thumbnail-final.png`.

## What goes in a spec

| Key | Meaning |
|---|---|
| `series_number` | The number viewers see, in published order |
| `shot` | `thinking`, `skeptical`, `finger`, `curious` (files in `assets/presenter/`), `photo:<path to a transparent PNG>`, or `none` |
| `lines` | Headline lines as `[text, size, color]`. Colors: YELLOW GREEN WHITE RED BLUE ORANGE |
| `banner`, `banner_size` | The red banner under the headline |
| `max_w` | Widest the headline may be. Keep it left of the face (about 590 to 640) |
| `icons` | Optional row of `[icon, label]`. Icons: wrench folder bulb search memo globe lock gear rocket check |
| `panels` | Optional layout with a title and colored panels: `{"title": [...], "items": [["MODEL", "wrench", "BLUE"]]}` |
| `hero` | Optional big-number layout: `{"left": "64", "right": "1", "size": 270, "banner": "ONE PROTOCOL"}` |

The episode tag at the bottom left uses `Series Badge` from `channel-config.md`. If a shot file is missing, the tool prints a note and uses a face-less background.

## Add a face: three ways

Use only faces you have the right to use.

1. **Your own photo (best for trust).** On macOS 14 or newer, cut yourself out locally:
   `python3 tools/dual_host/cutout.py photo.jpg assets/presenter/real/me.png` (the photo never leaves your computer).
   On Windows or Linux run `pip install rembg` first, or cut the photo out in any editor and save a transparent PNG.
   Then use `"shot": "photo:assets/presenter/real/me.png"`. Photos with direct eye contact, even light and no glasses glare work best.
2. **Generate presenter shots from a reference photo.** `python3 tools/dual_host/gen_presenter.py reference.jpg` makes four shots
   (thinking, skeptical, finger, curious) in `assets/presenter/`. It uses the OpenAI image API, so it costs money. Describe the person in `Presenter Look:` in `channel-config.md`.
3. **Draw your own** four 1280 by 720 PNGs with the person on the right and plain dark navy on the left, and save them in `assets/presenter/`.

## Before you publish

- Look at each thumbnail at the size of YouTube's grid, about 168 by 94 pixels. The headline must still read.
- Keep the headline to about six words. Put the face to the right of the text.
- Upload both options and let YouTube's Test and compare feature choose after a week or two. Do not change many things at once.
