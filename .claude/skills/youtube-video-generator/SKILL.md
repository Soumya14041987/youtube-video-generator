---
name: youtube-video-generator
argument-hint: "[topic | URL | next | ideas | Topic:/URL:/Series: fields]"
description: Master orchestrator for YouTube video production. Accepts structured input (topic, URL, title, audience level, duration) or bare topic or URL or nothing at all ("what's next"), resolves to a concrete episode spec, then orchestrates the full pipeline — research + web asset fetch, script, diagram generation, voiceover, timeline sync, assembly. Produces engagement-optimized output. Trigger on "/youtube-video-generator", or a request to make a video from a link, or "what's the next video".
---

# YouTube Video Generator — Master Orchestrator

**Toolkit root and project folder.** Paths like `tools/dual_host/...` and `scripts/...` below are relative to the toolkit root.
When this skill runs from a Claude Code plugin install, the toolkit root is `${CLAUDE_PLUGIN_ROOT}`. When the repo is cloned into your
project, it is the project folder. Your own files (`.env`, `channel-config.md`, `assets/`, `episodes/`) always live in the project
folder, which is where you start the session. Run `python3 scripts/doctor.py` once to check the setup. In a plugin install the
sub-agent names carry a prefix, for example `youtube-video-generator:youtube-researcher`; use the prefixed name when spawning them.


**Master orchestrator for end-to-end YouTube video production.** Receives structured
or bare user input, resolves to a concrete episode spec, then invokes subagents
in sequence to produce research + real web assets, script, visuals, voiceover,
timeline, final video, and metadata.

**Token discipline**: wrap noisy shell calls with rtk; extract only essential
facts from URLs; never paste raw responses back. Report decisions in 1–2 lines.


## What the user typed

The text typed after the command: $ARGUMENTS

If that line is empty or still shows the literal word `$ARGUMENTS`, nothing was typed (or this tool does not substitute it). Use the user's message instead; if it holds no topic, start at Step 1.

Read the typed text once, decide which of these it is, and skip every gate question the text already answers. Never ask for something the user already gave.

| Typed text | Treat it as | Go to |
|---|---|---|
| nothing | no input | Step 1 (workflow question) |
| starts with `http://` or `https://` | reference URL. Any words after the URL are the user's angle | Step 3 |
| `next`, `what's next`, `next in <series>` | predict from the playlist | Step 5 |
| `ideas`, `give me ideas`, `N ideas about <x>` | topic ideation. Stop after the list and wait for a pick | Step 5 |
| lines starting with `Topic:`, `URL:`, `Title:`, `Series:`, `Audience:`, `Duration:`, `Style:` | structured input | Step 2 |
| `series: <name>, topic: <x>` or `<x> for <series>` | topic that belongs to a series. Match `<name>` to `playlists/*.md` and `series-log.md` | Step 4 |
| a long pasted block of narration or slides | draft script (DRAFT mode) | Step 4 |
| any other sentence | bare topic | Step 4 |

If a URL and a topic are both given, the URL is the source of facts and the topic is the angle. If the URL cannot be fetched, say so and ask for the text instead. Do not invent facts.
If a series name is given and no `playlists/` file or log matches it, ask once whether to start a new series, then create the files from `examples/playlist.md.example` and `examples/series-log.md.example`.
Parsing never needs a question. Missing values (audience, length, style) are asked in Step 6.

---

## Accepted Input Formats

### Structured (preferred)
```
Topic: <what the video is about>
URL:   <reference page, spec, docs, GitHub release — optional>
Title: <preferred title or working title — optional>
Series: <series name — optional>
Audience: Beginner | Intermediate | Advanced | Mixed
Duration: short (60–90s) | medium (3–5 min) | long (7–10 min)
Style: two hosts (default) | single narrator
```

All fields except Topic are optional. If Audience/Duration are missing, ask
via AskUserQuestion (2 questions, 4 options each) before proceeding.

### Bare inputs, still supported
- **A URL alone** → treat as reference, derive topic from page.
- **A bare topic / one-liner** → derive everything else.
- **Nothing / "what's next"** → predict from playlist.

Full list of input forms with examples: `docs/EPISODE-INPUT.md`.

### Which pipeline
Two-host (`Style: two hosts`) is the default and is what Steps 7–10, then the Dual-Host Mode section, then Steps 13b–15 use.
Steps 11–13 below describe the older single-narrator pipeline (one voice, sub-agent assembly). Use them only when the user chooses `single narrator`.
In two-host mode the voices, cue sheet and video all come from `tools/dual_host/build_episode.py`; do not run Steps 11, 12 and 13 as well.

