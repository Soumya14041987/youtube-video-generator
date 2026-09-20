# Cue Sheet — Episode 02: Build Your First MCP Server

**Total duration:** 185.611s
**Final hold extended by:** 3.0s (end-card's raw computed duration was under the 3s minimum; video assembler must pad audio track with this much extra silence)

## Sections

| Section | Start | End | Duration |
|---|---|---|---|
| Hook | 0.000 | 9.320 | 9.320 |
| Core concept | 9.320 | 60.860 | 51.540 |
| My angle | 60.860 | 171.380 | 110.520 |
| CTA | 171.380 | 185.611 | 14.231 |

## Assets (VISUAL / ANIMATION)

| File | Start | End | Duration | % of total |
|---|---|---|---|---|
| visual-01.png | 0.000 | 9.320 | 9.320 | 5.0% |
| visual-02.png | 9.320 | 18.730 | 9.410 | 5.1% |
| visual-03.png | 18.730 | 32.360 | 13.630 | 7.3% |
| visual-04.png | 32.360 | 41.500 | 9.140 | 4.9% |
| visual-05.png | 41.500 | 50.470 | 8.970 | 4.8% |
| visual-06.png | 50.470 | 60.860 | 10.390 | 5.6% |
| visual-07.png | 60.860 | 69.260 | 8.400 | 4.5% |
| animation-01.mp4 | 69.260 | 76.540 | 7.280 | 3.9% |
| visual-08.png | 76.540 | 89.730 | 13.190 | 7.1% |
| visual-09.png | 89.730 | 105.450 | 15.720 | 8.5% |
| animation-02.mp4 | 105.450 | 118.120 | 12.670 | 6.8% |
| visual-10.png | 118.120 | 134.670 | 16.550 | 8.9% |
| visual-11.png | 134.670 | 144.340 | 9.670 | 5.2% |
| animation-03.mp4 | 144.340 | 162.170 | 17.830 | 9.6% |
| visual-12.png | 162.170 | 182.611 | 20.441 | 11.0% |
| visual-13.png | 182.611 | 185.611 | 3.000 | 1.6% |

## Callouts

| Text | Start | End | Duration |
|---|---|---|---|
| How an MCP server actually gets built | 0.000 | 1.800 | 1.800 |
| The server doesn't remember you — you remind it | 134.670 | 136.470 | 1.800 |

## Sanity check

- Asset count: 16 (13 visuals + 3 animations)
- Callout count: 2
- Assets are contiguous: each asset's `end` equals the next asset's `start`, and the last asset ends exactly at `total_duration`.
- No asset or callout has zero/negative duration.
- No window falls outside [0, total_duration].
- No adjacent-tag (zero-gap) fallback was triggered — every asset tag had at least one spoken paragraph before the next asset tag.

## Notes for script author

- **Final hold rule triggered:** visual-13 (the end-card) anchors almost exactly at the audio's real end (its preceding CTA paragraph's last word timestamp landed at/after the real `voiceover.wav` duration after whisper-timing rounding), giving it a raw computed duration near 0s. Extended to a full 3.0s hold; `total_duration` was extended from 182.611s to 185.611s to match. The video assembler must pad the audio track with 3.0s of trailing silence rather than trusting `voiceover.wav`'s raw length as the final video length.
- **Callout timing precision:** both callouts anchor to the end of the whole preceding paragraph (or 0.0 for the Hook-opening callout, which has nothing preceding it). The second callout ("The server doesn't remember you — you remind it") anchors to the end of a multi-sentence paragraph ending "...you're telling it, every single time." If this callout is meant to land exactly on a specific sentence rather than after the whole paragraph, split that sentence into its own paragraph in script.md for more precise anchoring.
- **Whisper timing drift:** the last mapped narration word's end timestamp (183.42s) was 0.809s later than ffprobe's real `voiceover.wav` duration (182.611s) — within the ~1s tolerance, but on the higher end. All tag anchors were clamped to `total_duration` where they would otherwise exceed it, to keep asset/callout windows non-negative.
