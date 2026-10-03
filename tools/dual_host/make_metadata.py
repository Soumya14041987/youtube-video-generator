#!/usr/bin/env python3
"""Build and check everything needed to upload an episode to YouTube.

Usage: make_metadata.py <episode_dir>

Reads   <episode_dir>/upload-brief.json   (episode-specific words written by the author or the model)
        <episode_dir>/cue-sheet.json      (real chapter times)
        <episode_dir>/dualhost.json       (slide titles, for chapter names when the brief gives none)
        channel-config.md                 (follow links, subscribe link, slot)
Writes  <episode_dir>/metadata.md         (title, description, tags, pinned comment, settings, plan)
        <episode_dir>/upload-check.md     (PASS / WARN / FAIL report)
Exit code 1 if any FAIL, so the pipeline cannot call an episode "ready" with a broken upload package.
"""
import json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg as config_value, cfg_float, load_config  # noqa: E402

SERIES = config_value("Series Name", config_value("Channel Name", "this channel"))
FOLLOW_NAME = config_value("Follow Name", (config_value("Presenter", "the creator") or "the creator").split()[0])
BANNED_LINKS = [x.strip() for x in config_value("Banned Links", "").split(",") if x.strip()]
SOCIAL_ORDER = [("LinkedIn", "LinkedIn"), ("Medium", "Medium"), ("X", "X"), ("GitHub", "GitHub"), ("Instagram", "Instagram"),
                ("Website", "Website"), ("AWS Builder Center", "AWS Builder Center")]
SENTENCE_SOCIAL = ("LinkedIn", "Medium", "X", "GitHub", "Instagram")
LIMITS = {"title": 100, "title_good": 70, "description": 5000, "tags_total": 500, "tag": 30, "hashtags": 15}


def read_config():
    """Follow links and subscribe link from channel-config.md (see channel-config.md.example)."""
    c = load_config()
    out = {}
    for label, _ in SOCIAL_ORDER:
        v = c.get(label.lower())
        if v and v.startswith("http"):
            out[label] = v.split()[0]
    sub = (c.get("subscribe link") or "").split()[0] if c.get("subscribe link") else None
    if not sub and c.get("channel id"):
        sub = f"https://www.youtube.com/channel/{c['channel id']}?sub_confirmation=1"
    if not sub:
        sys.exit("channel-config.md needs 'Subscribe link:' (or 'Channel ID:'). Copy channel-config.md.example and fill it in.")
    out["Subscribe link"] = sub
    if not [k for k in out if k != "Subscribe link"]:
        print("warning: channel-config.md has no follow links (LinkedIn, Medium, X ...); the follow block will be empty")
    return out


def mmss(sec):
    t = int(round(sec))
    return f"{t // 60}:{t % 60:02d}"


def chapters(ep, brief):
    cue = json.load(open(os.path.join(ep, "cue-sheet.json")))
    starts = sorted({round(s["start"], 2) for s in cue["slides"]})
    names = brief.get("chapter_titles")
    if not names:
        script = json.load(open(os.path.join(ep, "dualhost.json")))
        titles = {s["n"]: s["title"] for s in script["slides"]}
        names = []
        for sl in sorted(cue["slides"], key=lambda x: x["start"]):
            names.append(titles.get(sl["n"], f"Part {sl['n']}"))
    return list(zip(starts, names)), cue


def build(ep, brief, cfg):
    chs, cue = chapters(ep, brief)
    quiz = cue.get("quiz")
    reveal = mmss(quiz["reveal_at"]) if quiz else None
    quiz_start = mmss(min(s["start"] for s in cue["slides"] if s["n"] == quiz["slide"])) if quiz else None
    ch_lines = "\n".join(f"{mmss(t)} {n}" for t, n in chs)
    learn = "\n".join(f"- {x}" for x in brief["learn"])
    sources = "\n".join(brief.get("sources", []))
    follow = "\n".join(f"{k}: {cfg[k]}" for k, _ in SOCIAL_ORDER if k in cfg and k not in ("GitHub", "Instagram", "Website"))
    names = [k for k in SENTENCE_SOCIAL if k in cfg]
    named = (", ".join(names[:-1]) + " and " + names[-1]) if len(names) > 1 else (names[0] if names else "my channels")
    parts = [brief["hook"], brief["summary"]]
    if brief.get("hindi_summary"):
        parts.append(brief["hindi_summary"])
    parts += [f"WHAT YOU WILL LEARN\n{learn}", f"CHAPTERS\n{ch_lines}"]
    if sources:
        parts.append(f"SOURCES\n{brief.get('sources_label', 'Official sources')}:\n{sources}")
    parts.append(f"NEXT EPISODE\n{brief['next_episode']}")
    parts.append(f"{brief.get('series_name', SERIES.upper())}\n{brief['series_blurb']}")
    parts.append(f"ABOUT THE CHANNEL\n{brief['channel_blurb']}")
    parts.append(f"Subscribe: {cfg['Subscribe link']}")
    parts.append(f"Follow {FOLLOW_NAME} to reach out and keep learning:\n" + follow +
                 f"\nIf this helped, follow on {named}, and send your questions.")
    if brief.get("quiz_cta"):
        parts.append(brief["quiz_cta"])
    parts.append(" ".join(brief["hashtags"]))
    description = "\n\n".join(parts)
    pinned = brief["pinned_comment"].replace("{reveal}", reveal or "")
    return chs, cue, description, pinned, reveal, quiz_start


