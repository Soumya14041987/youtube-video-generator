# Changelog

## Unreleased

Added
- Shorts mode: `make_short.py` cuts vertical 1080 by 1920 Shorts from an episode with hook banner, word by word captions and a follow line. Guide: docs/SHORTS.md.
- `docs/EPISODE-INPUT.md`, example series files, builder input checks, typed-argument handling in the skill.

## 1.0.0 (2026-10-03)

Added
- Two-host episodes with separate male and female voices, a spoken intro, per-line speech checks and timelines built from the real audio.
- Quiz slides with a 40 second ticking countdown and a green answer reveal.
- Spec-driven thumbnails (`thumbnail-spec.json`), always two options, with a face-less fallback and optional real-photo cutout.
- Upload package builder with a pass, warn or fail readiness report (`make_metadata.py`).
- VidIQ growth stages in the skill, and ready-made VidIQ connection files for Claude Code, VS Code, Cursor, Kiro, Junie and Codex.
- Claude Code plugin and marketplace manifests.
- `AGENTS.md`, `CLAUDE.md`, a Cursor rule, Copilot instructions and a Kiro steering file.
- `scripts/doctor.py` setup checker and `scripts/install_ide.py` for Kiro, Junie and shared skill folders.
- Guides: IDE setup, thumbnails, troubleshooting. New README.
- `requirements.txt`, `.env.example`, a fuller `channel-config.md.example`, third-party notices.

Changed
- Hosts, series name, badge, length rule, follow links and banned links now come from `channel-config.md` instead of being fixed in code.
- Tools find your project folder from where you run them, so a plugin install works.
- API keys are read from the environment first, then `.env`.
- Fonts and the emoji font fall back across macOS, Windows and Linux.
- `.gitignore` now excludes creator media, presenter photos, music and local settings.

Removed
- One-off scripts replaced by `compose_thumbnails.py`, and unused AI host portraits.
