# YouTube Shorts

Turn a finished episode into vertical Shorts (1080 by 1920) with one command. It runs on your computer, costs nothing, and uses the real audio timing from the episode, so voices and captions stay in sync.

## Quick use

```bash
python3 tools/dual_host/make_short.py episodes/<folder> --suggest 3          # 3 suggested clips, with reasons
python3 tools/dual_host/make_short.py episodes/<folder> --list               # every spoken line with its number
python3 tools/dual_host/make_short.py episodes/<folder> --lines 4-5 \
    --hook "What is an MCP transport?" --title "What is an MCP transport? #Shorts"
python3 tools/dual_host/make_short.py episodes/<folder> --auto 3             # build the 3 best suggestions
```

In your assistant, ask: "Make 3 Shorts from episode <folder>". The skill picks clips, writes a hook and title for each, and builds them.

## What each Short has

- A blurred copy of the slide as the backdrop, with the sharp slide on top and a slow push in.
- A red hook banner for the first 2.8 seconds. Keep it to about 8 words.
- Word by word captions, current word in yellow. Timing comes from Whisper run on the clip, matched to your script's spelling.
- A closing line, "Follow <Follow Name> for more", over the last two seconds.
- The narration and the music bed if you have one. Length is 25 to 55 seconds (change with `--min` and `--max`). The tool refuses clips of 60 seconds or more.

Output goes to `episodes/<folder>/shorts/`: `short-NN.mp4` and `short-NN.md` with the title, description, hashtags, pinned comment, upload steps and a pass or fail check list.

## Choosing good clips

A Short must make sense on its own. Good picks: a question the viewer is already asking, a surprising fact, a simple rule, a before and after. Avoid the greeting, the quiz (it needs the countdown), the end screen, and anything that starts with "as I said".
`--suggest` scores clips with simple rules (opens with a question, hook words, a number, a clean slide start). It is a starting point. Read the lines before you build.

## Posting

1. Upload the file in YouTube Studio. Vertical and under 60 seconds makes it a Short.
2. Paste the title and description from the `.md` file and add the real link to the full episode.
3. Post the pinned comment.
4. After 48 hours, look at viewed versus swiped away. Keep the hooks that held viewers.

No tool can promise views, likes or subscribers. Strong hooks, clear captions and posting often improve your chances.

## Limits

- The clip only uses the slides and audio of the episode. It does not re-shoot or re-record.
- The built-in picture area is the slide, so slides with tiny text look small on a phone. Slides with big diagrams work best.
- Whisper must be installed for exact caption timing. Without it, captions are timed inside each real line only.
- The look is the same for every Short. Change colors and sizes at the top of `tools/dual_host/make_short.py`.
