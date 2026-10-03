# AGENTS.md

This repository is a toolkit that turns a topic into a finished YouTube episode: script, visuals, voices, timeline, video,
thumbnails and upload details. It works as a Claude Code plugin or as a project you open in any agentic IDE.

## Make an episode
- Claude Code: run `/youtube-video-generator`, then give a topic, a URL, or say "what's next".
- Inputs that work after the command: a topic, a URL, `next`, `next in <series>`, `ideas`, or `Topic:`/`URL:`/`Series:`/`Audience:`/`Duration:`/`Style:` lines. See `docs/EPISODE-INPUT.md`.
- Any other tool: ask it to follow `.claude/skills/youtube-video-generator/SKILL.md` for your topic. That file is the full workflow.
  The sub-agents in `.claude/agents/` are Claude Code only. Other tools should do those steps themselves, in order.

## Set up
- `pip install -r requirements.txt` and install ffmpeg.
- Copy `.env.example` to `.env` and add `OPENAI_API_KEY`. Copy `channel-config.md.example` to `channel-config.md` and fill it in.
- `python3 scripts/doctor.py` checks everything. It must show 0 FAIL before you build an episode.
- Kiro and Junie only read their own skill folders: `python3 scripts/install_ide.py --ide kiro` (or `junie`, `agents`, `all`).
- Full guide for each IDE: `docs/IDE-SETUP.md`.

## Commands
- Build voices, timeline, checks and video: `python3 tools/dual_host/build_episode.py episodes/<folder> --bible <script.md> --ep N`
- Thumbnails (two options): `python3 tools/dual_host/compose_thumbnails.py episodes/<folder>`
- Upload package and readiness check: `python3 tools/dual_host/make_metadata.py episodes/<folder>`
- Chapter list from the real timeline: `python3 tools/dual_host/make_chapters.py episodes/<folder>`
- Vertical Shorts from a built episode: `python3 tools/dual_host/make_short.py episodes/<folder> --suggest 3`, then `--lines A-B --hook "..."` (see `docs/SHORTS.md`)
- Syntax check after editing tools: `python3 -m py_compile tools/dual_host/*.py scripts/*.py`
- Setup check without keys: `python3 scripts/doctor.py --ci`

## Rules for any agent working here
- Never print, log or commit API keys. `.env` is ignored by git. Read keys from the environment or `.env` only.
- Timing comes from real audio lengths and a Whisper check, never from word counts.
- Thumbnail and slide text is drawn by code, never by an image model.
- Use the published episode number from `channel-config.md`, not the folder number, on screen, in speech and in descriptions.
- Links come only from `channel-config.md`. Never invent a link.
- Episodes, `channel-config.md`, `.env`, `assets/presenter`, `assets/music` and series files are the creator's. They are ignored by git. Do not commit them.
- Keep changes small and run the syntax check and `python3 scripts/doctor.py --ci` before finishing.

## Layout
- `.claude/skills/` the skills (Agent Skills format: a folder with `SKILL.md`). `.claude/agents/` Claude Code sub-agents.
- `tools/dual_host/` the Python tools. `scripts/` setup and install helpers. `config/mcp/` example MCP settings per IDE.
- `docs/` guides. `.claude-plugin/` Claude Code plugin files.
