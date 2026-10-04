# YouTube Video Generator — Master Orchestrator

**Master orchestrator for end-to-end YouTube video production.**

Entry point: `/youtube-video-generator`

---

## Overview

The master orchestrator coordinates the entire video production pipeline from
user input to final deliverable. It resolves what video to make, then invokes
specialized subagents in sequence to handle research, script writing, asset
generation, voiceover, timeline synchronization, and video assembly.

```
User Input (topic / URL / "what's next")
    ↓
Input Resolution (steps 1-4)
    ├─ Classify input type
    ├─ Check playlists & series-log for duplicates
    ├─ Resolve to concrete episode spec
    └─ Ask user for duration + audience level
    ↓
Research (step 6) — Subagent: youtube-researcher
    └─ Brief: core facts, existing coverage gap, sources
    ↓
Script (step 7) — Local synthesis
    └─ 4-section script with visual/animation/callout tags
    ↓
Assets (step 8) — Subagents: youtube-archify-diagrammer + youtube-asset-builder
    └─ Static visuals, animated clips, thumbnails
    ↓
Voiceover (step 9) — Local Gemini TTS
    └─ 24kHz mono WAV with Puck (male) voice
    ↓
Timeline (step 10) — Subagent: youtube-cue-sheet-builder
    └─ Word-level timestamps via forced alignment
    ↓
Assembly (step 11) — Subagent: youtube-video-assembler
    └─ Final .mp4: Ken Burns pans + animated clips + callout text
    ↓
Metadata (step 12) — Local generation
    └─ Titles, tags, hashtags, description, publish slot recommendation
    ↓
Output (steps 13-14)
    ├─ episodes/episode-NN-<slug>/ folder (complete structure)
    ├─ series-log.md updated with new row
    └─ Report: token savings, folder location, next steps
```

---

## Quick Start

### Make a Video from a Topic

```
/youtube-video-generator
→ "What is model context protocol (MCP)?"
→ Orchestrator asks: duration (Short/Long)? audience (Beginner/Intermediate/Advanced)?
→ Orchestrator runs full pipeline
→ Output: episodes/episode-03-what-is-model-context-protocol/
```

### Make a Video from a URL

```
/youtube-video-generator
→ "https://aws.amazon.com/about-aws/whats-new/2026-09-20/..."
→ Orchestrator fetches, extracts key facts
→ Asks: duration? audience?
→ Runs full pipeline
→ Output: episodes/episode-04-aws-new-feature/
```

### Predict Next Video

```
/youtube-video-generator
→ (no input, or "what's next?")
→ Orchestrator reads playlists/, predicts "Episode 05: Topic X"
→ User confirms
→ Runs full pipeline
→ Output: episodes/episode-05-topic-x/
```

---

## Documentation

### Core Specification

**[SKILL.md](SKILL.md)** — Complete 14-phase specification.

Phases:
- **Phase 1: Input Resolution** (steps 1–4) — resolve what to make
- **Phase 2: Orchestration** (steps 5–14) — invoke subagents and assemble output

Each step lists inputs, outputs, required actions, quality gates, and error handling.

### Implementation Reference

**[ORCHESTRATION.md](ORCHESTRATION.md)** — Practical guide for implementing the orchestrator.

Topics:
- Agent invocation patterns
- State threading between agents
- Quality gates and validation
- Error recovery strategies
- Inter-agent communication
- Folder and file management
- Token optimization checklist
- Full pseudocode example

### Migration Guide

**[MIGRATION.md](MIGRATION.md)** — How to transition from the old youtube-episode flow.

Topics:
- What changed (before/after diagrams)
- Backward compatibility
- Testing checklist
- Fallback to old youtube-episode
- Performance impact
- Future enhancements
- Rollback procedure

---

## Key Features

### Quality Gates at Every Phase

After each agent/step completes:
- Validate output structure (JSON schema, file existence, etc.)
- Check against constraints (visual density, duration range, etc.)
- Ask user to approve or retry if issues detected
- Fail loud and clear for critical issues

### Error Recovery

- **Retry**: Re-invoke agent with clearer prompt or reduced scope
- **Skip**: Skip non-critical phases (e.g., thumbnails) if they fail
- **Stop**: Halt on critical failures (no voiceover.wav, video assembly failed)

### Token Optimization

- Wrap noisy shell output with `rtk` (30-40% savings vs. old monolithic flow)
- Extract only essential facts from fetched URLs
- Never paste full file contents into agent prompts
- Report savings at the end (`rtk gain`)

### Credential Safety

- `GEMINI_API_KEY` is read and used only in step 9 (voiceover generation)
- Never passed to subagents
- Never printed in output
- Verified at start (fail if missing)

---

## Files Generated Per Episode

```
episodes/episode-NN-<slug>/
  ├─ script.md              ← Orchestrator writes (step 7)
  ├─ narration.txt          ← Extracted from script, for TTS
  ├─ visuals/
  │  ├─ visual-01.png       ← Asset agents generate (step 8)
  │  ├─ visual-02.png
  │  └─ animation-01.mp4
  ├─ thumbnails/
  │  ├─ thumbnail-candidate-1.png
  │  └─ thumbnail-candidate-2.png
  ├─ thumbnail-final.png    ← Chosen by asset agent
  ├─ voiceover.wav          ← Orchestrator generates (step 9)
  ├─ cue-sheet.json         ← Cue sheet agent generates (step 10)
  ├─ cue-sheet.md           ← Human-readable cue sheet
  ├─ episode.mp4            ← Assembly agent generates (step 11)
  └─ metadata.md            ← Orchestrator writes (step 12)
```

