# Install and configure in your IDE

This guide shows how to use the YouTube Video Generator in Claude Code, VS Code, Cursor, Kiro, PyCharm and other agentic tools.
Details were checked against each tool's official documentation on 2026-10-03. These tools change quickly, so each section
links to the official page. If something here no longer matches, trust the official page and open an issue.

## Which tool reads what

| Tool | Loads the skills from | Instruction file it reads | MCP settings file | Sub-agents | Extra install step |
|---|---|---|---|---|---|
| Claude Code (terminal, VS Code, JetBrains) | `.claude/skills` | `CLAUDE.md` (imports `AGENTS.md`) | `.mcp.json` or `claude mcp add` | Yes (5) | none, or the plugin |
| VS Code with Copilot | `.claude/skills`, `.agents/skills`, `.github/skills` | `.github/copilot-instructions.md`, `AGENTS.md` | `.vscode/mcp.json` or `.mcp.json` | No | none |
| Cursor | `.claude/skills`, `.agents/skills`, `.cursor/skills` | `.cursor/rules/*.mdc`, `AGENTS.md` | `.cursor/mcp.json` | No | none |
| Kiro | `.kiro/skills` only | `.kiro/steering/*.md`, `AGENTS.md` | `.kiro/settings/mcp.json` | No | run the installer |
| PyCharm with Junie | `.junie/skills`, `.agents/skills` | `.junie/AGENTS.md` or `AGENTS.md` | `.junie/mcp/mcp.json` | No | run the installer |
| Codex CLI, Zed, Warp, Aider and others | varies | `AGENTS.md` | varies | No | none |

Sub-agents are a Claude Code feature. In every other tool the agent does those steps itself, in order, by following
`.claude/skills/youtube-video-generator/SKILL.md`. The result is the same files. It is just one agent doing all the steps.

## Before you start (all tools)

You need Python 3.10 or newer, ffmpeg, and an OpenAI API key. Node 18 or newer is needed only for the architecture diagram skill (Archify).

macOS or Linux:

```bash
git clone https://github.com/Soumya14041987/youtube-video-generator.git
cd youtube-video-generator
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                              # then open .env and add OPENAI_API_KEY
cp channel-config.md.example channel-config.md    # then fill in your channel details
python3 scripts/doctor.py
```

Windows PowerShell:

```powershell
git clone https://github.com/Soumya14041987/youtube-video-generator.git
cd youtube-video-generator
py -3 -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env                       # then open .env and add OPENAI_API_KEY
Copy-Item channel-config.md.example channel-config.md
py -3 scripts\doctor.py
```

Install ffmpeg first: macOS `brew install ffmpeg`, Windows `winget install ffmpeg`, Ubuntu `sudo apt install ffmpeg`.

`python3 scripts/doctor.py` must show 0 FAIL. It checks Python, Pillow, Whisper, ffmpeg and its encoders, fonts, your keys (it never prints them),
that `.env` is ignored by git, that no key sits in a file git would commit, and which IDE files are in place.

API keys can come from `.env`, from your shell, or from your IDE's environment settings. The tools read the environment first, then `.env`.

## 1. Claude Code (terminal)

