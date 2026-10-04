#!/usr/bin/env python3
"""Cut vertical YouTube Shorts (1080x1920) from a finished two-host episode.

Usage:
  make_short.py <episode_dir> --list                       show every spoken line with its number and time
  make_short.py <episode_dir> --suggest [N]                suggest N good clips (default 3) with a reason for each
  make_short.py <episode_dir> --lines 4-9 --hook "Why your AI forgets everything"
  make_short.py <episode_dir> --auto 3                     build the 3 best suggested clips
Options: --title TEXT  --cta TEXT  --name short-01  --min 25 --max 55  --no-captions

Reads    cue-sheet.json (real line times), voiceover_mix.wav or voiceover.wav, visuals/*.png, channel-config.md
Writes   <episode_dir>/shorts/<name>.mp4 and <name>.md (title, description, hashtags, pinned comment, checks)

How it stays in sync: the clip audio is cut at the real line boundaries from the cue sheet. Word by word captions use
Whisper word times on the clip itself, matched to the script's own spelling. Nothing is timed from word counts alone,
except a word Whisper missed, which is placed between its neighbours inside the same line.
Exit code 1 if a check fails.
"""
import argparse, difflib, json, os, re, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg, find_font, load_config  # noqa: E402

W, H, FPS = 1080, 1920, 25
TAIL = 1.6                                   # silence after the last line so the closing text can be read
PAD_START, PAD_END = 0.10, 0.45
CAP_Y, CAP_H = 1030, 440                     # caption band; Shorts buttons and title cover the bottom 280 px
SLIDE_Y, HOOK_Y, CTA_Y = 410, 130, 1500
HOOK_SECONDS, CTA_SECONDS = 2.8, 2.0
GOOD_WORDS = ("nobody", "never", "mistake", "wrong", "secret", "why", "how", "stop", "skip", "changed", "real", "simple", "most", "only")
YELLOW, WHITE, NAVY = (255, 214, 10), (255, 255, 255), (8, 14, 30)


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def mmss(sec):
    t = int(round(sec))
    return f"{t // 60}:{t % 60:02d}"


def norm(x):
    return re.sub(r"[^\w]", "", x).lower()


# ---------------------------------------------------------------- choosing clips
def load_cue(ep_dir):
    p = os.path.join(ep_dir, "cue-sheet.json")
    if not os.path.exists(p):
        sys.exit(f"{p} not found. Build the episode first (build_episode.py).")
    return json.load(open(p))


def is_intro(line):
    return bool(re.match(r"(hi everyone, i'm|and i'm)", line["text"].strip(), re.I))


def blocked_slides(cue):
    """Slides a Short must not cut into: the quiz (needs the countdown) and the final end screen."""
    bad = set()
    if cue.get("quiz"):
        bad.add(cue["quiz"]["slide"])
    bad.add(max(l["slide"] for l in cue["lines"]))
    return bad


def span(cue, a, b):
    return cue["lines"][b]["end"] - cue["lines"][a]["start"]


def candidates(cue, lo, hi):
    lines, bad, out = cue["lines"], blocked_slides(cue), []
    for a in range(len(lines)):
        if is_intro(lines[a]) or lines[a]["slide"] in bad:
            continue
        for b in range(a + 1, len(lines)):
            if lines[b]["slide"] in bad:
                break
            d = span(cue, a, b)
            if d > hi:
                break
            if d >= lo and lines[b]["text"].rstrip().endswith((".", "?", "!")):
                first = lines[a]["text"].lower()
                reasons, score = [], 0.0
                if "?" in lines[a]["text"]:
                    score += 3; reasons.append("opens with a question")
                hits = [w for w in GOOD_WORDS if re.search(rf"\b{w}\b", first)]
                if hits:
                    score += min(len(hits), 3); reasons.append("hook words: " + ", ".join(hits[:3]))
                if re.search(r"\d", first):
                    score += 1; reasons.append("has a number")
                if a == 0 or lines[a]["slide"] != lines[a - 1]["slide"]:
                    score += 1; reasons.append("starts a new slide")
                if lines[b]["speaker"] != lines[a]["speaker"]:
                    score += 0.5
                if re.match(r"(welcome|let's recap|next up|if you enjoyed|before we)", first):
                    score -= 2; reasons.append("opening is a greeting, so a weak hook")
                score -= abs(d - 38) / 20
                out.append((score, a, b, d, reasons))
                break
    return out


