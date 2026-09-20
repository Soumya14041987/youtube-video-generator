#!/usr/bin/env python3
"""
detect.py - a five-check panel scoring how machine-written a draft reads,
plus an optional voice-lock check against the user's voice.md.

Derived in part from li-human in Jakeschincariol/linkedin-agent-skill (MIT).
See THIRD_PARTY_NOTICES.md.

What this is: five local heuristics modelled on the signals public AI
detectors key on - sentence-length variation, concreteness, stock
vocabulary, typographic fingerprint, and voice. Computed on this machine
from the text alone. Nothing is uploaded.

What this is NOT: GPTZero, Originality, Copyleaks, Winston or Turnitin.
It does not call those APIs and cannot promise their verdict. Fixing what
it measures tends to move those numbers too, because they key on the same
underlying signals - that's the only honest claim here.

Each check returns 0-100, higher is more human.

Usage
  python3 detect.py draft.txt
  pbpaste | python3 detect.py -
  python3 detect.py draft.txt --json
  python3 detect.py before.txt after.txt              # before/after delta
  python3 detect.py draft.txt --voice ~/.claude/linkedin/voice.md
"""

import argparse
import json
import os
import re
import statistics
import sys
import unicodedata

import humanize
import voice

HERE = os.path.dirname(os.path.abspath(__file__))
LEX = os.path.join(HERE, "slop.json")

SENT_RE = re.compile(r"[^.!?\n]+[.!?]*")
WORD_RE = re.compile(r"[A-Za-z']+")
CONTRACTIONS = re.compile(r"\b\w+'(?:s|t|re|ve|ll|d|m)\b", re.IGNORECASE)
PRONOUNS = re.compile(r"\b(i|me|my|mine|we|us|our|you|your)\b", re.IGNORECASE)
NUMBERS = re.compile(r"\b\d[\d,.]*%?\b|\$\d")
PROPER = re.compile(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]{2,}\b", re.MULTILINE)


def clamp(n):
    return max(0.0, min(100.0, n))


def scale(value, human, machine):
    if human == machine:
        return 50.0
    return clamp((value - machine) / (human - machine) * 100)


def sentences(text):
    return [s.strip() for s in SENT_RE.findall(text) if len(s.split()) > 2]


def words(text):
    return WORD_RE.findall(text)


def check_burstiness(text):
    lens = [len(s.split()) for s in sentences(text)]
    if len(lens) < 4:
        return 50.0, "too short to judge"
    mean = statistics.mean(lens)
    cv = statistics.pstdev(lens) / mean if mean else 0
    return scale(cv, human=0.70, machine=0.22), f"variation {cv:.2f} across {len(lens)} sentences (want 0.55+)"


def check_specificity(text):
    w = words(text)
    if len(w) < 25:
        return 50.0, "too short to judge"
    per100 = 100 / len(w)
    hits = len(NUMBERS.findall(text)) + len(set(PROPER.findall(text)))
    density = hits * per100
    return scale(density, human=6.0, machine=0.5), f"{hits} concrete markers, {density:.1f} per 100 words (want 4+)"


def check_slop(text, lex):
    text, _ = humanize.protect(text, lex)
    w = words(text)
    if not w:
        return 50.0, "empty"
    hits, found = 0, []
    entries = sorted(lex["words"] + lex["phrases"], key=lambda e: len(e["find"]), reverse=True)
    for entry in entries:
        pattern = humanize.lexicon_pattern(entry["find"])
        n = len(pattern.findall(text))
        if n:
            hits += n
            found.append(entry["find"])
            text = pattern.sub(" ", text)
    density = hits * 100 / len(w)
    detail = f"{hits} stock terms, {density:.1f} per 100 words"
    if found:
        detail += " (" + ", ".join(sorted(found)[:4]) + (", ..." if len(found) > 4 else "") + ")"
    return scale(density, human=0.0, machine=4.0), detail


def check_fingerprint(text):
    invisible = sum(1 for c in text if unicodedata.category(c) == "Cf")
    em = text.count("—")
    curly = sum(text.count(c) for c in "‘’“”")
    ellip = text.count("…")
    nbsp = sum(text.count(c) for c in "      ")
    total = invisible * 4 + em * 2 + curly + ellip + nbsp
    per1k = total * 1000 / max(len(text), 1)
    detail = f"{invisible} invisible, {em} em dash, {curly} curly quote, {ellip} ellipsis, {nbsp} hard space"
    return scale(per1k, human=0.0, machine=12.0), detail