---

## Phase 1: Input Resolution (Steps 1–5)

### 1. Classify input + Workflow Gate

First, ask one orienting question so the user lands in the right flow:

```
AskUserQuestion:
  Q: "How do you want to start this video?"
  Header: "Workflow"
  Options:
    - "Fresh topic I have in mind"
      (description: "I'll give you a topic — you research and build everything")
    - "I have a URL or reference to base it on"
      (description: "Paste a link, announcement, or docs page — I'll extract and build from it")
    - "Predict my next video from my playlist"
      (description: "Read my playlists/ folder and pick the next planned episode")
    - "I have a draft script to finish"
      (description: "I'll paste a partial script — you fill gaps and generate assets")
```

Route based on answer:
- Fresh topic → step 4.
- URL → step 3.
- Predict next → step 5.
- Draft script → step 4 (treat pasted content as DRAFT mode input).

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

### 5. No input — predict next video OR generate ideas

If user said "what's next": Read all `playlists/*.md`. Find first `Planned`
row per series (skip `Planned (superseded)`). Cross-check `series-log.md`.
Confirm in one line before proceeding.

If user said "give me ideas" / "what should I make" / "I need topics":
Run the Topic Ideation Mode (see professor-of-how-style.md for prompt template).
Invoke youtube-researcher subagent with the ideation prompt to generate
30 curiosity-hook titles. Present to user as a numbered list. Ask user to
pick one or type their own before proceeding to step 6.

---

## Phase 2: Orchestration (Steps 6–15)

### 6. Resolve episode details + read continuity — Video Idea Gate

- Read `series-log.md`: detect duplicate, assign next episode number NN.
- Detect input mode (SHORT or DRAFT).

If Audience + Duration not already supplied, ask both together with three
additional intent questions — all five in one AskUserQuestion call:

```
AskUserQuestion (4 questions):

  Q1: "Who is this video for?"
  Header: "Audience"
  Options:
    - "Complete beginners — assume zero prior knowledge"
    - "Intermediate — familiar with the field, new to this topic"
    - "Advanced — practitioners who want depth and nuance"
    - "Mixed — pitch to beginners, reward the advanced viewer too"

  Q2: "How long should this video be?"
  Header: "Duration"
  Options:
    - "Short — 60 to 90 seconds (YouTube Shorts or punchy explainer)"
    - "Medium — 3 to 5 minutes (solid tutorial, most common)"
    - "Long — 8 to 12 minutes (deep dive, step-by-step walkthrough)"
    - "Let the content decide — script first, trim to fit"

  Q3: "What is the primary goal of this video?"
  Header: "Goal"
  Options:
    - "Explain a concept clearly (education / credibility)"
    - "Show how to do something step by step (tutorial / retention)"
    - "Cover breaking news or a trend (timeliness / discovery)"
    - "Share my take or opinion (personality / community)"

  Q4: "Where did this topic come from?"
  Header: "Origin"
  Options:
    - "My own expertise — I know this well"
    - "A gap I spotted in existing YouTube coverage"
    - "Audience question or request"
    - "It is the next episode in my planned series"

```

Record: episode number, input mode, duration, audience level, goal, origin.

Length rule: if `channel-config.md` sets `Episode Min Minutes` and `Episode Max Minutes`
(the example file uses 7 and 10), every episode must land in that range. Do not ask the
duration question then. The dual-host builder stops the build above the maximum and
warns below the minimum. With no rule set, ask the duration question as usual.
Language is always English. Script and voiceover are English-only.

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

### 9. Synthesize Script — Scripting Gate

Before writing, ask two scripting direction questions:

```
AskUserQuestion (2 questions):

  Q1: "What script style should this video use?"
  Header: "Script Style"
  Options:
    - "Deep explainer — curiosity-gap hook, twist reveal, ByteByteGo pace (default for this series)"
    - "Fast punchy narrator — short sentences, one idea per cut (Fireship style)"
    - "Step-by-step tutorial — numbered beats, show then explain (Ali Abdaal style)"
    - "Conversational take — speak directly, share opinions and examples"

  Q2: "What kind of hook should open the first 5 seconds?"
  Header: "Hook Type"
  Options:
    - "Question hook — open with a question the viewer feels they should already know"
    - "Surprising stat or fact — lead with a number or finding that reframes the topic"
    - "Bold contrarian claim — state something most people believe is wrong"
    - "Jump straight in — no preamble, first sentence is the first lesson"
```

