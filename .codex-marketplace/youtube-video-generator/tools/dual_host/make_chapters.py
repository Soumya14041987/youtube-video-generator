#!/usr/bin/env python3
"""Print YouTube chapter lines (m:ss Title) from an episode's real cue sheet.

Usage: make_chapters.py <episode_dir>
Slide titles come from dualhost.json. A quiz slide gets a second chapter where the answer is revealed.
"""
import json, os, sys

ep = sys.argv[1]
cue = json.load(open(os.path.join(ep, "cue-sheet.json")))
script = json.load(open(os.path.join(ep, "dualhost.json")))
titles = {s["n"]: s["title"] for s in script["slides"]}
quiz = cue.get("quiz")
rows, seen = [], set()
for sl in cue["slides"]:
    if quiz and sl["start"] == quiz["reveal_at"]:
        rows.append((sl["start"], "The Answer Revealed"))
    elif sl["n"] not in seen:
        seen.add(sl["n"])
        name = titles[sl["n"]]
        rows.append((sl["start"], name + (" (Pause and Think)" if quiz and sl["n"] == quiz["slide"] else "")))
out = []
for t, name in rows:
    t = int(round(t))
    out.append(f"{t // 60}:{t % 60:02d} {name}")
text = "\n".join(out)
open(os.path.join(ep, "chapters.txt"), "w").write(text + "\n")
print(text)
