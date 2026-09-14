---
description: Analyze a finished episode's rendered video and generate one final, unified, high-CTR thumbnail plus consolidated upload metadata
argument-hint: [episode folder path]
---

If `$ARGUMENTS` is non-empty, treat it as the episode folder path and invoke
the `youtube-thumbnail` skill with it immediately.

If `$ARGUMENTS` is empty, read `/series-log.md`, offer the most recent
episode as the likely target, and confirm with the user before proceeding —
do not guess silently.

Episode folder: $ARGUMENTS
