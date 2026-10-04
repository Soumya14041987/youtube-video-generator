#!/usr/bin/env python3
"""Stop private material from reaching GitHub.

Usage:
  python3 scripts/check_private.py --staged     files about to be committed (used by the git hook)
  python3 scripts/check_private.py --all        every file git would commit or push (used by CI and the doctor)

It fails (exit code 1) when a file that git would publish:
  1. is a private file type: .env files, channel-config.md, series logs, playlists, episode folders,
     presenter photos, music, or video and audio files
  2. contains something that looks like a key or token
  3. contains a value copied from your own private files: any value in .env, your channel ID, your follow
     and subscribe links and handles, and episode titles from your episodes folder
Values are never printed. Only the file name and the reason are shown.
Paths listed in .privacy-allow (one per line) are exempt from check 3, for example LICENSE.
"""
import fnmatch, json, os, re, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "dual_host"))

PRIVATE_PATHS = [
    ".env", ".env.*", "*.env", "channel-config.md", "series-log.md", "playlists/*", "episodes/*", "graft/*",
    "assets/presenter/*", "assets/music/*", "*.local.json", "*.mp4", "*.mov", "*.wav", "*.mp3", "*.m4a",
]
PRIVATE_OK = [".env.example", "assets/presenter/README.md", "assets/music/README.md", "channel-config.md.example"]
SECRET_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9_-]{24,}"), "OpenAI style key"),
    (re.compile(r"AIza[0-9A-Za-z_-]{30,}"), "Google API key"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"), "GitHub token"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"), "Slack token"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key block"),
    (re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{24,}"), "key assignment"),
]
THIRD_PARTY = (".claude/skills/archify/",)  # bundled code: the loose "key assignment" pattern is skipped here
SKIP_CONTENT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".pt", ".ico", ".pdf", ".woff", ".woff2", ".ttf", ".ttc", ".swift")


def git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True).stdout


def files(mode):
    if mode == "staged":
        out = git("diff", "--cached", "--name-only", "--diff-filter=ACM")
    else:
        out = git("ls-files", "-co", "--exclude-standard")
    return [f for f in out.splitlines() if f]


def private_values():
    """Values that must never appear in a published file. Short or generic values are skipped."""
    vals = {}
    env = os.path.join(ROOT, ".env")
    if os.path.exists(env):
        for line in open(env, errors="ignore"):
            if "=" in line and not line.lstrip().startswith("#"):
                v = line.split("=", 1)[1].strip().strip("'\"")
                if len(v) >= 12:
                    vals[v] = "a value from your .env"
    try:
        import common
        cfg = common.load_config()
    except Exception:  # noqa: BLE001
        cfg = {}
    for key, v in cfg.items():
        v = (v or "").split("#")[0].strip()
        if key == "channel id" and len(v) >= 10:
            vals[v] = "your channel ID"
        for tok in re.findall(r"https?://\S+", v):
            if "github.com" in tok or tok.rstrip("/").count("/") < 3:
                continue
            vals[tok.rstrip("/")] = f"your {key} link"
        for tok in re.findall(r"(?<![\w.])@[A-Za-z0-9_.]{4,}", v):
            vals[tok] = f"your {key} handle"
    # video details: titles from your episodes folder and series log
    ep_root = os.path.join(ROOT, "episodes")
    if os.path.isdir(ep_root):
        for d in os.listdir(ep_root):
            p = os.path.join(ep_root, d, "upload-brief.json")
            if os.path.exists(p):
                try:
                    for t in json.load(open(p)).get("titles", []):
                        if len(t) >= 20:
                            vals[t] = "one of your episode titles"
                except Exception:  # noqa: BLE001
                    pass
    log = os.path.join(ROOT, "series-log.md")
    if os.path.exists(log):
        for line in open(log, errors="ignore"):
            cells = [c.strip() for c in line.split("|")]
            if len(cells) > 4 and cells[1].isdigit() and len(cells[3]) >= 20:
                vals[cells[3]] = "an episode title from your series log"
    return vals


def allowed(path):
    p = os.path.join(ROOT, ".privacy-allow")
    if not os.path.exists(p):
        return False
    pats = [l.strip() for l in open(p) if l.strip() and not l.startswith("#")]
    return any(fnmatch.fnmatch(path, x) for x in pats)


def main():
    mode = "staged" if "--staged" in sys.argv else "all"
    problems, vals = [], private_values()
    for f in files(mode):
        if f in PRIVATE_OK:
            continue
        if any(fnmatch.fnmatch(f, pat) or fnmatch.fnmatch(os.path.basename(f), pat) for pat in PRIVATE_PATHS):
            problems.append((f, "private file type (it is kept out of GitHub on purpose)"))
            continue
        path = os.path.join(ROOT, f)
        if f.endswith(SKIP_CONTENT) or not os.path.isfile(path) or os.path.getsize(path) > 2_000_000:
            continue
        text = open(path, errors="ignore").read()
        for rx, what in SECRET_PATTERNS:
            if what == "key assignment" and f.startswith(THIRD_PARTY):
                continue
            if rx.search(text):
                problems.append((f, f"looks like a {what}"))
                break
        if not allowed(f):
            for v, what in vals.items():
                if v in text:
                    problems.append((f, f"contains {what}"))
                    break
    if problems:
        print("PRIVACY CHECK FAILED. Do not commit or push these:")
        for f, why in problems:
            print(f"  {f}: {why}")
        print("Remove the private text, or add the file to .gitignore. Values are not shown.")
        sys.exit(1)
    print(f"privacy check passed ({mode}: {len(files(mode))} files, {len(vals)} private values checked)")


if __name__ == "__main__":
    main()
