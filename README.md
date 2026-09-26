
# YouTube Video Generator

A Claude Code plugin that turns a topic, a URL, or "what's next" into a
finished YouTube video — script, visuals, voiceover, timeline sync, final
MP4, thumbnail, and upload metadata — fully automated inside your terminal.

MIT License. Open source. Works with any YouTube channel.

---

## Why this exists

Producing a decent YouTube video by hand means running six separate tools:
a research tool, a script editor, a design tool, a screen recorder or slide
deck, audio software, and a video editor. Each handoff costs time and breaks
your flow.

This plugin does all six steps inside Claude Code, in order, without you
switching windows. You type a topic. You get a video.

---

## What makes it different from other AI video tools

| Other tools | This plugin |
|-------------|-------------|
| Web UI, manual upload steps | Runs inside your terminal via Claude Code |
| One monolithic prompt | Six specialized subagents, each with fresh context |
| Generic talking-head output | Architecture diagrams via Archify, animated clips via PIL/ffmpeg |
| Locked to one creator style | Reads your channel identity from channel-config.md |
| 150,000-200,000 tokens per video | 80,000-120,000 tokens per video (fresh context per phase) |
| Starts over if one step fails | Detects existing files and skips completed phases |

---

## What you get from one command

```
/youtube-video-generator
```

From a topic like "What is model context protocol?" you get:

- script.md — four-section script with visual and animation tags
- visuals/ — PNG diagrams and animated diagram clips
- thumbnail-final.png — high-CTR thumbnail
- voiceover.wav — narration at 24kHz (Gemini TTS, Puck voice)
- cue-sheet.json — word-level audio timestamps via forced alignment
- episode.mp4 — fully assembled video with Ken Burns pans and callout text
- metadata.md — title options, tags, hashtags, publish slot

All files land in episodes/episode-NN-your-slug/.

---

## Step-by-step: first time setup

### 1. Install Claude Code

If you do not have Claude Code yet, install it and make sure you can run
slash commands in a project directory.

### 2. Clone this repo into your project

```bash
git clone https://github.com/Soumya14041987/youtube-video-generator.git
```

Or copy the .claude/ directory into an existing project.

### 3. Configure your channel

```bash
cp channel-config.md.example channel-config.md
```

Open channel-config.md and fill in your channel name, social links, publish
schedule, and end-card text. This file stays local and is never committed.

### 4. Set your Gemini API key

The voiceover step uses Gemini TTS. Set the key in your environment:

```bash
export GEMINI_API_KEY=your-key-here
```

Add it to your shell profile (.zshrc or .bashrc) so it persists.

### 5. Install ffmpeg

Video assembly requires ffmpeg. On Mac:

```bash
brew install ffmpeg
```

### 6. Install whisper for forced alignment

The cue-sheet step aligns narration to audio timestamps using whisper.

```bash
pip install openai-whisper
```

### 7. Make your first video

In Claude Code, run:

```
/youtube-video-generator
```

Then type a topic, paste a URL, or say "what's next" if you have a playlist
file set up.

---

## Step-by-step: making a video

### Give it a topic

```
What is model context protocol?
```

The orchestrator asks two questions:
- Duration: Short (60-90 seconds) or Long (up to 5 minutes)?
- Audience: Beginner, Intermediate, or Advanced?

Answer both and the full pipeline runs.

### Give it a URL

```
https://example.com/some-announcement
```

It fetches the page, extracts key facts, derives a topic, and runs the same
pipeline.

### Let it decide

```
what's next
```

It reads your playlists/ folder, finds the first unproduced episode, confirms
with you, then runs.

---

## What each phase does

Phase 1 — Input resolution (steps 1-5):
- Classify your input (structured, URL, bare topic, or predict next)
- Check for duplicate episodes in series-log.md
- Ask about duration and audience if not given
- Assign an episode number and folder path

Phase 2 — Production (steps 6-15):
- Step 6: Read series continuity, assign episode folder
- Step 7: Research subagent — returns structured brief, facts, sources
- Step 8: Write script.md — four sections, visual and animation tags
- Step 9: Diagram subagent — real architecture diagrams for infrastructure tags
- Step 10: Asset builder subagent — PNG visuals, animated clips, thumbnails
- Step 11: Generate voiceover.wav locally via Gemini TTS
- Step 12: Cue sheet subagent — forced alignment timestamps
- Step 13: Assembly subagent — ffmpeg composite, Ken Burns pans, callout text
- Step 14: Write metadata.md — titles, tags, description, publish slot
- Step 15: Assemble output folder, append to series-log.md

Each step validates its output before passing to the next. If something fails
you are asked: retry, skip, or stop. Nothing fails silently.

---

## File layout

```
your-project/
  .claude/
    skills/
      youtube-video-generator/   <- orchestrator skill
      youtube-episode/           <- legacy single-agent pipeline
      youtube-thumbnail/         <- standalone thumbnail optimizer
      archify/                   <- architecture diagram engine
    agents/
      youtube-researcher.md
      youtube-archify-diagrammer.md
      youtube-asset-builder.md
      youtube-cue-sheet-builder.md
      youtube-video-assembler.md
    commands/
      youtube-episode.md
  channel-config.md.example      <- copy this to channel-config.md
  LICENSE
  .gitignore
```

Your episodes/ folder, series-log.md, and playlists/ are excluded from git
by default. They are yours, not part of the plugin.

---

## Credential safety

GEMINI_API_KEY is read only in the voiceover step by the orchestrator.
It is never passed to subagents. It is never printed in any output.
If the key is missing the pipeline stops before attempting TTS.

---

## Customizing for your channel

Everything creator-specific lives in channel-config.md:

- Channel name and tagline shown in end-cards and metadata footers
- Social links shown in video descriptions
- Publish schedule rules (which days, which times)
- End-card wordmark text and series tag
- Channel icon overlay badge style

If channel-config.md is missing, the plugin runs with placeholder text and
tells you which lines to fill in.

---

## Troubleshooting

Voiceover too short for the chosen format:
Edit script.md to expand the middle section. Regenerate from step 11.

Visual does not match narration:
Read cue-sheet.md and look for suspiciously short or long windows. Edit
script.md to split the problem paragraph. Regenerate from step 11.

Research subagent returns malformed output:
The orchestrator catches this and retries automatically. If it fails twice,
confirm and proceed — the script step fills in the gaps.

Assembly subagent fails:
Check that voiceover.wav exists and that all visual-NN.png files named in
cue-sheet.json are present in visuals/.

---

## Performance

- Wall-clock time per episode: 30-40 minutes
- Token cost per episode: 80,000-120,000 (30-40 percent less than monolithic)
- Subagents spawned: 5 per full pipeline run
- Quality gates: 8 mandatory validations

---

## License

MIT License. Copyright 2026 Soumyadip Chatterjee.
See LICENSE for full text.

---

## Contributing

Open an issue with:
- Which step failed
- The exact error message
- What input you gave the orchestrator
- Whether the episode folder exists and which files are present