Official docs: [skills](https://code.claude.com/docs/en/skills), [plugins](https://code.claude.com/docs/en/plugins), [MCP](https://code.claude.com/docs/en/mcp).

Install Claude Code by following the [quickstart](https://code.claude.com/docs/en/quickstart), and sign in with a paid Claude plan or a Console account.

### Option A: clone the repo (recommended)

Open the cloned folder and start Claude Code there. The skills in `.claude/skills` and the sub-agents in `.claude/agents` load by themselves.

```bash
cd youtube-video-generator
claude
```

Then type:

```
/youtube-video-generator
```

and give a topic, a URL, or say "what's next".

### Option B: install as a plugin

Use this when you want the skills in every project without cloning. First put your own files (`.env`, `channel-config.md`, `assets/`, `episodes/`)
in the folder where you start Claude Code. The tools find that folder automatically, or you can point to it with `YTVG_PROJECT=/path/to/folder`.

```bash
claude plugin marketplace add Soumya14041987/youtube-video-generator
claude plugin install youtube-video-generator@ytvg-marketplace
```

Inside a session the same steps are `/plugin marketplace add ...` and `/plugin install ...`. To try it without installing, run
`claude --plugin-dir /path/to/youtube-video-generator`. To check the plugin files, run `claude plugin validate /path/to/youtube-video-generator`.

Plugin notes:
- The tools (`tools/`, `scripts/`) stay inside the plugin. The skill reaches them through `${CLAUDE_PLUGIN_ROOT}`. Run `scripts/doctor.py` from that folder once.
- Sub-agent names get a prefix, for example `youtube-video-generator:youtube-researcher`.
- A plugin install does not read `CLAUDE.md` or `AGENTS.md`. The skill itself carries the instructions.
- Do not install the plugin inside a folder that already holds a clone of this repo. The skills would load twice.

### Connect VidIQ (optional)

VidIQ powers keyword research for India, competitor titles, title and thumbnail scoring, and publishing details. Without it, those steps are skipped.

```bash
claude mcp add --transport http vidiq https://mcp.vidiq.com/mcp
```

Start `claude`, run `/mcp`, choose vidiq and sign in. For a project-wide setting copy [config/mcp/claude-code.mcp.json](../config/mcp/claude-code.mcp.json) to `.mcp.json`.
Claude Code asks you to approve a project `.mcp.json` the first time. Check the connection with `claude mcp list`.

## 2. Claude Code inside VS Code

Install the official extension: [Claude Code for VS Code](https://code.claude.com/docs/en/vs-code), extension id `anthropic.claude-code`. It needs VS Code 1.94 or newer.
Open the project folder and use the Claude panel. It reads the same `.claude/skills`, `.claude/agents` and MCP settings as the terminal, so Section 1 applies unchanged.
The same extension also installs in Cursor, and in forks like Kiro and Windsurf through the Open VSX registry.

## 3. VS Code with GitHub Copilot

Official docs: [custom instructions](https://code.visualstudio.com/docs/copilot/customization/custom-instructions),
[agent skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills), [MCP servers](https://code.visualstudio.com/docs/copilot/customization/mcp-servers).

1. Open the folder in VS Code. VS Code scans `.claude/skills`, `.agents/skills` and `.github/skills`, so the skills appear without any install.
2. It reads `.github/copilot-instructions.md` and `AGENTS.md` (both are in this repo). Run **Chat: Open Customizations** to confirm what it found.
3. In agent mode type `/youtube-video-generator`, or ask the agent to follow `.claude/skills/youtube-video-generator/SKILL.md`.

Connect VidIQ: copy [config/mcp/vscode.mcp.json](../config/mcp/vscode.mcp.json) to `.vscode/mcp.json`. The file uses the key `servers`.
A root `.mcp.json` with the key `mcpServers` also works. Or run **MCP: Add Server** and follow the prompts. VS Code asks you to trust the server the first time.
Run **MCP: List Servers** to see its status and logs. Never put a key in the file. Use `"${input:name}"` and VS Code asks for it securely.

## 4. Cursor

Official docs: [rules](https://cursor.com/docs/context/rules), [skills](https://cursor.com/docs/context/skills), [MCP](https://cursor.com/docs/context/mcp).

1. Open the folder in Cursor. Cursor finds skills in `.agents/skills`, `.cursor/skills` and, for compatibility, `.claude/skills`. Type `/youtube-video-generator` in chat.
2. The rule `.cursor/rules/youtube-video-generator.mdc` tells the agent when to use the workflow. Cursor also reads `AGENTS.md`.
3. Connect VidIQ: copy [config/mcp/cursor.mcp.json](../config/mcp/cursor.mcp.json) to `.cursor/mcp.json` (or `~/.cursor/mcp.json` for every project).
   Turn the server on in the Customize panel. If it will not connect, open the Output panel (Cmd+Shift+U) and pick **MCP Logs**.
   Reference secrets as `${env:NAME}` so they stay out of the file.

You can also run the Claude Code extension inside Cursor (Section 2) to get the sub-agents.

## 5. Kiro

Official docs: [steering](https://kiro.dev/docs/steering/), [MCP](https://kiro.dev/docs/mcp/), [skills](https://kiro.dev/docs/skills/).

1. Install Kiro from [kiro.dev](https://kiro.dev/) and open the folder.
2. Kiro only looks for skills in `.kiro/skills` (project) or `~/.kiro/skills` (all projects). Install them once:

   ```bash
   python3 scripts/install_ide.py --ide kiro            # project
   python3 scripts/install_ide.py --ide kiro --user     # every project
   ```

   The installer links the skills (it copies them on Windows if linking is not allowed), so there is still one copy to update.
3. The steering file `.kiro/steering/youtube-video-generator.md` is picked up automatically (`inclusion: auto`). Kiro also reads `AGENTS.md`.
4. Connect VidIQ: copy [config/mcp/kiro.mcp.json](../config/mcp/kiro.mcp.json) to `.kiro/settings/mcp.json` (or `~/.kiro/settings/mcp.json`).
   Check the MCP servers tab in the Kiro panel. If your Kiro version does not support remote servers, use
   [config/mcp/bridge-for-tools-without-remote-support.mcp.json](../config/mcp/bridge-for-tools-without-remote-support.mcp.json), which uses the `mcp-remote` bridge through `npx`.
5. Type `/youtube-video-generator`.

## 6. PyCharm and other JetBrains IDEs

There are two ways. You can use both.

### Claude Code plugin for JetBrains (full features, includes sub-agents)

Install the Claude Code CLI (Section 1), then install the [Claude Code plugin](https://plugins.jetbrains.com/plugin/27310-claude-code-beta-) from the JetBrains Marketplace and restart the IDE.
Open it with Cmd+Esc (Mac) or Ctrl+Esc (Windows and Linux), or run `claude` in the IDE terminal. From an outside terminal run `/ide` to connect.
Official guide: [JetBrains IDEs](https://code.claude.com/docs/en/jetbrains). On Windows with WSL set the Claude command to `wsl -d Ubuntu -- bash -lic "claude"`
(use your distribution name). With JetBrains Remote Development, install the plugin on the remote host.

### Junie (JetBrains AI agent)

Official docs: [Junie](https://junie.jetbrains.com/docs/), [IDE plugin](https://junie.jetbrains.com/docs/junie-ide-plugin.html), [agent skills](https://junie.jetbrains.com/docs/agent-skills.html).

1. In PyCharm open Settings, Plugins, search for **Junie by JetBrains** and install it. You need PyCharm 2025.1 or newer and a JetBrains AI subscription (a 30 day trial is available).
2. Junie reads guidelines from `.junie/AGENTS.md` first, then `AGENTS.md` at the project root. This repo has the root file, so there is nothing to add.
3. Junie loads skills from `.junie/skills` and `.agents/skills`. Install them once:

   ```bash
   python3 scripts/install_ide.py --ide junie
   ```

   Then use `/youtube-video-generator` or `$youtube-video-generator` in a prompt.
4. Connect VidIQ: Settings, Tools, Junie, MCP Settings, or copy [config/mcp/junie.mcp.json](../config/mcp/junie.mcp.json) to `.junie/mcp/mcp.json`
   (or `~/.junie/mcp/mcp.json`). Use the bridge file from Section 5 if remote servers are not supported in your version.
5. Set the PyCharm project interpreter to the virtual environment where you ran `pip install -r requirements.txt`. Otherwise the tools fail with "No module named PIL".

## 7. Other agentic tools

Anything that reads [AGENTS.md](https://agents.md/) can run this project. The list on that site includes OpenAI Codex, Gemini CLI, Zed, Warp, Aider, Goose, Devin and others.
The tool needs three abilities: read `AGENTS.md`, run shell commands, and write files. Skills and MCP are optional extras.

- **Codex CLI:** it reads `AGENTS.md`. Add VidIQ to `~/.codex/config.toml` with [config/mcp/codex.config.toml](../config/mcp/codex.config.toml).
- **Windsurf:** it reads `AGENTS.md`. Its rules live in `.windsurf/rules/` and its MCP file is `~/.codeium/windsurf/mcp_config.json`. This comes from a search of its documentation, so check the current Windsurf docs.
- **Any other tool:** tell it "follow AGENTS.md, then follow `.claude/skills/youtube-video-generator/SKILL.md`". If it supports skill folders, run
  `python3 scripts/install_ide.py --ide agents` to put the skills in the shared `.agents/skills` folder.

## Check that it works

Run these in order. Stop at the first one that fails and see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

1. `python3 scripts/doctor.py` shows 0 FAIL.
2. Ask the agent: "What skills do you have for making YouTube videos?" It should name `youtube-video-generator`.
3. Ask it to run `python3 scripts/doctor.py --ci` and read you the summary line.
4. If VidIQ is connected, ask it to check the VidIQ credit balance. A number means the connection works.
5. Make a test thumbnail with no face and no keys: see [THUMBNAILS.md](THUMBNAILS.md).

## Security

- Keys live in `.env` or your environment, never in a prompt, a chat, a rule file or an MCP file.
- `.env`, `channel-config.md`, `episodes/`, `assets/presenter`, `assets/music` and series files are ignored by git on purpose. The doctor warns if a key could be committed.
- MCP servers and plugins run with your permissions. Read what you approve. VidIQ signs in with OAuth in the tool, so no key is stored in a file.
- Treat text from web pages the agent reads as data, not instructions.
