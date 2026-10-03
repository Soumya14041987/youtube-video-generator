#!/usr/bin/env python3
"""Dual-host episode builder: two hosts (default Alex and Elena) with their own voices.

Usage:
  build_episode.py <episode_dir> [--bible PATH --ep N] [--steps parse,tts,timeline,verify,render]

Inputs : <episode_dir>/visuals/visual-NN.png, and either dualhost.json or --bible/--ep to parse it.
Outputs: dualhost.json, audio/lines/*.wav, voiceover.wav, cue-sheet.json, cue-sheet.md, episode.mp4

Sync rule: every line is spoken by its own TTS call, so real audio length is known exactly. The timeline is
built by adding those real lengths (plus fixed gaps), never estimated. A Whisper pass then double-checks it.

Hosts, series name and the episode length rule come from channel-config.md (see channel-config.md.example).
"""
import argparse, base64, difflib, concurrent.futures as cf, hashlib, json, os, re, subprocess, sys, tempfile, time, wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CODE_ROOT as ROOT, cfg, cfg_float, data_path, env_key, find_font  # noqa: E402

PROVIDER = "openai"
H1, H2 = cfg("Host 1 Name", "Alex"), cfg("Host 2 Name", "Elena")
K1, K2 = H1.lower(), H2.lower()
SERIES = cfg("Series Name", cfg("Channel Name", "this channel"))
_PACE = ("Natural, brisk conversational pace of about 150 words per minute with clear enunciation, like a "
         "confident technical YouTube presenter. Read the text exactly as written, do not add or skip words.")
VOICES = {"openai": {K1: cfg("Host 1 Voice", "ash"), K2: cfg("Host 2 Voice", "coral")},
          "gemini": {K1: cfg("Host 1 Gemini Voice", "Fenrir"), K2: cfg("Host 2 Gemini Voice", "Kore")}}
STYLE = {
    K1: cfg("Host 1 Style", f"Male host {H1}. Warm, confident Indian English accent. " + _PACE),
    K2: cfg("Host 2 Style", f"Female host {H2}. Warm, articulate, neutral English accent. " + _PACE),
}
NAMES = {K1: H1, K2: H2}
TARGET_WPM = 150
TEMPO_LIMITS = (0.80, 1.35)
INTRO = [
    {"speaker": K1, "text": f"Hi everyone, I'm {H1}."},
    {"speaker": K2, "text": f"And I'm {H2}. We are your hosts for the {SERIES} series, and today we will explain one concept at a time."},
]
TURN_GAP, SLIDE_GAP, LEAD_IN, TAIL = 0.35, 0.60, 0.30, 1.5
MIN_SECONDS = int(cfg_float("Episode Min Minutes", 0) * 60)  # 0 means no minimum
MAX_SECONDS = int(cfg_float("Episode Max Minutes", 0) * 60)  # 0 means no maximum
MUSIC_BED = data_path("assets", "music", "bed.mp3")
MUSIC_GAIN = 0.11
THINK_PAUSE = 40  # seconds of countdown with ticking sound while viewers answer the quiz
TTS_MODEL = "gemini-2.5-flash-preview-tts"


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


# ---------------------------------------------------------------- parse
def parse_bible(bible, ep):
    text = open(bible).read()
    m = re.search(rf"^## EP0*{ep}\b.*$", text, re.M)
    if not m:
        sys.exit(f"EP{ep} section not found in bible")
    body = text[m.end():]
    end = re.search(r"^(## EP|### CHATGPT IMAGE PROMPTS)", body, re.M)
    body = body[: end.start()] if end else body
    slides = []
    parts = re.split(r"^#### Slide (\d+): (.+?)(?: \(.*\))?$", body, flags=re.M)
    for i in range(1, len(parts), 3):
        n, title, block = int(parts[i]), parts[i + 1].strip(), parts[i + 2]
        vis = re.search(r"VISUAL:\s*(visual-\d+\.png)", block)
        lines = []
        for sm in re.finditer(rf"^({re.escape(H1)}|{re.escape(H2)})\b[^\n]*:\s*\n\s*\"(.+?)\"\s*$", block, re.M | re.S):
            lines.append({"speaker": sm.group(1).lower(), "text": " ".join(sm.group(2).split())})
        slides.append({"n": n, "title": title, "visual": vis.group(1) if vis else f"visual-{n:02d}.png", "lines": lines})
    return {"episode": ep, "slides": slides}


