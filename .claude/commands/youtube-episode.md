---
description: Produce a full YouTube episode package (script, visuals, thumbnails, metadata) from a topic
argument-hint: [topic one-liner or paragraph]
---

If `$ARGUMENTS` is non-empty, treat it as the episode topic and invoke the
`youtube-episode` skill with it immediately.

If `$ARGUMENTS` is empty, ask the user for the topic (one-liner or
paragraph) before doing anything else — do not guess a topic.

Topic: $ARGUMENTS