Record script_style and hook_type. Use them to shape tone, sentence length,
and the opening lines of script.md.

**Local step — no subagent.** Write `script.md` using research brief +
audience level + duration + web asset references + script_style + hook_type.

Fixed structure:
1. **Hook** (first 5s) — opens a curiosity gap. States a question, surprising
   fact, or bold claim the viewer feels compelled to resolve. The hook title
   must also double as the clickable video title — reframe the topic as a
   mystery or a revelation, not a description.
   Bad: "MCP Server Architecture Explained"
   Good: "Why Your AI Keeps Forgetting Everything (MCP Fixes This)"
2. **Core concept** (plain English, concrete examples, visual-dense)
3. **Twist** — the mind-blowing reframe or reveal promised by the hook.
   Lands in the final third before the CTA. One specific insight that changes
   how the viewer thinks about the topic. Not a summary — a perspective shift.
   Example: "So MCP isn't about making AI smarter. It's about giving it
   a nervous system. That's the difference between a brain in a jar and
   one that can actually act in the world."
4. **CTA** (dark-themed end-card, all 5 platforms, exact tag format per
   youtube-episode step 4) — no generic "like and subscribe" lines.
   The closing line before the CTA must be memorable and standalone,
   not a setup for the subscribe button.

**Engagement-first writing rules**:
- Hook must open a named curiosity gap — state what the viewer does NOT yet
  know and why that gap matters to them specifically. Not a teaser, a promise.
- Curiosity-gap title rule: every episode title must follow one of these
  three patterns:
    - Hidden truth: "The [X] Nobody Talks About"
    - Reframe: "You've Been [Doing X] Wrong. Here's Why."
    - Stakes: "Why [X] Changes Everything About [Y]"
