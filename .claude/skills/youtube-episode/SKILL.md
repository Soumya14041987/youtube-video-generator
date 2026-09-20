---
name: youtube-episode
description: Turn a topic (one-liner or paragraph) into a complete, ready-to-upload YouTube episode package for the "Claude Explains" channel — researched script, a real-audio-aligned cue sheet, generated visuals, thumbnails, a rendered faceless .mp4 with AI voiceover (no burned-in captions — YouTube's own automatic-captions handles that post-upload), and upload metadata with hashtags. Trigger on "/youtube-episode", or when the user gives a topic and asks for an episode, video script, or YouTube content.
---

# YouTube Episode Pipeline — "Claude Explains"

Produces everything up to the upload click: script, real image assets,
thumbnails, a rendered narrated `.mp4`, and metadata. Faceless format (AI
voiceover over visuals, no avatar) — you still upload manually.

Model staging across stages (see `token-optimizer` skill for the token
side of this): **simple/structured tasks run on Sonnet 5** — research,
asset rendering, and archify diagram authoring. **The complex task (video
assembly) runs on Opus 5** — multi-segment timing, overlay composition, and
crop math proved too failure-prone on a lighter model in production. Script
synthesis (step 4) is done by whichever model is running this skill —
there's no way for a skill file to switch the main thread's model
mid-conversation, so for best script quality **run `/youtube-episode` itself
while on Sonnet 5 or Opus 5**.

## 0. Read continuity file first

Read `/series-log.md` before anything else.
- Check the topic against existing rows to avoid duplicating a covered topic.
  If it looks like a near-duplicate, tell the user which prior episode
  overlaps and ask whether to proceed, angle it differently, or skip.
- Determine the next episode number = highest existing episode + 1
  (zero-padded to 2 digits, e.g. `03`). If the file has no rows, start at `01`.
- If `/series-log.md` is missing or its table is unparseable, stop and tell
  the user — do not silently recreate it (it's the only cross-session
  continuity mechanism; guessing the next episode number wrong causes
  collisions).

## 1. Detect input mode

- **SHORT** — a one-liner or bare topic name, no real structure or opinion
  given. Needs broad research from scratch.
- **DRAFT** — a paragraph or more that already contains a point of view,
  structure, or specific claims. Needs tightening/structuring more than
  fresh research.

State which mode you detected and why, in one line, before continuing.

## 2. Ask duration + audience level (one AskUserQuestion call, two questions — always ask unless both already given)

**Question 1 — duration** (max 3 options): this sets the word budget for
step 4 and the duration target for step 6.

- **Short (60-90s)** — YouTube Shorts have a **60-second floor**, not a
  ceiling — a 42-45s video is genuinely too short to count. Target
  ~165-185 spoken words total across all 4 sections (natural pace lands
  that around 65-75s, comfortably clear of the floor with room for pauses).
- **Long (≤5min)** — target ~650-750 spoken words total
- **Auto-detect** — pick short vs long yourself from topic complexity (a
  one-fact concept → short; anything needing real walkthrough/nuance →
  long), and say which you picked and why

Whichever is chosen, write to fill the range, not pad past it — the goal is
"exact gist, nothing boring," but for Short that gist must still clear 60s.
Count words before moving on; if the draft comes in under ~160 words for
Short, the angle section is almost always the one that's too thin — expand
it, don't pad the hook or CTA.

**Question 2 — audience level** (max 3 options): this sets step 4's
vocabulary/analogy rules and step 4's minimum visual-density target.

- **Beginner** — assume zero prior familiarity with the topic. Every
  technical term gets defined in plain words the first time it's used, and
  every abstract concept gets a concrete real-world analogy (the way "the
  M×N integration problem" only lands once you've shown the USB-C/multiple
  incompatible phone-charger problem next to it — an abstract claim without
  a paired analogy is a Beginner-episode defect, not a stylistic choice).
  No unexplained acronyms, no assumed prior tools/protocols knowledge.
- **Intermediate** — some jargon is fine with a brief inline gloss; assumes
  the viewer knows adjacent concepts (e.g. "an API," "a protocol") without
  needing them re-explained from zero.
- **Advanced** — full technical depth, no hand-holding (this is what
  episode 01's SRE/session-affinity/load-balancer framing was — assumes a
  practitioner audience).

Auto-detect is not offered for this question — the presenter (you, the
user) knows their intended viewer better than topic complexity alone can
infer; always ask.

## 3. Delegate research

Invoke the `youtube-researcher` subagent with the topic (and, in DRAFT mode,
the user's paragraph as context to verify/sharpen rather than replace).
Do not do the research yourself and do not let this subagent write any
script prose — it returns a structured brief only:
`[Core facts] [What existing videos already cover] [The gap / differentiated angle] [Sources]`.

## 4. Synthesize the script

Write `script.md` using this fixed structure, and no other structure:

1. **Hook** — first 3 seconds, states the question the video answers.
2. **Core concept** — the plain-English answer.
3. **My angle** — the differentiated point the researcher's brief flagged as
   missing from existing coverage. If the brief found no real gap, say so
   explicitly rather than inventing one.
4. **CTA** — follow/next-episode tie-in. The CTA's `[VISUAL:]` end-card
   must show all 5 platforms on screen (LinkedIn, Medium, AWS Builder
   Center, X, GitHub) as a **dark-themed card grid** — not the old plain
   white-background text list, which looked disconnected from every other
   dark-bg frame in the video and undersold the channel. **The tag text
   must spell out the correct handle for each platform individually,
   verbatim, exactly as below, and must spell out the channel wordmark
   text explicitly too — never just say "channel wordmark" and leave the
   actual text to be inferred.** Three real production bugs came from
   under-specifying this tag: (1) writing only `LinkedIn · Medium · AWS
   Builder Center · X — @AIWithSoumya` let the asset builder reuse the one
   visible handle for all platforms, mislabeling LinkedIn and Medium; (2)
   writing "channel wordmark" without its literal text produced an
   end-card headlined with the *episode's own series title* instead of the
   channel name, and a bare AWS Builder Center row with no value; (3) a
   plain white-bg text-list design read as generic and inconsistent with
   the rest of the video. The asset builder has no other source for any of
   this at generation time — `metadata.md`'s Connect footer, which has the
   correct values, is written later in step 9. Copy this exact tag text
   every time, don't paraphrase or drop any value down to just a platform
   name:
   ```
   [VISUAL: end-card — dark #0d1117 background (matching every other frame in the video, not white), the literal text "AI WITH SOUMYA" as a large centered channel wordmark (this is the channel name, not the episode or series title — never substitute the episode/playlist title here) with a thin accent-color underline beneath it, a small series tag below that reading "MCP : ZERO TO HERO", then a horizontal row of 5 rounded platform cards, each with a colored top accent bar in that platform's brand color, a circular monogram/initial in the same color, the platform name, and its handle: LinkedIn (blue, aiops-genai-developer) · Medium (white, @soumya14041987) · AWS Builder Center (orange, builder.aws.com) · X (white, @AIWithSoumya) · GitHub (light blue, mcp-zero-to-hero) — every card gets a label AND a value, none bare — and a bold accent-outlined CTA box beneath the cards reading "FOLLOW FOR THE NEXT EPISODE". Same design every episode uses.]
   ```
   or stacked as 4 short lines if that reads better at the format's aspect
   ratio (still one label-and-value pair per line, never just a platform
   name with nothing after it). These 4 values
   are fixed for this channel — never invent or infer a handle for any of
   them.

Inline three kinds of tags — the handoff contract to the asset builder and
video assembler, so be concrete (not just "diagram here"):

- `[VISUAL: description]` — a static diagram/comparison table/flow that
  doesn't need to move. **If it names real system/cloud/pipeline components**
  (AWS/GCP/Azure services, Kubernetes topology, CI/CD pipeline, a data
  pipeline, microservice call graph — not an abstract 2-4-box concept),
  flag it as real-world in your own notes when you get to step 5 — it goes
  to `youtube-archify-diagrammer`, not the general asset builder.
- `[ANIMATION: description]` — a diagram that builds or moves over time
  (nodes appearing one by one, an orbit rotating, a graph's bars/line
  growing, a flow lighting up step by step). This is the channel's signature
  visual now (see the reference "Model" orbit diagram this format is modeled
  on) — every episode should have at least one.
- `[CALLOUT: exact short phrase]` — a big bold on-screen text burst timed to
  a punchy line (e.g. the hook question, or the angle's payoff sentence).
  Not a caption paraphrase — the exact words as they should appear on
  screen, short enough to read at a glance (≤8 words). Use 1-2 per episode:
  the hook line is a natural first callout, the angle's key sentence a
  natural second one.

**Visual density budget — target roughly one `[VISUAL:]`/`[ANIMATION:]`
change every 10-15 seconds of narration, not one per section.** A sparse
script (a handful of tags across a whole Long episode) reads as visually
static even with Ken Burns pan — verified against a real successful
beginner-explainer benchmark in this niche (~1 visual change every ~13s).
Concrete minimums by duration:
- **Short (60-90s):** 6-9 total `[VISUAL:]`/`[ANIMATION:]` tags combined
  (still just 1-2 of those as `[ANIMATION:]`, each 3-6s — the rest are
  `[VISUAL:]`).
- **Long (≤5min):** 15-25 total tags combined (3-6 of those as
  `[ANIMATION:]`, each 3-6s — the rest `[VISUAL:]`).

Hit this by breaking each paragraph's ideas into more, smaller visual
beats rather than one diagram covering three sentences — e.g. instead of
one architecture diagram sitting through an entire multi-sentence
explanation, introduce it as a simpler 2-box `[VISUAL:]`, then a follow-up
`[VISUAL:]` a sentence later that adds the next piece, rather than one
diagram doing all the work silently for 60+ seconds. This also gives
`youtube-cue-sheet-builder` (step 7) more anchor points, which makes
timing more precise, not just busier.

**If audience level (step 2) is Beginner: every abstract or technical
claim needs its own concrete visual anchor, not just narration.** This is
the actual mechanism that makes "complex topic, simple terms" real instead
of aspirational — a claim like "this solves the M×N integration problem"
lands as an abstraction unless paired with a `[VISUAL:]`/`[ANIMATION:]`
showing the concrete before/after (many tangled connections → one shared
hub), the same way a real-world analogy (multiple incompatible phone
chargers → one USB-C) does more work than the technical claim alone. Write
the analogy into the narration AND give it its own tag — don't rely on the
viewer to picture it unaided. For Intermediate/Advanced, an analogy is
still encouraged for the single hardest idea in the episode, but not
mandatory throughout.

Write the hook and angle lines with punchy, high-energy phrasing suited to
being a `[CALLOUT:]` on screen, not just narration — short declarative
sentences beat long explanatory ones here. Keep total spoken word count
inside the step-2 budget — count it before moving on.

## 5. Delegate asset generation

First, number every `[VISUAL:]`/`[ANIMATION:]` tag in script order (the
first `[VISUAL:]` anywhere is `visual-01.png`, the first `[ANIMATION:]`
anywhere is `animation-01.mp4`, etc. — both subagents below need this same
numbering to agree).

**If any `[VISUAL:]` tag names real system/cloud/pipeline components**,
invoke `youtube-archify-diagrammer` first, passing it: that tag's exact
description, its assigned `visual-0N.png` filename, the episode folder
path, and the format. It returns that specific PNG, built via archify
rather than hand-drawn.

Then invoke `youtube-asset-builder` for everything else, passing it:
- the full `script.md` (for its `[VISUAL: ...]` and `[ANIMATION: ...]` tags)
- the target episode folder path
- whether this is short-form (1080x1920) or long-form (1280x720 thumbnails)
- which `visual-0N.png` numbers archify-diagrammer already produced (skip
  those)

It returns real PNG files in `visuals/` for each remaining `[VISUAL:]`,
real short silent `.mp4` clips in `visuals/` for each `[ANIMATION:]`, and 2
thumbnail PNGs in `thumbnails/` (bold-callout-text + hand-drawn-arrow
annotation style) — never accept a text description back as if it were a
finished asset from either subagent.

With step 4's density budget (up to 15-25 tags for Long), most `[VISUAL:]`
tags are simple, cheap, small-element cards (a 2-3 box addition, not a full
new diagram) — the asset-builder can and should batch these efficiently
rather than treating each as a from-scratch composition; only tags that
genuinely name real infra get the heavier archify path.

## 6. Generate the voiceover yourself (do not delegate this part)

Credentials never go to a subagent — a subagent has twice mishandled
`GEMINI_API_KEY` in practice (once blocked by the platform's own
credential-protection layer, once printed the raw key into its report
despite being told not to). Generate `voiceover.wav` yourself, in this
same trusted context:

1. Extract narration text from `script.md`'s Hook/Core-concept/My-angle/CTA
   sections: for each of the 4 sections, strip its header and every
   `[VISUAL:]`/`[ANIMATION:]`/`[CALLOUT:]` tag line, then join that
   section's *remaining* lines into one continuous paragraph with single
   spaces (not blank lines) — a section's prose must become one unbroken
   block, never multiple blank-line-separated fragments. Only then join the
   4 resulting section-paragraphs together with exactly one blank line
   between each, and save as `narration.txt`. The file must contain
   **exactly 4** blank-line-separated chunks — count them
   (`narration.split("\n\n")`) before calling the TTS endpoint; anything
   else means a section's internal line breaks leaked through as extra
   chunk separators. This exact bug happened in production once: joining
   every stripped *line* with blank lines (instead of every *section*)
   produced 10 fragments instead of 4, which fed spurious pause breaks into
   the TTS audio itself (unnaturally choppy pacing, not just a metadata
   problem) and threw off every downstream section-boundary timestamp the
   assembler relies on.
2. Read `GEMINI_API_KEY` from `.env` yourself and call the Gemini TTS
   endpoint directly (`gemini-2.5-flash-preview-tts`, `responseModalities:
   ["AUDIO"]`, `voiceConfig.prebuiltVoiceConfig.voiceName: "Puck"` by
   default — a male voice, the channel's standing choice from episode 3
   onward; episodes 1-2 used the earlier default, "Kore," a female voice)
   — use Python's `requests` library, not bare `urllib`, if you hit
   an SSL cert verification error. Decode the base64 PCM response and write
   it as a real WAV (24kHz, 16-bit, mono) to `voiceover.wav`.
3. Never print the key value anywhere in your output.
4. Check `ffprobe`'s duration against step-2's range yourself. For Short,
   that's **60-90s — both directions matter**: under 60s, expand the
   angle section (the weakest, thinnest one is almost always there) and
   regenerate; over 90s, trim the weakest section and regenerate. For
   Long, the cap is ≤5min, ceiling only. Don't hand an out-of-range track
   to the assembler and hope it's caught downstream.

If `GEMINI_API_KEY` is missing entirely, stop and tell the user to set it
(env var or project-root `.env` file) — do not fabricate audio, do not fall
back to any OS/local TTS, do not ship a silent video.

**Staleness rule**: if `script.md` is ever edited *after* `voiceover.wav`
already exists (e.g. a fact-check correction, a reworded callout), both
`voiceover.wav` and `cue-sheet.json` (step 7) are now stale and **must**
be regenerated before assembly — a script edit changes word timing, which
invalidates every downstream timestamp. Never hand the assembler an old
cue sheet against a newer script; check `script.md`'s mtime against
`voiceover.wav`'s before invoking step 8 if there's any doubt.

## 7. Build the cue sheet

Invoke the `youtube-cue-sheet-builder` subagent, passing it the episode
folder path (containing the just-generated `voiceover.wav` and
`narration.txt`, plus `script.md`). No credentials involved, safe to
delegate. It runs local whisper forced-alignment against the real audio
and writes `cue-sheet.json` + `cue-sheet.md` — the single source of truth
for exactly which asset/callout is on screen at which real second.

This step exists because the video assembler (step 8) used to infer this
timing itself, invisibly, once per render attempt — which is what let a
proportional-character-count guess drift up to ~48s from real speech, and
let a real-world architecture diagram get shown before its own narration
ever introduced it (a *placement* bug, not a timing-math bug, but the same
root cause: nothing forced the visual assignment to answer to the actual
audio before rendering). Read `cue-sheet.md` yourself before moving on —
it's the cheapest point in the whole pipeline to catch a bad pairing (e.g.
an asset given a suspiciously long or short window, or a callout landing
somewhere that doesn't match its narration line) before spending a render
on it.

If the builder flags an adjacent-tag fallback or a callout-precision note,
decide whether to fix `script.md` (e.g. split a paragraph so a callout
anchors more precisely) and re-run steps 6-7, or accept the current cue
sheet and proceed — don't silently ignore the flag either way.

## 8. Delegate video assembly

Invoke the `youtube-video-assembler` subagent, passing it:
- the episode folder path (containing `voiceover.wav`, `narration.txt`,
  and `cue-sheet.json` from steps 6-7, plus the assets from step 5)
- format (`short` = 1080x1920 video, or `long` = 1920x1080 video)
- the duration range from step 2 (60-90s for short, 0-300s for long)

It reads `cue-sheet.json` directly for every asset's and callout's
start/end (it does **not** recompute timing itself — see its own
instructions), splices `[VISUAL:]` PNGs (Ken Burns pan, with a
background-color safety margin padded in first so crop never touches real
content) and `[ANIMATION:]` clips (played at native speed, trimmed/looped
to their cue-sheet duration) in that order, burns in `[CALLOUT:]` bursts
(upper third, never dead-center — that collides with centered animation
content) via PIL-rendered transparent-PNG overlays (this ffmpeg build has
no libass/libfreetype, so `subtitles=`/`drawtext=` don't work — don't let
it try them), and returns `episode.mp4` and `thumbnail-final.png`. **No
captions are burned in** — that's a standing default now, not an
oversight; YouTube's own automatic-captions feature generates and syncs
captions against the uploaded audio track post-upload instead. It never
touches `GEMINI_API_KEY` or generates audio — if it ever tries to, stop
it; that's step 6's job. If it reports the narration is outside the
duration range, that means step 6's check was wrong — go back, fix
`script.md`, regenerate `voiceover.wav` and `cue-sheet.json` (steps 6-7),
then re-invoke this step.

**Verify the actual output yourself before trusting any report** — extract
3-4 frames with `ffmpeg -ss <t> -frames:v 1` covering a static segment, an
animation segment, and each callout window, and `Read` them. Confirm no
caption text appears anywhere (standing default is off) and that each
frame's visual actually matches what's being narrated at that timestamp
per `cue-sheet.md`. Subagent self-reports on this specific step have been
wrong before (claimed fixes that weren't applied, claimed captions burned
that weren't, fabricated a substitute TTS engine once, and — the specific
bug this cue-sheet step was built to prevent — a real diagram shown before
its own narration ever explained it). Confirmed on disk beats confidently
reported.

## 9. Metadata and scheduling

Write `metadata.md` with:
- 2-3 title options
- tags (comma-separated, for the YouTube tags field)
- a `## Hashtags` section (3-5 `#hashtags` for the description/pinned comment)
- a description draft
- a `## Connect` footer block appended to the end of the description, always
  exactly this (same every episode, verbatim):
  ```
  Connect with me:
  LinkedIn: https://www.linkedin.com/in/aiops-genai-developer
  Medium: https://medium.com/@soumya14041987
  AWS Builder Center: https://builder.aws.com/
  X: https://x.com/AIWithSoumya
  GitHub (series code + episode assets): https://github.com/Soumya14041987/mcp-zero-to-hero
  ```
- a recommended day/time slot

Apply exactly one of these rules, and always state in `metadata.md` which
one applied and why:

| Content type | Slot | Rule name |
|---|---|---|
| Short-form, beginner concept | Tue / Thu / Sat / Sun, 8-9 PM IST | `short-beginner` |
| Long-form, advanced or personal-workflow content | Saturday, 9-10 AM IST | `long-advanced` |

Never output a slot recommendation without naming which rule fired. If the
episode doesn't cleanly fit either (e.g. long-form beginner content), say so
and pick the closer rule explicitly rather than silently defaulting.

## 10. Assemble the output folder

Every episode lives under a single `episodes/` directory at the project
root — never loose at the project root itself. This keeps the root to just
skill config (`.claude/`, `series-log.md`, etc.) even as episode count
grows; `episodes/episode-01-...`, `episodes/episode-02-...` and so on
accumulate in one place instead of cluttering the top level.

`episodes/episode-NN-<slug>/` (NN = zero-padded episode number, slug =
kebab-case topic) should now contain:

```
episodes/episode-NN-<slug>/
  script.md
  narration.txt          (stripped, section-joined narration text baked into voiceover.wav)
  visuals/               (real PNGs for [VISUAL:], real silent .mp4 clips for [ANIMATION:])
  thumbnails/            (2 candidate PNGs, bold-callout + hand-drawn-annotation style)
  thumbnail-final.png    (the one video-assembler picked)
  voiceover.wav           (Gemini TTS narration, standalone)
  cue-sheet.json          (machine-readable timing — every asset/callout's real start/end)
  cue-sheet.md            (human-readable version of the same)
  episode.mp4             (final rendered video — no burned-in captions)
  metadata.md
```

Don't leave debug/backup copies (e.g. a superseded `voiceover-old-*.wav`
kept during a bugfix) sitting in the episode folder once the fix is
verified — clean those up as part of finishing the fix, not left for a
later cleanup pass.

## 11. Log the episode

Append one row to `/series-log.md`'s table — do not rewrite existing rows,
do not renumber anything, only add. Columns: Episode, Slug, Title (pick the
first title option), Format (short/long), Duration Pref (`short-60to90s` /
`long-5min`), Slot Rule Applied, Video (`yes` once `episode.mp4` exists,
never mark it `yes` before the file is actually on disk), Date Logged
(today's date), Topic (the original one-liner/paragraph, trimmed).

A hook validates the file immediately after this write and will surface an
error if the table becomes malformed or an episode number collides — if that
happens, fix the row you just added rather than touching any other row.

## 12. Token savings note (optional, once per run)

If `rtk` is installed, run `rtk gain` once at the end and mention the
savings figure to the user in one line — see the `token-optimizer` skill
for the full input/output discipline this pipeline follows.

## Out of scope (do not build or attempt)

- No YouTube upload automation / no MCP server for posting — mention it as a
  possible future phase if relevant, don't build it.
- No talking-avatar rendering — this is a faceless format (voiceover over
  visuals). If the user wants an avatar later, that's a separate,
  bigger build (HeyGen/D-ID integration + likeness setup).
- No auto-posting to any social platform.