All files are permanent — delete only if you intend to re-render the episode.

---

## Continuity Files

### series-log.md

Tracks all episodes produced. Orchestrator:
1. Reads it at the start (step 5) to detect duplicates and assign episode number
2. Appends one row at the end (step 14) after successful production

Format:
```
| Episode | Slug | Title | Format | Duration Pref | Slot Rule | Video | Date | Topic |
|---------|------|-------|--------|---------------|-----------|-------|------|-------|
| 01 | what-is-mcp | What is MCP? | short | short-60to90s | short-beginner | yes | 2026-09-15 | What is Model Context Protocol? |
| 02 | build-first-mcp-server | How to Build Your First MCP Server | long | long-5min | long-advanced | yes | 2026-09-20 | Building an MCP server from scratch |
```

### playlists/your-series-name.md

Optional playlist file for a planned episode series. Orchestrator:
1. Reads it during input resolution (step 3) to match bare topics
2. Reads it during "what's next" prediction (step 4)

Create one per series with a descriptive filename. Format:
```
| # | Title | Format | Level | Focus | Status |
|----|-------|--------|-------|-------|--------|
| 1 | First Episode Title | short | beginner | conceptual | Produced |
| 2 | Second Episode Title | long | intermediate | practical | Planned |
```

---

## Troubleshooting

### "Research agent returned malformed output"

**Fix**: The orchestrator catches this and asks you to retry. The agent's
second attempt usually succeeds with a clearer error message in the prompt.

### "Voiceover.wav is 42 seconds, but needs 60–90s for Short"

**Fix**: Edit `script.md` to expand the angle section (usually the thinnest).
Regenerate voiceover and cue sheet. Orchestrator detects the change and
re-invokes assembly.

### "Asset agent didn't generate visual-05.png"

**Fix**: Check asset agent's error report. Common issues:
- Tag was too vague ("show a diagram" without describing what)
- Tag referenced a real-world architecture but went to general asset builder
  instead of archify-diagrammer
- Too many visuals queued, asset builder timed out

Solution: Edit `script.md` (clarify the tag or move to archify), regenerate
assets (step 8), re-invoke assembly.

### "Episode.mp4 looks wrong — visual doesn't match narration"

**Fix**: This usually means a cue-sheet timing bug. Read `cue-sheet.md` and
look for:
- Suspiciously long or short windows for a visual
- Callout landing at wrong timestamp

Extract frames from the video at suspicious timestamps:
```
ffmpeg -ss 30 -frames:v 1 frame-30s.png
```

Compare against `cue-sheet.md`. If cue sheet is wrong, the fix is:
1. Edit `script.md` (split paragraph, clarify callout anchor)
2. Regenerate voiceover (step 9)
3. Regenerate cue sheet (step 10)
4. Re-invoke assembly (step 11)

Do NOT skip step 9–10 — new script timing requires new audio.

---

## Performance

| Metric | Value |
|--------|-------|
| **Wall-clock time per episode** | 30–40 minutes (includes agent spawn overhead) |
| **Token cost per episode** | ~80k–120k (estimated, 30–40% savings vs. old monolithic) |
| **Subagent count** | 4 per episode (researcher, asset builders, cue sheet, assembly) |
| **Quality gates** | ~8 mandatory validations per pipeline run |

---

## Design Principles

1. **Separation of Concerns**: Each subagent owns one well-defined phase (research,
   assets, etc.); orchestrator coordinates and validates.

2. **Fail-Safe by Default**: Quality gates at every phase. Failures are
   explicit and ask for user input (retry/skip/stop), never silent.

3. **Token Discipline**: Fresh context per agent means smaller memory footprint.
   Noisy shell output is wrapped with `rtk`. Facts extracted, never full
   responses dumped.

4. **Audit Trail**: All intermediate files (script.md, narration.txt, cue-sheet.md,
   metadata.md) are on disk. Easy to debug, easy to re-run a single phase.

5. **Backward Compatible**: Existing episodes, series-log.md, playlists — all
   unchanged. Orchestrator is opt-in for new episodes.

---

## Future Enhancements

- **Resume from checkpoint**: Detect existing cue-sheet.json and voiceover.wav,
  skip research-to-timeline, resume at assembly.
- **Parallel asset generation**: Spawn multiple asset agents for non-dependent
  visuals.
- **A/B thumbnail voting**: Generate 5 candidates, let user vote before final pick.
- **Direct YouTube upload**: Once video is ready, upload via YouTube API
  (credentials management TBD).
- **Playlist sync**: Auto-update playlist markdown when episode completes.

---

## Contact

Questions or issues? Check MIGRATION.md for common troubleshooting. For bugs,
open an issue with:
- Which step failed
- Error message (exact text)
- Input provided to orchestrator
- Folder path (if episode folder exists)

---

**Last updated**: 2026-09-21  
**Version**: 1.0 (master orchestrator)  
**Maintained by**: Soumyadip Chatterjee
