#!/usr/bin/env python3
"""Check that an episode covers its whole topic, end to end.

Usage: check_coverage.py <episode_dir>

Reads  <episode_dir>/coverage.json   the list of things the episode must cover
       <episode_dir>/dualhost.json   the spoken script
Format of coverage.json:
  {"topic": "MCP tools",
   "must_cover": [
     {"item": "Tools are chosen by the model, and a human can say no", "keywords": ["model controlled", "human"]},
     {"item": "Two kinds of error", "keywords": ["protocol error", "isError"], "all": true}
   ]}
An item is covered when ANY of its keywords is spoken (or ALL of them when "all" is true). Keywords are not case sensitive.
Exit code 1 if anything is missing. A shorter video is fine; a missing topic is not. If it cannot fit in the length
limit, split it into two parts instead of dropping it.
"""
import json, os, re, sys


def spoken_text(ep):
    script = json.load(open(os.path.join(ep, "dualhost.json")))
    return " ".join(l["text"] for s in script["slides"] for l in s["lines"]).lower()


def check(ep):
    """Returns (covered, missing) lists of item names, or None when the episode has no coverage.json."""
    path = os.path.join(ep, "coverage.json")
    if not os.path.exists(path):
        return None
    text = re.sub(r"\s+", " ", spoken_text(ep))
    covered, missing = [], []
    for it in json.load(open(path)).get("must_cover", []):
        kws = [k.lower() for k in it["keywords"]]
        hit = all(k in text for k in kws) if it.get("all") else any(k in text for k in kws)
        (covered if hit else missing).append(it["item"])
    return covered, missing


def main():
    ep = os.path.abspath(sys.argv[1])
    res = check(ep)
    if res is None:
        sys.exit("no coverage.json in this episode folder. List what the episode must cover (see the docstring).")
    covered, missing = res
    for c in covered:
        print(f"PASS     {c}")
    for m in missing:
        print(f"MISSING  {m}")
    print(f"\n{len(covered)} covered, {len(missing)} missing")
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