def checks(ep, brief, cfg, chs, cue, description):
    res = []  # (level, text)
    ok = lambda t: res.append(("PASS", t))
    warn = lambda t: res.append(("WARN", t))
    bad = lambda t: res.append(("FAIL", t))
    kw = brief["target_keyword"].lower()
    titles = brief["titles"]
    t0 = titles[0]
    (ok if len(t0) <= LIMITS["title"] else bad)(f"title length {len(t0)} (limit {LIMITS['title']})")
    (ok if len(t0) <= LIMITS["title_good"] else warn)(f"title shows fully in search if under about {LIMITS['title_good']} characters ({len(t0)})")
    (ok if kw in t0.lower()[:60] else warn)(f'target keyword "{kw}" appears in the first 60 characters of the title')
    (ok if len(titles) >= 2 else warn)("at least two title options")
    first_two = " ".join(description.split("\n")[:2]).lower()
    (ok if kw in first_two else bad)(f'target keyword "{kw}" is in the first two description lines')
    (ok if len(description) <= LIMITS["description"] else bad)(f"description length {len(description)} (limit {LIMITS['description']})")
    (ok if "<" not in description and ">" not in description else bad)("description has no angle brackets (YouTube rejects them)")
    tags = brief["tags"]
    total = len(", ".join(tags))
    (ok if total <= LIMITS["tags_total"] else bad)(f"tags total {total} characters (limit {LIMITS['tags_total']})")
    long_tags = [t for t in tags if len(t) > LIMITS["tag"]]
    (ok if not long_tags else warn)(f"every tag is {LIMITS['tag']} characters or fewer" + (f": {long_tags}" if long_tags else ""))
    hashtags = re.findall(r"#\w+", description)
    (ok if len(hashtags) <= LIMITS["hashtags"] else bad)(f"{len(hashtags)} hashtags (YouTube may ignore all above {LIMITS['hashtags']})")
    (ok if len(brief["hashtags"]) >= 3 else warn)("at least 3 hashtags so three show above the title")
    # chapters
    times = [t for t, _ in chs]
    (ok if times and times[0] == 0 else bad)("first chapter starts at 0:00")
    (ok if len(chs) >= 3 else bad)(f"{len(chs)} chapters (need at least 3)")
    gaps = [round(b - a, 1) for a, b in zip(times, times[1:])]
    (ok if not gaps or min(gaps) >= 10 else bad)(f"every chapter is at least 10 seconds (shortest {min(gaps) if gaps else 'n/a'})")
    # links
    for b in BANNED_LINKS:
        (ok if b not in description else bad)(f"no outdated link text '{b}'")
    for k, _ in SOCIAL_ORDER:
        if k in cfg and k not in ("Website",):
            (ok if cfg[k] in description else bad)(f"{k} follow link from channel-config.md is present")
    (ok if cfg["Subscribe link"] in description else bad)("subscribe link is present")
    # numbering
    n = int(brief["series_number"])
    wrong = [m for m in re.findall(r"Episode (\d+)", description) if int(m) not in (n, n + 1)]
    (ok if not wrong else bad)(f"episode numbers in the description match series number {n} (next {n + 1})" + (f": found {wrong}" if wrong else ""))
    # thumbnails
    final = os.path.join(ep, "thumbnail-final.png")
    if os.path.exists(final):
        from PIL import Image
        im = Image.open(final)
        (ok if im.size == (1280, 720) else bad)(f"thumbnail-final.png is {im.size[0]}x{im.size[1]} (need 1280x720)")
        (ok if os.path.getsize(final) < 2 * 1024 * 1024 else bad)(f"thumbnail-final.png is {os.path.getsize(final) / 1048576:.2f} MB (limit 2 MB)")
    else:
        bad("thumbnail-final.png exists")
    tdir = os.path.join(ep, "thumbnails")
    pair = [f for f in os.listdir(tdir) if re.match(r"thumb-[ab]\.png$", f)] if os.path.isdir(tdir) else []
    (ok if len(pair) == 2 else warn)(f"exactly two thumbnail options in thumbnails/ ({len(pair)} found)")
    # video
    mp4 = os.path.join(ep, "episode.mp4")
    if os.path.exists(mp4):
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,codec_type,width,height",
                              "-of", "json", mp4], capture_output=True, text=True)
        try:
            info = json.loads(out.stdout)
            dur = float(info["format"]["duration"])
            codecs = {s["codec_type"]: s["codec_name"] for s in info["streams"]}
            lo, hi = cfg_float("Episode Min Minutes", 0) * 60, cfg_float("Episode Max Minutes", 0) * 60
            if lo or hi:
                too_long, too_short = bool(hi and dur > hi), bool(lo and dur < lo)
                (bad if too_long else warn if too_short else ok)(f"video length {mmss(dur)} (rule {mmss(lo)} to {mmss(hi) if hi else 'any'})")
            else:
                ok(f"video length {mmss(dur)} (no length rule set in channel-config.md)")
            (ok if codecs.get("video") == "h264" and codecs.get("audio") == "aac" else warn)(f"codecs {codecs}")
            head = open(mp4, "rb").read(65536)
            (ok if head.find(b"moov") != -1 else warn)("moov index near the start (fast start)")
            (ok if abs(dur - cue["total_duration"]) < 1.0 else bad)(f"video length matches the cue sheet ({dur:.1f}s vs {cue['total_duration']:.1f}s)")
        except Exception as e:
            bad(f"video could not be read: {e}")
    else:
        bad("episode.mp4 exists")
    return res


