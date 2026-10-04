# YouTube Video Generator — Migration Guide

Transitioning from old youtube-episode skill to the new master orchestrator.

---

## What Changed

### Before (Old Flow)

```
User input
    ↓
/youtube-video-generator (input resolver only)
    ↓
/youtube-episode (monolithic skill)
    ↓
    ├─ research
    ├─ script
    ├─ assets
    ├─ voiceover
    ├─ cue sheet
    ├─ assembly
    ├─ metadata
    └─ logging
```

**Problem**: All stages run in one skill context; if one stage fails, entire
production halted. Token context grows monotonically through 14 steps. Difficult
to debug individual stages.

### After (New Master Orchestrator)

```
User input
    ↓
/youtube-video-generator (master orchestrator + all 14 steps)
    ├─ INPUT RESOLUTION (steps 1–4, local)
    ├─ RESEARCH (step 6, spawn youtube-researcher subagent)
    ├─ SCRIPT (step 7, local)
    ├─ ASSETS (step 8, spawn youtube-archify-diagrammer + youtube-asset-builder)
    ├─ VOICEOVER (step 9, local, credential-safe)
    ├─ CUE SHEET (step 10, spawn youtube-cue-sheet-builder)
    ├─ ASSEMBLY (step 11, spawn youtube-video-assembler)
    ├─ METADATA (step 12, local)
    ├─ FOLDER (step 13, local)
    └─ LOGGING (step 14, local)
```

**Benefit**: Each subagent runs in fresh context, reducing memory pressure.
Easier to retry individual stages. Better error isolation. Master orchestrator
coordinates.

---

## Backward Compatibility

### What Still Works

- All existing `episodes/episode-0N-*/` folders (unchanged structure)
- `series-log.md` (same format)
- `playlists/*.md` (same parsing)
- All subagent outputs (same file formats)
- `GEMINI_API_KEY` usage (still in trusted context, step 9 only)

### What Changed

- **No direct `/youtube-episode` invocation from users** — use
  `/youtube-video-generator` instead (which now orchestrates the full pipeline).
- `youtube-episode` skill still exists but is now **delegated to by the
  orchestrator** (if you still want the old monolithic flow, you can run it
  directly, but the recommended path is the orchestrator).

---

## Migration Steps

### Step 1: Deploy New Orchestrator Skill

Copy the updated `youtube-video-generator/SKILL.md` to your `.claude/skills/`
directory. It replaces the old input-resolver-only version.

### Step 2: No Changes to Subagents Required

All existing agents (`youtube-researcher`, `youtube-asset-builder`,
`youtube-cue-sheet-builder`, `youtube-video-assembler`, `youtube-archify-diagrammer`)
remain unchanged. The orchestrator delegates to them with the same contracts.

### Step 3: Preserve series-log.md and playlists/

No format changes. Existing history is fully compatible.

### Step 4: Update User-Facing Docs

- Update any docs that say "use `/youtube-episode` to make a video" →
  "use `/youtube-video-generator` to make a video"
- The orchestrator is the new entry point.

---

## Testing the New Orchestrator

### Quick Test (Short Form)

```
/youtube-video-generator
→ User provides topic: "What is function composition?"
→ Orchestrator:
  ✓ Resolves input
  ✓ Asks for duration (Short) + audience (Beginner)
  ✓ Spawns researcher agent → gets brief
  ✓ Writes script locally
  ✓ Spawns asset agents → gets visuals
  ✓ Generates voiceover locally
  ✓ Spawns cue-sheet agent → gets timing
  ✓ Spawns assembly agent → gets episode.mp4
  ✓ Writes metadata locally
  ✓ Appends to series-log.md
  ✓ Output: episodes/episode-03-function-composition/
```

### Longer Test (URL Input)

```
/youtube-video-generator
→ User provides URL: https://example.com/new-release.html
→ Orchestrator:
  ✓ Fetches URL once
  ✓ Extracts facts (3 key points, date)
  ✓ Checks against playlists/ and series-log.md for duplicates
  ✓ Classifies as DRAFT input
  ✓ Asks for duration + audience
  ✓ Spawns all agents as above
```

### Predict-Next Test

```
/youtube-video-generator
→ User provides no input (or "what's next")
→ Orchestrator:
  ✓ Reads all playlists/*.md
  ✓ Finds first Planned row
  ✓ Cross-checks against series-log.md for duplicates
  ✓ Confirms with user ("Next up: playlist item #3, 'Topic X', Long/Beginner")
  ✓ User confirms → spawns agents
```

---

## Fallback: If You Need the Old youtube-episode Flow

The old `/youtube-episode` skill still works. You can invoke it directly if you
need a monolithic production run (though this is not recommended for new work):

