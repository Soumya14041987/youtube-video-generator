# YouTube Video Generator

Turn a topic into a finished YouTube episode: script, slides, two-voice narration, a video that matches the audio exactly, two thumbnails, and a full upload package with title, description, tags, chapters and pinned comment.

It runs inside an AI coding assistant (Claude Code, VS Code, Cursor, Kiro, PyCharm and others). You describe the episode. The assistant does the work and keeps your API keys on your own computer.

MIT licensed. Works for any channel. Your channel details live in one file, `channel-config.md`.

## What you get

For each episode, in `episodes/episode-NN-name/`:

| File | What it is |
|---|---|
| `episode.mp4` | The finished video (1080p, H.264 and AAC) |
| `thumbnails/thumb-a.png`, `thumb-b.png`, `thumbnail-final.png` | Exactly two thumbnail options, plus the one chosen by default |
| `voiceover.wav` and `audio/lines/` | Narration, one recording per spoken line |
| `cue-sheet.json`, `cue-sheet.md` | When every slide and sound happens, measured from the real audio |
| `metadata.md` | Title, description, tags, hashtags, chapters, pinned comment, settings |
| `upload-check.md` | A pass, warn or fail report so a broken upload package is caught before you upload |

## How the video stays in sync

Every line of the script is spoken by its own text-to-speech call. The length of each recording is read from the file, so the timeline is built from real numbers and never from word counts. A speech-recognition check (Whisper) then confirms every line says what the script says, and any line that does not match is regenerated. Slides change a fraction of a second before the narration reaches them, and quizzes get a 40 second ticking countdown followed by the green answer.

## Which tools work

| Tool | Skills load from | Sub-agents | Extra step |
|---|---|---|---|
| Claude Code (terminal) | `.claude/skills` | Yes | none |
| Claude Code in VS Code, Cursor, Kiro | `.claude/skills` | Yes | install the extension |
| Claude Code in PyCharm and JetBrains IDEs | `.claude/skills` | Yes | install the plugin |
| VS Code with Copilot | `.claude/skills` | No | none |
| Cursor | `.claude/skills` | No | none |
| Kiro | `.kiro/skills` | No | `python3 scripts/install_ide.py --ide kiro` |
| PyCharm with Junie | `.junie/skills` | No | `python3 scripts/install_ide.py --ide junie` |
| Codex, Zed, Warp, Gemini CLI and other tools that read AGENTS.md | varies | No | see the guide |

Without sub-agents, one agent does every step itself. The output is the same.

The full step by step guide for each tool, including the VidIQ connection, is in [docs/IDE-SETUP.md](docs/IDE-SETUP.md).

## Quick start

You need Python 3.10 or newer, ffmpeg, and an OpenAI API key. Node 18 or newer is needed only for the architecture diagram skill.

```bash
git clone https://github.com/Soumya14041987/youtube-video-generator.git
cd youtube-video-generator
python3 -m venv .venv && source .venv/bin/activate     # Windows: py -3 -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env                                   # add your OPENAI_API_KEY
cp channel-config.md.example channel-config.md         # fill in your channel details
python3 scripts/doctor.py                              # must show 0 FAIL
```

Install ffmpeg first if you do not have it: macOS `brew install ffmpeg`, Windows `winget install ffmpeg`, Ubuntu `sudo apt install ffmpeg`.

Open the folder in your assistant and ask for an episode. In Claude Code, Cursor, VS Code and Junie type:

```
/youtube-video-generator
```

In other tools say: "Follow AGENTS.md and make an episode about <your topic>."

The assistant asks a few questions (audience, length, style), researches, writes the script, builds the slides, records the voices, assembles the video, makes the thumbnails, and writes the upload package. It stops for your approval at the points that matter.

### Install as a Claude Code plugin instead

Use this if you want the skills in every project without cloning:

```bash
claude plugin marketplace add Soumya14041987/youtube-video-generator
claude plugin install youtube-video-generator@ytvg-marketplace
```

Keep your own `.env`, `channel-config.md`, `assets/` and `episodes/` in the folder where you start Claude Code. See [docs/IDE-SETUP.md](docs/IDE-SETUP.md) for details.

## Set up your channel

Edit `channel-config.md`. Every value is optional except the subscribe link or channel ID.

| Setting | Used for |
|---|---|
| `Channel Name`, `Presenter`, `Follow Name` | Spoken intro and end screen |
| `Series Name`, `Series Badge` | Thumbnail badge and descriptions |
| `Host 1 Name`, `Host 2 Name` | The two speakers (defaults Alex and Elena) |
| `Episode Min Minutes`, `Episode Max Minutes` | Length check (0 turns it off) |
| `Channel ID` or `Subscribe link` | The subscribe link in every description |
| `LinkedIn`, `Medium`, `X`, `GitHub`, `Instagram`, `Website`, `AWS Builder Center` | Follow links added to descriptions |
| `Banned Links` | Words that must never appear in a description (catches wrong links) |
| `Publish slot` | Suggested day and time |
| `Presenter Look` | Describes the presenter for generated photos |

