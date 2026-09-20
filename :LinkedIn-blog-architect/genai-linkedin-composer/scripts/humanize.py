#!/usr/bin/env python3
"""
humanize.py - strip the machine fingerprint out of a LinkedIn draft.

Derived in part from li-human in Jakeschincariol/linkedin-agent-skill (MIT).
See THIRD_PARTY_NOTICES.md.

Three automatic passes, in order:

  1. INVISIBLE     delete or space-normalise characters a keyboard never
                    types: zero-width joiners, word joiners, soft hyphens,
                    BOMs, Unicode tag characters, non-breaking/narrow spaces.
  2. TYPOGRAPHIC    em dash -> comma, en dash -> hyphen, curly quotes ->
                    straight, ellipsis -> three dots, bullet -> hyphen.
  3. LEXICAL        swap the slop.json lexicon for plain words, preserving
                    capitalisation. URLs, `code spans`, hyphenated compounds
                    (force-unlock) and slop.json's technical_allow phrases
                    (test harness, terraform unlock) are never touched.
                    Terms that are also real infra vocabulary (harness,
                    unlock, elevate...) are marked "mode": "flag" - reported
                    for review, not swapped.

Structural tells (rule-of-three, "not just X, it's Y", hashtag walls,
buzzword stacks) are REPORTED, not rewritten - reshaping a sentence needs
judgement a regex doesn't have. That's step 2 of the QA gate in SKILL.md,
done by the model, not this script.

Usage
  python3 humanize.py draft.txt
  python3 humanize.py draft.txt --report
  pbpaste | python3 humanize.py - --report
  python3 humanize.py draft.txt --json
  python3 humanize.py draft.txt -o clean.txt
"""

import argparse
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
LEX = os.path.join(HERE, "slop.json")

URL_RE = re.compile(r"https?://\S+|www\.\S+|\S+@\S+\.\S+")
CODE_RE = re.compile(r"```.*?```|`[^`\n]+`", re.DOTALL)
SENT_RE = re.compile(r"[^.!?\n]+[.!?]*")


def load_lexicon(path=LEX):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def codepoint(spec):
    if "-" in spec:
        a, b = spec.split("-")
        return (int(a[2:], 16), int(b[2:], 16))
    return int(spec[2:], 16)


def protect(text, lex):
    """Swap code spans, technical_allow phrases and URLs for placeholders so
    no pass rewrites them. Returns (text, stashed)."""
    found = []

    def _sub(m):
        found.append(m.group(0))
        return f"\x00P{len(found) - 1}\x00"

    patterns = ([CODE_RE] + [re.compile(p, re.IGNORECASE) for p in lex.get("technical_allow", [])]
                + [URL_RE])
    for pattern in patterns:
        text = pattern.sub(_sub, text)
    return text, found


def restore(text, found):
    for i in reversed(range(len(found))):
        text = text.replace(f"\x00P{i}\x00", found[i])
    return text


def strip_invisible(text, lex):
    hits = []
    for entry in lex["invisible"]:
        cp = codepoint(entry["cp"])
        pattern = ("[" + re.escape(chr(cp[0])) + "-" + re.escape(chr(cp[1])) + "]"
                   if isinstance(cp, tuple) else re.escape(chr(cp)))
        n = len(re.findall(pattern, text))
        if not n:
            continue
        hits.append({"name": f"{entry['cp']} {entry['name']}", "count": n, "action": entry["action"]})
        text = re.sub(pattern, "" if entry["action"] == "delete" else " ", text)
    stray = [c for c in text if unicodedata.category(c) == "Cf"]
    if stray:
        hits.append({"name": "unlisted Unicode format character", "count": len(stray), "action": "delete"})
        text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    return text, hits


def fix_typography(text, lex):
    hits = []
    for entry in lex["typographic"]:
        ch = entry["from"]
        n = text.count(ch)
        if not n:
            continue
        hits.append({"name": f"{ch} {entry['name']}", "count": n, "to": entry["to"].strip() or "(removed)"})
        if ch == "—":
            text = re.sub(r"\s*—\s*", ", ", text)
        elif ch == "–":
            text = re.sub(r"\s*–\s*(?=\d)", "-", text)
            text = re.sub(r"\s+–\s+", ", ", text)
            text = text.replace("–", "-")
        else:
            text = text.replace(ch, entry["to"])
    text = re.sub(r",\s*([,.;:!?])", r"\1", text)
    text = re.sub(r",\s*\n", "\n", text)
    return text, hits


def match_case(original, replacement):
    if not replacement:
        return replacement
    if original.isupper() and len(original) > 1:
        return replacement.upper()
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def lexicon_pattern(find):
    """Whole-term match that does not fire inside hyphenated or snake_case
    compounds (force-unlock, test_harness)."""
    return re.compile(r"(?<![\w-])" + re.escape(find).replace(r"\ ", r"\s+") + r"(?![\w-])",
                      re.IGNORECASE)


def _cut(m):
    """Delete a phrase plus its trailing punctuation; capitalise the next
    word if the phrase opened a sentence."""
    before = m.string[:m.start()].rstrip(" \t")
    at_start = before == "" or before[-1] in ".!?\n"
    nxt = m.group("nxt") or ""
    return nxt.upper() if at_start else nxt


