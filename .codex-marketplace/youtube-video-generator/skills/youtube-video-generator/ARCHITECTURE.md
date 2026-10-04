# YouTube Video Generator — Architecture

Visual and conceptual overview of the master orchestrator system.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE LAYER                            │
│  /youtube-video-generator ← (CLI or chat interface)                      │
│  Input: topic | URL | "what's next"                                    │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────────┐
│              ORCHESTRATOR (Master Controller)                            │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │ PHASE 1: Input Resolution (Steps 1-4)                      │       │
│  │  • Classify input (topic / URL / predict-next)             │       │
│  │  • Check series-log.md + playlists/*.md for duplicates    │       │
│  │  • Resolve to: topic, mode (SHORT/DRAFT), episode#        │       │
│  │  • Ask user: duration? audience level?                    │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                             │                                            │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │ PHASE 2: Production Orchestration (Steps 5-14)            │       │
│  │                                                             │       │
│  │  Step 5: Read continuity (series-log.md)                  │       │
│  │    └─ Detect duplicates, assign episode#, read folder     │       │
│  │                                                             │       │
│  │  Step 6: ┌──────────────────────────────────────────┐     │       │
│  │          │ youtube-researcher (Subagent)           │     │       │
│  │          │ → Structured brief: facts, gap, sources │     │       │
│  │          └──────────────────────────────────────────┘     │       │
│  │                                                             │       │
│  │  Step 7: Write script.md locally                          │       │
│  │    └─ Hook, Core, Angle, CTA + visual/animation tags    │       │
│  │                                                             │       │
│  │  Step 8: ┌──────────────────────────────────────────┐     │       │
│  │          │ youtube-archify-diagrammer (Subagent)   │     │       │
│  │          │ → Real-world architecture diagrams      │     │       │
│  │          └──────────────────────────────────────────┘     │       │
│  │              + youtube-asset-builder (Subagent)          │       │
│  │          │ → Static visuals, animations, thumbnails     │       │
│  │          └──────────────────────────────────────────┘     │       │
│  │                                                             │       │
│  │  Step 9: Generate voiceover.wav locally (Gemini TTS)      │       │
│  │    └─ Extract narration, call Gemini, save WAV           │       │
│  │                                                             │       │
│  │  Step 10: ┌──────────────────────────────────────────┐    │       │
│  │           │ youtube-cue-sheet-builder (Subagent)    │    │       │
│  │           │ → Whisper forced-alignment timestamps   │    │       │
│  │           └──────────────────────────────────────────┘    │       │
│  │                                                             │       │
│  │  Step 11: ┌──────────────────────────────────────────┐    │       │
│  │           │ youtube-video-assembler (Subagent)      │    │       │
│  │           │ → Ken Burns pans, clips, callouts       │    │       │
│  │           │ → episode.mp4 + thumbnail-final.png     │    │       │
│  │           └──────────────────────────────────────────┘    │       │
│  │                                                             │       │
│  │  Step 12: Write metadata.md locally                       │       │
│  │    └─ Titles, tags, hashtags, description, slot rule     │       │
│  │                                                             │       │
│  │  Step 13: Assemble episodes/episode-NN-<slug>/ folder    │       │
│  │    └─ All files in correct structure, cleanup backups    │       │
│  │                                                             │       │
│  │  Step 14: Append to series-log.md                         │       │
│  │    └─ One new row, validate, report token savings        │       │
│  │                                                             │       │
│  └─────────────────────────────────────────────────────────────┘       │
│                             │                                            │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │ Quality Gates at Each Phase                               │       │
│  │  • Structure validation (JSON, file existence)            │       │
│  │  • Content validation (visual density, duration, etc.)    │       │
│  │  • Spot-check verification (extract frames, read files)  │       │
│  │  • Error recovery (retry, skip, stop)                    │       │
│  └─────────────────────────────────────────────────────────────┘       │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────────┐
│                       OUTPUT FOLDER                                      │
│  episodes/episode-NN-<slug>/                                            │
│  ├─ script.md          (fully written, tagged with visuals)            │
│  ├─ narration.txt      (extracted from script, 4 sections)             │
│  ├─ voiceover.wav      (Puck voice, 24kHz, 16-bit mono)                │
│  ├─ cue-sheet.json     (machine-readable: asset/callout timing)        │
│  ├─ cue-sheet.md       (human-readable version of cue-sheet)           │
│  ├─ visuals/           (PNGs for [VISUAL:], MP4s for [ANIMATION:])    │
│  ├─ thumbnails/        (2 candidates from asset builder)               │
│  ├─ thumbnail-final.png (chosen thumbnail)                            │
│  ├─ episode.mp4        (final rendered video, no captions burned)      │
│  └─ metadata.md        (titles, tags, hashtags, publish slot)          │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────────┐
│                    Continuity Files (Updated)                           │
│  ├─ series-log.md      (new episode row appended)                       │
│  └─ playlists/*.md     (unchanged, referenced for planning)             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Between Phases

```
Input
  ↓
[Step 5] Read series-log.md, assign episode#, folder path
  ↓
[Step 6] Research Agent
  ├─ Input: topic, audience level, (optional: DRAFT content)
  └─ Output: {core_facts, existing_coverage, gap, sources}
  ↓
[Step 7] Write script.md locally
  ├─ Input: research brief, audience level, duration budget
  └─ Output: script.md (with [VISUAL:], [ANIMATION:], [CALLOUT:] tags)
  ↓
[Step 8a] Archify Agent (if real-world architecture tags exist)
  ├─ Input: tag description, target filename, episode folder
  └─ Output: visual-0N.png
  ↓
[Step 8b] Asset Builder Agent
  ├─ Input: script.md, episode folder, format, archify-generated visual #s
  └─ Output: visual-*.png, animation-*.mp4, thumbnail-*.png
  ↓
[Step 9] Generate voiceover.wav locally
  ├─ Input: narration.txt (extracted from script.md)
  └─ Output: voiceover.wav (24kHz, Puck voice)
  ↓
[Step 10] Cue Sheet Agent
  ├─ Input: voiceover.wav, narration.txt, script.md, episode folder
  └─ Output: cue-sheet.json, cue-sheet.md (word-level timestamps)
  ↓
[Step 11] Video Assembly Agent
  ├─ Input: episode folder, voiceover.wav, cue-sheet.json, all visuals
  └─ Output: episode.mp4, thumbnail-final.png
  ↓
[Step 12] Write metadata.md locally
  ├─ Input: script content, audience level, duration, format
  └─ Output: metadata.md (titles, tags, description, publish slot)
  ↓
[Step 13] Assemble output folder
  ├─ Input: all files from steps 7-12
  └─ Output: episodes/episode-NN-<slug>/ (complete structure)
  ↓
[Step 14] Log episode
  ├─ Input: all episode metadata
  └─ Output: series-log.md (new row appended)
```

---

## Subagent Communication Pattern

Each subagent is invoked independently with complete context:

```
Orchestrator                          Subagent
    │                                    │
    ├─────── Agent() call ───────────→  │
    │ (topic, audience, folder path)    │
    │                                    │
    │                         [Fresh context]
    │                         [Does work]
    │                         [Generates output]
    │                                    │
    │  ←────── Return result ──────────┤
    │ (JSON/text structured output)     │
    │                                    │
    ├─ Validate structure               │
    ├─ Check quality gates              │
    └─ Pass to next step                │
```

**Key principle**: No stateful agent continuation. Each agent is fresh. State
is threaded via:
- File system (script.md, voiceover.wav, cue-sheet.json on disk)
- Explicit parameter passing (folder path, topic, prior output summary)

This keeps context lightweight and allows easy retries.

---

## Quality Gate Sequence

```
Step 6 (Research)
  └─ Validate: brief has core_facts, gap, sources
     └─ On fail: Ask user to retry or proceed anyway

Step 7 (Script)
  └─ Validate: visual density ≥ min (6–9 for Short, 15–25 for Long)
     └─ On fail: Ask user to expand script or proceed

Step 9 (Voiceover)
  └─ Validate: duration in [min, max] (60–90s for Short, ≤300s for Long)
     └─ On fail: Stop, ask user to edit script, regenerate

Step 10 (Cue Sheet)
  └─ Validate: cue-sheet.json parses, timestamps are sequential
     └─ Read cue-sheet.md for timing anomalies
     └─ On fail: Ask user to review, maybe edit script and regenerate

Step 11 (Assembly)
  └─ Validate: episode.mp4 exists and is playable (ffprobe)
     └─ Spot-check: Extract 3–4 frames, read visually
     └─ On fail: Ask user to review cue sheet, regenerate (steps 9–11)

Step 14 (Logging)
  └─ Validate: series-log.md table is well-formed, no episode # collisions
     └─ On fail: Stop, ask user to fix malformed row
```

---

## Error Recovery Paths

```
Any Agent Fails
  ├─ Retry with clearer prompt
  │  └─ Usually succeeds on 2nd attempt
  ├─ Skip phase (non-critical phases only)
  │  └─ Proceed to next step, mark as skipped
  └─ Stop (critical phases)
     └─ Halt orchestration, display error, ask user to fix input/assets

State Inconsistency (e.g., script.md edited after voiceover.wav generated)
  ├─ Detect: Compare script.md mtime vs. voiceover.wav mtime
  ├─ Action: Regenerate voiceover.wav + cue-sheet.json (steps 9–10)
  └─ Resume: Continue to assembly (step 11)

Out-of-Range Duration (voiceover too short/long)
  ├─ Detect: ffprobe duration check at step 9
  ├─ Action: Stop, ask user to edit script.md, regenerate (step 9)
  └─ Resume: Regenerate cue sheet (step 10), continue
```

---

## Files on Disk (Persistence Model)

```
Project Root
├─ .claude/
│  └─ skills/
│     └─ youtube-video-generator/
│        ├─ SKILL.md              (spec, 14 phases)
│        ├─ ORCHESTRATION.md      (implementation reference)
│        ├─ MIGRATION.md          (transition guide)
│        ├─ README.md             (quick start)
│        └─ ARCHITECTURE.md       (this file)
│
├─ series-log.md                   (episode log, updated by step 14)
│
├─ playlists/
│  └─ your-series-name.md         (planned episodes, referenced by steps 3-4)
│
└─ episodes/
   ├─ episode-01-what-is-mcp/
   ├─ episode-02-build-first-mcp-server/
   └─ episode-03-<slug>/          (new episodes created by orchestrator)
      ├─ script.md
      ├─ narration.txt
      ├─ voiceover.wav
      ├─ cue-sheet.json
      ├─ cue-sheet.md
      ├─ visuals/
      │  ├─ visual-01.png
      │  ├─ visual-02.png
      │  └─ animation-01.mp4
      ├─ thumbnails/
      │  ├─ thumbnail-candidate-1.png
      │  └─ thumbnail-candidate-2.png
      ├─ thumbnail-final.png
      ├─ episode.mp4
      └─ metadata.md
```

All files are written to disk immediately after generation. This ensures:
- Easy debugging (all intermediate files visible)
- Easy retry (delete a file, re-run that step)
- Audit trail (git tracks all changes)
- Recovery (orchestrator can detect existing files and skip completed steps)

---

## Token Management

### Old Flow (Monolithic youtube-episode)

```
Step 1: Research phase
  → ~20k tokens

Step 2: Script phase
  → Prior research context still in memory
  → ~30k tokens (cumulative: 50k)

Step 3: Assets phase
  → All prior context still in memory
  → ~40k tokens (cumulative: 90k)

Step 4: Assembly phase
  → All prior context still in memory
  → ~60k tokens (cumulative: 150k)

Total: ~150k–200k tokens per episode
```

### New Orchestrator Flow

```
Orchestrator context: ~5k tokens

Step 6: Research subagent (fresh context)
  → ~20k tokens (isolated)

Step 7: Orchestrator continues
  → Receive research brief (~2k tokens)

Step 8: Asset builders (fresh context)
  → ~40k tokens (isolated, no prior context)

Step 9: Orchestrator continues
  → Generate voiceover locally (~1k tokens)

Step 10: Cue sheet subagent (fresh context)
  → ~10k tokens (isolated)

Step 11: Assembly subagent (fresh context)
  → ~30k tokens (isolated)

Total: ~80k–120k tokens per episode
Savings: 30–40% fewer tokens vs. monolithic
```

Each subagent's output is stored on disk (cue-sheet.json, visuals/, etc.) and
only a brief summary is passed to the next phase. This keeps intermediate
context lightweight.

---

## Comparison: Old vs. New

| Aspect | Old youtube-episode | New Master Orchestrator |
|--------|-------------------|------------------------|
| **Entry point** | `/youtube-episode` | `/youtube-video-generator` |
| **Input resolution** | Separate skill (youtube-video-generator) | Steps 1–4, integrated |
| **Subagents** | Delegated per phase | Explicitly invoked, isolated contexts |
| **Token cost** | ~150k–200k per episode | ~80k–120k per episode |
| **Error recovery** | Halt on any failure | Retry, skip, or stop (user chooses) |
| **Context pressure** | Monotonic growth (all stages accumulate) | Fresh per subagent (lightweight) |
| **Debugging** | Hard (all stages in one transcript) | Easy (each phase is a separate file) |
| **Quality gates** | Implicit (hope for the best) | Explicit at every phase |
| **Resume capability** | Not possible | Possible (detect existing files, skip done phases) |

---

## System Guarantees

1. **Continuity**: Once an episode is appended to series-log.md, it's part of
   the canon. Old rows are never rewritten.

2. **Idempotency (per phase)**: If you re-run a phase (e.g., re-generate
   voiceover), prior output is overwritten, but the episode number and series-log
   row remain stable.

3. **Audit trail**: All intermediate files (script.md, voiceover.wav, etc.) are
   on disk and tracked by git. Nothing is generated in-memory and forgotten.

4. **Token discipline**: No redundant context carry-over. Fresh agent per phase.
   Output stored on disk, not re-derived.

5. **Fail-safe default**: Errors are explicit (not silent). Quality gates ask
   user for direction (retry, skip, stop), never guess.

---

## Future Scalability

Current design supports:
- **Multiple series** (multiple playlists/*.md files, each with their own
  episode stream)
- **High-volume production** (orchestrator can handle dozens of episodes with
  no degradation; each episode is independent)
- **Parallel execution** (if needed: assets for one episode can be generated
  while assembly for another completes — currently sequential for simplicity)
- **Extensibility** (adding new phases: add a new step, define subagent
  contract, update orchestrator)

---

**Last updated**: 2026-09-21  
**Maintained by**: Soumyadip Chatterjee