def write_files(ep, brief, cfg, chs, cue, description, pinned, reveal, quiz_start, res):
    titles = "\n".join(f"{i + 1}. {t}   ({len(t)} characters)" for i, t in enumerate(brief["titles"]))
    evidence = "\n".join(f"- {x}" for x in brief.get("evidence", []))
    sw = brief.get("short_window_slides")
    short = ""
    if sw:
        starts = {s["n"]: s["start"] for s in cue["slides"]}
        short = f"- 48 hours after publishing, cut one Short from {mmss(starts[sw[0]])} to {mmss(starts[sw[1]])} (about 12 credits). Prompt: {brief.get('short_prompt', 'most useful idea explained simply')}.\n"
    cards = f"Cards: one at {quiz_start} for the quiz and one at {reveal} for the answer\n" if reveal else ""
    md = f'''{brief["code"]} UPLOAD DETAILS - {SERIES}  (generated by tools/dual_host/make_metadata.py)

FILES TO UPLOAD
Video: episode.mp4
Thumbnail 1 (use this): thumbnail-final.png
Thumbnail 2 (backup / test): thumbnails/thumb-b.png

TITLE (use the first one)
{titles}

DESCRIPTION (copy only the text between the two dashed lines)
------------------------------------------------------------
{description}
------------------------------------------------------------

PINNED COMMENT (post after the video is live)
{pinned}

TAGS (paste into the tags box)
{", ".join(brief["tags"])}

HASHTAGS
The first three show above the title. They are already the last line of the description. Keep the total under 15.

SEARCH EVIDENCE (VidIQ)
{evidence}

UPLOAD SETTINGS
Category: Education
Audience: No, not made for kids
Language: English
Playlist: {SERIES}
Chapters: on, taken from the timestamps in the description
Automatic captions: leave on
Comments: on
{cards}End screen (last 20 seconds): Next episode element plus a Subscribe element
Upload first as Private, set the thumbnail, then schedule it

PUBLISH SLOT
{config_value("Publish Slot", "see channel-config.md")}

AFTER UPLOADING
- Send the video link. Score the thumbnail with VidIQ (5 credits each, two at most) and keep the higher one.
- Pin the comment above and reply to every comment in the first hour.
{short}- After 10 to 14 days, compare click-through rate and average view percentage before changing anything.
'''
    open(os.path.join(ep, "metadata.md"), "w").write(md)
    icon = {"PASS": "PASS", "WARN": "WARN", "FAIL": "FAIL"}
    lines = [f"{icon[l]}  {t}" for l, t in res]
    summary = f"{sum(1 for l, _ in res if l == 'FAIL')} FAIL, {sum(1 for l, _ in res if l == 'WARN')} WARN, {sum(1 for l, _ in res if l == 'PASS')} PASS"
    open(os.path.join(ep, "upload-check.md"), "w").write(f"UPLOAD READINESS - {summary}\n\n" + "\n".join(lines) + "\n")
    return summary, lines


def main():
    ep = os.path.abspath(sys.argv[1])
    brief = json.load(open(os.path.join(ep, "upload-brief.json")))
    cfg = read_config()
    chs, cue, description, pinned, reveal, quiz_start = build(ep, brief, cfg)
    res = checks(ep, brief, cfg, chs, cue, description)
    summary, lines = write_files(ep, brief, cfg, chs, cue, description, pinned, reveal, quiz_start, res)
    print(summary)
    for l in lines:
        if not l.startswith("PASS"):
            print(" ", l)
    sys.exit(1 if any(l == "FAIL" for l, _ in res) else 0)


if __name__ == "__main__":
    main()
