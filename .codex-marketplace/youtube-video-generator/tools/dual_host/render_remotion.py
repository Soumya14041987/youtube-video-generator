#!/usr/bin/env python3
"""Render an episode with Remotion (animated scenes made from code) instead of still slide images.

Usage:
  render_remotion.py --setup                 install the Remotion project once (needs Node 18 or newer and internet)
  render_remotion.py <episode_dir>           render <episode_dir>/episode.mp4
  render_remotion.py <episode_dir> --data-only   only write the props file (to preview in Remotion Studio)
Options: --width 1280 --height 720 --fps 30 --crf 20 --concurrency N --out episode.mp4

Reads   <episode_dir>/dualhost.json  (each slide has a "scene" spec, see docs/REMOTION.md)
        <episode_dir>/cue-sheet.json (real audio timing from build_episode.py --steps tts,timeline,verify)
        <episode_dir>/voiceover_mix.wav or voiceover.wav
        channel-config.md            (series badge, follow links)
Writes  <episode_dir>/episode.mp4, plus a still image of every scene in <episode_dir>/visuals/ so Shorts and thumbnails can reuse them.
Scene reveal times come from the real start time of the spoken line each item belongs to, never from word counts.
"""
import argparse, json, math, os, re, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CODE_ROOT, cfg  # noqa: E402

RDIR = os.path.join(CODE_ROOT, "tools", "remotion")
LISTS = ("items", "notes", "nodes", "commands", "hints")


def run(cmd, **kw):
    return subprocess.run(cmd, **kw)


def need_node():
    node, npm = shutil.which("node"), shutil.which("npm")
    if not node or not npm:
        sys.exit("Node.js 18 or newer is needed for Remotion. Install it from nodejs.org, then run: python3 tools/dual_host/render_remotion.py --setup")
    v = subprocess.run([node, "-v"], capture_output=True, text=True).stdout.strip().lstrip("v")
    if int(v.split(".")[0]) < 18:
        sys.exit(f"Node {v} is too old. Remotion needs Node 18 or newer.")


def setup():
    need_node()
    if not os.path.isdir(os.path.join(RDIR, "node_modules")):
        print("installing the Remotion project (one time)...", flush=True)
        r = run(["npm", "install", "--no-audit", "--no-fund"], cwd=RDIR)
        if r.returncode:
            sys.exit("npm install failed. Check your internet connection and Node version.")
    print("checking the headless browser Remotion renders with (downloads it the first time)...", flush=True)
    r = run(["npx", "remotion", "browser", "ensure"], cwd=RDIR)
    if r.returncode:
        sys.exit("Remotion could not get its headless browser. See https://www.remotion.dev/docs/miscellaneous/troubleshooting")
    print("Remotion is ready.")


def handle(url, kind):
    url = (url or "").split()[0] if url else ""
    if not url:
        return None
    path = url.rstrip("/").split("/")[-1]
    if kind == "linkedin":
        return "/in/" + path
    return path if path.startswith("@") else "@" + path


def follow_list():
    out = []
    for label, key, kind in (("LinkedIn", "LinkedIn", "linkedin"), ("Medium", "Medium", "x"), ("X", "X", "x")):
        h = handle(cfg(key), kind)
        if h:
            out.append({"label": label, "handle": h})
    return out


def spread(items, lines, scene_start, default_gap=0.45):
    """Give every item an 'at' time (seconds from the scene start): the start of the spoken line it belongs to."""
    n = len(lines)
    last_line, offset = None, 0.0
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            continue
        if "at" in it:
            continue
        li = it.get("line")
        if li is None:
            li = min(n - 1, int(i * n / max(1, len(items)))) if n else 0
        li = max(0, min(li, n - 1)) if n else 0
        base = (lines[li]["start"] if n else 0.0) + 0.15
        offset = offset + default_gap if li == last_line else 0.0
        last_line = li
        it["at"] = round(base + offset, 3)


