---
name: youtube-video-generator
description: Smart front-door for episode production. Accepts a bare topic, a URL (spec page, changelog, GitHub release, docs), or nothing at all ("what's next"), resolves it to a concrete, well-formed input, then hands off to the youtube-episode skill for the actual pipeline. Token-disciplined per the token-optimizer skill. Trigger on "/youtube-video-generator", or a request to make a video from a link, or "what's the next video".
---

# YouTube Video Generator — smart input resolver

This skill does not build episodes itself — it figures out **what episode
to build**, in the cheapest way possible, then invokes `/youtube-episode`
with a properly-formed input. All actual production (research, script,
assets, voiceover, cue sheet, assembly, metadata, logging) stays in that
skill; duplicating it here would be exactly the kind of redundant-pass
waste this skill exists to avoid.

**Token discipline**: this skill is a thin resolver — apply the
`token-optimizer` skill's two-way discipline throughout (rtk-wrap noisy
shell calls; when you fetch a URL, extract only the facts you need and
never paste the full page back into the conversation). Report your
resolution decision in 1-2 lines, not a transcript of how you got there.

## 1. Classify the input

- **A URL** — go to step 2.
- **A bare topic / one-liner or short paragraph** — go to step 3.
- **Nothing, or "what's next" / "next video" / similar** — go to step 4.

## 2. Input is a URL

Fetch it once (`WebFetch`). Extract only: what it announces/documents, the
date, and 2-3 concrete facts worth building an episode around — don't
paste the raw page back to the user or into the episode's research step.

This extracted summary becomes **DRAFT** input for `/youtube-episode` (the
source page already gives it a point of view and specific claims — no
need for `youtube-episode`'s own researcher to start from scratch, though
it should still run to sharpen/cross-check and catch anything the single
source missed or got wrong, exactly as DRAFT mode already does).

Check the URL's domain/topic against `series-log.md` and any
`playlists/*.md` first — if it's a near-duplicate of an existing or
planned episode, surface that the same way `/youtube-episode`'s own step 0
would, before spending a fetch on confirming what's already known.

## 3. Input is a bare topic

Before passing it straight through, check `playlists/*.md` for a title
that's a close match — if the topic matches a planned playlist item,
prefer that item's already-decided Format/Audience-Level/Focus over
re-deriving them, and say so in one line ("matches playlist item #N,
using its Format/Level"). If no match, pass the topic through to
`/youtube-episode` as-is (SHORT or DRAFT, per its own step 1 detection).

## 4. No input — predict the next video

Read every `playlists/*.md` file (there may be more than one series over
time, not just MCP: Zero to Hero). For each, find the first row still
marked `Planned` (skip `Planned (superseded)` rows — those were
intentionally dropped, not queued). If more than one playlist has a
`Planned` row, ask the user which series to continue rather than guessing
between two active series.

Cross-check the candidate against `series-log.md` (same duplicate check
`/youtube-episode` step 0 does) — if it's already been produced under a
different slug (this happened once: an episode replaced its own playlist
slot, leaving the original playlist row stale), say so and pick the next
genuinely-unproduced row instead of re-suggesting done work.

State the predicted next video in one line ("Next up: playlist item #N,
'<title>', <Format>/<Level>") and confirm with the user before invoking
`/youtube-episode` — predicting wrong here wastes a full production run,
so this is worth one confirmation even though step 4 elsewhere in this
skill doesn't require it.

## 5. Hand off

Invoke the `youtube-episode` skill with the resolved topic/DRAFT content.
Do not re-implement any of its steps here — this skill's job ends at
producing a well-formed input for it.
