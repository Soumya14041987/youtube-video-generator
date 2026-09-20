---
name: lin-blog-architect
description: >-
  Turn a topic, link, or long-form asset (blog post, transcript, changelog,
  release note) into a publish-ready LinkedIn post plus a matching
  architecture diagram or infographic, for a Sr GenAI/AIOps/Kubernetes/
  Terraform/Bedrock/Agentic-AI practitioner. Given a bare topic, runs live
  discovery (Google News RSS, AWS What's New, GitHub releases for
  Kubernetes/LangChain/LangGraph/Bedrock AgentCore) instead of inventing an
  angle. Drafts against a locked voice.md profile, generates a visual for
  every post, runs a humanizer + voice-lock QA gate, and stops at a
  copy-paste block - it never posts anything itself. Use when the user says
  "turn this into a LinkedIn post", "write a post about X", "repurpose this
  blog/changelog/transcript for LinkedIn", "make me a diagram for this
  post", or invokes /lin-blog-architect.
---

# genai-linkedin-composer

A content pipeline for a senior GenAI/cloud-native practitioner: topic,
link, or long asset in — publish-ready LinkedIn post + diagram out. Every
draft passes a voice-lock and humanizer gate before it's shown. Nothing in
this skill posts, schedules, or touches a LinkedIn account — the last step
is always a block of text and a file, handed to the user to paste.

## Setup (once)

1. Copy [`templates/voice.md`](templates/voice.md) to
   `~/.claude/linkedin/voice.md` and fill it in. Every step below reads it.
   Without it, refuse to draft — ask for it instead. A thin or empty
   voice.md produces generic drafts; that's the file's whole job to prevent.
2. `scripts/discovery.py` and `scripts/detect.py --voice` need no install
   beyond Python 3 (stdlib only). If `discovery.py` reports a certificate
   error on macOS, it's this Python install's CA bundle, not the script —
   run `pip install certifi` or the interpreter's `Install Certificates.command`.
3. Diagram step (§4) needs three things outside this folder: the **archify**
   skill, Node 18+, and Google Chrome or Chromium (for `scripts/export_png.py`).
   Without archify, fall back to an image-generation infographic and say so.
   There is no bundled diagram fallback yet.
4. Review `scripts/sources.json` — the GitHub repo list in particular
   drifts; confirm the entries match the user's actual stack before relying
   on them for discovery.

## Pipeline

### 0. Voice lock gate

Before anything else, run `python3 scripts/voice.py ~/.claude/linkedin/voice.md`.
It prints what the pipeline will actually read: `banned_terms`, `focus_areas`
and `positions`. If the file is missing, or `positions` and `banned_terms`
are both empty (the blank template), stop and hand the template over instead
of drafting against nothing. An empty `banned_terms` also means the VOICE LOCK
check will silently not run, so say so rather than reporting a clean gate.

### 1. Classify the input

- **Bare topic** ("write about Kubernetes autoscaling") → discovery path.
- **Link** → fetch it, treat the fetched content as the asset → repurpose path.
- **Pasted asset** (blog, transcript, changelog, release notes) → repurpose path.

### 2a. Discovery (topic path only)

Run `scripts/discovery.py --topic "<topic>" --voice ~/.claude/linkedin/voice.md`.
It pulls Google News RSS, the AWS "What's New" feed, and recent GitHub
releases for the repos in `sources.json`, scores each by recency and
overlap with the topic and with voice.md's "My positions," and prints the
top candidates newest-and-most-relevant first.

Show the user 3-5 candidates with source links and dates. Let them pick,
or pick the top-ranked one and say why. Never invent a "what's new" claim
that isn't backed by one of these candidates or a direct web search.

### 2b. Repurpose (link/asset path)

Forked from li-repurpose's extraction pattern. Read the whole asset before
extracting anything — a summary is not a post. Pull out, with counts:

| pull | what it is |
| --- | --- |
| **Claims** | every sentence that would start an argument |
| **Numbers** | every figure, cost, duration, percentage, benchmark |
| **Stories** | every incident, migration, or postmortem with a concrete cost |
| **Mechanisms** | every "the way this works is..." explanation |
| **Mistakes** | every admission of something that broke or went wrong |
| **Lines** | every sentence already quotable as-is |

