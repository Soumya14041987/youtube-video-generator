"""Shared helpers for the toolkit: where things live, API keys, channel config and fonts.

Two roots matter:
- CODE_ROOT:    the folder that holds this toolkit (the cloned repo, or the Claude Code plugin cache).
- PROJECT_ROOT: the creator's working folder, where .env, channel-config.md, assets/ and episodes/ live.
In a normal clone they are the same folder. When the toolkit is installed as a Claude Code plugin they differ,
so user files are always looked up in PROJECT_ROOT first.
"""
import os
import re
import sys

CODE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def find_project_root():
    """YTVG_PROJECT wins, then the nearest folder (from the current one upward) that looks like a project."""
    env = os.environ.get("YTVG_PROJECT")
    if env and os.path.isdir(env):
        return os.path.abspath(env)
    d = os.path.abspath(os.getcwd())
    while True:
        if any(os.path.exists(os.path.join(d, m)) for m in ("channel-config.md", ".env")) or os.path.isdir(os.path.join(d, "episodes")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return CODE_ROOT
        d = parent


PROJECT_ROOT = find_project_root()


def data_path(*parts):
    """A user-owned file or folder: PROJECT_ROOT first, then CODE_ROOT, else the PROJECT_ROOT location."""
    for root in (PROJECT_ROOT, CODE_ROOT):
        p = os.path.join(root, *parts)
        if os.path.exists(p):
            return p
    return os.path.join(PROJECT_ROOT, *parts)


# ---------------------------------------------------------------- API keys
def env_key(name, required=True):
    """Read a key from the environment first, then from a .env file. Never prints the value."""
    val = os.environ.get(name)
    if val:
        return val.strip().strip('"')
    for root in (PROJECT_ROOT, CODE_ROOT):
        path = os.path.join(root, ".env")
        if os.path.exists(path):
            for line in open(path):
                line = line.strip()
                if line.startswith(name + "="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    if required:
        sys.exit(f"{name} is not set. Add it to {os.path.join(PROJECT_ROOT, '.env')} "
                 f"(see .env.example) or export it in your shell or IDE environment.")
    return None


# ---------------------------------------------------------------- channel config
_CONFIG = None


def load_config():
    """Parse 'Key: value' lines from channel-config.md. Keys are lower-cased. Missing file gives an empty dict."""
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = {}
        path = data_path("channel-config.md")
        if os.path.exists(path):
            for line in open(path):
                m = re.match(r"^\s*([A-Za-z][A-Za-z0-9 ()/_-]*?)\s*:\s*(\S.*?)\s*$", line)
                if m and not line.lstrip().startswith("#"):
                    _CONFIG.setdefault(m.group(1).strip().lower(), m.group(2).strip())
    return _CONFIG


def cfg(key, default=None):
    return load_config().get(key.lower(), default)


def cfg_float(key, default=0.0):
    try:
        return float(cfg(key, default))
    except (TypeError, ValueError):
        return float(default)


# ---------------------------------------------------------------- fonts (macOS, Windows, Linux)
_FONT_FILES = {
    "impact": ["/System/Library/Fonts/Supplemental/Impact.ttf", r"C:\Windows\Fonts\impact.ttf",
               "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
               "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"],
    "black": ["/System/Library/Fonts/Supplemental/Arial Black.ttf", r"C:\Windows\Fonts\ariblk.ttf",
              "/usr/share/fonts/truetype/msttcorefonts/Arial_Black.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"],
    "bold": ["/System/Library/Fonts/Helvetica.ttc|1", "/System/Library/Fonts/Supplemental/Arial Bold.ttf", r"C:\Windows\Fonts\arialbd.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
             "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"],
    "regular": ["/System/Library/Fonts/Helvetica.ttc|0", "/System/Library/Fonts/Supplemental/Arial.ttf", r"C:\Windows\Fonts\arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/usr/share/fonts/dejavu/DejaVuSans.ttf"],
}
_EMOJI_FONTS = [("/System/Library/Fonts/Apple Color Emoji.ttc", 160), (r"C:\Windows\Fonts\seguiemj.ttf", 109),
                ("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109), ("/usr/share/fonts/noto/NotoColorEmoji.ttf", 109)]


def find_font(kind, size):
    """Best available font for kind: impact, black, bold or regular. Falls back to Pillow's default."""
    from PIL import ImageFont
    for entry in _FONT_FILES[kind]:
        path, _, idx = entry.partition("|")
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size, index=int(idx or 0))
            except Exception:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def emoji_font():
    """(font, native_size) for a color emoji font, or None when this computer has none."""
    from PIL import ImageFont
    for path, size in _EMOJI_FONTS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size), size
            except Exception:
                continue
    return None
