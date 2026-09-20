---
name: youtube-video-generator
description: Master orchestrator for "Claude Explains" video production. Accepts a bare topic, a URL (spec page, changelog, GitHub release, docs), or nothing at all ("what's next"), resolves it to a concrete input, then orchestrates the entire production pipeline via sequential subagents — research, script writing, asset generation, voiceover, timeline sync, and assembly. Token-optimized. Trigger on "/youtube-video-generator", or a request to make a video from a link, or "what's the next video".
---

# YouTube Video Generator — Master Orchestrator

**Master orchestrator for end-to-end video production.** Receives user input
(topic, URL, or "what's next"), resolves it to a concrete episode spec, then
invokes subagents in sequence to produce research, script, assets, voiceover,
timeline, final video, and metadata.

**Token discipline**: apply token-optimizer's two-way discipline — wrap noisy
shell calls with rtk; when fetching URLs, extract only essential facts; never
paste raw responses back. Report decisions in 1-2 lines.

---

## Phase 1: Input Resolution (Steps 1–4)

### 1. Classify input

- **A URL** → go to step 2.
- **A bare topic / one-liner or short paragraph** → go to step 3.
- **Nothing, or "what's next" / "next video" / similar** → go to step 4.

### 2. Input is a URL

Fetch once via `WebFetch`. Extract only: announcement/docs, date, 2-3 concrete
facts. Never paste raw page back.

Check URL topic against `series-log.md` + `playlists/*.md` first — if
near-duplicate exists, surface it before fetching. Extracted summary becomes
**DRAFT** input (source already has POV; researcher still verifies).

### 3. Input is a bare topic