List what was found before writing anything. Fewer than four items means
the source is thin — say so rather than padding it into four weak posts.
Each extract becomes one post; each post stands alone (the reader hasn't
seen the source and never will — never write "as I covered in the
changelog").

### 3. Draft

Write the post against `voice.md`: its tone, sentence length, emoji rule,
positions, and off-limits list. Narrative or Q&A per the user's stated
default, per-post override always allowed. Technical claims come from the
source material or discovery candidate, never invented. Do not reach for
generic hook formulas — the audience is CNCF/AWS-technical, not
marketing-general; open with the specific claim or number, not a template
hook.

### 4. Visual

Generate exactly one diagram or infographic per post — see
[`references/diagram-routing.md`](references/diagram-routing.md) for the
archify-vs-infographic decision. This step is not optional; a post without
a visual is not done. After archify delivers the HTML, turn it into the
attachment with `python3 scripts/export_png.py diagram.html diagram.png`
(1200x675, dark, viewer chrome hidden).

### 5. QA gate: humanize + voice-lock

Forked from li-human's two-script pass, plus a voice-lock check this fork
adds on top.

```bash
python3 scripts/humanize.py draft.txt --report -o clean.txt
python3 scripts/detect.py draft.txt clean.txt --voice ~/.claude/linkedin/voice.md
```

`humanize.py` strips invisible characters, em dashes, curly quotes, and
the slop lexicon automatically. It never touches URLs, `code spans`,
hyphenated compounds (`force-unlock`), or the phrases in `slop.json`'s
`technical_allow` list (test harness, terraform unlock, elevated
privileges), because this audience's real vocabulary overlaps with the slop
list. Terms that are ambiguous in infra text (harness, unlock, elevate,
mission-critical, enterprise-grade, AI-powered...) are marked `"mode": "flag"`
and appear under **REVIEW**, left as written: decide each one from context.
Structural tells (rule-of-three, "not just X, it's Y," engagement bait,
buzzword stacks) are also flagged for hand rewrite, since reshaping a
sentence needs judgment a regex doesn't have. That part is the model's job.
Word swaps can still collide (`use new AI to use Kubernetes`), so always
reread the cleaned text before scoring it.

`detect.py` scores five checks (0-100, higher is more human) plus a sixth,
**VOICE LOCK**, when `--voice` is passed: it scans the draft against
voice.md's "Words I would never use" and any additional hard-fail phrases
listed there. This is the fork's addition over the source skill — a clean
humanizer score means nothing if the draft still says a phrase the user
explicitly banned.

Order of operations:

1. Run `humanize.py`, rewrite every flagged structural tell by hand.
2. Run `detect.py` with `--voice` on the cleaned draft.
3. If the verdict isn't PASS, fix the weakest named check (including
   VOICE LOCK) and rerun. Two rounds is normal. Five means the draft needs
   a rewrite, not more passes.
4. Show the user the cleaned text and the score — never the score alone.

Say honestly what this is: five local heuristics plus a keyword check
against the user's own list, not GPTZero/Originality/Copyleaks/Winston/
Turnitin, and not a promise their text is undetectable.

### 6. Timing

Suggest a posting window per
[`references/timing-heuristics.md`](references/timing-heuristics.md),
labeled explicitly as a heuristic from published best-practice data — not
an algorithm read, not a personalized prediction.

### 7. Output — hard stop

Hand back, every time:

- the final copy-ready post text, in its own block
- the diagram/infographic file
- the suggested posting window + one-line rationale
- an explicit line: **"Paste this into LinkedIn yourself — this skill
  does not post."**

Nothing in this skill calls the LinkedIn API, schedules a post, or claims
to detect the algorithm. That line is not a caveat, it's the design: a
personal-profile automation would violate LinkedIn's ToS, and no skill
anywhere actually has a working "best time to post, verified" detector —
so this one doesn't pretend to.

## Credits and what this deliberately skips

Derived in part from two skills in
[Jakeschincariol/linkedin-agent-skill](https://github.com/Jakeschincariol/linkedin-agent-skill)
(MIT): li-repurpose's extraction pattern (§2b) and li-human's humanize/detect
gate (§5). The code was rewritten, but the design follows the originals
closely, so the MIT notice is reproduced in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and must travel with any
copy of this skill. Two things from that pack are explicitly left out:

- **li-post's 21 hook formulas** - sales/marketing-toned, wrong register
  for a CNCF/AWS-technical audience. Open with the claim, not a formula.
- **Any auto-posting or "algorithm timing detected" capability** - not a
  real capability in that pack or anywhere else, and personal-profile
  automation violates LinkedIn's ToS. §6 and §7 above are the honest
  replacement for both.
