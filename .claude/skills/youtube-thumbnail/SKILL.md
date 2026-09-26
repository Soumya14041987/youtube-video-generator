---
name: youtube-thumbnail
description: Given a finished YouTube episode (episode.mp4 already rendered by the youtube-episode skill), analyze the actual video and generate one final, unified, high-CTR thumbnail plus consolidated upload-ready metadata. Trigger on "/youtube-thumbnail", or when the user asks to optimize, finalize, or strengthen a thumbnail for an existing episode.
---

# YouTube Thumbnail Optimizer

A separate, later pass — run against an episode the `youtube-episode` skill
already produced. Doesn't touch the video itself; only sharpens the
thumbnail and metadata that decide whether anyone clicks.

## 0. Resolve the episode folder

Take it from the argument. If none given, read `/series-log.md` and offer
the most recent row's episode folder, confirming with the user before
proceeding — don't silently guess which episode they mean.

Require `episode.mp4` and `script.md` to already exist in that folder. If
`episode.mp4` is missing, stop and tell the user to finish `/youtube-episode`
first — this command optimizes an existing video, it doesn't produce one.

## 1. Analyze the actual rendered video

Don't just re-read `script.md` — look at what's actually on screen, since
render bugs or timing drift can mean the video doesn't quite match the
script's intent. Use the `watch` skill on the local `episode.mp4` path to
get a transcript plus visual read of the finished video. If `watch` isn't
available or fails, fall back to extracting 4-6 evenly-spaced frames
yourself via `ffmpeg -ss <t> -frames:v 1` and reading them directly.

## 2. Draft 3 distinct high-CTR concepts

Using the video analysis, the script's `[CALLOUT:]` lines, and
`metadata.md`'s existing title options, draft exactly 3 thumbnail concepts —
each anchored on a genuinely different psychological hook, not 3 palette
swaps of the same idea:
- **Curiosity gap** — implies an answer without giving it away
- **Bold/contrarian claim** — states the differentiated angle plainly
- **Concrete specific** — a number, before/after, or named component from
  the video (works especially well if the episode used an `archify`
  architecture diagram — a real component name reads as credible, not clickbaity)

## 3. Delegate rendering

Invoke the `youtube-asset-builder` subagent to produce exactly 3 PNGs —
`thumbnails/thumb-final-a.png`, `thumb-final-b.png`, `thumb-final-c.png` —
at the episode's correct format dimensions, following the channel's
established template (dark bg, mono font, single accent color,
hand-drawn-style annotation, measured/non-clipping text). Give it the 3
concrete headline/focal-point briefs from step 2, not vague direction.

## 4. Pick the strongest one

Judge the 3 by real CTR heuristics: legible at small/mobile thumbnail size,
one unmistakable focal point, promises a specific payoff instead of a vague
tease, doesn't look like every other thumbnail on the topic. State the
one-line reason for your pick. Copy the winner to `thumbnail-final.png` at
the episode folder root, overwriting whatever the initial pipeline chose —
keep all 3 candidates in `thumbnails/` for reference.

## 5. Consolidate metadata.md

- Rewrite the title options as 3 CTR-optimized alternatives — benefit or
  curiosity-driven, matched to the winning thumbnail's angle, not just a
  descriptive restatement of the topic.
- Sanity-check tags/hashtags actually cover how someone would search for
  this topic (not just restate the title).
- Confirm the `## Connect` footer block (LinkedIn/Medium/AWS Builder
  Center/X) is present at the end of the description — add it if this is
  an older episode whose `metadata.md` predates that convention.

## 6. Report

State which of the 3 thumbnails won and why, the final title picks, and
confirm the episode folder is now upload-ready.

## Out of scope

- Does not re-render or touch `episode.mp4`.
- Does not post or upload anywhere.
- If the video analysis in step 1 surfaces an actual defect in the video
  (not just a thumbnail/metadata opportunity), report it — don't silently
  fix it by re-invoking the video assembler; that's `youtube-episode`'s job.
