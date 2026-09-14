---
name: token-optimizer
description: Two-way token discipline (input filtering + output-schema capping) for any multi-subagent pipeline in this project. Not invoked standalone — referenced by youtube-episode and other skills that spawn subagents or shell out heavily.
---

# Token Optimizer — two-way discipline

Two independent levers. Both must be applied, not just one — that's the
"two-way sword": cut tokens coming IN to the main thread from tools/shell,
and cap tokens coming IN from subagent responses.

## 1. Input side — shell/tool output (via `rtk`)

This machine has `rtk` (Rust Token Killer, `~/.claude/RTK.md`) installed at
`~/.local/bin/rtk`. It filters verbose CLI output (git, ls, logs, ffmpeg
progress, etc.) down to the token-relevant part before it ever reaches
context.

- If the project's Claude Code hook already rewrites bash commands
  transparently (per the user's global `~/.claude/CLAUDE.md`/`RTK.md`),
  no action needed — every `Bash` call any subagent makes is already routed.
- If a subagent is invoked in an environment where that hook isn't active,
  it should prefix noisy commands itself: `rtk <cmd>` instead of `<cmd>`
  directly (e.g. `rtk ffmpeg -i ...`, `rtk ls -la visuals/`). Never wrap
  commands whose exact raw output is the thing being verified (e.g. reading
  back a hook's own pass/fail line) — filter noise, not signal.
- After a full episode pipeline run, `rtk gain` reports session savings —
  worth surfacing to the user once, not on every sub-step.

## 2. Output side — subagent response caps

This is enforced by contract, not by a tool: every subagent in this project
must return ONLY its declared output shape, never the intermediate
reasoning or raw tool dumps that produced it.

- `youtube-researcher` returns exactly the 4-section brief — not search
  result dumps, not page text it fetched along the way.
- `youtube-asset-builder` / `youtube-archify-diagrammer` / `youtube-video-assembler`
  return a short list of files generated (path + size/dimensions/duration)
  — never a description of what's drawn inside them; the calling skill can
  look at the file.
- The orchestrating skill (`youtube-episode`) should not paste full
  subagent output back to the user verbatim — summarize the decision it
  made off the back of that output in 1-2 lines.

Violating either side individually still leaves the other side leaking
tokens — apply both.