def suggest(cue, n, lo, hi):
    picked, used = [], []
    for score, a, b, d, why in sorted(candidates(cue, lo, hi), reverse=True):
        if any(not (b < x or a > y) for x, y in used):
            continue
        picked.append({"a": a, "b": b, "seconds": round(d, 1), "score": round(score, 2), "why": why or ["steady explanation"]})
        used.append((a, b))
        if len(picked) == n:
            break
    return picked


# ---------------------------------------------------------------- captions
def align_words(clip_wav, lines, t0):
    """[(word, start, end)] per line, times relative to the clip. Whisper times matched to the script spelling."""
    words = []
    for l in lines:
        for w in l["text"].split():
            words.append([w, None, None, l])
    heard = []
    try:
        import whisper
        res = whisper.load_model("base").transcribe(clip_wav, word_timestamps=True, verbose=False)
        heard = [(norm(w["word"]), w["start"], w["end"]) for s in res["segments"] for w in s.get("words", []) if norm(w["word"])]
    except Exception as e:  # noqa: BLE001
        print("  note: Whisper not available, captions timed inside each real line only:", str(e)[:80])
    script = [norm(w[0]) for w in words]
    sm = difflib.SequenceMatcher(None, script, [h[0] for h in heard], autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                words[i1 + k][1], words[i1 + k][2] = heard[j1 + k][1], heard[j1 + k][2]
    # words Whisper missed: spread evenly between the nearest timed neighbours inside the same line
    for idx, l in enumerate(lines):
        mine = [w for w in words if w[3] is l]
        ls, le = l["start"] - t0, l["end"] - t0
        for k, w in enumerate(mine):
            if w[1] is not None:
                continue
            prev = next((mine[j][2] for j in range(k - 1, -1, -1) if mine[j][2] is not None), ls)
            nxt_i = next((j for j in range(k + 1, len(mine)) if mine[j][1] is not None), None)
            nxt = mine[nxt_i][1] if nxt_i is not None else le
            gap_words = [j for j in range(k, nxt_i if nxt_i is not None else len(mine)) if mine[j][1] is None]
            step = (nxt - prev) / (len(gap_words) + 0.0001)
            pos = gap_words.index(k)
            w[1], w[2] = prev + step * pos, prev + step * (pos + 1)
    for w in words:  # keep every word inside its own line
        ls, le = w[3]["start"] - t0, w[3]["end"] - t0
        w[1] = min(max(w[1], ls), le); w[2] = min(max(w[2], w[1] + 0.05), le + 0.3)
    return [(w[0], w[1], w[2]) for w in words]


def chunks(words, per=3):
    """Group words into short caption chunks, breaking at punctuation."""
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        if len(cur) >= per or w[0].endswith((".", "?", "!", ",", ";", ":")):
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


def text_with_outline(d, xy, text, font, fill, stroke=9):
    d.text(xy, text, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))


