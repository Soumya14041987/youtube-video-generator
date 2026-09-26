---
name: youtube-video-generator
description: Master orchestrator for "Claude Explains" video production. Accepts structured input (topic, URL, title, audience level, duration) or bare topic or URL or nothing at all ("what's next"), resolves to a concrete episode spec, then orchestrates the full pipeline — research + web asset fetch, script, diagram generation, voiceover, timeline sync, assembly. Produces engagement-optimized output. Trigger on "/youtube-video-generator", or a request to make a video from a link, or "what's the next video".
---

# YouTube Video Generator — Master Orchestrator

**Master orchestrator for end-to-end video production.** Receives structured
or bare user input, resolves to a concrete episode spec, then invokes subagents
in sequence to produce research + real web assets, script, visuals, voiceover,
timeline, final video, and metadata.

**Token discipline**: wrap noisy shell calls with rtk; extract only essential
facts from URLs; never paste raw responses back. Report decisions in 1–2 lines.

---

## Accepted Input Formats

### Structured (preferred)
```
Topic: <what the video is about>
URL:   <reference page, spec, docs, GitHub release — optional>
Title: <preferred title or working title — optional>
Audience: Beginner | Intermediate | Advanced
Duration: short (60–90s) | long (≤5min)
```

All fields except Topic are optional. If Audience/Duration are missing, ask
via AskUserQuestion (2 questions, 4 options each) before proceeding.

### Bare inputs (legacy, still supported)
- **A URL alone** → treat as reference, derive topic from page.
- **A bare topic / one-liner** → derive everything else.
- **Nothing / "what's next"** → predict from playlist.

---

## Phase 1: Input Resolution (Steps 1–5)

### 1. Classify input

- Structured block (Topic: / URL: / Title: fields) → step 2.
- URL only → step 3.
- Bare topic → step 4.
- Empty / "what's next" → step 5.

### 2. Structured input

Parse all provided fields. If URL given, fetch once via WebFetch — extract
title, date, 3–5 concrete facts. Check `playlists/*.md` for near-duplicate
title before fetching. Merge extracted facts into episode brief. If Title
field given, use it as first title candidate in step 12.

### 3. URL only

Fetch once via WebFetch. Extract: announcement/docs, date, 2–3 concrete
facts. Derive topic from page title. Check `series-log.md` + `playlists/*.md`
for near-duplicates first.

### 4. Bare topic

Check `playlists/*.md` for close-match. If matched, use its
Format/Audience-Level/Focus. Else pass through as-is.

### 5. No input — predict next video

Read all `playlists/*.md`. Find first `Planned` row per series (skip
`Planned (superseded)`). If multiple series have `Planned` rows, ask user
to pick one. Cross-check `series-log.md` for duplicates. Confirm in one
line before proceeding.

---

## Phase 2: Orchestration (Steps 6–15)

### 6. Resolve episode details + read continuity

- Read `series-log.md`: detect duplicate, assign next episode number NN.
- Detect input mode (SHORT or DRAFT).
- If Audience + Duration not supplied in structured input, ask user
  (AskUserQuestion, 2 questions).
- Record: episode number, input mode, duration, audience level.

### 7. Spawn Research Agent (youtube-researcher)

**Subagent**: youtube-researcher

**Input**: topic, audience level, DRAFT content (if DRAFT mode), reference URL
facts (if any from step 2–3).

**Output**:
```
[Core facts — 5–8 bullets]
[What existing videos cover]
[Gap / differentiated angle]
[Visual reference candidates — image search terms for step 8]
[Sources]
```

The researcher MUST also return 6–10 **image search terms** — specific enough
to find real diagrams, screenshots, or photos usable as visuals. These feed
directly into step 8.

### 8. Fetch Real Web Assets

**Local step — no subagent.**

For each image search term from step 7:
1. Run WebSearch with term + site filters for high-quality sources
   (official docs, GitHub, cloud provider image libraries).
2. For each candidate URL returned, run WebFetch to confirm the image exists
   and extract direct image URL or page URL.
3. Save a reference list: `web-assets.md` in episode folder.
   Format per line: `[search-term] → [image-url-or-page-url] → [caption]`
