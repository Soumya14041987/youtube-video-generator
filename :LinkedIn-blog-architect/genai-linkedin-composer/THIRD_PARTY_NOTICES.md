# Third-party notices

This skill is derived in part from **linkedin-agent-skill** by Jake
Schincariol (https://github.com/Jakeschincariol/linkedin-agent-skill),
released under the MIT License. Two of that pack's skills, `li-repurpose`
and `li-human`, were used as the design basis. The code and text here were
rewritten rather than copied, but the approach, structure, thresholds and
several detection patterns follow the originals closely enough that the
MIT notice below applies.

## What is derived

| File here | Derived from | Nature of derivation |
| --- | --- | --- |
| `SKILL.md` §2b (extract-don't-summarise) | `li-repurpose` | extraction categories and the "thin source" rule |
| `scripts/humanize.py` | `li-human/humanize.py` | three-pass design (invisible chars, typography, lexicon) plus structural flagging |
| `scripts/detect.py` | `li-human/detect.py` | five-check scorer, thresholds, and mean-plus-weakest-check weighting |
| `scripts/slop.json` (`invisible`, `typographic`, `structures`) | `li-human/slop.json` | character classes and structural-tell patterns |
| `templates/voice.md` | `templates/voice.md` | section layout, extended with GenAI-specific fields |

## What is original to this skill

Discovery (`scripts/discovery.py`, `scripts/sources.json`), the shared
voice.md parser and the VOICE LOCK check (`scripts/voice.py`, `detect.py`),
the technical allowlist and flag-only lexicon mode, the GenAI/cloud
vocabulary in `slop.json`, diagram routing, and the timing reference.

## Not taken from the source pack

`li-post` (including its hook formulas) and every auto-posting or
timing-detection claim.

## MIT License (linkedin-agent-skill)

MIT License

Copyright (c) 2026 Jake Schincariol

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
