# Changelog

## Unreleased

Added
- `remotion-video` skill and `render_remotion.py`: topic in, animated Remotion video out (scenes: title, bullets, code, terminal, diagram, compare, quiz with countdown, takeaways, end). Slides can carry a `scene` instead of an image. Guide: docs/REMOTION.md.
- Install paths for Codex CLI (plugin), claude.ai and Claude Desktop, OpenClaw, Hermes Agent and the skills CLI, plus a `skills/` mirror and a generated Codex package (`scripts/sync_codex_package.py`).
- Privacy guard: `scripts/check_private.py`, git hooks in `.githooks/`, a CI step and a doctor check block private files, keys and anything copied from your own channel files.
- Coverage check (`check_coverage.py`, `coverage.json`) so shortening a video never drops part of the topic.
- `Target Country` and `Category` settings; the skill and tools no longer carry creator-specific text.
- `TTS Provider` setting (openai or gemini) in channel-config.md, a clear message when a Gemini key is on the free tier, and a doctor check for the chosen provider's key.
- Per-episode overrides in dualhost.json (`intro_style`, `length_minutes`) so older episodes keep their own rules when the channel rules change.
- Growth checks in make_metadata.py (fast start, early ask, real search tags) and skill stage V8 with a monthly audit routine.
- `description.txt` and `upload-guide.md` for every episode: the exact text to paste and a step by step YouTube Studio guide. Descriptions are English only (no translated summary).
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
