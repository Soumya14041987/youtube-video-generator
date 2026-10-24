---
name: remotion-video
description: Make a complete animated technical video (cloud, DevOps, AWS, GenAI, agentic AI, coding tutorials) from ONLY a topic. Researches and fact-checks, writes a two-host script with animated Remotion scenes (code, terminal, diagrams, comparisons, quiz), records the voices, renders the video with Remotion, then makes thumbnails, Shorts and the upload text. Works in Claude Code (CLI), the Claude desktop app Code tab and IDE extensions. Trigger on "/remotion-video <topic>", or when the user asks for a Remotion video, an animated explainer, or a coded video about a topic.
argument-hint: "<topic>"
---

# Remotion video from a topic

The user types a topic. You do everything else. The look comes from React code (Remotion), so every command, line of code and diagram is exact, never a generated picture.
This skill uses the same toolkit as `youtube-video-generator` (voices, timing, thumbnails, upload text, Shorts). Only the picture side is different: animated scenes instead of still slides.

The topic typed after the command: $ARGUMENTS
(If that is empty or still shows the word `$ARGUMENTS`, use the user's message. If there is no topic, ask for one topic in one short question.)

**Toolkit root.** Paths below are relative to the toolkit root: the nearest folder that holds `tools/dual_host/` and `scripts/doctor.py` (the project folder, or `${CLAUDE_PLUGIN_ROOT}` in a plugin install). Your own files (`.env`, `channel-config.md`, `episodes/`) live in the project folder.

## Where this works
- Works fully where you can run shell commands and Node: Claude Code in a terminal, the Claude desktop app Code tab, VS Code, Cursor, JetBrains and other IDE agents.
- In a plain chat window with no shell (claude.ai chat, Claude desktop chat), you can still write the script and scene files, but you cannot render. Give the user the exact commands to run in a terminal.

## Rules
1. Topic only. Do not ask for audience, length, voices or style. Take them from `channel-config.md` (hosts, length rule, voice provider, target country). Ask a question only if something blocks you: a missing API key, Node missing, or an unclear topic.
2. Truth first. Facts come from official sources you fetched today. Any code shown on screen must be code you ran and saw work. Say "not tested" in the facts file for anything you did not run.
3. Cover the whole topic. Write `coverage.json` before the script and run `check_coverage.py`. A shorter video is fine; a half-covered topic is not. If it does not fit the length rule, split into Part 1 and Part 2.
4. One idea per scene. 10 to 15 scenes. Two hosts alternate; no more than about four sentences from one host in a row.
5. Timing comes from the real audio (cue sheet), never from word counts. Scene items appear when the spoken line they belong to starts.
6. Never print or log a key. Never commit private files (`python3 scripts/check_private.py --staged` runs in the git hook).
7. Stop once, after the script and the cost estimate, for the user's approval, unless they said "autopilot" or "no questions". Voices cost a little money.

## Steps

### 0. Setup check (first time only)
```bash
python3 scripts/doctor.py          # must show 0 FAIL
python3 tools/dual_host/render_remotion.py --setup   # installs the Remotion project and its headless browser; needs Node 18+ and internet
```
If Node is missing, tell the user to install it from nodejs.org and stop.

### 1. Research and fact sheet
Use the researcher sub-agent if you have one (Claude Code), otherwise search yourself. Save `episodes/episode-NN-<slug>/facts.md` with sources, verified facts, what you ran, and cautions. For code or CLI topics, run the commands and the code in a scratch folder and record the real output.
Optional: VidIQ keyword research and title scoring (see the `youtube-video-generator` skill, stages V1 to V3).

### 2. Coverage map
Save `coverage.json` (format at the top of `tools/dual_host/check_coverage.py`). List everything a viewer needs from start to finish: what it is, how it works, a worked example, how it fails, safety, and one check question.

### 3. Script with scenes
Write `episodes/episode-NN-<slug>/dualhost.json`. Each slide has `n`, `title`, `lines` (speaker is the lowercase host name) and a `scene` that says what to draw. Scene types, fields and examples are in `docs/REMOTION.md`:
`title`, `bullets`, `code`, `terminal`, `diagram`, `compare`, `quiz`, `takeaways`, `end`.
- First scene: `title`, with the payoff in the first 8 seconds. Last scene: `end`. A quiz scene needs two lines: the question (with options read aloud) and the answer; the title of the slide must contain the word Exam.
- Tie each item to a spoken line with `"line": 0` or `"line": 1`, so it appears when that sentence starts.
- Code on screen is exactly the tested code. Keep a code scene under about 14 lines.
- Do not write an introduction; the builder adds the hosts' short introduction.

Show the user a short outline (scene titles, estimated length, the voice cost) and wait for approval, unless they asked for autopilot.

### 4. Voices and timing
```bash
python3 tools/dual_host/check_coverage.py episodes/<folder>
python3 tools/dual_host/build_episode.py episodes/<folder> --steps tts,timeline,verify
```
Fix any problem it lists. If the length rule fails, shorten the script or split it.

### 5. Render
```bash
python3 tools/dual_host/render_remotion.py episodes/<folder>
```
It writes `episode.mp4` and a still of every scene in `visuals/scene-NN.png`. Look at the stills for text that overflows or overlaps; fix the scene fields and render again (a full episode renders in a few minutes). To preview live: `python3 tools/dual_host/render_remotion.py episodes/<folder> --data-only`, then `cd tools/remotion && npx remotion studio src/index.ts --props=out/props.json`.

### 6. Thumbnails, upload text, Shorts
Follow steps 13b and 14 of the `youtube-video-generator` skill: `thumbnail-spec.json` then `python3 tools/dual_host/compose_thumbnails.py episodes/<folder>`; `upload-brief.json` then `python3 tools/dual_host/make_metadata.py episodes/<folder>` (it also writes `description.txt` and `upload-guide.md`); Shorts with `python3 tools/dual_host/make_short.py episodes/<folder> --suggest 3`.

### 7. Report
Tell the user: length, voices used, coverage result, upload check result, anything not tested, and what they must do by hand (watch it once, upload as Private, send the link). Never upload or post anything yourself.

## Limits to state honestly
- Remotion has its own licence; some companies need a company licence. Read https://github.com/remotion-dev/remotion/blob/main/LICENSE.md before commercial use at a company.
- The scenes are templates: they look consistent, but they are not free-form motion graphics. For a new layout, add a scene component in `tools/remotion/src/Episode.tsx`.
- AI video generators (LTX-Video, Open-Sora) are not part of this skill: they cannot draw exact commands or diagrams, and they need strong GPUs.
