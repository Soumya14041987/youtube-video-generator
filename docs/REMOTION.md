# Videos made with Remotion

[Remotion](https://github.com/remotion-dev/remotion) draws video frames from React code. This toolkit uses it to turn a script into an animated video: code that types in, terminal commands, diagrams that build step by step, side by side comparisons and a quiz with a ticking countdown. Text is drawn by code, so every command is exact.

You only give a topic. The `remotion-video` skill does the research, the script, the voices, the render, the thumbnails and the upload text.

## Use it

In Claude Code, the Claude desktop app (Code tab) or an IDE agent:

```
/remotion-video How to build an MCP server in Python
```

In tools without slash commands, say: "Follow skills/remotion-video/SKILL.md and make a video about <topic>."

## One time setup

You need Node 18 or newer and an internet connection.

```bash
python3 tools/dual_host/render_remotion.py --setup
```

This installs the project in `tools/remotion/` and downloads Remotion's headless browser (about 170 MB). Run `python3 scripts/doctor.py` to check.

## The commands behind the skill

```bash
python3 tools/dual_host/build_episode.py episodes/<folder> --steps tts,timeline,verify   # voices and real timing
python3 tools/dual_host/render_remotion.py episodes/<folder>                              # episode.mp4 plus a still of every scene
python3 tools/dual_host/render_remotion.py episodes/<folder> --data-only                  # props file for the live preview
cd tools/remotion && npx remotion studio src/index.ts --props=out/props.json              # preview in the browser
```

Options for the renderer: `--width 1280 --height 720 --fps 30 --crf 20 --concurrency N`. A 6 minute episode took about as long as it plays or less on a laptop (about 70 frames a second in our test).

## Scene reference

Put a `scene` object on each slide in `dualhost.json`. Items appear when the spoken line they belong to starts. Give an item `"line": 0` or `"line": 1` (which line of that slide), or leave it out and items are spread across the lines in order.

Colors: `blue`, `green`, `orange`, `purple`, `red`, `yellow`.

| type | Fields |
|---|---|
| `title` | `headline` (list of 1 to 3 short lines), `subtitle`, `tag` |
| `bullets` | `items`: list of `{head, text, color, line}` (or plain strings); `banner`, `bannerColor` |
| `code` | `code` (text), `highlight` (line numbers), `codeLine` (which spoken line starts the typing), `notes`: `{head, text, color, line}`; `banner` |
| `terminal` | `commands`: `{text, line}` (a text starting with # is a comment); `hints`: `{cmd, text}` for a side panel; `banner` |
| `diagram` | `nodes`: `{label, sub, caption, color, line}` drawn left to right with arrows; `banner` |
| `compare` | `left` and `right`: `{head, color, items (list of text), code}`; `banner` |
| `quiz` | `question`, `options` (list), `correct` (0 based), `explanation`, `kicker`. The slide title must contain the word Exam. Two spoken lines: the question, then the answer. The countdown and the green reveal follow the real audio |
| `takeaways` | `items`: list of short strings |
| `end` | `nextLabel`, `nextTitle`, `cta`. The follow handles come from `LinkedIn`, `Medium` and `X` in `channel-config.md` |

Example slide:

```json
{
  "n": 4,
  "title": "The server and your first tool",
  "lines": [
    {"speaker": "alex", "text": "Import MCPServer, create one, and decorate a normal function."},
    {"speaker": "elena", "text": "The type hints become the input schema."}
  ],
  "scene": {
    "type": "code",
    "code": "mcp = MCPServer(\"demo\")\n\n@mcp.tool()\ndef add(a: int, b: int) -> int:\n    return a + b",
    "highlight": [3, 4],
    "notes": [{"head": "Type hints", "text": "a: int and b: int are the schema.", "line": 1}],
    "banner": "No schema written by hand"
  }
}
```

Scenes look the same on every episode (a theme with your series badge). To add a layout, add a component to `tools/remotion/src/Episode.tsx` and a branch for its `type`.

## Limits

- Remotion has its own licence, and some companies need a company licence. Read the [Remotion licence](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md) before commercial use at a company.
- Needs Node and a headless browser download. In a chat window with no shell (claude.ai chat, Claude desktop chat) the skill can write the files but cannot render; run the commands in a terminal.
- AI video generators such as LTX-Video and Open-Sora are a different thing: they make short clips, cannot draw exact text, and need strong GPUs. They are not part of this toolkit.
