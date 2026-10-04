#!/usr/bin/env python3
"""Build the Codex plugin package from the main skills, so Codex can install this toolkit from GitHub.

Usage:
  python3 scripts/sync_codex_package.py            rebuild .codex-marketplace/youtube-video-generator and .agents/plugins/marketplace.json
  python3 scripts/sync_codex_package.py --check    exit code 1 if the package is out of date (used by CI)

Codex reads .agents/plugins/marketplace.json, which points at a plain folder holding .codex-plugin/plugin.json and the
skills. That folder has to be a real copy (not links), so this script copies the skills and the tools they run.
Archify (the optional diagram skill, about 8 MB, needs Node) is left out of the Codex package; install it separately.
Run this after you change a skill, a tool or a doc, then commit the result.
"""
import filecmp, json, os, shutil, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PKG_REL = os.path.join(".codex-marketplace", "youtube-video-generator")
PKG = os.path.join(ROOT, PKG_REL)
SKILLS = ["youtube-video-generator", "youtube-episode", "youtube-thumbnail", "token-optimizer"]
COPY_DIRS = ["tools", "scripts", "docs", "config", "examples"]
COPY_FILES = ["requirements.txt", ".env.example", "channel-config.md.example", "LICENSE", "THIRD_PARTY_NOTICES.md", "AGENTS.md"]
PLACEHOLDERS = ["assets/presenter/README.md", "assets/music/README.md"]
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "node_modules")


def manifest():
    base = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
    return {
        "name": base["name"],
        "description": base["description"],
        "version": base["version"],
        "author": base["author"],
        "license": base["license"],
        "homepage": base["homepage"],
        "repository": base["repository"],
        "keywords": base.get("keywords", []),
        "skills": "./skills/",
        "interface": {
            "displayName": base.get("displayName", base["name"]),
            "shortDescription": "Topic or URL in, finished YouTube episode out.",
            "longDescription": base["description"],
            "developerName": base["author"]["name"],
            "category": "Productivity",
            "capabilities": ["Interactive", "Read", "Write"],
            "websiteURL": base["homepage"],
            "defaultPrompt": [
                "Make a YouTube episode about <my topic>.",
                "Make an episode from this link.",
                "What is the next episode in my series?",
            ],
        },
    }


def marketplace():
    base = json.load(open(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
    return {
        "name": base["name"],
        "interface": {"displayName": base.get("displayName", base["name"])},
        "plugins": [{
            "name": base["name"],
            "source": {"source": "local", "path": "./" + PKG_REL.replace(os.sep, "/")},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Productivity",
        }],
    }


def build(dest):
    os.makedirs(os.path.join(dest, ".codex-plugin"), exist_ok=True)
    json.dump(manifest(), open(os.path.join(dest, ".codex-plugin", "plugin.json"), "w"), indent=2)
    open(os.path.join(dest, ".codex-plugin", "plugin.json"), "a").write("\n")
    for s in SKILLS:
        shutil.copytree(os.path.join(ROOT, ".claude", "skills", s), os.path.join(dest, "skills", s), ignore=IGNORE, symlinks=False)
    for d in COPY_DIRS:
        shutil.copytree(os.path.join(ROOT, d), os.path.join(dest, d), ignore=IGNORE)
    for f in COPY_FILES:
        shutil.copy2(os.path.join(ROOT, f), os.path.join(dest, f))
    for f in PLACEHOLDERS:
        os.makedirs(os.path.join(dest, os.path.dirname(f)), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, f), os.path.join(dest, f))


def same(a, b):
    cmp = filecmp.dircmp(a, b)
    if cmp.left_only or cmp.right_only or cmp.funny_files:
        return False
    _, mismatch, errors = filecmp.cmpfiles(a, b, cmp.common_files, shallow=False)
    if mismatch or errors:
        return False
    return all(same(os.path.join(a, d), os.path.join(b, d)) for d in cmp.common_dirs)


def main():
    check = "--check" in sys.argv
    tmp = os.path.join(ROOT, ".codex-marketplace", ".building")
    shutil.rmtree(tmp, ignore_errors=True)
    build(tmp)
    mp = json.dumps(marketplace(), indent=2) + "\n"
    mp_path = os.path.join(ROOT, ".agents", "plugins", "marketplace.json")
    if check:
        ok = os.path.isdir(PKG) and same(tmp, PKG) and os.path.exists(mp_path) and open(mp_path).read() == mp
        shutil.rmtree(tmp, ignore_errors=True)
        print("codex package is up to date" if ok else "codex package is OUT OF DATE: run python3 scripts/sync_codex_package.py and commit the result")
        sys.exit(0 if ok else 1)
    shutil.rmtree(PKG, ignore_errors=True)
    os.rename(tmp, PKG)
    os.makedirs(os.path.dirname(mp_path), exist_ok=True)
    open(mp_path, "w").write(mp)
    print(f"wrote {PKG_REL} and .agents/plugins/marketplace.json")


if __name__ == "__main__":
    main()
