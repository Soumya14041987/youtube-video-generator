# Playlist: MCP (Model Context Protocol) — Zero to Hero

Ordered curriculum, beginner → advanced. Each row becomes one
`/youtube-episode` run (topic + duration + audience level from this table).
Update `Status` as episodes are produced; `Episode` links to its folder
under `episodes/` once built.

| # | Title | Format | Audience Level | Focus | Status | Episode |
|---|---|---|---|---|---|---|
| 1 | What is MCP (Model Context Protocol)? | Long | Beginner→Advanced (built as Advanced) | Core concept, M×N problem, architecture, 2026 stateless spec — DevOps framing | Produced | `episodes/episode-01-what-is-mcp/` |
| 2 | MCP Explained in 60 Seconds | Short | Beginner | Same core concept as #1, compressed for Shorts discovery/algorithm reach | Planned | — |
| 3 | The M×N Problem — Why MCP Had to Exist | Short | Beginner | Isolate the integration-explosion problem with the USB-C-style analogy, standalone hook | Planned | — |
| 4 | MCP Architecture Deep Dive: Host, Client, Server | Long | Intermediate | Full protocol mechanics — JSON-RPC, capability negotiation, real request/response flow | Planned | — |
| 5 | MCP Tools vs Resources vs Prompts | Short | Intermediate | The 3 primitives an MCP server exposes, one clear example each | Planned | — |
| 6 | How to Build Your First MCP Server | Long | Intermediate | Hands-on walkthrough, minimal working server, what "exposing a tool" actually looks like in code | Planned | — |
| 7 | MCP vs Function Calling — What's the Difference? | Short | Intermediate | Common confusion point, direct comparison | Planned | — |
| 8 | MCP Authentication & Security: What Changed | Long | Advanced | OAuth-based authorization rewrite, what broke, what it protects against | Planned | — |
| 9 | MCP in DevOps: Wiring AI Agents Into Your CI/CD Pipeline | Long | Advanced | Practical DevOps integration — real pipeline, real MCP server, real payoff | Planned | — |
| 10 | The Stateless MCP Spec Rewrite, Explained | Long | Advanced | July 2026 spec deep dive — dropped sessions, per-request auth, load-balancer implications | Planned | — |
| 11 | Building an MCP Client From Scratch | Long | Advanced | The other half of #6 — what a host/client actually has to implement | Planned | — |
| 12 | Top 5 MCP Servers Every DevOps Engineer Should Know | Short/Long | Intermediate | Practical tool roundup — real, currently-useful servers | Planned | — |
| 13 | MCP + AIOps: Automating Incident Response | Long | Advanced | Applied capstone — MCP tying together monitoring/logs/ticketing for an AIOps workflow | Planned | — |
| 14 | The Future of MCP: Governance, the Agentic AI Foundation, and What's Next | Long | Intermediate | Wrap-up/capstone — where the protocol is headed, ties back to #1 | Planned | — |

## Notes

- Episode 1 was built before this playlist existed (Advanced level, per the
  original episode) — kept as-is rather than rebuilt, since its content is
  correct; a beginner-friendlier companion is #2, not a replacement for #1.
- Format/level here are starting recommendations — confirm via step 2's
  `AskUserQuestion` at production time in case either should shift once
  the topic is actually researched.
- This file is the planning artifact; `/series-log.md` remains the
  production log (filled in only once an episode is actually rendered).