4. Download usable images via Bash (`curl -L -o visuals/web-XX.png <url>`).
   Only download from HTTPS sources. Skip if content-type is not image/*.
5. Keep only 4–8 images max. Prefer: official architecture diagrams,
   flowcharts, comparison tables, real screenshots over stock photos.

These become candidate overlay/background assets for the asset builder.

### 9. Synthesize Script

**Local step — no subagent.** Write `script.md` using research brief +
audience level + duration + web asset references.

Fixed structure:
1. **Hook** (3s, states the question — designed as pattern interrupt)
2. **Core concept** (plain English, with concrete examples)
3. **My angle** (differentiated gap or explicit "no gap found")
4. **CTA** (dark-themed end-card, all 5 platforms, exact tag format per
   youtube-episode step 4)

**Engagement-first writing rules**:
- Hook must create a "knowledge gap" the viewer needs to fill (curiosity loop).
- Every 15–20s of narration must have a visual change (pattern interrupt).
- First 5s must state a specific outcome/promise ("By the end of this you'll…").
- Use power words in callouts: "The real reason", "Most people miss this",
  "Here's what changes everything".
- End every major section with a micro-CTA or tension hook into next section.

**Requirements**:
- Number every `[VISUAL:]` / `[ANIMATION:]` tag in script order
  (`visual-01.png`, `animation-01.mp4`).
- Annotate web assets: `[VISUAL: web-01.png — <caption>]` where applicable.
- Visual density: ~one change per 10–15s narration.
  - Short (60–90s): 6–9 total tags (1–2 animations, rest visuals).
  - Long (≤5min): 15–25 total tags (3–6 animations, rest visuals).
- Beginner: every abstract claim needs a concrete visual anchor.
- Count spoken words; stay within step-6 budget.

### 10. Delegate Asset Generation (Archify + Asset Builder)

**First**: Identify `[VISUAL:]` tags naming real system/cloud/pipeline
components. Skip tags marked as `web-XX.png` (already fetched in step 8).

**Subagent 1 (youtube-archify-diagrammer)**: Spawn for any real-world
architecture tags (AWS, Kubernetes, CI/CD, microservice graphs).

**Input**: tag description, filename, episode folder, format.
**Output**: PNG for that visual.

**Subagent 2 (youtube-asset-builder)**: After archify, spawn for remaining
visuals + animations + thumbnails.

**Input**: full `script.md`, episode folder, format, archify-generated visual
numbers to skip, web asset filenames to skip (already in visuals/).
**Output**: PNG files, silent MP4 clips, 2 thumbnail candidates in `thumbnails/`.

### 11. Generate Voiceover (Gemini TTS)

**Local step — credentials stay here.**

1. Extract narration from `script.md`:
   - Strip headers + all `[VISUAL:]` / `[ANIMATION:]` / `[CALLOUT:]` lines.
   - Join sections with one blank line between. Save as `narration.txt`.
   - Must have exactly 4 blank-line chunks.

2. Read `GEMINI_API_KEY` from `.env`. Call Gemini TTS:
   - Model: `gemini-2.5-flash-preview-tts`
   - Voice: `Puck` (male default) or user override
   - Response: base64 PCM → decode → WAV (24kHz, 16-bit, mono)
   - Write to `voiceover_raw.wav`

3. Never print API key.

4. **Slow down audio to 82% speed** (natural YouTube 1.0x pace; viewers can still
   speed to 1.25–2x):
   ```bash
   ffmpeg -y -i voiceover_raw.wav -af "atempo=0.82" voiceover.wav
   ```
   This is mandatory — Gemini Puck runs fast by default; 0.82 gives a calm,
   clear delivery. Never skip this step.

5. Check duration of `voiceover.wav` via ffprobe:
   - Short: 60–90s (before slowdown budget the script for ~50–74s raw).
   - Long: ≤5min (before slowdown budget for ≤4min raw).
   - Out of range → edit `script.md`, regenerate, re-run steps 9–11.

### 12. Build Cue Sheet (Timeline Synchronization)

**Subagent**: youtube-cue-sheet-builder

**Input**: episode folder (containing `voiceover.wav`, `narration.txt`,
`script.md`)

**Output**: `cue-sheet.json` + `cue-sheet.md`

Maps every asset/callout start/end to real audio time via local Whisper
forced-alignment (no API cost). Read `cue-sheet.md` yourself before step 13
— cheapest point to catch timing bugs.

**Sync quality check**: Verify web-fetched assets appear at the right
timestamps. A diagram should appear 0.5s before the narration that references
it (pre-cue rule). Flag any asset with duration < 3s for replacement.

### 13. Delegate Video Assembly

**Subagent**: youtube-video-assembler

**Input**: episode folder, format, duration range, cue-sheet.json.
Web assets in `visuals/` are treated identically to generated visuals.

**Output**: `episode.mp4` + `thumbnail-final.png`

Assembler reads `cue-sheet.json` directly — never recomputes timing.

**Mandatory overlay specs** (pass to assembler explicitly):

#### Callout overlays (bottom-third style)
- Position: bottom 18% of frame (y = 82% of height), horizontally centered
- Size: max 75% frame width, auto-wrap at 2 lines
- Font: bold sans-serif, 52px (not 75px — previous was too large)
- Style: white text on dark semi-transparent rounded box (rgba 0,0,0,0.72),
  4px green (#39d353) border, 16px corner radius, 24px horizontal padding
- Duration: 2.5s per callout (readable at normal pace)
- Fade: 0.2s in / 0.2s out
- No ALL-CAPS — title-case only (less aggressive)

#### Channel icon overlay (top-right corner, persistent)
- Source: `channel-icon-overlay.png` (320×60px pill badge, pre-generated)
- Position: top-right, 24px margin from both edges
- Opacity: 85%
- Present for entire video duration
- If `channel-icon-overlay.png` missing: generate it via PIL (green-dot +
  "Claude Explains" / "MCP Zero to Hero" on dark rounded pill, RGBA)

#### Visual sync quality (reference-video style)
- Every visual must appear within 0.5s of the first spoken word that
  references its content — not just within the paragraph.
- For comparison visuals (e.g. "stdio vs HTTP"): the visual should cut in
  exactly when the narrator starts that comparison.
- Assembler must report any asset it could not sync within 1s of target.

**Verify yourself**: Extract 3–4 frames via ffmpeg (static, animation,
callout, end-card). Read them. Confirm:
- No burned-in captions (YouTube auto-captions handle post-upload).
- Callouts are bottom-third, not top-center.
- Channel icon visible top-right.
- Visuals match narration per cue-sheet.

If duration out of range: back to step 11, fix script, regen voiceover +
cue sheet, re-invoke step 13.

### 14. Write Metadata (Engagement-Optimized)

**Local step — no subagent.**

Write `metadata.md`:

**Title options** (3 options):
- Option A: Curiosity gap ("Why [X] Changes Everything About [Y]")
- Option B: Outcome-first ("How to [Result] with [Topic] in [Time]")
- Option C: Contrarian ("The [Topic] Mistake Everyone Makes")
If user supplied a Title field in structured input, use it as Option A and
write B + C as alternates.

**Tags**: comma-separated YouTube tags — lead with exact certification exam
domain keywords if MCPA/exam-prep content.

**Hashtags**: 3–5 `#hashtags` — mix of broad (#AI, #MachineLearning) and
specific (#MCP, #ClaudeAI).

**Description draft**:
- First 2 lines visible before "more" fold — must contain the promise.
- Timestamps if long format.
- Full series context.

**`## Connect` footer** (fixed):
```
Connect with me:
LinkedIn: https://www.linkedin.com/in/aiops-genai-developer
Medium: https://medium.com/@soumya14041987
AWS Builder Center: https://builder.aws.com/
X: https://x.com/AIWithSoumya
GitHub: https://github.com/Soumyadip1987/mcp-zero-to-hero
```

**Publish slot**:
- `short-beginner`: Tue/Thu/Sat/Sun, 8–9 PM IST
- `long-advanced`: Saturday, 9–10 AM IST
- State which rule applied.

**Engagement checklist** (append to metadata.md):
```
## Engagement Checklist
- [ ] Hook states specific outcome in first 5s
- [ ] Curiosity gap opened in first 10s
- [ ] Visual change every 10–15s
- [ ] End-card platforms: LinkedIn / Medium / AWS / X / GitHub
- [ ] Description first 2 lines contain promise
- [ ] Pinned comment drafted (add to description as ## Pinned Comment section)
- [ ] Thumbnail contrast > 70% (bright text on dark bg)
```

### 15. Assemble Episode Folder + Log

**Local step.**

Final structure:
```
episodes/episode-NN-<slug>/
  script.md
  narration.txt
  web-assets.md          ← new: web image references
  visuals/
    visual-01.png … visual-0N.png
    web-01.png … web-0N.png   ← fetched web images
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

Clean up debug/backup copies. Then append one row to `series-log.md`:
- Episode, Slug, Title (option A), Format, Duration Pref, Slot Rule,
  Video (yes/no), Date Logged, Topic.

Run `rtk gain` once, mention token savings in one line.

---

## Quality Gates & Error Recovery

**After each agent**:
- Check output structure. Fix via SendMessage or re-invoke.
- Critical failure (no `episode.mp4`): surface clearly, do not mask.

**Staleness rule**: `script.md` edited after `voiceover.wav` exists →
both `voiceover.wav` and `cue-sheet.json` are stale and must be regenerated.

**Web asset quality rule**: Any web-fetched image < 200px wide or > 5MB
is rejected. Replace with generated visual or different web source.

---

## Avatar Integration (Optional — Step 10b)

After asset generation, if the user has requested an avatar overlay:

### What "avatar" means here
A picture-in-picture (PiP) of a male presenter appearing in the bottom-right
corner throughout the video, creating a "presenter explains" feel.

### Implementation (two paths — try A first, fall back to B)

**Path A — Higgsfield Mode B (lip-synced talking head, photorealistic)**
Requirements: Higgsfield credits + user photo.
1. Upload base `episode.mp4` + user photo via `media_upload`.
2. Run the narrator workflow `Mode B` pipeline: green-screen identity reference
   → `generate_video_batch` (28 blocks × 10s for a ~278s video, model `gemini_omni`,
   aspect_ratio `9:16`, 720p) → `voice_change` each block → composite with
   `presenter_composite.sh --style cutout --pos br`.
3. Covers full video duration; replaces original audio with voice_change'd audio.

**Path B — Local PIL avatar (immediate, no credits needed)**
Use when no Higgsfield credits available OR no user photo supplied.
1. Generate `soumya-avatar.png` using PIL: 280×320 RGBA, circular portrait with
   green ring border, illustrative South Asian male face, name badge.
   Script: see `make_soumya_avatar.py` pattern in session scratchpad.
2. Overlay onto episode.mp4 via ffmpeg:
   ```bash
   ffmpeg -y -i episode.mp4 -i soumya-avatar.png \
     -filter_complex "[1:v]scale=200:-1[av];[0:v][av]overlay=W-w-18:H-h-18:format=auto" \
     -c:a copy -c:v libx264 -crf 22 -preset fast episode_with_soumya.mp4
   ```
3. Scale: 200px wide. Position: 18px from right and bottom edges.
4. Keep original audio (voiceover.wav already composited). PIL avatar is static.

Check balance with `mcp__c12fa810__balance` before attempting Path A.
If credits = 0, go directly to Path B.

**Avatar is disabled by default** — enable only when user explicitly requests it.

---

## Script Visual-Sync Rules (Fireship/ByteByteGo style)

Script writers must follow these rules to ensure tight visual-narration sync:

1. **One visual per concept**, not per paragraph. If a paragraph covers 3
   sub-concepts, use 3 separate `[VISUAL:]` tags within it.
2. **Tag placement = where the visual should appear**. Place the `[VISUAL:]`
   tag on the line immediately before the narration sentence that references it.
3. **Example visuals must match the example**. If narration says "a GitHub MCP
   server wraps GitHub's GraphQL API", the visual must show exactly that
   (not a generic MCP diagram).
4. **Comparison visuals appear at comparison start**. "stdio vs Streamable HTTP"
   visual tag goes before "Two transport types" sentence, not after.
5. **Animations are for sequences, not facts**. Use `[ANIMATION:]` only when
   something builds step-by-step over 4–15s. Don't animate a static comparison.

---

## Out of Scope

- No YouTube upload automation.
- No auto-posting to social platforms.
- Never generate credentials or let subagents handle them.
