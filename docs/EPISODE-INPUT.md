# How to ask for an episode

Everything starts with one command. In Claude Code, Cursor, VS Code and Junie type `/youtube-video-generator` followed by what you want.
In tools without slash commands, write the same words in plain English, for example: "Follow AGENTS.md and make an episode about MCP transports."

## What you can type after the command

| You type | What happens |
|---|---|
| `/youtube-video-generator` and nothing else | The assistant asks how you want to start (own topic, link, next in series, or draft script) |
| `/youtube-video-generator What is the Model Context Protocol` | A topic. It researches this topic and builds the episode |
| `/youtube-video-generator https://example.com/announcement` | A link. It reads the page, pulls out the facts and builds the episode from them |
| `/youtube-video-generator https://example.com/spec  focus on what changed for beginners` | A link plus your own angle |
| `/youtube-video-generator next` or `what's next in My Series Name` | It reads your `playlists/` folder and `series-log.md`, and builds the first row marked Planned |
| `/youtube-video-generator ideas` or `give me 30 ideas about Kubernetes` | It lists 30 title ideas for you to pick from. Nothing is built until you pick one |
| `/youtube-video-generator series: My Series Name, topic: Build your first MCP server` | A topic that belongs to a named series. The series name is only used to match your playlist file and log |
| The structured form below | Everything answered up front, so it asks fewer questions |
| `/youtube-video-generator` then paste your own draft script | It keeps your wording and fills the gaps |

Structured form (every line except Topic is optional):

```
/youtube-video-generator
Topic: MCP transports, stdio versus Streamable HTTP
URL: https://example.com/spec
Title: MCP Transport Changed in 2026
Series: My Series Name
Audience: Beginner | Intermediate | Advanced | Mixed
Duration: short (60 to 90 s) | medium (3 to 5 min) | long (7 to 10 min)
Style: two hosts (default) | single narrator
```

Anything you leave out is asked as a short question, or taken from `channel-config.md`.
The assistant always stops for your approval before it spends money on voices or changes anything on YouTube.

## What a series is here

A series is a list of episodes you plan to make in order. Two plain files track it, and both stay on your computer (they are ignored by git):

- `playlists/<name>.md` is the plan. Copy `examples/playlist.md.example` to start. The assistant reads the Status column.
- `series-log.md` is the record of what you built. It sets the next episode number and catches repeated topics. Copy `examples/series-log.md.example`. The assistant creates it for you if it is missing.

Your channel and series name live in `channel-config.md` (Series Name, Series Badge, host names, length rule).

## Where the video comes from, step by step

1. Topic, link or "next" is turned into an episode brief (audience, length, goal).
2. A researcher agent collects facts and real images. Facts from links are checked against the page.
3. The script is written as slides with two speakers.
4. Slide images are drawn, then written to `episodes/<folder>/visuals/visual-01.png`, `visual-02.png` and so on.
5. The script is saved as `episodes/<folder>/dualhost.json` (format below).
6. `build_episode.py` records every line, measures the real audio, checks the words, and renders `episode.mp4`.
7. Thumbnails, upload package and readiness report are built.

You can also do steps 5 and 6 by hand. That is useful if you write your own script.

## The script file, dualhost.json

```json
{
  "episode": 1,
  "slides": [
    {
      "n": 1,
      "title": "Hook",
      "visual": "visual-01.png",
      "lines": [
        {"speaker": "alex",  "text": "Most tutorials skip one simple question."},
        {"speaker": "elena", "text": "Today we answer it in plain words."}
      ]
    },
    {
      "n": 2,
      "title": "Exam question",
      "visual": "visual-02.png",
      "lines": [
        {"speaker": "elena", "text": "Here is the question. Which option is correct?"},
        {"speaker": "alex",  "text": "The answer is B, because it matches how the protocol works."}
      ]
    }
  ]
}
```

Rules:
- `speaker` must be the lowercase first host name from `channel-config.md` (default `alex` and `elena`).
- Each slide needs a picture `visuals/<visual>` in the episode folder.
- A slide whose title contains the word Exam becomes a quiz. The first line is read, a 40 second ticking countdown runs, then the second line gives the answer. It also needs a second picture named like the first with a `b`, for example `visual-02b.png`, which shows the answer in green.
- The two hosts introduce themselves automatically. Do not add an intro.
- Keep each host's turn to about four sentences. Keep the whole episode inside your length rule.

Build it:

```bash
python3 tools/dual_host/build_episode.py episodes/episode-01-what-is-mcp
```

The builder tells you in plain words what is missing (an image, a wrong speaker name, an empty slide) before it spends anything on voices.

If your script is a Markdown file with `## EP01` sections and `#### Slide N: Title` blocks, pass `--bible your-script.md --ep 1` and the builder writes `dualhost.json` for you.