def swap_lexicon(text, lex):
    hits, review = [], []
    entries = sorted(lex["words"] + lex["phrases"], key=lambda e: len(e["find"]), reverse=True)
    for entry in entries:
        find, replace = entry["find"], entry["replace"]
        pattern = lexicon_pattern(find)
        if entry.get("mode") == "flag":
            n = len(pattern.findall(text))
            if n:
                review.append({"find": find, "suggest": replace or "(cut it)",
                               "count": n, "family": entry["family"]})
            continue
        if replace:
            found = pattern.findall(text)
            if found:
                text = pattern.sub(lambda m: match_case(m.group(0), replace), text)
        else:
            cutter = re.compile(pattern.pattern + r"[,;:]?[ \t]*(?P<nxt>[A-Za-z])?", re.IGNORECASE)
            found = cutter.findall(text)
            if found:
                text = cutter.sub(_cut, text)
        if found:
            hits.append({"find": find, "replace": replace or "(deleted)",
                         "count": len(found), "family": entry["family"]})
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"(?m)^[ \t]*([,.;:])\s*", "", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([.!?])[ \t]*\.(?=\s|$)", r"\1", text)
    text = re.sub(r"(?m)^[ \t]+$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r",\s*(also|so|still|next)\s*,\s*",
                  lambda m: ". " + m.group(1)[0].upper() + m.group(1)[1:] + ", ", text)
    return text, hits, review


def flag_structures(text, lex):
    flags = []
    for s in lex["structures"]:
        try:
            pattern = re.compile(s["regex"], re.MULTILINE)
        except re.error:
            continue
        found = pattern.findall(text)
        if found:
            flags.append({"name": s["name"], "count": len(found), "fix": s["fix"]})
    lens = [len(s.split()) for s in SENT_RE.findall(text) if len(s.split()) > 2]
    if len(lens) >= 4:
        mean = sum(lens) / len(lens)
        var = sum((n - mean) ** 2 for n in lens) / len(lens)
        cv = (var ** 0.5) / mean if mean else 0
        if cv < 0.35:
            flags.append({
                "name": f"Uniform sentence length (variation {cv:.2f})",
                "count": len(lens),
                "fix": "Break one sentence in half. Let another run long.",
            })
    return flags


def humanize(text, lex):
    text, stashed = protect(text, lex)
    text, inv = strip_invisible(text, lex)
    text, typo = fix_typography(text, lex)
    text, lexical, review = swap_lexicon(text, lex)
    text = restore(text, stashed)
    return text.strip() + "\n", {
        "invisible": inv,
        "typographic": typo,
        "lexical": lexical,
        "review": review,
        "structures": flag_structures(text, lex),
    }


def render_report(report, out=sys.stderr):
    def head(title):
        print(f"\n{title}\n" + "-" * len(title), file=out)

    total = (sum(h["count"] for h in report["invisible"])
             + sum(h["count"] for h in report["typographic"])
             + sum(h["count"] for h in report["lexical"]))

    head("HUMANIZE REPORT")
    print(f"{total} machine artefacts removed, "
          f"{len(report['review'])} ambiguous terms and {len(report['structures'])} structural tells "
          f"flagged for you to review", file=out)

    if report["invisible"]:
        head("1. INVISIBLE CHARACTERS")
        for h in report["invisible"]:
            print(f"  {h['count']:>3}x  {h['name']}  -> {h['action']}", file=out)
    if report["typographic"]:
        head("2. TYPOGRAPHY")
        for h in report["typographic"]:
            print(f"  {h['count']:>3}x  {h['name']}  -> {h['to']}", file=out)
    if report["lexical"]:
        head("3. SLOP LEXICON")
        for h in report["lexical"]:
            print(f"  {h['count']:>3}x  {h['find']}  -> {h['replace']}   [{h['family']}]", file=out)
    if report["review"]:
        head("4. REVIEW  (ambiguous in technical text - left as written)")
        for h in report["review"]:
            print(f"  {h['count']:>3}x  {h['find']}  -> maybe: {h['suggest']}   [{h['family']}]", file=out)
    if report["structures"]:
        head("5. STRUCTURAL TELLS  (rewrite these by hand)")
        for h in report["structures"]:
            print(f"  {h['count']:>3}x  {h['name']}\n        {h['fix']}", file=out)
    if not any(report.values()):
        head("CLEAN")
        print("  Nothing to strip.", file=out)
    print("", file=out)


def main():
    ap = argparse.ArgumentParser(description="Strip the machine fingerprint out of a LinkedIn draft.")
    ap.add_argument("input", nargs="?", default="-", help="file, or - for stdin")
    ap.add_argument("-o", "--out", help="write cleaned text here instead of stdout")
    ap.add_argument("--report", action="store_true", help="print what changed, to stderr")
    ap.add_argument("--json", action="store_true", help="emit {text, report} as JSON")
    ap.add_argument("--lexicon", default=LEX, help="path to slop.json")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    lex = load_lexicon(args.lexicon)
    clean, report = humanize(raw, lex)

    if args.json:
        print(json.dumps({"text": clean, "report": report}, indent=2, ensure_ascii=False))
        return
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(clean)
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(clean)
    if args.report:
        render_report(report)


if __name__ == "__main__":
    main()
