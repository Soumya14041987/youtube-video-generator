# Troubleshooting

Start with `python3 scripts/doctor.py`. It names most problems and the fix.

## Setup

**`ModuleNotFoundError: No module named 'PIL'` (or `whisper`)**
The tools run in a different Python than the one you installed packages into. Activate your virtual environment, or run `python3 -m pip install -r requirements.txt` with the same Python.
In PyCharm set the project interpreter to your virtual environment. In VS Code pick it with **Python: Select Interpreter**.

**`OPENAI_API_KEY is not set`**
Copy `.env.example` to `.env` and add the key, or export it in your shell or IDE environment settings. Run the tool from your project folder, or set `YTVG_PROJECT` to that folder.

**The Whisper model fails to download with an SSL error**
This happens with some python.org builds, especially on macOS. Run the "Install Certificates.command" that came with your Python, or download the model once by hand:

```bash
mkdir -p ~/.cache/whisper
python3 -c "import whisper; print(whisper._MODELS['base'])"      # prints the URL
curl -L -o ~/.cache/whisper/base.pt "<the URL it printed>"
```

Without Whisper the build still works, but the sync and wording checks are skipped.

**`ffmpeg` has no `libx264` or `aac` encoder**
You have a minimal build. Install a full one: macOS `brew install ffmpeg`, Windows `winget install ffmpeg`, Ubuntu `sudo apt install ffmpeg`.

**Fonts or icons look different on Windows or Linux**
Impact and Arial Black are used when installed. Otherwise a similar bold font is used. Icons need a color emoji font (Linux: `sudo apt install fonts-noto-color-emoji`); without one a simple circle is drawn.

## Voices

**OpenAI voice request fails or says quota**
Check your OpenAI billing and limits. The builder stops with a clear message when credit is used up and resumes from the cached lines on the next run.

**Gemini voices stop after about 10 requests**
The free Gemini tier allows only 10 speech requests a day. Enable billing, or use the default OpenAI voices.

**A voice line says something different from the script**
The builder checks every line on its own and regenerates any line that matches less than 85 percent, up to three times. If it still fails, shorten that line or remove unusual symbols.

**The video is over the length limit**
Set `Episode Min Minutes` and `Episode Max Minutes` in `channel-config.md` (or leave them out for no limit), or shorten the script.

## IDEs

**The skill does not appear**
Restart the IDE. For Kiro and Junie run `python3 scripts/install_ide.py --ide kiro` (or `junie`). For Claude Code plugins run `/reload-plugins`, then `claude plugin validate .`.
Skill folder names must be lowercase with hyphens, and must match the `name` in `SKILL.md`.

**Symlink error on Windows**
The installer falls back to copying. To use links, turn on Developer Mode in Windows or run the installer as administrator, or use `--mode copy` on purpose.

**MCP server shows "needs authentication" or "failed to connect"**
Claude Code: run `/mcp` and sign in. Cursor: open the Output panel and choose **MCP Logs**. VS Code: run **MCP: List Servers** and open the logs. Kiro: check the MCP servers tab.
Remote servers need internet. If your tool does not support remote servers, use `config/mcp/bridge-for-tools-without-remote-support.mcp.json` (it needs Node and `npx`).

**VidIQ asks for a YouTube security check before it changes a video**
This is VidIQ's own multi-factor step. Complete it in your VidIQ account, then repeat the request. Updates to titles, descriptions and thumbnails also cost VidIQ credits.

**The plugin and the cloned repo both load the skills**
You installed the plugin inside a clone. Remove one of them.

## Uploading

Neither VidIQ nor this toolkit can upload the video file to YouTube. Upload `episode.mp4` yourself in YouTube Studio as Private, then paste the title, description and tags from `metadata.md`.
`python3 tools/dual_host/make_metadata.py episodes/<folder>` checks the whole package first and lists anything to fix in `upload-check.md`.
