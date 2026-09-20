# Episode 02 — How to Build Your First MCP Server

## Hook

[CALLOUT: How an MCP server actually gets built]

[VISUAL: a row of "build an MCP server" video thumbnails, all screen-recorded code editors, then a text card: "none of them are built like this one"]

You understand what MCP is. Here's how a server actually gets built — not with a screen recording of an IDE, but with the three conversations that make one work.

## Core concept

[VISUAL: quick recap card — three boxes: Host, Client, Server, small labels "you already know this from Episode 1"]

Quick recap: a host runs a client, the client talks to a server, the server exposes tools, resources, and prompts. Today we're building one specific server.

[VISUAL: a labeled server box — "AI Developer Assistant" — with 4 small tool icons beneath it: inspect a Git repo, read files, search code, run a controlled system command]

Call it an AI Developer Assistant. It inspects Git repositories, reads files, searches code, and runs a small set of controlled developer operations. Not a toy weather server — something a real coding assistant would actually use.

[VISUAL: three-panel roadmap card: "1. Connect" / "2. Discover" / "3. Call a tool"]

Three conversations build this: connecting, discovering what's available, and calling a tool. Here's what each one actually looks like today — not in 2024.

[VISUAL: a laptop icon labeled "your machine" running a small server process, a dotted line labeled "stdio" connecting it to a host app icon]

You build and test this locally first. The server runs as a plain process on your machine, talking to the host over a simple local transport before anything touches a network.

[VISUAL: a magnifying glass over a raw JSON-RPC message, labeled "this is what you actually debug"]

Debugging one of these isn't mysterious — you're reading the same JSON-RPC messages the client and server exchange, checking that a tool's declared inputs match what you're actually sending.

## My angle

[VISUAL: old handshake diagram (initialize → initialized → session ID) with a red "X" stamped over it, label "most tutorials still teach this"]

Most "build an MCP server" tutorials still show a connection handshake and a session ID pinning you to one server instance. That model doesn't exist anymore.

[ANIMATION: a client and server connecting with a single self-describing request — no handshake step, no session ID tag appearing — a "connected" checkmark lighting up immediately]

Today, a client just sends a request. No handshake. No session to negotiate. Any request can hit any server instance behind a load balancer.

[VISUAL: "tools/list" request card, response card listing 4 tools, small badges "cacheable" and "same list for everyone"]

Second conversation: discovery. The client asks what's available with a tools list request. Each tool in that list carries a name, a description, and a JSON schema for its inputs — that's how the client knows what arguments to send before ever calling it.

[VISUAL: one tool entry expanded — name "inspect_repo", description "reads a Git repository's structure", input schema showing a single "path" field]

Take the repo-inspection tool. Its schema says it takes one input, a path. That's the whole contract — no hidden setup, no separate registration step for the client to worry about.

The response is cacheable now too, and — this matters — it's the same list no matter who's asking, not a per-connection answer.

[ANIMATION: a "tools/call" request labeled "list files in this repo" flowing into the server, a response flowing back containing both the file list AND a small glowing "handle" token]

Third conversation, and the one that actually trips people up: calling a tool. Ask the Dev Assistant to list files in a repo, and the response comes back with the file list — plus a handle. A small token standing in for "the repo you just opened."

[VISUAL: a second "tools/call" labeled "read file X" with that same handle token attached as an argument, arrow into the server]

Want to read a file from that same repo next? You pass the handle back as an ordinary argument on your next call.

It's the same pattern for every follow-up. Search the code in that repo next, and the search tool takes the same handle as an input — the server never has to remember which repo you were working in, because you're telling it, every single time.

[CALLOUT: The server doesn't remember you — you remind it]

[VISUAL: side-by-side comparison — left "OLD: server remembers your session" with a brain icon, right "NOW: server hands you a token and forgets" with a ticket-stub icon]

Old tutorials have the server remember your session. The current spec has the server hand you a token and forget you existed. That's the actual mental shift — not OAuth, not remote hosting, this.

[ANIMATION: a gateway/proxy box inspecting two small header tags, "Mcp-Method" and "Mcp-Name", routing arrows fanning out to different backend server instances without opening the message body]

One more piece worth knowing, since a Dev Assistant doing real Git and system operations is exactly the kind of thing you'd put behind real infrastructure: new routing headers let a gateway see which tool is being called without reading the full request body at all. It can block, log, or route a "run_system_command" call differently from a harmless "read_file" call, just by looking at the header.

[VISUAL: the Dev Assistant server box connecting into a real host app icon labeled "Claude Code / your IDE", a config file icon beside it]

Once it works locally, connecting it to a real AI application is a config step, not new code — you point the host at your server process, and every tool you built shows up in that discovery list automatically.

## CTA

That's the shape of building one: connect without a handshake, discover a cacheable tool list, call a tool and carry its handle forward yourself. Follow for the next stop in the series — what the client side has to implement to make all three of these conversations happen.

[VISUAL: end-card — the literal text "AI WITH SOUMYA" as the centered channel wordmark (this is the channel name, not the episode or series title), a thin accent-color underline beneath it, then a compact 4-row block below: "LinkedIn: aiops-genai-developer · Medium: @soumya14041987 · AWS Builder Center: builder.aws.com · X: @AIWithSoumya" — every row gets a label AND a value, none bare, white background, same simple template every episode uses]
