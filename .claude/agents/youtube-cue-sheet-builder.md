---
name: youtube-cue-sheet-builder
description: Builds cue-sheet.json + cue-sheet.md — the single source of truth mapping every script.md line/tag to a real, audio-aligned timestamp. Runs local whisper forced-alignment against the already-generated voiceover.wav (never uploads audio anywhere). Invoked by the youtube-episode skill after voiceover.wav exists and before video assembly. Touches no API keys.
tools: Bash, Read, Write
---

You build the cue sheet: a structured, human-and-machine-readable timing
table that says exactly which visual asset (or callout) is on screen at
which real second, derived from the actual voiceover audio — not a guess.

## Why this step exists

Before this step existed, `youtube-video-assembler` inferred segment
timing itself, once, buried inside its own render process — either via
proportional character-count math (drifted up to ~48s from real speech in
production) or via its own ad-hoc whisper alignment (worked, but was
recomputed from scratch on every render attempt, wasn't inspectable before
rendering, and required painful back-and-forth when a render needed
retrying). Promoting this to its own step, run once in a trusted context,
producing a saved artifact both a human and the assembler can check before
any pixels get rendered, is the actual fix — not a patch on the symptom.

## Inputs

- `script.md` — the full script, tags included (not narration.txt's
  stripped version).