- Every 15–20s of narration must have a visual change (pattern interrupt).
- First 5s must name the specific outcome or revelation ("By the end of
  this you will understand exactly why...").
- Use power words in callouts: "The real reason", "Most people miss this",
  "Here is what changes everything", "This is the part no one explains".
- End every major section with a micro-tension hook pulling into the next
  section ("But here is where it gets interesting...").
- Twist must be earned — it must connect directly back to the hook's
  curiosity gap and close it with a specific insight, not a platitude.
- No generic closing lines. Last spoken sentence must work as a standalone
  thought the viewer will remember after the video ends.

**Requirements**:
- Number every `[VISUAL:]` / `[ANIMATION:]` tag in script order
  (`visual-01.png`, `animation-01.mp4`).
- Annotate web assets: `[VISUAL: web-01.png — <caption>]` where applicable.
- Visual density: ~one change per 10–15s narration.
  - Short (60–90s): 6–9 total tags (1–2 animations, rest visuals).
  - Long (≤5min): 15–25 total tags (3–6 animations, rest visuals).
- Beginner: every abstract claim needs a concrete visual anchor.
- Count spoken words; stay within step-6 budget.

### 9b. Per-Shot Storyboard Generation (Cinematic 3D Mode)

Skip this step unless visual_style is "Cinematic 3D — Professor of How style".

Read professor-of-how-style.md for the Visual Style Blueprint and per-shot
format. For each line in script.md, generate one or more shots using the
Scene ID / Line ID / Shot ID / IMAGE PROMPT / ANIMATION PROMPT structure.

Rules:
- One script line with multiple physical actions = multiple Shot IDs
- IMAGE PROMPT must use the exact technical vocabulary from the blueprint
  (volumetric lighting, PBR textures, chromatic aberration, etc.)
- Forbidden words: cool, nice, detailed, amazing
- Each IMAGE PROMPT is a single paragraph — no internal line breaks
- ANIMATION PROMPT specifies camera movement + subject motion + pacing

Save output as `storyboard.md` in the episode folder.

This storyboard replaces vague [VISUAL:] tags for the asset builder.
Pass the storyboard to youtube-asset-builder as its primary visual brief
instead of script.md visual tags. The asset builder uses IMAGE PROMPTs
to drive image generation (Higgsfield generate_image or PIL fallback).

Also generate `image-prompts-whisk.txt` at this step:
- Extract only IMAGE PROMPTs, one per paragraph, no labels, no numbering
- Separated by exactly one blank line
- Ready to paste into Midjourney, Whisk, Ideogram, or Adobe Firefly
- Save in episode folder alongside storyboard.md

### 10. Delegate Asset Generation — Image Generation Gate

Before spawning asset agents, ask two visual direction questions:

```
AskUserQuestion (2 questions):

  Q1: "What visual style should this video use?"
  Header: "Visual Style"
  Options:
    - "Dark code aesthetic — dark background, green/white diagrams, monospace labels (default)"
    - "Cinematic 3D — Professor of How style: 8K PBR render, teal/orange grade, macro fly-through"
    - "Real architecture diagrams — named AWS/Kubernetes/cloud components, accurate topology"
    - "Screenshot-heavy — real product UIs and terminal output as primary visuals"

  Q2: "How many visual changes should the viewer see?"
  Header: "Visual Density"
  Options:
    - "One key diagram — one strong visual that stays and builds on screen"
    - "Standard — one new visual or callout roughly every 12 seconds"
    - "High density — visual change every 5 to 8 seconds (fast-cut YouTube style)"
    - "Script decides — follow the visual tags I wrote, do not adjust"
```

Pass visual_style and visual_density to both subagents. If visual_style is
"Screenshot-heavy", bias web asset fetching in step 8 toward real product
screenshots over stock diagrams.

**First**: Identify `[VISUAL:]` tags naming real system/cloud/pipeline
components. Skip tags marked as `web-XX.png` (already fetched in step 8).

**Subagent 1 (youtube-archify-diagrammer)**: Spawn for any real-world
architecture tags (AWS, Kubernetes, CI/CD, microservice graphs).

**Input**: tag description, filename, episode folder, format.
**Output**: PNG for that visual.

**Subagent 2 (youtube-asset-builder)**: After archify, spawn for remaining
visuals + animations only. Do NOT ask it to generate thumbnails here —
thumbnail generation is handled exclusively in Step 13b after the video
is assembled and frames can be read.

**Input**: full `script.md`, episode folder, format, archify-generated visual
numbers to skip, web asset filenames to skip (already in visuals/).
**Output**: PNG files, silent MP4 clips. No thumbnails at this stage.

### 11. Generate Voiceover — Voice Generation Gate

Before calling Gemini TTS, ask two voice direction questions:

```
AskUserQuestion (2 questions):

  Q1: "What delivery pace should the voice use?"
  Header: "Voice Pace"
  Options:
    - "Calm and clear — 82% speed (default, works for most topics)"
    - "Slow and deliberate — 72% speed (complex technical content, non-native speakers)"
    - "Natural conversational — 90% speed (casual topics, shorter videos)"
    - "Fast and energetic — 95% speed (trends, highlights, YouTube Shorts)"

  Q2: "Which male accent should the narrator use?"
  Header: "Accent"
  Options:
    - "Male UK accent — Charon (British English, clear and authoritative)"
    - "Male India accent — Fenrir (Indian English, warm and articulate)"
    - "Male US accent — Puck (American English, deep and clear — default)"
    - "Male US accent — Orus (American English, neutral presenter tone)"
```

Single-narrator episodes: voice is always male English, no non-English languages.
Dual-host episodes (MCP Zero to Hero series and any conversational episode): see the Dual-Host Mode section below. It overrides this rule and uses one male and one female voice.
Map pace choice to atempo value: calm=0.82, slow=0.72, natural=0.90, fast=0.95.
Map accent choice to Gemini voice name. Pass both to the TTS call below.

Note: Gemini TTS accent rendering is approximate — voice names determine
tonal character more than strict phonetic accent. Test your preferred voice
on a 30-second sample before committing to a full episode.

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

### 13. Delegate Video Assembly — Editing Gate

Before spawning the assembler, ask two final production questions:

```
AskUserQuestion (2 questions):

  Q1: "How should callout text overlays appear?"
  Header: "Callout Style"
  Options:
    - "Standard bottom-third — key terms highlighted, moderate density (default)"
    - "Minimal — only the most important 2 or 3 callouts per video"
    - "Heavy — callout for every named concept (suits dense technical tutorials)"
    - "None — no callout overlays, visuals carry all context"

  Q2: "How should the video end?"
  Header: "End Card"
  Options:
    - "Full end card — social links from channel-config.md + subscribe CTA"
    - "Subscribe + next video CTA only — minimal, drives retention"
    - "Fade to black — no end card, clean finish"
    - "Loop back — last frame loops into first 3 seconds (suits Shorts)"

  Q3: "What psychological hook should lead the thumbnail? (used in Step 13b)"
  Header: "Thumbnail"
  Options:
    - "Curiosity gap — imply the answer without revealing it (default)"
    - "Bold claim — state the contrarian angle plainly"
    - "Concrete specific — show a named component, number, or before/after"
    - "Two contrasting options — the default pair, then pick one"
```

Pass callout_style, end_card, and thumbnail_hook to the assembler and forward
thumbnail_hook to Step 13b.

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
- If `channel-icon-overlay.png` missing: generate it via PIL using the
  channel name and tagline from `channel-config.md` (dark rounded pill,
  green border, RGBA). If `channel-config.md` is absent, use placeholder
  text and log a warning for the user to configure their channel details.

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

### 13b. Thumbnail Optimization (Inline — runs every episode)

Runs immediately after episode.mp4 is confirmed valid. This step is mandatory
— not optional — because thumbnail quality directly determines CTR and
therefore whether the algorithm promotes the video at all.

**Step 1 — Analyze the rendered video**

Extract 5 evenly-spaced frames via ffmpeg and read them visually:
```bash
ffmpeg -i episode.mp4 -vf "select=eq(n\,0)+eq(n\,floor(N/4))+eq(n\,floor(N/2))+eq(n\,floor(3*N/4))+eq(n\,N-1)" -vsync 0 thumbnails/frame-%02d.png
```
Read all 5 frames. Note: strongest visual moment, most readable diagram,
best callout text visible, most distinctive on-screen element. These
observations feed the concept drafting below — do not skip and draft from
script.md alone.

**Step 2 — Draft 2 CTR concepts (maximum two, never more)**

Generate exactly 2 thumbnail concepts, each anchored on a different
psychological hook. Pick the two most contrasting from this list, leading
with the hook the user chose:

A. Curiosity gap — implies an answer without giving it away.
   Title format: "The [X] Nobody Talks About" / "Why [X] Actually Means [Y]"
   Visual focal point: a diagram element that looks significant but unexplained.

B. Bold claim — states the differentiated angle of the episode plainly.
   Title format: "You've Been [Doing X] Wrong" / "[X] Changes Everything"
   Visual focal point: the twist reveal moment from the script's third section.

C. Concrete specific — a named component, number, or before/after from
   the actual video. Credible, not clickbaity. Works best for technical content.
   Title format: "[Real Named Thing] Explained in [Time]" or "[Number] Things..."
   Visual focal point: the clearest architecture diagram frame extracted above.

If thumbnail_hook was set in the Gate 6 elicitation, that type is concept 1 and
the most different remaining type is concept 2. Never produce a third. Two
choices keep the pick easy and keep VidIQ scoring cost low.

**Step 3 — Generate 2 thumbnail PNGs**

Invoke youtube-asset-builder subagent with the 2 concrete concept briefs.
Produce: `thumbnails/thumb-a.png` and `thumbnails/thumb-b.png`

Mandatory thumbnail spec (pass explicitly to asset builder):
- Dimensions: 1280x720 (all formats — YouTube standard)
- Background: dark (#0d1117 or similar), never white or light
- Text: bold sans-serif, maximum 6 words, high contrast (white or bright accent)
- Single focal point: one diagram, one callout, or one strong graphic — never
  three competing elements
- No face/avatar (unless user explicitly requested avatar overlay)
- Legibility test: thumbnail must read clearly at 168x94px (YouTube grid size)
  — large text only, no fine detail that disappears at small size
- Accent color: match channel brand from channel-config.md if present

**How to draw thumbnails (required method)**
Image models misspell text, clip it at the edges, and sometimes change letters (Episode 4 once came back as "N x 1" instead of "N x M"). So the model draws only the presenter, and the code draws everything else:
- Presenter shots live in `assets/presenter/` (thinking, skeptical, finger, curious). Make new ones with `tools/dual_host/gen_presenter.py`. They are reusable across every episode, so a normal episode costs nothing for the photo.
- `tools/dual_host/compose_thumbnails.py` draws the headline (Impact font), the red banner, icons and the series badge (from `Series Badge` in `channel-config.md`) with the episode number inside safe margins. For a new episode write `thumbnail-spec.json` (series number, plus variants `a` and `b` with presenter shot, headline lines, banner) and run `python3 tools/dual_host/compose_thumbnails.py episodes/<folder>`. Two thumbnails maximum.
- Keep headline text to about 6 words, keep it left of the face, and check the result at 168 by 94 pixels before accepting it.

**Step 4 — Score and pick the winner**

Judge each of the 2 by these criteria (score 1-3 per criterion):
- Legible at small size (168x94px): can you read the text and identify focal point?
- Unique on this topic: does it look different from the top 5 videos on this topic?
- Promises a specific payoff: does it make the viewer feel they will gain something?
- Matches the title: thumbnail concept and chosen title work as a pair?

Highest total score wins. State the one-line reason. Copy winner to
`thumbnail-final.png` at episode root. Keep both in `thumbnails/`. After the
private upload, VidIQ scoring (stage V4 below) confirms the pick.

**Step 5 — Align metadata.md titles to winning thumbnail**

Rewrite all 3 title options in metadata.md to match the winning thumbnail's
angle. If thumbnail B (bold claim) won, all 3 title variants should carry
that energy — benefit-driven, curiosity-driven, and outcome-specific.
Descriptive titles ("MCP Server Architecture Explained") are not permitted
as any of the 3 options at this point.

CTR title rules:
- Must contain a knowledge gap OR a specific outcome OR a reframe
- Under 60 characters for search truncation
- Lead keyword within the first 3 words when possible

### 14. Write the Upload Package (generated and checked by code)

Thumbnail is already finalized in Step 13b. The upload package is built by `tools/dual_host/make_metadata.py`, not typed by hand, so every episode gets the same exact layout and the same checks.

1. Write `upload-brief.json` in the episode folder. It holds only the episode-specific words: `titles` (3, best first), `target_keyword` (from VidIQ stage V1), `hook` (two lines carrying the keyword and the promise), `summary`, optional `hindi_summary` (marked as an English-language video), `learn` bullets, `chapter_titles` (one per chapter), `sources`, `next_episode`, `series_blurb`, `channel_blurb`, `quiz_cta`, `hashtags` (3 to 5), `tags`, `pinned_comment` (use `{reveal}` for the answer time), `evidence` (the VidIQ numbers), `short_window_slides`, `series_number` (published order, see channel-config.md).
2. Run `python3 tools/dual_host/make_metadata.py episodes/<folder>`. It reads the real chapter times from `cue-sheet.json`, the follow links and subscribe link from `channel-config.md`, and writes `metadata.md` and `upload-check.md`.
3. The description always follows the standard layout in `channel-config.md`: hook, summary, optional Hindi summary, what you will learn, chapters, sources, next episode, series blurb, about the channel, subscribe link, follow block, quiz ask, hashtags last.
4. VidIQ-based title choice (credits permitting): call `vidiq_generate_titles` once (5 credits) with `competitorTitles` taken from the V2 outlier results, then keep the highest scored titles that also pass the keyword rule. If credits are low, call `vidiq_score_title` once on the recommended title instead. Record the scores in `evidence`.
5. Publish slot, upload settings, the Short plan and the after-upload steps come from the generator. Do not hand-write them.

### 14b. Upload Readiness Gate (must pass before telling the user the episode is ready)

`make_metadata.py` exits with an error if anything fails. It checks: title at most 100 characters and the keyword in its first 60; keyword in the first two description lines; description at most 5,000 characters with no angle brackets; tags at most 500 characters in total; at most 15 hashtags, at least 3; chapters start at 0:00, at least 3 of them, each at least 10 seconds; the follow links and subscribe link from `channel-config.md` are present and no outdated link appears; episode numbers match the published series number; `thumbnail-final.png` is 1280 by 720 and under 2 MB; exactly two thumbnail options; the video is 7 to 10 minutes, h264 plus aac, with the index at the start, and matches the cue sheet length.

Fix every FAIL and re-run. Report any WARN to the user. The YouTube upload itself is manual (VidIQ and this tool cannot upload to YouTube): the user uploads `episode.mp4` as Private using `metadata.md`, then sends the link so the thumbnail score, pinned comment and any metadata update can be done.

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
  web-assets.md               ← web image references
  storyboard.md               ← only if visual style is Cinematic 3D
  image-prompts-whisk.txt     ← only if visual style is Cinematic 3D
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

Clean up debug/backup copies. If `series-log.md` does not exist, create it from `examples/series-log.md.example`. Then append one row to `series-log.md`:
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

## VidIQ Growth Stages (MCP Zero to Hero and any episode)

Goal of every video: maximum views, likes and new subscribers. These stages use
the VidIQ connector (tools named `mcp__...vidiq_*`). They are added around the
existing pipeline. They do not replace the builder, the OpenAI voices, the
timing checks or the local video assembly.

Not used, on purpose. VidIQ voiceover (one voice only, 14 credits per 1,000
characters, no Indian accent), VidIQ compose (capped at 240 seconds, loses exact
sync and the quiz countdown), and per-episode music (25 credits each).

Credit guard. Call `vidiq_balance` (free) before any stage that costs credits.
Never start a stage if it would leave fewer than 20 credits. Costs: outliers 5,
thumbnail score 5, publish update 5, shorts 9 per minute of source, music 25.
Keyword research cost is not listed, so check the balance before and after the
first run and note it here. Typical episode: about 35 credits.

V1. Keyword research for India (before Step 7, research)
- Call `vidiq_keyword_research` with mode country_search, keyword the episode
  topic, country IN, limit 10.
- Also call it with mode questions, language en, to find the questions viewers type.
- Keep the keyword with the highest country volume and the lowest competition as
  TOP_KEYWORD. Keep 3 to 5 question keywords for the description and the quiz.
- Save to `growth-brief.md` in the episode folder. TOP_KEYWORD goes in the title
  (within the first 3 words when it reads naturally), the first two description
  lines, the first 30 seconds of the script, and the tags.

V2. Outlier research (before Step 9, script)
- Call `vidiq_outliers` with the topic as keyword, language en, publishedWithin
  threeMonths, maxSubscribers 50000, limit 10. Cost 5 credits.
- From the results record the winning title patterns and thumbnail patterns in
  `growth-brief.md`. Use them to shape the hook and the two thumbnail concepts.
  Copy patterns, never titles or images.

V3. Metadata that serves search (Step 14, generated by code)
- Fill `upload-brief.json` from `growth-brief.md`, then run `make_metadata.py`. It builds title options, description, tags and hashtags in the standard layout and checks them. The first
  two description lines carry TOP_KEYWORD and the promise. Add chapters from
  `tools/dual_host/make_chapters.py`. Add a pinned comment that asks viewers to
  answer the quiz.

V4. Thumbnail score (after the private upload, maximum two thumbnails)
- The scoring tool needs a YouTube video ID, so the user uploads the video as
  Private first and sets thumbnail 1.
- Call `vidiq_score_thumbnail` with the video ID and the title. Cost 5 credits.
  Set thumbnail 2, score again. Keep the higher one. If both score under 70,
  regenerate only the weaker one once. Never go beyond two thumbnails.

V5. Publish metadata (only after the user approves the exact values)
- Call `vidiq_user_channels` for the channel ID. Show the user the exact title,
  description, tags and publish time. Only after they approve, call
  `vidiq_update_video` with privacyStatus private and publishAt set to the next
  slot (Tuesday or Thursday, 9:00 AM India time = 03:30 UTC unless
  `channel-config.md` says otherwise). Cost 5 credits. Never publish without approval.

V6. Shorts (free, local, built from the finished episode; do it right after the episode is built)
- Vertical 1080 by 1920 clips come from `tools/dual_host/make_short.py`. They use the real audio and cue sheet, so sync is exact. No credits are spent.
- Steps: (1) run `make_short.py <episode_dir> --suggest 3` and read the reasons; (2) read the lines with `--list` and pick up to 3 clips that make sense on their own (a question, a surprising fact, a before and after). Avoid the intro, the quiz and the end screen (the tool refuses those); (3) for each clip write a hook of at most 8 words that states the payoff or poses a question, and a title under 90 characters; (4) build with `make_short.py <episode_dir> --lines A-B --hook "<hook>" --title "<title> #Shorts"`.
- Each clip is 25 to 55 seconds, ends with a "Follow <Follow Name> for more" line, has word by word captions timed from Whisper on the clip, a blurred backdrop, a slow push in, and a red hook banner for the first 2.8 seconds.
- It writes `shorts/short-NN.mp4` and `short-NN.md` (title, description, hashtags, pinned comment, upload steps, pass or fail checks). Fix any FAIL. Report WARNs.
- Post the Short 1 to 2 days after the full episode, then paste the full video link into the Short description. Do not claim any result: views, likes and subscribers cannot be promised. After 48 hours, compare viewed versus swiped away in YouTube Studio and keep the hooks that held viewers.
- Optional paid alternative: VidIQ `vidiq_generate_clips` on the published URL (clipDuration 55, a 90 second window, about 14 credits). Use it only if the user asks. Never publish a Short without the user's approval.

V7. Music bed (one-time, reused by every episode)
- One 180 second track lives at `assets/music/bed.mp3`. The builder mixes it in
  automatically at low volume and dips it under speech. Do not generate a new
  track per episode. Delete the file to build an episode with no music.

Growth rules for the script and upload
1. The hook states the payoff in the first 15 seconds and uses TOP_KEYWORD.
2. Ask for one like right after a value moment (the quiz answer), and ask to
   subscribe once, at the end, tied to the next episode title.
3. The quiz question goes in the pinned comment, which lifts comments.
4. The end screen shows the next episode so viewers keep watching the series.
5. Length stays between 7 and 10 minutes.

---

## Dual-Host Mode (default)

Two voices share every episode. By default they are Alex (male, OpenAI voice ash) and Elena (female, OpenAI voice coral); change the names, voices and style in `channel-config.md` (`Host 1 Name`, `Host 1 Voice`, `Host 1 Style`, and the same for host 2). Voices come from the OpenAI speech model gpt-4o-mini-tts because the Gemini free tier caps speech at 10 requests per day. Gemini stays available with `--tts gemini` once billing is on.

How to run it, in order:

1. Steps 7 to 10 give the research brief, the script as slides, and one image per slide in `episodes/<folder>/visuals/visual-01.png`, `visual-02.png`, and so on. Quiz slides (title contains Exam) also need `visual-NNb.png` showing the answer in green.
2. Write the script to `episodes/<folder>/dualhost.json` using the format in `docs/EPISODE-INPUT.md`. Speakers are the lowercase host names. Do not write an intro; the builder adds it.
3. Build:

```bash
python3 tools/dual_host/build_episode.py episodes/<episode-folder>
```

If the user keeps scripts in a Markdown file with `## EPNN` sections and `#### Slide N: Title` blocks, add `--bible <file> --ep N` and the builder writes `dualhost.json` itself. The builder stops with a plain list of problems (missing image, wrong speaker, empty slide) before it spends anything on voices. Fix them and run it again.

Hard rules. Every episode must follow all of them:

1. Each spoken turn is its own text-to-speech call in the speaker's own voice. Never read both hosts with one voice.
2. Every episode opens with both hosts introducing themselves ("Hi everyone, I'm Alex." then "And I'm Elena..."), then they start explaining. The builder adds this intro automatically unless the script already has it.
3. Mix the voices intelligently: the hosts alternate, and aim for no more than about four sentences from one host before the other host takes a turn. Split long single-host blocks into shorter back-and-forth turns before generating audio.
4. Speaking speed is standard: about 150 words per minute, neither slow nor fast. The builder measures each generated line and adjusts its tempo to reach the target, so both voices match. Never fix pace with a single fixed tempo number.
5. Nothing about the hosts is shown on screen. No portraits, no name tags, no "Speaking" labels, no "Hosts" strip. Slides fill the whole frame. 
6. Slides must not show time ranges, slide timestamps, or a bottom series-name strip. Only the title card badge and the end screen may carry the series name.
7. Timing comes from real audio lengths, never from word counts. The builder adds the exact length of every generated line plus fixed gaps, builds each slide clip frame-exact, and then runs a Whisper check that stops the build if any line drifts more than one second.
8. Exact words: every line is transcribed on its own by Whisper and compared with the script. Any line below 85 percent match is regenerated automatically, up to three times, before the build continues.
9. The slide changes 0.3 seconds before the first line of that slide starts.
10. Speech requests run four at a time. A full episode takes a few minutes and costs a few cents. Never print API keys.
11. Images: architecture and flow diagrams are drawn programmatically (sharp text). Illustration-style images use the OpenAI image API (gpt-image-1) with the key from `.env`.
12. Quiz slides: when a slide title contains Exam, the question is read with no answer marked, then a 40 second countdown with a ticking sound runs (the last five ticks are higher and louder), then the correct option turns green and the explanation appears. Change `THINK_PAUSE` in the builder to alter the length.
13. Follow request, every episode: the end screen slide shows the follow handles from `channel-config.md` under "Follow <Follow Name> to reach out". The last spoken line asks viewers to follow <Follow Name> on those platforms, with links in the description. Every description ends with the follow block from `channel-config.md`. Take links only from that file. Never invent a link.
14. Episode numbers: use the published order from `channel-config.md` (for example, files EP01, EP03, EP04, EP05 may be published as Episodes 1, 2, 3, 4). Never print the folder or file id on screen, in speech, or in a description.

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
