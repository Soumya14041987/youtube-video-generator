#!/usr/bin/env python3
"""Check this computer and project are ready to make episodes. Prints PASS, WARN or FAIL for every check.

Usage:  python3 scripts/doctor.py            full check
        python3 scripts/doctor.py --ci       skip the checks that need your keys, models or channel files

Exit code 1 if anything FAILs. API key values are never printed.
"""
import importlib.util, os, platform, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools", "dual_host"))
import common  # noqa: E402

CI = "--ci" in sys.argv
RESULTS = []


def add(level, text, fix=None):
    RESULTS.append((level, text, fix))


def have_module(name):
    return importlib.util.find_spec(name) is not None


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except Exception as e:  # noqa: BLE001
        return subprocess.CompletedProcess(cmd, 1, "", str(e))


def check_python():
    v = sys.version_info
    add("PASS" if v >= (3, 9) else "FAIL", f"Python {v.major}.{v.minor}.{v.micro} (need 3.9 or newer)", "Install Python 3.10 or newer from python.org")


def check_packages():
    add("PASS" if have_module("PIL") else "FAIL", "Pillow (image drawing)" + ("" if have_module("PIL") else " is missing"),
        "pip install -r requirements.txt")
    if not CI:
        has = have_module("whisper")
        add("PASS" if has else "WARN", "openai-whisper (timing and wording checks)" + ("" if has else " is missing; those checks are skipped"),
            "pip install -r requirements.txt")
        if has:
            cached = os.path.exists(os.path.expanduser("~/.cache/whisper/base.pt"))
            add("PASS" if cached else "WARN", "Whisper 'base' model downloaded" + ("" if cached else " (it downloads on first use)"),
                "If the download fails with an SSL error, see docs/TROUBLESHOOTING.md")


def check_ffmpeg():
    ff, fp = shutil.which("ffmpeg"), shutil.which("ffprobe")
    add("PASS" if ff and fp else "FAIL", "ffmpeg and ffprobe on PATH" + ("" if ff and fp else " are missing"),
        "macOS: brew install ffmpeg   Windows: winget install ffmpeg   Ubuntu: sudo apt install ffmpeg")
    if ff:
        enc = run(["ffmpeg", "-hide_banner", "-encoders"]).stdout
        for name in ("libx264", "aac"):
            add("PASS" if re.search(rf"\b{name}\b", enc) else "FAIL", f"ffmpeg has the {name} encoder",
                "Install a full ffmpeg build (not a minimal one)")


def check_fonts():
    for kind, label in (("impact", "Impact (thumbnail headlines)"), ("black", "Arial Black (banners)")):
        found = any(os.path.exists(e.partition("|")[0]) for e in common._FONT_FILES[kind][:3])
        add("PASS" if found else "WARN", label + ("" if found else " not found; a similar bold font is used instead"),
            "Optional: install the font for the exact look")
    em = common.emoji_font()
    add("PASS" if em else "WARN", "Color emoji font" + ("" if em else " not found; icon rows use a simple circle instead"),
        "Linux: sudo apt install fonts-noto-color-emoji")