def draw_caption(words, group, active, font):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (W, CAP_H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    texts = [words[i][0].upper() for i in group]
    space = d.textlength(" ", font=font)
    widths = [d.textlength(t, font=font) for t in texts]
    total = sum(widths) + space * (len(texts) - 1)
    if total > W - 140:  # long words: put them on two lines
        rows = [list(range(0, (len(texts) + 1) // 2)), list(range((len(texts) + 1) // 2, len(texts)))]
    else:
        rows = [list(range(len(texts)))]
    y = (CAP_H - len(rows) * 110) // 2
    for row in rows:
        rw = sum(widths[k] for k in row) + space * (len(row) - 1)
        x = (W - rw) / 2
        for k in row:
            text_with_outline(d, (x, y), texts[k], font, YELLOW if group[k] == active else WHITE)
            x += widths[k] + space
        y += 110
    return img


def draw_banner(text, size, fill, bg, w=W - 120):
    """A rounded box with wrapped, centred text. Returns an RGBA image."""
    from PIL import Image, ImageDraw
    font = find_font("impact", size)
    d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    rows, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if d0.textlength(t, font=font) > w - 80 and cur:
            rows.append(cur); cur = word
        else:
            cur = t
    rows.append(cur)
    lh = int(size * 1.15)
    img = Image.new("RGBA", (w, lh * len(rows) + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, img.height - 1), 34, fill=bg)
    for i, r in enumerate(rows):
        d.text(((w - d.textlength(r, font=font)) / 2, 28 + i * lh), r, font=font, fill=fill)
    return img


def make_backdrop(src, out):
    """1080x1920 frame: blurred, darkened copy of the slide behind a sharp slide in the upper middle."""
    from PIL import Image, ImageFilter, ImageEnhance
    im = Image.open(src).convert("RGB")
    bg = im.resize((int(H * im.width / im.height), H)).crop((0, 0, W, H)) if im.width / im.height > W / H else im.resize((W, int(W * im.height / im.width)))
    bx, by = (bg.width - W) // 2, (bg.height - H) // 2
    bg = bg.crop((bx, by, bx + W, by + H)).filter(ImageFilter.GaussianBlur(38))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    fw = W - 40
    fg = im.resize((fw, int(fw * im.height / im.width)))
    bg.paste(fg, (20, SLIDE_Y))
    bg.save(out)


# ---------------------------------------------------------------- build
def build_short(ep_dir, cue, a, b, name, hook, title, cta, captions):
    from PIL import Image
    lines = cue["lines"][a:b + 1]
    t0 = max(0.0, lines[0]["start"] - PAD_START)
    t1 = lines[-1]["end"] + PAD_END
    speech = t1 - t0
    total = speech + TAIL
    out_dir = os.path.join(ep_dir, "shorts"); work = os.path.join(out_dir, f".{name}-work")
    shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
    src_audio = os.path.join(ep_dir, "voiceover_mix.wav")
    if not os.path.exists(src_audio):
        src_audio = os.path.join(ep_dir, "voiceover.wav")
    clip = os.path.join(work, "clip.wav")
    r = run(["ffmpeg", "-y", "-ss", f"{t0:.3f}", "-t", f"{speech:.3f}", "-i", src_audio, "-af", f"apad=pad_dur={TAIL}",
             "-ar", "24000", "-ac", "1", clip])
    if r.returncode:
        sys.exit("audio cut failed: " + r.stderr[-300:])
    voice_only = os.path.join(ep_dir, "voiceover.wav")
    align_src = clip
    if src_audio != voice_only:  # align on voices only, without the music bed
        align_src = os.path.join(work, "voice.wav")
        run(["ffmpeg", "-y", "-ss", f"{t0:.3f}", "-t", f"{speech:.3f}", "-i", voice_only, "-ar", "16000", "-ac", "1", align_src])

    # base video: one backdrop per slide shown in the window
    slides = sorted(cue["slides"], key=lambda s: s["start"])
    segs = []
    for i, s in enumerate(slides):
        s_end = slides[i + 1]["start"] if i + 1 < len(slides) else cue["total_duration"]
        if s_end <= t0 or s["start"] >= lines[-1]["end"] - 0.05:  # a slide that starts after the last spoken line is not shown
            continue
        segs.append((max(s["start"], t0) - t0, s["visual"]))
    segs[0] = (0.0, segs[0][1])
    cmd = ["ffmpeg", "-y"]
    chains = []
    frames = round(total * FPS)
    edges = [round(s[0] * FPS) for s in segs] + [frames]
    for i, (st, vis) in enumerate(segs):
        back = os.path.join(work, f"back{i}.png")
        make_backdrop(os.path.join(ep_dir, "visuals", vis), back)
        n = max(edges[i + 1] - edges[i], 1)
        cmd += ["-i", back]
        chains.append(f"[{i}:v]scale=2160:3840,zoompan=z='1+0.05*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},setsar=1,format=yuv420p[s{i}]")
    k = len(segs)
    graph = ";".join(chains) + ";" + "".join(f"[s{i}]" for i in range(k)) + f"concat=n={k}:v=1:a=0[base]"
    idx = k

    # hook, captions, closing text
    overlays = []
    if hook:
        hp = os.path.join(work, "hook.png"); draw_banner(hook.upper(), 80, WHITE, (200, 20, 40, 235)).save(hp)
        cmd += ["-i", hp]; overlays.append((idx, 60, HOOK_Y, f"between(t,0,{HOOK_SECONDS})")); idx += 1
    if cta:
        cp = os.path.join(work, "cta.png"); draw_banner(cta, 66, NAVY, (255, 214, 10, 240)).save(cp)
        cmd += ["-i", cp]; overlays.append((idx, 60, CTA_Y, f"gte(t,{total - CTA_SECONDS - 0.1:.3f})")); idx += 1
    cap_idx = None
    if captions:
        words = align_words(align_src, lines, t0)
        font = find_font("impact", 104)
        states, last_end = [], 0.0
        for g in chunks(words):
            for j, wi in enumerate(g):
                st = words[wi][1]
                nxt = words[wi + 1][1] if wi + 1 < len(words) else None
                # hold the caption through short pauses so it does not flicker; clear it after a long silence
                en = nxt if nxt is not None and nxt - words[wi][2] < 0.7 else words[wi][2] + 0.25
                if st > last_end + 0.02:
                    states.append((None, st - last_end))
                path = os.path.join(work, f"cap{len(states):03d}.png")
                draw_caption(words, g, wi, font).save(path)
                states.append((path, max(en - st, 0.04))); last_end = st + max(en - st, 0.04)
        if last_end < total:
            states.append((None, total - last_end))
        blank = os.path.join(work, "blank.png"); Image.new("RGBA", (W, CAP_H), (0, 0, 0, 0)).save(blank)
        lst = os.path.join(work, "caps.txt")
        with open(lst, "w") as f:
            for p, d in states:
                f.write(f"file '{(p or blank).replace(chr(39), '')}'\nduration {d:.3f}\n")
            f.write(f"file '{blank}'\n")
        cmd += ["-f", "concat", "-safe", "0", "-i", lst]; cap_idx = idx; idx += 1
    cur = "base"
    for n_, (i, x, y, en) in enumerate(overlays):
        graph += f";[{cur}][{i}:v]overlay={x}:{y}:enable='{en}'[o{n_}]"; cur = f"o{n_}"
    if cap_idx is not None:
        graph += f";[{cap_idx}:v]fps={FPS},format=rgba[caps];[{cur}][caps]overlay=0:{CAP_Y}:shortest=0[oc]"; cur = "oc"
    cmd += ["-i", clip]
    out = os.path.join(out_dir, f"{name}.mp4"); tmp = os.path.join(out_dir, f".{name}.tmp.mp4")
    cmd += ["-filter_complex", graph, "-map", f"[{cur}]", "-map", f"{idx}:a", "-t", f"{total:.3f}", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart", tmp]
    r = run(cmd)
    if r.returncode:
        sys.exit("render failed:\n" + r.stderr[-1500:])
    os.replace(tmp, out)
    shutil.rmtree(work, ignore_errors=True)
    return out, total, lines


# ---------------------------------------------------------------- text and checks
def subscribe_link():
    c = load_config()
    s = (c.get("subscribe link") or "").split()
    if s:
        return s[0]
    return f"https://www.youtube.com/channel/{c['channel id']}?sub_confirmation=1" if c.get("channel id") else None


def write_notes(ep_dir, out, name, title, hook, lines, total, a, b):
    sub, banned = subscribe_link(), [x.strip().lower() for x in (cfg("Banned Links", "") or "").split(",") if x.strip()]
    series = cfg("Series Name", cfg("Channel Name", ""))
    follow = cfg("Follow Name", "")
    tags = ["#Shorts"] + ([f"#{re.sub(r'[^A-Za-z0-9]', '', series)}"] if series else []) + ["#AI", "#LearnAI"]
    first = re.split(r"(?<=[.?!])\s", lines[0]["text"].strip())[0]
    desc = [first, "", "Full episode on the channel (paste the full video link here after you upload it).",
            *( [f"Subscribe: {sub}"] if sub else [] ), "", " ".join(tags)]
    pinned = "Want the whole explanation? The full episode is on the channel. What should we explain next?"
    checks = []
    def chk(ok, text, level="FAIL"):
        checks.append(("PASS" if ok else level, text)); return ok
    probe = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,codec_name",
                 "-of", "csv=p=0", out]).stdout.strip()
    aud = run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "csv=p=0", out]).stdout.strip()
    dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out]).stdout.strip() or 0)
    chk(probe.startswith("h264,1080,1920"), f"video is 1080 by 1920 h264 ({probe})")
    chk(aud == "aac", f"audio is aac ({aud})")
    chk(dur <= 59.0, f"length {dur:.1f}s is under 60 seconds")
    chk(dur >= 15.0, f"length {dur:.1f}s is at least 15 seconds", "WARN")
    chk(bool(hook), "an on-screen hook is set (shown for the first 2.8 seconds)", "WARN")
    chk(len(title) <= 100, f"title is {len(title)} characters (limit 100)")
    chk("#shorts" in title.lower() or "#Shorts" in " ".join(desc), "#Shorts is in the description")
    chk(not any(x in (title + " ".join(desc)).lower() for x in banned), "no banned link or word")
    chk(bool(sub), "subscribe link found in channel-config.md", "WARN")
    body = [f"# {name}", "", f"Clip: lines {a} to {b} of the cue sheet, {mmss(lines[0]['start'])} to {mmss(lines[-1]['end'])} in the full episode. Length {dur:.1f}s.",
            "", "## Title", title, "", "## Description", *desc, "", "## Pinned comment", pinned, "",
            "## On-screen hook", hook or "(none)", "", "## Upload steps",
            "1. YouTube Studio, Create, Upload. Choose this file. Vertical and under 60 seconds makes it a Short.",
            "2. Paste the title and description. Replace the full-video line with the real link (or add it as a Related video in Studio).",
            "3. Pick the frame for the cover in Studio. Custom Short thumbnails may only be available in the YouTube mobile app; check Studio.",
            "4. Post the pinned comment after it is live, and reply to early comments within the first hour.",
            "5. After 48 hours compare viewed vs swiped away. Keep the hooks that held viewers, change the ones that lost them.", "",
            "## Checks", *[f"- {l}: {t}" for l, t in checks], ""]
    open(os.path.join(ep_dir, "shorts", f"{name}.md"), "w").write("\n".join(body))
    return checks, dur


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("episode_dir")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--suggest", nargs="?", const=3, type=int)
    ap.add_argument("--auto", type=int)
    ap.add_argument("--lines", help="first and last line number, for example 4-9")
    ap.add_argument("--hook"); ap.add_argument("--title"); ap.add_argument("--cta"); ap.add_argument("--name")
    ap.add_argument("--min", type=float, default=25); ap.add_argument("--max", type=float, default=55)
    ap.add_argument("--no-captions", action="store_true")
    a = ap.parse_args()
    ep = os.path.abspath(a.episode_dir)
    cue = load_cue(ep)
    if a.list:
        for i, l in enumerate(cue["lines"]):
            print(f"{i:3d}  {mmss(l['start'])}  slide {l['slide']:2d}  {l['speaker']:6} {l['text'][:90]}")
        return
    if a.suggest is not None:
        picks = suggest(cue, a.suggest, a.min, a.max)
        if not picks:
            sys.exit("no clip fits. Try --min 15 or --max 58.")
        for p in picks:
            print(f"lines {p['a']}-{p['b']}  {p['seconds']}s  score {p['score']}  {'; '.join(p['why'])}")
            print(f"    starts: {cue['lines'][p['a']]['text'][:100]}")
        print("These are suggestions from simple rules. Read them and choose; set --hook yourself.")
        return
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found. See docs/TROUBLESHOOTING.md")
    jobs = []
    if a.lines:
        m = re.fullmatch(r"(\d+)-(\d+)", a.lines.strip())
        if not m or int(m.group(1)) > int(m.group(2)) or int(m.group(2)) >= len(cue["lines"]):
            sys.exit(f"--lines must look like 4-9 and stay between 0 and {len(cue['lines']) - 1}. Run --list to see the numbers.")
        jobs.append((int(m.group(1)), int(m.group(2)), a.hook))
    elif a.auto:
        jobs = [(p["a"], p["b"], a.hook) for p in suggest(cue, a.auto, a.min, a.max)]
    else:
        sys.exit("choose one of --list, --suggest, --auto N or --lines A-B")
    bad = blocked_slides(cue)
    follow = cfg("Follow Name", "")
    os.makedirs(os.path.join(ep, "shorts"), exist_ok=True)
    existing = len([f for f in os.listdir(os.path.join(ep, "shorts")) if f.endswith(".mp4")])
    failed = False
    for n, (x, y, hook) in enumerate(jobs, 1):
        if any(cue["lines"][i]["slide"] in bad for i in range(x, y + 1)):
            sys.exit(f"lines {x}-{y} include the quiz or the end screen slide. Choose lines before them.")
        name = a.name or f"short-{existing + n:02d}"
        sentences = re.split(r"(?<=[.?!])\s+", cue["lines"][x]["text"].strip())
        hook = hook or next((t for t in sentences if t.endswith("?") and len(t) <= 70), None)
        base = hook or sentences[0]
        if len(base) > 85:
            base = base[:85].rsplit(" ", 1)[0]
        title = a.title or (base.rstrip(" ?.!,:;") + " #Shorts")
        cta = a.cta if a.cta is not None else (f"Follow {follow} for more" if follow else "Follow for more")
        print(f"building {name}: lines {x}-{y}", flush=True)
        out, total, lines = build_short(ep, cue, x, y, name, hook, title, cta, not a.no_captions)
        checks, dur = write_notes(ep, out, name, title, hook, lines, total, x, y)
        for lvl, t in checks:
            print(f"  {lvl}: {t}")
        failed |= any(l == "FAIL" for l, _ in checks)
        print(f"  wrote {os.path.relpath(out)} ({dur:.1f}s)")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
