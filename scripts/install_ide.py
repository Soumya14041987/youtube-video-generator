#!/usr/bin/env python3
"""Put this toolkit's skills where your IDE or agent looks for them.

Usage:
  python3 scripts/install_ide.py --ide kiro                 Kiro reads .kiro/skills only
  python3 scripts/install_ide.py --ide junie                Junie reads .junie/skills (and .agents/skills)
  python3 scripts/install_ide.py --ide agents               shared .agents/skills (Cursor, VS Code, Junie, Codex-style tools)
  python3 scripts/install_ide.py --ide all
  python3 scripts/install_ide.py --ide kiro --user          install for every project (~/.kiro/skills)
  python3 scripts/install_ide.py --ide kiro --mode copy     copy instead of linking (the default links, and copies on Windows)
  python3 scripts/install_ide.py --ide all --dry-run

Claude Code, Cursor and VS Code already read .claude/skills, so they need no install step.
The skills themselves stay in .claude/skills and the other folders point at them, so there is one copy to update.
Sub-agents (.claude/agents) are Claude Code only; other tools run those steps inline.
"""
import argparse, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SOURCE = os.path.abspath(os.path.join(HERE, ".."))
SKILLS = ["youtube-video-generator", "youtube-episode", "youtube-thumbnail", "archify", "token-optimizer"]
TARGETS = {"kiro": ".kiro/skills", "junie": ".junie/skills", "agents": ".agents/skills"}


def install_one(src, dst, mode, force, dry):
    if os.path.lexists(dst):
        if not force:
            return "exists (use --force to replace)"
        if not dry:
            if os.path.islink(dst) or os.path.isfile(dst):
                os.unlink(dst)
            else:
                shutil.rmtree(dst)
    if dry:
        return f"would {mode}"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if mode == "link":
        try:
            os.symlink(os.path.relpath(os.path.realpath(src), os.path.realpath(os.path.dirname(dst))), dst, target_is_directory=True)
            return "linked"
        except (OSError, NotImplementedError):
            mode = "copy"  # Windows without symlink permission
    shutil.copytree(src, dst)
    return "copied"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ide", required=True, help="kiro, junie, agents, or all (comma separated)")
    ap.add_argument("--mode", choices=["link", "copy"], default="link")
    ap.add_argument("--project", default=DEFAULT_SOURCE, help="project folder to install into (default: this repo)")
    ap.add_argument("--source", default=DEFAULT_SOURCE, help="folder holding .claude/skills (default: this repo)")
    ap.add_argument("--user", action="store_true", help="install into your home folder instead of the project")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    names = list(TARGETS) if a.ide == "all" else [x.strip() for x in a.ide.split(",")]
    bad = [n for n in names if n not in TARGETS]
    if bad:
        sys.exit(f"unknown --ide value: {', '.join(bad)} (choose from {', '.join(TARGETS)} or all)")
    base = os.path.expanduser("~") if a.user else os.path.abspath(a.project)
    missing = [s for s in SKILLS if not os.path.isdir(os.path.join(a.source, ".claude", "skills", s))]
    if missing:
        sys.exit(f"skills not found in {a.source}/.claude/skills: {', '.join(missing)}")
    for ide in names:
        for skill in SKILLS:
            src = os.path.join(a.source, ".claude", "skills", skill)
            dst = os.path.join(base, TARGETS[ide], skill)
            if os.path.abspath(src) == os.path.abspath(dst):
                continue
            print(f"{ide:7} {TARGETS[ide]}/{skill}: {install_one(src, dst, a.mode, a.force, a.dry_run)}")


if __name__ == "__main__":
    main()