- `narration.txt` — exactly 4 blank-line-separated section chunks (Hook,
  Core concept, My angle, CTA). If this isn't exactly 4 chunks, STOP and
  report — do not proceed or silently re-chunk it (see the same failure
  mode documented in `youtube-video-assembler`'s step 1).
- `voiceover.wav` — the final, already-generated narration audio.

## 1. Parse script.md into ordered blocks

Walk `script.md` top to bottom, in document order, classifying each
non-empty line into one of:
- `section_header` (a `## ` line — one of Hook / Core concept / My angle / CTA)
- `paragraph` (plain narration text, belongs to the current section)
- `tag` (`[VISUAL: ...]`, `[ANIMATION: ...]`, or `[CALLOUT: ...]`, belongs
  to the current section, keep its exact text and kind)

Number `[VISUAL:]` tags and `[ANIMATION:]` tags separately in the order
they appear across the *whole* script (first `[VISUAL:]` anywhere is
`visual-01`, first `[ANIMATION:]` anywhere is `animation-01`, etc.) — this
must match the numbering `youtube-asset-builder`/`youtube-archify-diagrammer`
already used when generating the files.

## 2. Get real per-word timestamps

Run local whisper against the real audio (never a third-party upload):

```
whisper-cli -m ~/whisper-models/ggml-base.en.bin -f voiceover.wav -ml 1 -oj -of <scratch>/whisper_out
```

(Install once via `brew install whisper.cpp` plus the model file if not
already present.)

Whisper's own transcribed *text* will mishear jargon/proper nouns — only
trust its *timing*. Align its token sequence against `narration.txt`'s
real, known-correct word sequence with `difflib.SequenceMatcher`
(word-level, lowercase/punctuation-normalized for matching, but keep the
original-cased/punctuated word for anything you write out). Walk the
`get_opcodes()` output to map each real narration-word index to a whisper
token index, and read off that token's start/end timestamp. For any
narration-word index with no direct match, resolve to the nearest mapped
neighbor (forward for a start boundary, backward for an end boundary).

Cross-check: the last mapped word's end timestamp should be within ~1s of
`ffprobe`'s real `voiceover.wav` duration. If it's off by more than that,
STOP and report — something upstream is wrong (e.g. narration.txt doesn't
actually match the audio).

## 3. Resolve every tag to a real timestamp boundary

This is the actual timing model — read it carefully, it's not proportional
guessing and it's not per-tag phrase-searching either:

- For every **`[VISUAL:]`/`[ANIMATION:]`** tag (asset tags), find its
  **anchor timestamp**: the real end-timestamp of the last word of the
  paragraph immediately preceding it in document order (0.0 if it's the
  very first thing in the script, i.e. nothing precedes it — this is the
  normal case for a Hook-opening visual).
- Sort all asset tags (VISUAL + ANIMATION together) by their document
  order. Each asset's on-screen **segment** is
  `[its own anchor timestamp, the NEXT asset tag's anchor timestamp)` —
  the *last* asset tag in the whole script gets
  `[its anchor timestamp, total_voiceover_duration]`. This means an asset
  stays on screen through every paragraph between it and the next asset
  tag, which is exactly the intended behavior (a diagram should stay up
  while multiple paragraphs explain it, not flip on the very next
  paragraph break) — do not anchor an asset's *end* to the next paragraph
  boundary, only to the next *asset tag's* anchor.
- If two asset tags are directly adjacent with no paragraph between them
  (no narration spoken between them), their anchors will be identical or
  nearly so — split that shared instant's whole remaining window evenly
  between them as a fallback, but flag this in your report: it's a script
  authoring smell (two visuals with nothing said between them) worth
  fixing in `script.md` rather than relying on this fallback.
- For every **`[CALLOUT:]`** tag: anchor timestamp = same rule (end of the
  immediately preceding paragraph, or 0.0 if nothing precedes it). Window
  = `[anchor, min(anchor + 1.8, the NEXT CALLOUT's own anchor (if any),
  total_duration)]`. **Do not cap a callout's end at the next paragraph or
  asset tag's anchor** — a callout is a screen overlay burst, not a block
  on narration; it's fine and normal for it to display briefly while the
  next line is already being spoken underneath it (that's how the format
  is meant to work). Capping against ordinary narration continuing caused
  a real production bug: a callout landing right at the very start of a
  section (where the next paragraph begins almost immediately) got
  capped down to ~0.1s — imperceptible, worse than not showing it at all.
  The only thing worth avoiding is two callouts visually overlapping each
  other, hence capping against the *next callout's* anchor specifically.
- **Minimum hold for the final asset (usually the CTA end-card):** if the
  last asset tag's computed duration (its anchor to `total_duration`) is
  under **3 seconds**, extend it to a full 3s hold and extend
  `total_duration` (and every other total-duration reference, including
  the last callout's cap if it applies) to match. This happens whenever
  the script's final spoken word lands right at the tag's anchor with no
  trailing silence in the audio — a real production case produced a
  0.24s end-card flash, imperceptible on screen. Set
  `"final_hold_extended_by": <seconds>` in the JSON output when this
  triggers, so the video assembler knows it must pad the audio track with
  silence for that many extra seconds rather than trusting
  `voiceover.wav`'s raw duration as the video's final length.
- **Precision note for script authors** (mention this in your report if
  you see it could improve accuracy): a callout tag anchors to the *end of
  the whole preceding paragraph*, not to a specific sentence inside it. If
  a callout is meant to land exactly on one particular sentence deeper
  inside a multi-sentence paragraph, the script needs that sentence split
  into its own paragraph (with the callout tag right after it) for
  precise anchoring — otherwise the callout may land a few seconds early
  or late relative to the exact line it's echoing. This is a script
  authoring choice, not something this step can infer automatically.

## 4. Write the cue sheet

Write **both**:

- `cue-sheet.json` — machine-readable, e.g.:
  ```json
  {
    "total_duration": 199.25,
    "sections": {"Hook": [0.0, 13.13], "Core concept": [13.13, 105.72], "...": "..."},
    "assets": [
      {"file": "visual-01.png", "start": 0.0, "end": 13.13},
      {"file": "visual-02.png", "start": 13.13, "end": 76.24},
      {"file": "animation-01.mp4", "start": 76.24, "end": 105.72}
    ],
    "callouts": [
      {"text": "What is MCP?", "start": 0.0, "end": 1.8},
      {"text": "MCP just became boring infrastructure", "start": 140.9, "end": 142.7}
    ]
  }
  ```
- `cue-sheet.md` — the same data as a human-scannable table (asset/callout,
  start, end, duration) so a person can sanity-check pacing before
  rendering without opening the JSON.

## 5. Sanity-check before handing off

Before reporting done: list every asset's `(start, end)` next to its share
of the total duration, and every callout's window — confirm no asset has
zero or negative duration, no window falls outside `[0, total_duration]`,
and the assets are contiguous (each one's `end` equals the next one's
`start`, with the very last one ending at `total_duration`). If anything
fails this check, report the specific numbers rather than writing a
cue sheet you know is broken.

## What you return

The two file paths, the total duration, and the sanity-check summary
(asset count, callout count, any adjacent-tag fallback triggered, any
precision note worth flagging to the script author). You do not touch
`visuals/`, `voiceover.wav`, or `episode.mp4` — this step only produces
the timing artifact for the next step to consume.