def build_props(ep, a):
    script = json.load(open(os.path.join(ep, "dualhost.json")))
    cue = json.load(open(os.path.join(ep, "cue-sheet.json")))
    total = float(cue["total_duration"])
    firsts = {}
    for s in sorted(cue["slides"], key=lambda x: x["start"]):
        firsts.setdefault(s["n"], s["start"])
    ordered = script["slides"]
    scenes = []
    for i, sl in enumerate(ordered):
        start = firsts.get(sl["n"], 0.0)
        end = firsts.get(ordered[i + 1]["n"], total) if i + 1 < len(ordered) else total
        lines = [{"start": round(l["start"] - start, 3), "end": round(l["end"] - start, 3), "speaker": l["speaker"], "text": l["text"]}
                 for l in cue["lines"] if l["slide"] == sl["n"]]
        spec = json.loads(json.dumps(sl.get("scene") or {"type": "bullets", "items": [{"head": sl["title"]}]}))
        for key in LISTS:
            if isinstance(spec.get(key), list):
                field = "text" if spec.get("type") == "takeaways" else "head"
                spec[key] = [{field: x} if isinstance(x, str) else x for x in spec[key]]  # plain strings become items
                spread(spec[key], lines, start)
        if spec.get("type") == "code":
            li = spec.get("codeLine", 0)
            if "codeAt" not in spec and lines:
                spec["codeAt"] = round(lines[min(li, len(lines) - 1)]["start"] + 0.15, 3)
        if spec.get("banner") and "bannerAt" not in spec and lines:
            spec["bannerAt"] = round(lines[-1]["start"] + 0.2, 3)
        scenes.append({"n": sl["n"], "start": round(start, 3), "end": round(end, 3), "title": sl["title"], "lines": lines, "scene": spec})
    series_no = script.get("episode")
    brief = os.path.join(ep, "upload-brief.json")
    if os.path.exists(brief):
        series_no = json.load(open(brief)).get("series_number", series_no)
    badge_name = (cfg("Series Badge") or cfg("Series Name") or "EPISODE").split("#")[0].strip()
    q = cue.get("quiz")
    return {
        "fps": a.fps, "width": a.width, "height": a.height, "totalSeconds": round(total, 3), "audio": "current/audio.wav",
        "badge": f"{badge_name}  |  EPISODE {int(series_no):02d}" if str(series_no).isdigit() else badge_name,
        "follow": follow_list(),
        "quiz": {"countdownStart": q["countdown_start"], "revealAt": q["reveal_at"], "seconds": q["seconds"]} if q else None,
        "scenes": scenes,
    }, cue


def stills(ep, props, out_mp4):
    """One picture per scene, taken near the end of the scene when everything has appeared. Shorts and thumbnails reuse them."""
    vdir = os.path.join(ep, "visuals"); os.makedirs(vdir, exist_ok=True)
    q = props["quiz"]
    for sc in props["scenes"]:
        t = max(sc["start"], sc["end"] - 0.8)
        if sc["scene"].get("type") == "quiz" and q:
            shots = [(f"scene-{sc['n']:02d}.png", q["countdownStart"] - 0.5), (f"scene-{sc['n']:02d}b.png", min(sc["end"] - 0.3, q["revealAt"] + 1.5))]
        else:
            shots = [(f"scene-{sc['n']:02d}.png", t)]
        for name, ts in shots:
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{max(0, ts):.3f}", "-i", out_mp4, "-frames:v", "1",
                            "-vf", "scale=1280:720", os.path.join(vdir, name)], capture_output=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("episode_dir", nargs="?")
    ap.add_argument("--setup", action="store_true")
    ap.add_argument("--data-only", action="store_true")
    ap.add_argument("--width", type=int, default=1280); ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--fps", type=int, default=30); ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--concurrency", type=int, default=0)
    ap.add_argument("--out", default="episode.mp4")
    a = ap.parse_args()
    if a.setup:
        setup(); return
    if not a.episode_dir:
        sys.exit("give an episode folder, or use --setup")
    ep = os.path.abspath(a.episode_dir)
    for f in ("dualhost.json", "cue-sheet.json"):
        if not os.path.exists(os.path.join(ep, f)):
            sys.exit(f"{f} not found in {ep}. Run build_episode.py --steps tts,timeline,verify first.")
    props, cue = build_props(ep, a)
    audio = os.path.join(ep, "voiceover_mix.wav")
    if not os.path.exists(audio):
        audio = os.path.join(ep, "voiceover.wav")
    pub = os.path.join(RDIR, "public", "current"); os.makedirs(pub, exist_ok=True)
    shutil.copy2(audio, os.path.join(pub, "audio.wav"))
    os.makedirs(os.path.join(RDIR, "out"), exist_ok=True)
    pj = os.path.join(RDIR, "out", "props.json")
    json.dump(props, open(pj, "w"), indent=2)
    print(f"props written: {len(props['scenes'])} scenes, {props['totalSeconds']:.1f}s")
    if a.data_only:
        print("preview with: cd tools/remotion && npx remotion studio src/index.ts --props=out/props.json"); return
    need_node()
    if not os.path.isdir(os.path.join(RDIR, "node_modules")):
        setup()
    tmp = os.path.join(ep, "episode.remotion.tmp.mp4"); out = os.path.join(ep, a.out)
    cmd = ["npx", "remotion", "render", "src/index.ts", "Episode", tmp, f"--props={pj}", f"--crf={a.crf}", "--codec=h264", "--audio-codec=aac"]
    if a.concurrency:
        cmd.append(f"--concurrency={a.concurrency}")
    print("rendering (this can take several minutes)...", flush=True)
    r = run(cmd, cwd=RDIR)
    if r.returncode or not os.path.exists(tmp):
        sys.exit("Remotion render failed. Run python3 tools/dual_host/render_remotion.py --setup, then try again.")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", tmp],
                               capture_output=True, text=True).stdout.strip() or 0)
    if abs(dur - props["totalSeconds"]) > 0.6:
        sys.exit(f"rendered length {dur:.1f}s does not match the audio {props['totalSeconds']:.1f}s. Not replacing {a.out}.")
    os.replace(tmp, out)
    stills(ep, props, out)
    print(f"wrote {out} ({dur:.1f}s) and a still of every scene in visuals/")


if __name__ == "__main__":
    main()