# ---------------------------------------------------------------- tts
def finish_wav(raw, out_wav, text):
    dur = (os.path.getsize(raw) - 44) / (24000 * 2)
    raw_wpm = len(text.split()) / dur * 60
    tempo = min(max(TARGET_WPM / raw_wpm, TEMPO_LIMITS[0]), TEMPO_LIMITS[1])
    r = run(["ffmpeg", "-y", "-i", raw, "-af", f"atempo={tempo:.3f},loudnorm=I=-18:TP=-2:LRA=9",
             "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", out_wav])
    os.unlink(raw)
    if r.returncode:
        raise RuntimeError(r.stderr[-300:])


def tts_openai(text, speaker, out_wav, key):
    payload = {"model": "gpt-4o-mini-tts", "input": text, "voice": VOICES["openai"][speaker],
               "instructions": STYLE[speaker], "response_format": "wav"}
    pf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(payload, pf); pf.close()
    cfg = tempfile.NamedTemporaryFile("w", suffix=".cfg", delete=False)
    cfg.write(f'header = "Authorization: Bearer {key}"\n'); cfg.close()
    raw = out_wav + ".raw.wav"
    try:
        for attempt in range(6):
            r = run(["curl", "-s", "--max-time", "180", "-K", cfg.name, "-H", "Content-Type: application/json",
                     "-d", f"@{pf.name}", "-o", raw, "-w", "%{http_code}", "https://api.openai.com/v1/audio/speech"])
            if r.stdout.strip() == "200" and os.path.getsize(raw) > 1000:
                break
            err = open(raw, errors="ignore").read()[:200] if os.path.exists(raw) else ""
            if "insufficient_quota" in err:
                raise SystemExit("OpenAI credits exhausted: add credit to the OpenAI account.")
            time.sleep(3 * (attempt + 1))
        else:
            raise RuntimeError(f"OpenAI TTS failed ({r.stdout.strip()}): {text[:40]}")
    finally:
        os.unlink(pf.name); os.unlink(cfg.name)
    finish_wav(raw, out_wav, text)