Check `playlists/*.md` for close-match title. If matched to a playlist item,
use its Format/Audience-Level/Focus ("matches playlist item #N, using
Format/Level"). Else pass through as-is (SHORT or DRAFT per content).

### 4. No input — predict next video

Read all `playlists/*.md` files. Find first `Planned` row per series (skip
`Planned (superseded)`). If multiple series have `Planned` rows, ask user to
pick one.

Cross-check against `series-log.md` for duplicates. State prediction in one
line ("Next up: playlist item #N, '<title>', <Format>/<Level>") and confirm
with user before proceeding.

---

## Phase 2: Orchestration (Steps 5–14)

**Once input is resolved, invoke subagents sequentially. Each agent consumes
prior agent's output as input.**

### 5. Resolve episode details + read continuity

- Read `series-log.md` (step 0 from youtube-episode): detect duplicate,
  assign next episode number (NN = zero-padded). Stop if file unreadable.
- Detect input mode (SHORT or DRAFT).
- Ask user for duration + audience level (AskUserQuestion, 2 questions).
- Record episode number, input mode, duration, audience level for later steps.

### 6. Spawn Research Agent (youtube-researcher)

**Subagent**: youtube-researcher

**Input**: topic, audience level, DRAFT content (if DRAFT mode)

**Output**: structured brief
```
[Core facts]
[What existing videos cover]
[Gap / differentiated angle]
[Sources]
```

**Action**: Invoke via Agent tool with description "Researching video topic
and competitive landscape". Pass topic, audience level, and (if DRAFT) user's
paragraph as context. Store brief for step 7.

### 7. Synthesize Script

**Local step — no subagent.** You write `script.md` using research brief +
audience level + duration from step 5.

Fixed structure (no other structure):
1. Hook (3s, states the question)
2. Core concept (plain English)
3. My angle (differentiated gap or explicit "no gap found")
4. CTA (dark-themed end-card with all 5 platforms, exact tag format per
   youtube-episode step 4)

**Requirements**:
- Number every `[VISUAL:]` / `[ANIMATION:]` tag in script order
  (`visual-01.png`, `animation-01.mp4`, etc.).
- Hit visual density: ~one change per 10–15s narration.
  - Short (60–90s): 6–9 total tags (1–2 animations, rest visuals).
  - Long (≤5min): 15–25 total tags (3–6 animations, rest visuals).
- If audience level is Beginner: every abstract claim needs a concrete visual
  anchor, not just narration.
- Write Hook and CTA with punchy phrasing (suitable for `[CALLOUT:]` on screen).
- Count spoken words; stay within step-5 budget.
- Write `script.md` to episode folder.

### 8. Delegate Asset Generation (Archify + Asset Builder)

**First**: Identify `[VISUAL:]` tags naming real system/cloud/pipeline
components (AWS, Kubernetes, CI/CD, microservice call graphs, etc.).

**Subagent 1 (youtube-archify-diagrammer)**: If any real-world architecture
tags exist, spawn archify-diagrammer once per such tag.

**Input**: tag description, assigned `visual-0N.png` filename, episode folder,
format.

**Output**: PNG file for that visual.

**Subagent 2 (youtube-asset-builder)**: After archify finishes, spawn
asset-builder for remaining visuals + animations + thumbnails.

**Input**: full `script.md`, episode folder, format (short/long),
archify-generated visual numbers (to skip).

**Output**: PNG files for `[VISUAL:]`, silent MP4 clips for `[ANIMATION:]`,
2 thumbnail PNG candidates in `thumbnails/`.

**Action**: Invoke archify-diagrammer (if needed) first, then asset-builder.
Pass results to step 9.

### 9. Generate Voiceover (Gemini TTS)

**Local step — no subagent. Credentials stay in this trusted context.**

1. Extract narration text from `script.md`:
   - Per section (Hook/Core/Angle/CTA): strip header + all `[VISUAL:]` /
     `[ANIMATION:]` / `[CALLOUT:]` tag lines.
   - Join remaining lines with single spaces (one continuous paragraph).
   - Join 4 section-paragraphs with exactly one blank line between.
   - Save as `narration.txt`. **Must have exactly 4 blank-line chunks.**

2. Read `GEMINI_API_KEY` from `.env`. Call Gemini TTS endpoint:
   - Model: `gemini-2.5-flash-preview-tts`
   - Voice: `Puck` (male, default for episode 3+) or user override
   - Response: base64 PCM, decode to WAV (24kHz, 16-bit, mono)
   - Write to `voiceover.wav`

3. Never print API key in output.

4. Check duration via `ffprobe`:
   - Short: 60–90s (under 60s → expand angle section; over 90s → trim).
   - Long: ≤5min (ceiling only).
   - If out of range, edit `script.md`, regenerate `voiceover.wav`, re-run
     steps 7–9 before proceeding.

### 10. Build Cue Sheet (Timeline Synchronization)

**Subagent**: youtube-cue-sheet-builder

**Input**: episode folder path (containing `voiceover.wav`, `narration.txt`,
`script.md`)

**Output**: `cue-sheet.json` (machine-readable) + `cue-sheet.md` (human-readable)

**Action**: Invoke via Agent tool with description "Building cue sheet with
word-level timestamps". Cue sheet maps every asset/callout start/end to real
audio time (runs local Whisper forced-alignment, no API cost). Read
`cue-sheet.md` yourself before step 11 — cheapest point to catch timing bugs.

### 11. Delegate Video Assembly

**Subagent**: youtube-video-assembler

**Input**: episode folder path (containing `voiceover.wav`, `narration.txt`,
`cue-sheet.json`, all assets), format (short/long), duration range (step 5)

**Output**: `episode.mp4` + `thumbnail-final.png`

**Action**: Invoke via Agent tool with description "Assembling final video with
Ken Burns pans and animated clips". Assembler does NOT recompute timing —
reads `cue-sheet.json` directly. Never attempts to generate audio or handle
credentials.

**Verify output yourself**: Extract 3–4 frames via ffmpeg covering static
segment, animation, callouts, and Read them. Confirm no captions (standing
default is off) and visuals match narration per `cue-sheet.md`. Subagent
self-reports have been wrong before — confirmed on disk beats reported.

If assembler reports duration out of range: go back to step 9, fix
`script.md`, regenerate voiceover + cue sheet, re-invoke step 11.

### 12. Write Metadata

**Local step — no subagent.**

Write `metadata.md`:
- 2–3 title options
- Tags (comma-separated, for YouTube tags field)
- `## Hashtags` section (3–5 `#hashtags`)
- Description draft
- `## Connect` footer (fixed, same every episode):
  ```
  Connect with me:
  LinkedIn: https://www.linkedin.com/in/aiops-genai-developer
  Medium: https://medium.com/@soumya14041987
  AWS Builder Center: https://builder.aws.com/
  X: https://x.com/AIWithSoumya
  GitHub: https://github.com/Soumya14041987/mcp-zero-to-hero
  ```
- Recommended publish slot (apply one of these rules, state which):
  - `short-beginner`: Tue/Thu/Sat/Sun, 8–9 PM IST
  - `long-advanced`: Saturday, 9–10 AM IST

If neither rule cleanly fits, pick closer rule explicitly.

### 13. Assemble Episode Folder

**Local step — no subagent.**

Final structure under `episodes/episode-NN-<slug>/`:

```
episodes/episode-NN-<slug>/
  script.md
  narration.txt
  visuals/
    visual-01.png … visual-0N.png
    animation-01.mp4 … animation-0N.mp4
  thumbnails/
    thumbnail-candidate-1.png
    thumbnail-candidate-2.png
  thumbnail-final.png
  voiceover.wav
  cue-sheet.json
  cue-sheet.md
  episode.mp4
  metadata.md
```

Clean up any debug/backup copies (e.g., `voiceover-old-*.wav`) once verified.

### 14. Log Episode + Token Savings

**Local step — no subagent.**

Append one row to `series-log.md` table (do not rewrite existing rows):
- Episode: NN (from step 5)
- Slug: kebab-case topic
- Title: first title option from metadata.md
- Format: short/long
- Duration Pref: `short-60to90s` / `long-5min`
- Slot Rule: which rule from step 12
- Video: `yes` (only once `episode.mp4` exists on disk)
- Date Logged: today
- Topic: original one-liner/paragraph, trimmed

A hook validates the table immediately after write — if it becomes malformed
or episode number collides, fix the row you just added.

**Optional**: Run `rtk gain` once and mention token savings to user in one line.

---

## Quality Gates & Error Recovery

**After each agent completes**:
- Check agent output structure. If malformed, ask agent to fix (via SendMessage,
  if reusing agent context) or re-invoke.
- If agent fails: log the failure, ask user whether to retry or skip that
  phase (limited retries only — don't loop indefinitely).
- If critical failure (e.g., no `episode.mp4` after step 11): surface error
  clearly, do not mask it.

**Staleness rule** (step 9 → step 11 pipeline):
If `script.md` is edited after `voiceover.wav` exists, both `voiceover.wav`
and `cue-sheet.json` are stale and **must** be regenerated before assembly.
Never hand assembler an old cue sheet against a newer script.

---

## Out of Scope

- No YouTube upload automation.
- No talking-avatar rendering (faceless format by design).
- No auto-posting to social platforms.
- Never generate credentials or let subagents handle them.
