# Playlist: MCP (Model Context Protocol) — Zero to Hero

Ordered curriculum, beginner → advanced. Each row becomes one
`/youtube-episode` run (topic + duration + audience level from this table).
Update `Status` as episodes are produced; `Episode` links to its folder
under `episodes/` once built.

| # | Title | Format | Audience Level | Focus | Status | Episode |
|---|---|---|---|---|---|---|
| 1 | MCP Fundamentals, Components, and the Rewrite Most Explainers Skip | Long | Intermediate | Core concept, M×N problem, architecture, current stateless spec (rebuilt from original DevOps-Advanced framing) | Produced | `episodes/episode-01-what-is-mcp/` |
| 2 | MCP Explained in 60 Seconds | Short | Beginner | Same core concept as #1, compressed for Shorts discovery/algorithm reach | Planned (superseded) | — (was built under episode-02, then replaced by item #6 per explicit request; not currently produced under any episode number — rebuild under a future episode slot if still wanted) |
| 3 | The M×N Problem — Why MCP Had to Exist | Short | Beginner | Isolate the integration-explosion problem with the USB-C-style analogy, standalone hook | Planned | — |
| 4 | MCP Architecture Deep Dive: Host, Client, Server | Long | Intermediate | Full protocol mechanics — JSON-RPC, capability negotiation, real request/response flow | Planned | — |
| 5 | MCP Tools vs Resources vs Prompts | Short | Intermediate | The 3 primitives an MCP server exposes, one clear example each | Planned | — |
| 6 | How to Build Your First MCP Server | Long | Intermediate | Diagram-only conceptual build (no screen recording, per the channel's faceless format) — connect/discover/call-a-tool, SEP-2567 stateless handle-passing, AI Developer Assistant example | Produced | `episodes/episode-02-build-your-first-mcp-server/` |
| 7 | MCP vs Function Calling — What's the Difference? | Short | Intermediate | Common confusion point, direct comparison | Planned | — |
| 8 | MCP Authentication & Security: What Changed | Long | Advanced | OAuth-based authorization rewrite, what broke, what it protects against | Planned | — |
| 9 | MCP in DevOps: Wiring AI Agents Into Your CI/CD Pipeline | Long | Advanced | Practical DevOps integration — real pipeline, real MCP server, real payoff | Planned | — |
| 10 | The Stateless MCP Spec Rewrite, Explained | Long | Advanced | July 2026 spec deep dive — dropped sessions, per-request auth, load-balancer implications | Planned | — |
| 11 | Building an MCP Client From Scratch | Long | Advanced | The other half of #6 — what a host/client actually has to implement | Planned | — |
| 12 | Top 5 MCP Servers Every DevOps Engineer Should Know | Short/Long | Intermediate | Practical tool roundup — real, currently-useful servers | Planned | — |
| 13 | MCP + AIOps: Automating Incident Response | Long | Advanced | Applied capstone — MCP tying together monitoring/logs/ticketing for an AIOps workflow | Planned | — |
| 14 | The Future of MCP: Governance, the Agentic AI Foundation, and What's Next | Long | Intermediate | Wrap-up/capstone — where the protocol is headed, ties back to #1 | Planned | — |

## Notes

- Episode 1 was originally built before this playlist existed (Advanced,
  DevOps-specific framing), then rebuilt at Intermediate level once the
  cue-sheet pipeline and density/audience-level features existed — current
  version reflects the current MCP spec (July 2026 stateless rewrite) as
  baseline, not a footnote. A beginner-friendlier companion is still #2,
  not a replacement for #1.
- Format/level here are starting recommendations — confirm via step 2's
  `AskUserQuestion` at production time in case either should shift once
  the topic is actually researched.
- This file is the planning artifact; `/series-log.md` remains the
  production log (filled in only once an episode is actually rendered).
