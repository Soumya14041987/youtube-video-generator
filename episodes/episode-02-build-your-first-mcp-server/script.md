# Episode 02 — MCP: Server, Client, Tools, Resources, Prompts & Discovery

## Hook

[CALLOUT: MCP servers expose three things, and clients discover them one way]

[VISUAL: three stacked cards — "Tools" (wrench icon) / "Resources" (folder icon) / "Prompts" (lightbulb icon) — with a downward arrow to a single "Discovery" card]

You know what MCP is. Here's what a server actually exposes, how a client finds it, and how they talk — not the old handshake tutorials. The 2026 spec changed everything.

## Core Concept

[VISUAL: quick recap — "Server" box on left with three icons (tools/resources/prompts), "Client" box on right, double-headed arrow labeled "JSON-RPC 2.0" between them]

A server exposes three primitives: **tools** (actions the model invokes), **resources** (read-only context data), and **prompts** (reusable instruction templates). The client connects, discovers what's available, and uses them. That's the whole shape.

[VISUAL: a "tool" card — name "list_files", description "List files in a directory", inputSchema box showing {path: string}]

A **tool** is a callable action. It has a name, a description, and a JSON Schema defining what inputs it takes. The model reads the schema and decides whether to call it.

[VISUAL: a "resource" card next to it — name "docs.md", description "Current documentation", uri: "file:///docs" — labeled "Read-only" in corner]

A **resource** is read-only context. Unlike tools (which the model invokes), resources are data the application pulls and includes in the prompt. Think file contents, database records, documentation.

[VISUAL: a "prompt" card — name "analyze_code", description "Analyze this code block", arguments: {language, code}]

A **prompt** is a reusable instruction template. The server stores a prompt; the client surfaces it as a command or menu item. When called, the server returns composed system and user messages — ready to inject into the conversation.

## My Angle

[VISUAL: a laptop with a server process box on it, labeled "stdio" — a dotted line going to a host app (IDE/Claude Code) labeled "Client", with a small note "July 2026: no session ID, no handshake"]

You build this locally first. Server runs as a plain process, talking to the client over stdio — JSON-RPC messages, one per line. No session negotiation. No protocol handshake.

[ANIMATION: a client icon sending a request box labeled "tools/list" to the server, the server immediately returning a response with a checkbox "✓ Cached for 30 seconds (ttlMs: 30000)"]

First thing the client does: ask for a list of tools. The server responds with names, descriptions, and input schemas. That response is cacheable — marked with `ttlMs` (time-to-live). Clients cache it, so repeated tool discovery hits memory, not the server.

[VISUAL: side-by-side comparison — OLD on left: "Server remembers your session_id" with a brain icon, NEW on right: "Server hands you a handle (stateless)" with a ticket/token icon]

The old model had servers remember session IDs. The 2026 spec flipped it: servers are stateless. If you need to carry state across tool calls, the server hands you a **handle** — an opaque token you pass back as an ordinary argument on your next call.

[ANIMATION: sequence — Step 1: tool call `create_session()` returns {handle: "sess_abc"}; Step 2: next call `run_query(handle="sess_abc", query="SELECT...") returns results; Step 3: final call with same handle to `close_session(handle="sess_abc")`]

Example: create a session, get back a handle. Run a query passing that handle. Close the session, still passing the handle. The server never has to remember you — you carry proof of what you're doing, every time.

[CALLOUT: The handle is the new session ID — but visible in the conversation]

[VISUAL: three-icon sequence — Icon 1 "Server/discover" (optional), Icon 2 "tools/list, resources/list, prompts/list" (discovery), Icon 3 "tools/call" (execution) — with arrows between them]

The discovery sequence for a client: optionally call `server/discover` to learn capabilities and protocol version. Always call `tools/list`, `resources/list`, `prompts/list` to see what's available. Then call tools with `tools/call`, passing handles from earlier responses when needed.

[VISUAL: a gateway/proxy box with two columns — left column: request goes in (JSON-RPC call), right column: routers send it to server-instance-1, server-instance-2, server-instance-3 (arrows fan out with no session stickiness)]

Because servers are stateless, you can put them behind a plain round-robin load balancer. Any request hits any instance. No sticky sessions, no shared state store. Scale horizontally, treat servers like cattle.

[VISUAL: a localhost server diagram — "Your machine" box containing "MCP Server Process" with stdio pipes to "Host App (Claude Code, Cursor, VS Code)" labeled "Development local stdio transport"]

Locally, you use stdio transport: stdin and stdout for JSON-RPC. No HTTP layer, no network overhead. Press a button, send a JSON request, read the response. Perfect for CLI tools, editor plugins, and testing.

[ANIMATION: a JSON-RPC request box flowing into server, a JSON response flowing back, both labeled with line-by-line breakdown: `{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{...}}` → response with `{"id":1,"result":{...}}`]

The protocol is just JSON-RPC 2.0 over pipes. Each request has `jsonrpc: "2.0"`, `id` (to match request to response), `method`, and `params`. Server responds with matching `id` and `result` or `error`. Debug by logging stdin/stdout to stderr.

[VISUAL: a "Resources/read" card — GET `/resources/read?uri=file:///docs.md"`, response contains file contents, plus `{ttlMs: 60000, cacheScope: "public"}` — labeled "Client-side cached""]

Resources are fetched via `resources/read` — just like tools/list, they carry cache hints. A client reads a resource once, caches it for the TTL duration, then fetches fresh if older.

[VISUAL: a "Prompts/get" call card — `{prompt_name: "analyze_code", arguments: {language: "python", code: "..."}}`, response: `{system: "You are an expert Python analyzer...", messages: [{role: "user", content: "Analyze this code..."}]}`]

When a client calls a prompt via `prompts/get`, the server returns a pre-composed system message and user message block. The client injects these into the conversation, letting the model work with domain knowledge the server encodes.

[VISUAL: comparison table — "Tool" (model invokes, active), "Resource" (client pulls, passive), "Prompt" (server provides, templated) — each with icon and use-case example]

Three primitives, three patterns: tools are active (model-driven), resources are passive (client-driven), prompts are templates (server-provided). Together, they let a server offer rich, composable capabilities without protocol-level state.

## CTA

[VISUAL: checklist card — "✓ Servers expose tools, resources, prompts" / "✓ Clients discover via list() calls (cacheable)" / "✓ Tools carry handles for stateless state" / "✓ Build locally via stdio JSON-RPC" / "✓ Deploy behind load balancers, no sessions"]

That's the shape of MCP in 2026: discover, cache, call — with handles threading state through every request. Follow for the next episode, where we show a real server built with all three primitives.

[VISUAL: end-card — dark #0d1117 background (matching every other frame in the video, not white), the literal text "AI WITH SOUMYA" as a large centered channel wordmark (this is the channel name, not the episode or series title — never substitute the episode/playlist title here) with a thin accent-color underline beneath it, a small series tag below that reading "MCP : ZERO TO HERO", then a horizontal row of 5 rounded platform cards, each with a colored top accent bar in that platform's brand color, a circular monogram/initial in the same color, the platform name, and its handle: LinkedIn (blue, aiops-genai-developer) · Medium (white, @soumya14041987) · AWS Builder Center (orange, builder.aws.com) · X (white, @AIWithSoumya) · GitHub (light blue, mcp-zero-to-hero) — every card gets a label AND a value, none bare — and a bold accent-outlined CTA box beneath the cards reading "FOLLOW FOR THE NEXT EPISODE". Same design every episode uses.]