```
/youtube-episode
→ Provide topic or DRAFT content
→ Old skill handles all 12 steps in one context
```

However, you lose:
- Token context separation (stages are not isolated)
- Granular error recovery (one failure halts everything)
- Easy retry on individual stages
- The coordinating quality gates of the orchestrator

Use the orchestrator for all new episodes.

---

## Troubleshooting Migration

### Issue: Old episodes have outdated cue sheets

**Solution**: If you need to re-render an old episode, run the orchestrator on
that existing folder. The orchestrator will:
1. Read existing script.md
2. Skip research (input is DRAFT already)
3. Ask user for duration + audience (may differ from original)
4. Regenerate voiceover (new Puck voice if desired, or keep existing)
5. Regenerate cue sheet
6. Re-assemble video

Existing folder is preserved; new outputs overwrite old ones.

### Issue: Agent invocation fails (network error, model error)

**Solution**: The orchestrator catches failures and offers retry or skip.
- **Retry**: Agent is re-invoked with same prompt.
- **Skip**: Phase is skipped (for non-critical phases only); proceed to next.
- **Stop**: Critical failure (e.g., no voiceover.wav) — halt and report.

### Issue: Token quota exceeded mid-pipeline

**Solution**: Orchestrator saves all intermediate files to disk. If you need to
pause and resume:
1. Edit `episodes/episode-NN-*/` folder directly (e.g., edit script.md, add
   visuals).
2. Re-run `/youtube-video-generator` on the same folder.
3. Orchestrator detects existing files and skips already-complete steps.

**Not yet implemented, but future enhancement**: Detect existing
`voiceover.wav` + `cue-sheet.json` and skip to assembly (step 11).

---

## Performance & Token Impact

### Token Savings (vs. Old Monolithic Flow)

- **Old youtube-episode**: All 14 steps in one context → ~150k–200k tokens per
  episode (full transcript of every stage accumulates).
- **New orchestrator**: Subagents are fresh contexts → ~80k–120k tokens per
  episode (each agent's output is stored, not re-derived).
- **Estimated savings**: 30–40% fewer tokens per production run.

Run `rtk gain` at the end to verify actual savings for your episode.

### Wall-Clock Time

Orchestrator has more latency due to agent spawn overhead:
- Old: ~25–35 minutes per episode (monolithic pipeline, one context)
- New: ~30–40 minutes per episode (agent spawns + IPC overhead)

Trade-off: slightly slower, but more resilient and debuggable.

---

## Future Enhancements

- **Resume from checkpoint**: Detect existing cue-sheet and voiceover, skip to
  assembly.
- **Parallel asset generation**: Spawn multiple asset agents for non-dependent
  visuals (archify + asset-builder can run in parallel for disjoint asset sets).
- **A/B thumbnail voting**: Generate 5 thumbnail candidates, let user vote via
  interactive UI.
- **Auto-publish to YouTube**: Once video is ready, direct upload via YouTube
  API (not yet in scope).

---

## Rollback (If Needed)

If the new orchestrator has an issue:

1. Restore old `youtube-video-generator` SKILL.md from git history.
2. Continue using `/youtube-episode` directly (old monolithic skill is still
   available).
3. File an issue on the new orchestrator design.

---

## Checklists for Team/Long-Term

### First Run Checklist

- [ ] Deploy new orchestrator SKILL.md
- [ ] Run test episode (quick short-form first)
- [ ] Spot-check output folder structure
- [ ] Verify series-log.md updated correctly
- [ ] Run `rtk gain` and confirm token savings
- [ ] Read cue-sheet.md and verify timing
- [ ] Extract 3–4 frames from episode.mp4 and spot-check visuals

### Ongoing Checklist (Per Episode)

- [ ] Use `/youtube-video-generator` (not `/youtube-episode`)
- [ ] Confirm input resolution (show resolved topic to user before proceeding)
- [ ] Approve duration + audience level
- [ ] Review research brief before script write
- [ ] Review script.md visual density (6–9 for Short, 15–25 for Long)
- [ ] Review cue-sheet.md before assembly
- [ ] Spot-check 3–4 frames from final video
- [ ] Verify episode.mp4 + thumbnail-final.png exist on disk
- [ ] Log episode to series-log.md

### Quality Gates (Automated Checks)

Before hand-off to user, orchestrator verifies:
- [ ] `series-log.md` is valid (parseable, no collisions)
- [ ] Episode folder has all required files
- [ ] `voiceover.wav` duration in range [minDuration, maxDuration]
- [ ] `cue-sheet.json` is valid JSON, not empty
- [ ] `episode.mp4` exists and is playable (ffprobe passes)
- [ ] `thumbnail-final.png` exists and is readable

Failures at any gate → halt and surface error clearly.