def check_voice(text, lex):
    w = words(text)
    if len(w) < 25:
        return 50.0, "too short to judge"
    per100 = 100 / len(w)
    contractions = len(CONTRACTIONS.findall(text)) * per100
    person = len(PRONOUNS.findall(text)) * per100
    tells, names = 0, []
    for s in lex["structures"]:
        try:
            n = len(re.compile(s["regex"], re.MULTILINE).findall(text))
        except re.error:
            continue
        if n:
            tells += n
            names.append(s["id"])
    bullets = [len(b.split()) for b in re.findall(r"(?m)^\s*[-*•]\s+(.+)$", text)]
    uniform = len(bullets) >= 3 and statistics.pstdev(bullets) < 1.6
    score = (scale(contractions, human=3.0, machine=0.0) * 0.35
             + scale(person, human=8.0, machine=1.0) * 0.35
             + clamp(100 - tells * 22) * 0.30)
    if uniform:
        score -= 12
        names.append("uniform-bullets")
    detail = f"{contractions:.1f} contractions, {person:.1f} personal pronouns per 100 words, {tells} structural tell(s)"
    if names:
        detail += " [" + ", ".join(names[:4]) + "]"
    return clamp(score), detail


def check_voice_lock(text, voice_terms):
    if not voice_terms:
        return None
    hits = []
    for term in voice_terms:
        if re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, re.IGNORECASE):
            hits.append(term)
    score = clamp(100 - len(hits) * 34)
    detail = ("clean against voice.md's banned list" if not hits
              else f"hit banned term(s): {', '.join(hits)}")
    return score, detail


CHECKS = ["BURSTINESS", "SPECIFICITY", "SLOP DENSITY", "FINGERPRINT", "VOICE"]


def run(text, lex, voice_terms=None):
    results = {
        "BURSTINESS": check_burstiness(text),
        "SPECIFICITY": check_specificity(text),
        "SLOP DENSITY": check_slop(text, lex),
        "FINGERPRINT": check_fingerprint(text),
        "VOICE": check_voice(text, lex),
    }
    checks = list(CHECKS)
    lock = check_voice_lock(text, voice_terms)
    if lock is not None:
        results["VOICE LOCK"] = lock
        checks.append("VOICE LOCK")
    scores = [results[c][0] for c in checks]
    overall = statistics.mean(scores) * 0.6 + min(scores) * 0.4
    verdict = "PASS" if overall >= 70 and min(scores) >= 55 else ("REVIEW" if overall >= 50 else "FLAGGED")
    return results, checks, overall, verdict


def bar(score, width=24):
    filled = round(score / 100 * width)
    return "#" * filled + "." * (width - filled)


def render(results, checks, overall, verdict, label=None, out=sys.stdout):
    title = "AI DETECTION + VOICE-LOCK PANEL" + (f"  -  {label}" if label else "")
    print("\n" + title, file=out)
    print("=" * max(len(title), 62), file=out)
    for name in checks:
        score, detail = results[name]
        print(f"  {name:<13} {bar(score)} {score:5.1f}", file=out)
        print(f"  {'':<13} {detail}", file=out)
    print("-" * 62, file=out)
    print(f"  {'HUMAN SCORE':<13} {bar(overall)} {overall:5.1f}   {verdict}", file=out)
    if verdict != "PASS":
        weakest = min(checks, key=lambda c: results[c][0])
        print(f"\n  Weakest signal: {weakest}. Fix that first.", file=out)
    print("", file=out)


def main():
    ap = argparse.ArgumentParser(description="Score how machine-written a LinkedIn draft looks.")
    ap.add_argument("input", nargs="?", default="-", help="file, or - for stdin")
    ap.add_argument("compare", nargs="?", help="second file, to show before/after")
    ap.add_argument("--voice", help="path to voice.md - adds a VOICE LOCK check")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--lexicon", default=LEX)
    args = ap.parse_args()

    lex = json.load(open(args.lexicon, encoding="utf-8"))
    voice_terms = []
    if args.voice:
        if not os.path.exists(voice.resolve(args.voice)):
            sys.exit(f"error: --voice file not found: {args.voice}")
        voice_terms = voice.banned_terms(args.voice)
        if not voice_terms:
            print("note: voice lock inactive - no banned terms found in voice.md "
                  "('Words I would never use' / hard-fail phrases are empty)", file=sys.stderr)
    read = lambda p: sys.stdin.read() if p == "-" else open(p, encoding="utf-8").read()

    targets = [(args.input, read(args.input))]
    if args.compare:
        targets.append((args.compare, read(args.compare)))

    payload = []
    for name, text in targets:
        results, checks, overall, verdict = run(text, lex, voice_terms)
        payload.append({
            "source": name,
            "checks": {k: {"score": round(v[0], 1), "detail": v[1]} for k, v in results.items()},
            "human_score": round(overall, 1),
            "verdict": verdict,
        })

    if args.json:
        print(json.dumps(payload if args.compare else payload[0], indent=2))
        return

    for (name, text), p in zip(targets, payload):
        results, checks, overall, verdict = run(text, lex, voice_terms)
        render(results, checks, overall, verdict, label=os.path.basename(name) if args.compare else None)
    if args.compare:
        a, b = payload
        delta = b["human_score"] - a["human_score"]
        print(f"  {a['human_score']:.1f} {a['verdict']}  ->  {b['human_score']:.1f} {b['verdict']}   ({delta:+.1f})\n")

    sys.exit(0 if payload[-1]["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
