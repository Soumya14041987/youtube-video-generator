---
name: youtube-thumbnail
description: Given a finished YouTube episode (episode.mp4 already rendered), analyze the actual video and generate one final, unified, high-CTR thumbnail plus consolidated upload-ready metadata. Can be called inline by the youtube-video-generator pipeline (Step 13b) or standalone via /youtube-thumbnail for any existing episode. Trigger on "/youtube-thumbnail", or when the user asks to optimize, finalize, or strengthen a thumbnail for an existing episode.
---

# YouTube Thumbnail Optimizer

Runs as Step 13b inside the youtube-video-generator pipeline automatically,
or as a standalone pass on any existing episode via /youtube-thumbnail.

Does not touch episode.mp4. Only sharpens the thumbnail and titles that
determine CTR and algorithm reach.

## 0. Resolve the episode folder

If called inline by the pipeline: episode folder is already known — skip
to step 1.

If called standalone (/youtube-thumbnail): take folder from the argument.
If none given, read `series-log.md` and offer the most recent row's folder,
confirming with the user before proceeding.

Require `episode.mp4` and `script.md` to exist. If `episode.mp4` is missing,
stop — this command cannot run before the video is assembled.

## 1. Analyze the actual rendered video

Do not re-read script.md alone — render bugs or timing drift mean the video
may not match the script's intent. Extract 5 evenly-spaced frames via ffmpeg
and read them visually:

```bash
ffmpeg -i episode.mp4 -vf "select=eq(n\,0)+eq(n\,floor(N/4))+eq(n\,floor(N/2))+eq(n\,floor(3*N/4))+eq(n\,N-1)" -vsync 0 thumbnails/frame-%02d.png
```

If the `watch` skill is available, use it instead for a fuller read. Fall
back to frame extraction if watch is unavailable or fails.

Note the strongest visual moment, most readable diagram, best callout text,
and most distinctive on-screen element from the 5 frames.

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
`thumbnails/thumb-a.png`, `thumbnails/thumb-b.png`, `thumbnails/thumb-c.png`
— at 1280x720 (YouTube standard). Pass the 3 concrete headline/focal-point
briefs from step 2, not vague direction.

Mandatory spec for all 3:
- Dark background (#0d1117 or similar), never white or light
- Bold sans-serif text, maximum 6 words, high contrast
- Single focal point — one diagram, callout, or graphic element
- Legible at 168x94px (YouTube grid thumbnail size)
- Accent color from channel-config.md if present, else green (#39d353)

## 4. Pick the strongest one

Score each of the 3 (1-3 per criterion):
- Legible at small size: text and focal point readable at 168x94px?
- Unique on this topic: looks different from top 5 videos on same topic?
- Promises specific payoff: makes the viewer feel they gain something concrete?
- Title alignment: thumbnail concept and chosen title work as a pair?

Highest total score wins. State the one-line reason. Copy winner to
`thumbnail-final.png` at episode root. Keep all 3 in `thumbnails/`.

## 5. Consolidate metadata.md

- Rewrite title options as 3 CTR-optimized alternatives matched to the
  winning thumbnail's angle. Descriptive titles are not permitted.
  Each must contain a knowledge gap, specific outcome, or reframe.
  Under 60 characters. Lead keyword in first 3 words.
- Sanity-check tags and hashtags cover actual search terms for this topic.
- Confirm the Connect footer block is present at the end of the description.
  Read social links from channel-config.md at the project root. If missing,
  leave a placeholder comment and tell the user to configure channel-config.md.

## 6. Report

State which of the 3 thumbnails won and why, the final title picks, and
confirm the episode folder is now upload-ready.

## Out of scope

- Does not re-render or touch `episode.mp4`.
- Does not post or upload anywhere.
- If the video analysis in step 1 surfaces an actual defect in the video
  (not just a thumbnail/metadata opportunity), report it — don't silently
  fix it by re-invoking the video assembler; that's `youtube-episode`'s job.
