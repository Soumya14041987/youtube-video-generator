#!/usr/bin/env python3
"""Check that relative links in the project's Markdown files point at files that exist.

Usage: python3 scripts/check_links.py
Exit code 1 if any link is broken. Web links are not fetched.
"""
import os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FILES = ["README.md", "AGENTS.md", "CLAUDE.md", "CHANGELOG.md", "THIRD_PARTY_NOTICES.md",
         ".github/copilot-instructions.md", ".cursor/rules/youtube-video-generator.mdc",
         ".kiro/steering/youtube-video-generator.md"]
FILES += [os.path.join("docs", f) for f in sorted(os.listdir(os.path.join(ROOT, "docs"))) if f.endswith(".md")]
LINK = re.compile(r"\]\(([^)\s]+)\)")


def main():
    bad = 0
    for rel in FILES:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        in_code = False
        for n, line in enumerate(open(path, encoding="utf-8"), 1):
            if line.lstrip().startswith("```"):
                in_code = not in_code
            if in_code:
                continue
            for target in LINK.findall(line):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                t = target.split("#")[0]
                if t and not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(path), t))):
                    print(f"BROKEN {rel}:{n} -> {target}")
                    bad += 1
    print("all relative links ok" if not bad else f"{bad} broken link(s)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
