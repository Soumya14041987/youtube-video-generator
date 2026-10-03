# Copilot instructions

This project makes YouTube episodes from a topic. Read `AGENTS.md` for commands, layout and rules.

- The workflow is the skill at `.claude/skills/youtube-video-generator/SKILL.md`. In VS Code agent mode type `/youtube-video-generator`, or ask the agent to follow that file.
- Run `python3 scripts/doctor.py` before building an episode. Stop on any FAIL.
- Never print or commit API keys. `.env` is ignored by git.
- Thumbnail and slide text is drawn by code. Timing comes from real audio lengths. Links come only from `channel-config.md`.
