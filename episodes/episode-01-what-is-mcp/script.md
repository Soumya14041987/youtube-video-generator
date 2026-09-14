# Episode 01 — What is MCP (Model Context Protocol)?

## Hook

[CALLOUT: What is MCP?]

[VISUAL: opening title card — dark background matching the channel template, channel wordmark, a simple abstract motif (a single glowing connector line linking three plain icon shapes: a chat/agent bubble, a small hub node, a generic tool/plug icon) with no specific product logos or real system names on it yet — this is a teaser card, not the architecture explainer, so it must not resemble or preview the detailed DevOps diagram that appears later]

Your AI coding assistant just read your deployment logs, cross-referenced your last three commits, and told you exactly why the build broke — without a developer writing a single custom integration for any of it. That's not a smarter model. That's MCP.

## Core concept

MCP stands for Model Context Protocol. Anthropic open-sourced it on November 25th, 2024, as a standard way to connect AI models and agents to external tools, data sources, and systems. It's a protocol, not a product — like HTTP, or USB-C — and it isn't owned or gatekept by any single vendor.

Here's the problem it was built to kill. Before MCP, every AI application that wanted to talk to every tool needed its own custom, one-off integration. Ten AI apps, ten data sources — that's potentially a hundred bespoke connectors. Engineers call this the M-by-N integration problem: multiply your assistants by your tools, and that's how many brittle, hand-built bridges someone has to maintain. MCP turns that into M-plus-N. Build one MCP-compliant client, build one MCP-compliant server, and they interoperate — no custom glue in between.

[VISUAL: MCP architecture from a DevOps perspective — an MCP host (a coding assistant like Claude Code) running an MCP client, connected over the protocol to an MCP server that exposes tools/resources; the server in turn connects to real DevOps systems: a cloud provider's deployment logs, a Git repository's recent commits, and a CI/CD pipeline status feed. Show the request flow: host asks a question, client calls the server, server pulls from cloud logs + git + CI/CD, response flows back — all through one shared protocol, not three custom scripts.]

The architecture has three pieces. An MCP host is the application you actually interact with — Claude Desktop, Claude Code, any agent-capable app. Inside it, an MCP client manages the connection. On the other end, an MCP server exposes specific capabilities in a standardized way: tools the model can call, resources it can read, prompts it can reuse. The model doesn't need custom code to understand your cloud provider's logs or your CI/CD pipeline — it just needs an MCP server sitting in front of them, speaking the same protocol every other server speaks.

Picture a second case: a support-ops agent that looks up a customer in a CRM through one MCP server, then checks an order status in a completely different backend through another — neither integration written specifically for that bot. Same protocol, two unrelated systems, zero bespoke glue code either time.

[ANIMATION: M-by-N integration problem collapsing into M-plus-N — start with a tangled web of many-to-many connector lines between a row of AI-app icons and a row of tool icons (databases, cloud, CI/CD, ticketing), lines multiplying and crossing chaotically; then wipe/transform into a clean single hub-and-spoke: all AI apps connect to one MCP layer, which connects once to each tool. End state clearly less cluttered than the start state.]

## My angle

Most explainers stop at "USB-C for AI" and leave it there. Here's what almost none of them mention: MCP's most consequential change didn't happen at launch — it happened on July 28th, 2026, with the protocol's biggest spec revision yet.

The original MCP was stateful — a session-based handshake, sticky connections, the kind of thing that's fine for a demo and painful in production. The July 2026 spec removed that. Protocol version and client capabilities now travel per-request instead of through a persistent session, and authorization got a stricter, hardened rewrite. The practical result: an MCP server can now sit behind a completely standard load balancer, with no sticky sessions required — the same way any ordinary stateless web service scales in Kubernetes or behind a CI/CD-deployed fleet.

[CALLOUT: MCP just became boring infrastructure]

That sounds like a downgrade in excitement. It's the opposite. "Boring infrastructure" is exactly the property an SRE wants before something goes anywhere near production. Before this change, running MCP at real scale meant fighting session affinity — pinning every client to the one server instance holding its session state, then hoping a rolling deploy didn't drop connections mid-handshake. That's the exact class of problem service meshes and API gateways were built to route around, and MCP's stateful design fought against all of it. Strip the session out, and an MCP server becomes just another stateless HTTP workload — the same deployment pattern already sitting behind every other production service you run, no special-cased infrastructure required.

Nearly every explainer, video or written, still tells MCP's story through its November 2024 stateful origins. The version of this story that actually matters to a DevOps audience is the one where MCP stopped being a clever AI demo protocol and started being something you can put behind a load balancer without thinking twice.

[ANIMATION: adoption timeline building left to right — nodes appearing one at a time in sequence: "Nov 2024 — Anthropic open-sources MCP" → "Mar 2025 — OpenAI adopts it" → "Apr 2025 — Google DeepMind (Gemini)" → "May 2025 — Microsoft + GitHub join steering committee" → "Dec 2025 — donated to the Agentic AI Foundation (Linux Foundation)" → "Jul 2026 — stateless spec rewrite". Each node lights up after the previous one, ending with all six connected on one timeline.]

## CTA

If you're building with AI agents in a real Cloud or DevOps stack, this is the layer worth understanding before you wire up your next integration. Follow for the next one — we're covering Agentic AI, MCP, AIOps, and DevSecOps every week.

[VISUAL: end-card — channel wordmark centered top, below it a compact 4-row block: "LinkedIn · Medium · AWS Builder Center · X — @AIWithSoumya", white background, same simple template every episode uses]