## Optional: VidIQ for growth

If you connect the VidIQ MCP server, the assistant also researches keywords for your audience, finds outlier videos in your niche, scores titles and thumbnails, and can update a live video after you approve it. Without VidIQ those steps are skipped and everything else still works. VidIQ cannot upload the video file itself. Upload `episode.mp4` in YouTube Studio as Private and paste in `metadata.md`.

Connect it with one command in Claude Code:

```bash
claude mcp add --transport http vidiq https://mcp.vidiq.com/mcp
```

Other tools use a small config file. Ready-made files are in [config/mcp](config/mcp).

## Thumbnails

Two options per episode. Text, banners and icons are drawn by code so spelling is always right. A face is optional: use a photo of yourself (cut out locally), generate presenter shots from a reference photo, or leave the face out. See [docs/THUMBNAILS.md](docs/THUMBNAILS.md).

## Tools you can run yourself

```bash
python3 scripts/doctor.py                                  # check your setup
python3 scripts/install_ide.py --ide kiro                  # put skills where Kiro or Junie look
python3 tools/dual_host/build_episode.py <episode_dir>     # voices, timeline, video
python3 tools/dual_host/compose_thumbnails.py <episode_dir>
python3 tools/dual_host/make_metadata.py <episode_dir>     # upload package and readiness report
python3 tools/dual_host/make_chapters.py <episode_dir>     # chapter list from real timings
python3 tools/dual_host/gen_presenter.py <reference_photo> # presenter shots for thumbnails
python3 tools/dual_host/cutout.py <photo> <out.png>        # cut a person out of a photo
```

## Cost and time

You pay your own providers. The main costs are OpenAI text-to-speech for the narration (about one recording per spoken line) and your assistant's usage. Presenter photo generation and VidIQ credits are optional extras. Prices change, so check the current pricing pages. A 7 to 10 minute episode usually takes a few hours of your attention, mostly for review and approval.

## Safety

- API keys are read from the environment or `.env`, and are never printed, logged, or sent to sub-agents.
- `.env`, `channel-config.md`, `episodes/`, your presenter photos and music, and other creator files are in `.gitignore`. `python3 scripts/doctor.py` fails if `.env` is not ignored or a key is found in a file git would commit.
- Nothing is published for you. You upload the video. VidIQ updates to live videos happen only after you say yes.
- MCP servers and plugins run with your permissions. Read what you approve.

## Known limits

- Sub-agents exist only in Claude Code. Other tools run the same steps in one agent.
- The built-in photo cutout uses macOS 14 or newer. On Windows and Linux install `rembg` or cut the photo out yourself.
- The Whisper `base` model is a one time download of roughly 140 MB.
- Gemini voices are optional (`--tts gemini`) and the free tier is only about 10 requests a day.
- Kiro and Junie only read skills from their own folders, so run the installer once.
- VidIQ credits are limited by your plan, and it cannot upload the video file.
- Details for Windsurf and some other tools come from their public docs and may have changed. Check their docs if a step fails.

## Folder layout

```
.claude/skills/        the skills (video generator, episode, thumbnail, Archify, token optimizer)
.claude/agents/        five sub-agents (Claude Code only)
.claude-plugin/        plugin and marketplace files
tools/dual_host/       episode builder, thumbnails, metadata, chapters, photo tools
scripts/               doctor.py and install_ide.py
config/mcp/            ready-made VidIQ connection files for each tool
docs/                  IDE-SETUP.md, THUMBNAILS.md, TROUBLESHOOTING.md
AGENTS.md              instructions every assistant reads
CLAUDE.md              Claude Code instructions (imports AGENTS.md)
.cursor/ .github/ .kiro/   Cursor rule, Copilot instructions, Kiro steering
```

Your own files (kept out of git): `.env`, `channel-config.md`, `episodes/`, `playlists/`, `series-log.md`, `assets/presenter/`, `assets/music/`.

## Troubleshooting

Run `python3 scripts/doctor.py` first. Then see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## Contributing

Issues and pull requests are welcome. Before you open one, run:

```bash
python3 -m py_compile tools/dual_host/*.py scripts/*.py
python3 scripts/doctor.py --ci
python3 scripts/check_links.py
```

Do not commit keys, channel files, or personal photos.

## License and credits

MIT. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The bundled Archify skill is MIT licensed, by tt-a1i, based on Cocoon-AI/architecture-diagram-generator (MIT). Higgsfield skills are third party, are not part of this repository, and are not needed. VidIQ, OpenAI, Anthropic, Cursor, Kiro and JetBrains are trademarks of their owners and are not affiliated with this project.