def tts_gemini(text, speaker, out_wav, key):
    voice = VOICES["gemini"][speaker]
    payload = {"contents": [{"parts": [{"text": text}]}],
               "generationConfig": {"responseModalities": ["AUDIO"],
                                    "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    pf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(payload, pf); pf.close()
    cfg = tempfile.NamedTemporaryFile("w", suffix=".cfg", delete=False)
    cfg.write(f'header = "x-goog-api-key: {key}"\n'); cfg.close()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{TTS_MODEL}:generateContent"
    try:
        for attempt in range(10):
            r = run(["curl", "-s", "--max-time", "240", "-K", cfg.name, "-H", "Content-Type: application/json",
                     "-d", f"@{pf.name}", url])
            try:
                parts = json.loads(r.stdout)["candidates"][0]["content"]["parts"]
                pcm = base64.b64decode(next(p["inlineData"]["data"] for p in parts if "inlineData" in p))
                break
            except Exception:
                if "PerDay" in r.stdout:
                    raise SystemExit("Gemini TTS daily quota exhausted (free tier: 10 requests per day).")
                m = re.search(r"retry in ([\d.]+)s", r.stdout)
                time.sleep(float(m.group(1)) + 3 if m else 8 + 4 * attempt)
        else:
            raise RuntimeError(f"TTS failed after retries: {text[:40]}")
    finally:
        os.unlink(pf.name); os.unlink(cfg.name)
    raw = out_wav + ".raw.wav"
    with wave.open(raw, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
    finish_wav(raw, out_wav, text)


def line_wav(d, n, i, ln):
    sig = str(TARGET_WPM) + PROVIDER + VOICES[PROVIDER][ln["speaker"]] + STYLE[ln["speaker"]] + ln["text"]
    return os.path.join(d, f"s{n:02d}_{i+1}_{ln['speaker']}_{hashlib.md5(sig.encode()).hexdigest()[:8]}.wav")


def step_tts(ep_dir, script):
    key = env_key("OPENAI_API_KEY" if PROVIDER == "openai" else "GEMINI_API_KEY")
    fn = tts_openai if PROVIDER == "openai" else tts_gemini
    d = os.path.join(ep_dir, "audio", "lines"); os.makedirs(d, exist_ok=True)
    jobs = []
    for s in script["slides"]:
        for i, ln in enumerate(s["lines"]):
            ln["wav"] = line_wav(d, s["n"], i, ln)
            if not os.path.exists(ln["wav"]):
                jobs.append(ln)
    print(f"TTS ({PROVIDER}): {len(jobs)} lines to generate", flush=True)
    with cf.ThreadPoolExecutor(max_workers=4 if PROVIDER == "openai" else 1) as ex:
        futs = {ex.submit(fn, ln["text"], ln["speaker"], ln["wav"], key): ln for ln in jobs}
        for f in cf.as_completed(futs):
            f.result(); print("  done", os.path.basename(futs[f]["wav"]), flush=True)


def step_fidelity(ep_dir, script):
    try:
        import whisper
        model = whisper.load_model("base")
    except Exception as e:
        print("fidelity check skipped:", str(e)[:120]); return
    norm = lambda x: re.sub(r"[^\w]", "", x).lower()
    for rnd in range(3):
        bad = []
        for s in script["slides"]:
            for ln in s["lines"]:
                heard = norm(model.transcribe(ln["wav"], verbose=None)["text"])
                ratio = difflib.SequenceMatcher(None, heard, norm(ln["text"])).ratio()
                if ratio < 0.85:
                    bad.append((s["n"], ln["speaker"], round(ratio, 2), ln))
        print(f"fidelity round {rnd + 1}: {len(bad)} line(s) below 85 percent", [b[:3] for b in bad], flush=True)
        if not bad:
            return
        for *_, ln in bad:
            os.unlink(ln["wav"])
        step_tts(ep_dir, script)
    sys.exit("TEXT CHECK FAILED: a line still does not match the script after 3 regenerations")


# ---------------------------------------------------------------- timeline
def wav_frames(path):
    with wave.open(path) as w:
        return w.readframes(w.getnframes()), w.getnframes() / w.getframerate()


def silence(sec):
    return b"\x00\x00" * int(round(sec * 24000))


def mix_ticks(pcm, quiz):
    import array, math
    buf = array.array("h")
    buf.frombytes(bytes(pcm))
    n = quiz["seconds"]
    span = quiz["reveal_at"] - quiz["countdown_start"]
    for i in range(n):
        last_five = i >= n - 5
        freq, amp = (1800, 0.45) if last_five else (1100, 0.28)
        start = int((quiz["countdown_start"] + span * i / n) * 24000)
        for k in range(int(0.06 * 24000)):
            j = start + k
            if j >= len(buf):
                break
            env = math.exp(-k / 24000 / 0.012)
            v = buf[j] + int(amp * 32767 * env * math.sin(2 * math.pi * freq * k / 24000))
            buf[j] = max(-32768, min(32767, v))
    return bytearray(buf.tobytes())


def apply_quiz_defaults(script):
    for sl in script["slides"]:
        if "Exam" in sl["title"] and len(sl["lines"]) >= 2 and "quiz" not in sl:
            sl["quiz"] = {"pause_after_line": 1, "reveal_visual": sl["visual"].replace(".png", "b.png")}


def step_timeline(ep_dir, script):
    pcm, t = bytearray(), 0.0
    lines, quiz = [], None
    for si, s in enumerate(script["slides"]):
        for li, ln in enumerate(s["lines"]):
            data, dur = wav_frames(ln["wav"])
            lines.append({"slide": s["n"], "speaker": ln["speaker"], "start": round(t, 3), "end": round(t + dur, 3),
                          "text": ln["text"]})
            pcm += data; t += dur
            last_in_slide = li == len(s["lines"]) - 1
            last_slide = si == len(script["slides"]) - 1
            gap = 0 if (last_in_slide and last_slide) else (SLIDE_GAP if last_in_slide else TURN_GAP)
            q = s.get("quiz")
            if q and li + 1 == q["pause_after_line"]:
                gap += THINK_PAUSE
                quiz = {"slide": s["n"], "question_visual": s["visual"], "reveal_visual": q["reveal_visual"],
                        "countdown_start": round(t + 0.4, 3), "reveal_at": round(t + gap - LEAD_IN, 3),
                        "seconds": THINK_PAUSE}
            pcm += silence(gap); t += gap
    pcm += silence(TAIL); t += TAIL
    if quiz:
        pcm = mix_ticks(pcm, quiz)
    with wave.open(os.path.join(ep_dir, "voiceover.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(bytes(pcm))
    total = len(pcm) / 2 / 24000
    slides = []
    for s in script["slides"]:
        first = next(l for l in lines if l["slide"] == s["n"])
        slides.append({"n": s["n"], "visual": s["visual"], "start": 0.0 if s["n"] == script["slides"][0]["n"]
                       else round(first["start"] - LEAD_IN, 3)})
    if quiz:
        slides.append({"n": quiz["slide"], "visual": quiz["reveal_visual"], "start": quiz["reveal_at"]})
        slides.sort(key=lambda x: x["start"])
    cue = {"episode": script["episode"], "total_duration": round(total, 3), "method": "per-line TTS lengths",
           "slides": slides, "lines": lines, "quiz": quiz}
    json.dump(cue, open(os.path.join(ep_dir, "cue-sheet.json"), "w"), indent=2)
    md = ["# Cue sheet", "", f"Total {total:.1f}s", "", "| Time | Slide | Speaker | Text |", "|---|---|---|---|"]
    md += [f"| {l['start']:.2f}-{l['end']:.2f} | {l['slide']} | {NAMES[l['speaker']]} | {l['text'][:70]} |" for l in lines]
    open(os.path.join(ep_dir, "cue-sheet.md"), "w").write("\n".join(md) + "\n")
    print(f"timeline: {len(lines)} lines, {total:.1f}s")
    if MAX_SECONDS and total > MAX_SECONDS:
        sys.exit(f"LENGTH CHECK FAILED: {total / 60:.1f} min is over the {MAX_SECONDS / 60:.0f} minute limit. Shorten the script.")
    if MIN_SECONDS and total < MIN_SECONDS:
        print(f"  warning: {total / 60:.1f} min is under the {MIN_SECONDS / 60:.0f} minute target. Add content if you can.")
    return cue


# ---------------------------------------------------------------- verify (Whisper)
def step_verify(ep_dir, cue):
    try:
        import whisper
        model = whisper.load_model("base")
    except Exception as e:
        print("verify skipped:", str(e)[:120]); return
    res = model.transcribe(os.path.join(ep_dir, "voiceover.wav"), word_timestamps=True, verbose=False)
    norm = lambda x: re.sub(r"[^\w]", "", x).lower()
    words = [(norm(w["word"]), w["start"]) for seg in res["segments"] for w in seg.get("words", [])]
    worst = 0.0
    similar = lambda x, y: difflib.SequenceMatcher(None, x, y).ratio() > 0.7
    for l in cue["lines"]:
        probe = [norm(x) for x in l["text"].split()[:4]]
        best = None
        for i in range(len(words) - 3):
            if abs(words[i][1] - l["start"]) >= 5:
                continue
            score = sum(similar(words[i + j][0], probe[j]) for j in range(4))
            key = (-score, abs(words[i][1] - l["start"]))
            if score >= 3 and (best is None or key < best[0]):
                best = (key, words[i][1])
        if best is None:
            print(f"  warn: slide {l['slide']} {l['speaker']} start not matched by Whisper"); continue
        worst = max(worst, abs(best[1] - l["start"]))
    print(f"verify: worst timing drift = {worst:.2f}s")
    if worst > 1.0:
        sys.exit("SYNC CHECK FAILED: drift over 1.0s")


# ---------------------------------------------------------------- render
def make_countdown(ep_dir, cue):
    from PIL import Image, ImageDraw
    q = cue["quiz"]
    fdir = os.path.join(ep_dir, "countdown"); os.makedirs(fdir, exist_ok=True)
    base = Image.open(os.path.join(ep_dir, "visuals", q["question_visual"])).convert("RGB")
    big, small = find_font("bold", 78), find_font("bold", 20)
    n = q["seconds"]
    span = q["reveal_at"] - q["countdown_start"]
    entries = []
    for i in range(n):
        img = base.copy(); d = ImageDraw.Draw(img)
        num = str(n - i)
        d.text((1120 - d.textlength(num, font=big) / 2, 586), num, font=big, fill=(255, 215, 0))
        d.text((1120 - d.textlength("seconds", font=small) / 2, 668), "seconds", font=small, fill=(230, 237, 243))
        path = os.path.join(fdir, f"cd_{i:02d}.png"); img.save(path)
        entries.append({"start": q["countdown_start"] + span * i / n, "path": path})
    return entries


def mix_music(ep_dir):
    """Return the audio file to use: voices with a quiet looped music bed that dips under speech."""
    voice = os.path.join(ep_dir, "voiceover.wav")
    if not os.path.exists(MUSIC_BED):
        return voice
    out = os.path.join(ep_dir, "voiceover_mix.wav")
    graph = (f"[1:a]volume={MUSIC_GAIN},afade=t=in:d=3[bed];"
             "[bed][0:a]sidechaincompress=threshold=0.05:ratio=2:attack=30:release=600[duck];"
             "[0:a][duck]amix=inputs=2:duration=first:normalize=0[a]")
    r = run(["ffmpeg", "-y", "-i", voice, "-stream_loop", "-1", "-i", MUSIC_BED, "-filter_complex", graph,
             "-map", "[a]", "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", out])
    if r.returncode:
        print("music mix failed, using voices only:", r.stderr[-200:])
        return voice
    return out


def step_render(ep_dir, cue, out_name="episode.mp4"):
    fps = 25
    entries = [{"start": x["start"], "path": os.path.join(ep_dir, "visuals", x["visual"])} for x in cue["slides"]]
    if cue.get("quiz"):
        entries += make_countdown(ep_dir, cue)
    entries.sort(key=lambda e: e["start"])
    edges = [round(e["start"] * fps) for e in entries] + [round(cue["total_duration"] * fps)]
    cmd = ["ffmpeg", "-y"]
    chains = []
    for i, e in enumerate(entries):
        cmd += ["-framerate", str(fps), "-loop", "1", "-t", f"{(edges[i + 1] - edges[i]) / fps:.3f}", "-i", e["path"]]
        chains.append(f"[{i}:v]scale=1280:720,setsar=1,format=yuv420p[v{i}]")
    n = len(entries)
    graph = ";".join(chains) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]"
    out = os.path.join(ep_dir, out_name)
    tmp = os.path.join(ep_dir, "episode.tmp.mp4")
    cmd += ["-i", mix_music(ep_dir), "-filter_complex", graph, "-map", "[v]", "-map", f"{n}:a",
            "-r", str(fps), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", tmp]
    r = run(cmd)
    if r.returncode:
        sys.exit(r.stderr[-500:])
    chk = run(["ffmpeg", "-v", "error", "-i", tmp, "-f", "null", "-"])
    if chk.returncode or chk.stderr.strip():
        sys.exit("render check failed, episode.mp4 left untouched: " + chk.stderr[-300:])
    os.replace(tmp, out)
    p = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "csv=p=0", out])
    print("episode.mp4 streams:", p.stdout.replace("\n", " "))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode_dir"); ap.add_argument("--bible"); ap.add_argument("--ep", type=int)
    ap.add_argument("--steps", default="parse,tts,timeline,verify,render")
    ap.add_argument("--tts", default="openai", choices=["openai", "gemini"])
    ap.add_argument("--out", default="episode.mp4")
    a = ap.parse_args()
    global PROVIDER
    PROVIDER = a.tts
    ep_dir, steps = os.path.abspath(a.episode_dir), a.steps.split(",")
    sj = os.path.join(ep_dir, "dualhost.json")
    if "parse" in steps and a.bible:
        json.dump(parse_bible(a.bible, a.ep), open(sj, "w"), indent=2)
    script = json.load(open(sj))
    apply_quiz_defaults(script)
    first = script["slides"][0]["lines"]
    if not first or f"I'm {H1}" not in first[0]["text"]:
        first[0:0] = [dict(x) for x in INTRO]
    for s in script["slides"]:
        if not s["lines"]:
            sys.exit(f"slide {s['n']} has no parsed lines")
    if "tts" in steps:
        step_tts(ep_dir, script)
        step_fidelity(ep_dir, script)
    else:
        for s in script["slides"]:
            for i, ln in enumerate(s["lines"]):
                ln["wav"] = line_wav(os.path.join(ep_dir, "audio", "lines"), s["n"], i, ln)
    cue = step_timeline(ep_dir, script) if "timeline" in steps else json.load(open(os.path.join(ep_dir, "cue-sheet.json")))
    if "verify" in steps:
        step_verify(ep_dir, cue)
    if "render" in steps:
        step_render(ep_dir, cue, a.out)


if __name__ == "__main__":
    main()
