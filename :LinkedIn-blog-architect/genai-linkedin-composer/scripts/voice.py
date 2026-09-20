#!/usr/bin/env python3
"""
voice.py - shared voice.md reader for detect.py and discovery.py.

Tolerates the markdown the template actually uses: bolded labels, values
that continue onto following lines or sub-bullets, and parenthetical
guidance text left in from the template (stripped, never treated as terms).

Usage
  python3 voice.py ~/.claude/linkedin/voice.md      # show what was parsed
"""

import json
import os
import re
import sys

BANNED_LABELS = ("Words I would never use", "hard-fail on")
FOCUS_LABEL = "Focus areas"


def resolve(path):
    return os.path.expanduser(path) if path else None


def read(path):
    path = resolve(path)
    if not path or not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def field(text, label):
    """Return the raw value of a `- **Label...:** value` field, including
    continuation lines, up to the next bolded field, heading, or blank-line
    gap followed by one."""
    m = re.search(r"^[ \t]*[-*][ \t]+\*{0,2}[^\n]*?" + re.escape(label) + r"[^\n:]*:\*{0,2}[ \t]*",
                  text, re.MULTILINE | re.IGNORECASE)
    if not m:
        return ""
    rest = text[m.end():]
    stop = re.search(r"^[ \t]*[-*][ \t]+\*\*|^#{1,6}[ \t]", rest, re.MULTILINE)
    return rest[: stop.start()] if stop else rest


def to_terms(raw):
    raw = re.sub(r"\([^)]*\)", " ", raw, flags=re.DOTALL)
    raw = raw.replace("**", "")
    terms = []
    for part in re.split(r"[,;\n]", raw):
        part = re.sub(r"^\s*[-*]\s+", "", part).strip().strip("\"'`").strip(" .")
        if part:
            terms.append(part)
    return terms


def banned_terms(path):
    text = read(path)
    terms = []
    for label in BANNED_LABELS:
        terms.extend(to_terms(field(text, label)))
    return terms


def focus_areas(path):
    return to_terms(field(read(path), FOCUS_LABEL))


def positions(path):
    text = read(path)
    m = re.search(r"^## My positions\s*\n(.*?)(?=^## |\Z)", text, re.DOTALL | re.MULTILINE)
    if not m:
        return []
    return [line.strip() for line in re.findall(r"^[ \t]*\d+\.[ \t]+(\S.*)$", m.group(1), re.MULTILINE)]


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "~/.claude/linkedin/voice.md"
    print(json.dumps({"banned_terms": banned_terms(p), "focus_areas": focus_areas(p),
                      "positions": positions(p)}, indent=2, ensure_ascii=False))
