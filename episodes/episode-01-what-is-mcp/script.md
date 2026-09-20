# Episode 01 — MCP Fundamentals, Components, Why & How (rebuild)

## Hook

[CALLOUT: MCP already changed once]

[VISUAL: a row of 4-5 generic "MCP Explained" video thumbnail cards on screen, then a red "OUTDATED" stamp slams down on one of them]

Almost every MCP explainer you'll find today teaches a version of the protocol that no longer exists. Here's what MCP actually is right now — fundamentals, components, why it exists, and how it really works.

## Core concept

[VISUAL: MCP logo, "Model Context Protocol" title, small subtext card: "open standard · Anthropic · November 2024"]

MCP stands for Model Context Protocol. It's an open standard, created by Anthropic in November 2024, that gives AI applications one consistent way to connect to external tools, data, and systems — instead of every app writing its own one-off integration for every tool.

[VISUAL: 5 labeled AI-app icons in a row (App 1 through App 5) connected by tangled crossing lines to 5 labeled tool icons in a row (Tool 1 through Tool 5) — every single app-tool pair has its own line, 25 lines total, visibly chaotic, a small caption reading "5 × 5 = 25 integrations"]

Here's why that mattered. Connect M AI apps to N tools the old way, and you need M times N custom connectors. Five apps, five tools — that's twenty-five separate integrations, each one hand-built, each one maintained on its own.

[ANIMATION: the same 25 tangled lines collapsing into a clean hub-and-spoke — all 5 apps connect once to a central MCP hub, MCP connects once to each of the 5 tools, the "5 × 5 = 25" caption fading out as a new "5 + 5 = 10" caption fades in]

MCP turns that into M plus N. Same five apps, five tools — now just ten connections, not twenty-five. Everyone builds against one shared interface once.

[VISUAL: three incompatible phone charger types shown side by side, then merging into a single USB-C connector]

It's the same fix as USB-C replacing a drawer full of incompatible chargers — one interface, works with everything.

[VISUAL: three labeled boxes left to right: Host (e.g. an IDE or Claude Desktop) → Client (inside the host) → Server (external program)]

The architecture has three roles. A host is the application you actually use. Inside it, a client manages a one-to-one connection to a server — a separate program that exposes real capabilities.

[VISUAL: three-column card: "Tools — callable actions" / "Resources — read-only data" / "Prompts — reusable templates"]

A server exposes three things: tools the model can call, resources it can read, and prompts that guide how to use them well. Tools have side effects — send an email, create a ticket. Resources don't — they're read-only, closer to a GET request than an action.

[VISUAL: a coding assistant host icon asking a question, an arrow to a client, an arrow to a server labeled "database", an arrow back with real query results]

Picture a coding assistant asking "why did the last deploy fail." The client sends that through to a database server as a tool call, the server actually queries real data, and the answer comes back as a real result — not a guess based on training data.

## My angle

[VISUAL: sequence diagram — client sends "initialize", server responds with capabilities, client sends "initialized", a session ID tag attaches to the connection]

Here's the part almost no current explainer gets right. MCP originally worked like this: a client and server shook hands — initialize, then initialized — and the server pinned that whole session to one specific instance with a session ID.

[ANIMATION: adoption timeline building left to right — "Mar 2025: OpenAI" → "Apr 2025: Google DeepMind" → "May 2025: Microsoft + GitHub" → "Dec 2025: Linux Foundation's Agentic AI Foundation"]

That handshake model is what the entire industry adopted through 2025 — OpenAI, Google DeepMind, Microsoft and GitHub, eventually governance itself moving to the Linux Foundation.

[VISUAL: a server box pinned by a thick line to one server instance, a load balancer icon with a red X trying to route around it]

But mass adoption exposed a second problem nobody talks about: a session pinned to one server instance can't sit behind a normal load balancer. That's not how anything scales in production.

[VISUAL: a rolling deployment diagram — old server instance draining connections while a new one spins up, a dropped-connection icon on the old instance]

Roll out a new version the ordinary way, and every session still pinned to the old instance either has to wait or gets dropped mid-request. Fine for a demo. Not fine for something real teams depend on.

[ANIMATION: the initialize/initialized handshake and session-ID tag both dissolving, replaced by a single self-contained request carrying its own version info in a small "_meta" tag]

So in July 2026, MCP shipped its biggest rewrite yet. The handshake is gone. The session ID is gone. Every request now describes itself — protocol version and capabilities travel with the request itself, not a stored session.

[VISUAL: a "tools/list" request card with a small badge reading "cacheable"]

List calls can now be cached. Routing can happen from the request headers alone.

[VISUAL: a "core protocol" box with a branch labeled "Extensions" pointing to two smaller boxes: "Tasks" and "MCP Apps"]

The component set evolved too. Tasks — for work that takes longer than one request-response cycle, checked via polling instead of holding a connection open — used to be an experimental core feature. Now it's a proper extension, redesigned around the same stateless model as everything else. MCP Apps, for servers that ship their own UI, got the same promotion. Extensions can now be built and adopted independently, without every implementation needing to support everything in core.

[VISUAL: three small labeled tags — "Roots", "Sampling", "Logging" — each stamped "deprecated"]

A few original pieces, Roots, Sampling, and Logging, are being phased out over the next year.

[CALLOUT: The rewrite solved a problem most explainers skip]

[VISUAL: a four-step causal chain diagram: "M×N problem" → "MCP" → "mass adoption" → "stateless rewrite"]

This wasn't a cosmetic update. The M-by-N problem is why MCP exists. Mass adoption is why MCP had to change again. Understanding both is understanding MCP as it actually works today, not as it launched.

## CTA

If you're building with MCP right now, build against the current spec, not the one every tutorial still shows. Follow for the next stop on this MCP series — we're going component by component, zero to hero.

[VISUAL: end-card — channel wordmark centered top, below it a compact 4-row block: "LinkedIn: aiops-genai-developer · Medium: @soumya14041987 · AWS Builder Center · X: @AIWithSoumya", white background, same simple template every episode uses]