def check_keys_and_secrets():
    if not CI:
        k = common.env_key("OPENAI_API_KEY", required=False)
        add("PASS" if k else "FAIL", "OPENAI_API_KEY is set (value not shown)" if k else "OPENAI_API_KEY is not set",
            "Copy .env.example to .env and add your key, or export it in your shell or IDE")
        g = common.env_key("GEMINI_API_KEY", required=False)
        add("PASS" if g else "WARN", "GEMINI_API_KEY is set (optional, only for --tts gemini)" if g else "GEMINI_API_KEY not set (optional)")
    git = shutil.which("git")
    if git and os.path.isdir(os.path.join(common.CODE_ROOT, ".git")):
        ignored = run(["git", "-C", common.CODE_ROOT, "check-ignore", "-q", ".env"]).returncode == 0
        add("PASS" if ignored else "FAIL", ".env is ignored by git" if ignored else ".env is NOT ignored by git",
            "Add '.env' to .gitignore before you commit")
        files = run(["git", "-C", common.CODE_ROOT, "ls-files", "-co", "--exclude-standard"]).stdout.splitlines()
        pat = re.compile(r"(sk-[A-Za-z0-9_-]{24,}|AIza[0-9A-Za-z_-]{30,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16})")
        hits = []
        for f in files:
            p = os.path.join(common.CODE_ROOT, f)
            try:
                if os.path.getsize(p) < 1_000_000 and not f.endswith((".png", ".jpg", ".jpeg", ".wav", ".mp3", ".mp4", ".webp", ".pt")):
                    if pat.search(open(p, errors="ignore").read()):
                        hits.append(f)
            except OSError:
                pass
        add("PASS" if not hits else "FAIL", "no API keys found in files git would commit" if not hits else f"possible API key in: {', '.join(hits[:5])}",
            "Remove the key from that file and rotate it")


def check_project():
    if CI:
        return
    cc = os.path.exists(common.data_path("channel-config.md"))
    add("PASS" if cc else "WARN", "channel-config.md found" if cc else "channel-config.md not found",
        "Copy channel-config.md.example to channel-config.md and fill it in")
    if cc:
        sub = common.cfg("Subscribe link") or common.cfg("Channel ID")
        add("PASS" if sub else "WARN", "Subscribe link or Channel ID set" if sub else "Subscribe link or Channel ID missing in channel-config.md",
            "Add 'Subscribe link: https://www.youtube.com/channel/<id>?sub_confirmation=1'")
    shots = [f for f in os.listdir(common.data_path("assets", "presenter")) if f.endswith(".png")] \
        if os.path.isdir(common.data_path("assets", "presenter")) else []
    add("PASS" if shots else "WARN", f"{len(shots)} presenter shot(s) in assets/presenter" if shots else
        "no presenter shots (thumbnails will have no face)", "See docs/THUMBNAILS.md")


def check_ides():
    root = common.CODE_ROOT
    items = [(".claude/skills/youtube-video-generator/SKILL.md", "Claude Code, Cursor, VS Code and Junie read this skill"),
             ("AGENTS.md", "Codex, Copilot, Zed, Junie, Kiro and others"), ("CLAUDE.md", "Claude Code instructions"),
             (".cursor/rules/youtube-video-generator.mdc", "Cursor rule"), (".github/copilot-instructions.md", "VS Code Copilot"),
             (".kiro/steering/youtube-video-generator.md", "Kiro steering"), (".claude-plugin/plugin.json", "Claude Code plugin manifest")]
    for rel, what in items:
        add("PASS" if os.path.exists(os.path.join(root, rel)) else "WARN", f"{rel}  ({what})")
    for rel, tool in ((".kiro/skills", "Kiro"), (".junie/skills", "Junie")):
        add("PASS" if os.path.isdir(os.path.join(root, rel)) else "WARN",
            f"{rel} installed ({tool} only looks here)", f"python3 scripts/install_ide.py --ide {tool.lower()}")


def main():
    add("PASS", f"{platform.system()} {platform.release()}, code at {common.CODE_ROOT}")
    add("PASS", f"project folder: {common.PROJECT_ROOT}")
    check_python(); check_packages(); check_ffmpeg(); check_fonts(); check_keys_and_secrets(); check_project(); check_ides()
    order = {"FAIL": 0, "WARN": 1, "PASS": 2}
    for level, text, fix in RESULTS:
        print(f"{level:5} {text}")
        if level != "PASS" and fix:
            print(f"      fix: {fix}")
    fails = sum(1 for l, *_ in RESULTS if l == "FAIL")
    warns = sum(1 for l, *_ in RESULTS if l == "WARN")
    print(f"\n{fails} FAIL, {warns} WARN, {sum(1 for l, *_ in RESULTS if l == 'PASS')} PASS")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
