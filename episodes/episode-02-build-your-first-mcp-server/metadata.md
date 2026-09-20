# Episode 02 — Metadata

## Title options

1. How to Build Your First MCP Server (No Code on Screen, Just the Architecture)
2. The Server Doesn't Remember You — Building an MCP Server in 2026
3. MCP: Zero to Hero — Building Your First Server

## Tags

MCP, Model Context Protocol, build MCP server, MCP tutorial, MCP architecture, tool discovery, stateless MCP, SEP-2567, AI agents, Agentic AI, Anthropic, developer tools, JSON-RPC

## Hashtags

#MCP #ModelContextProtocol #AgenticAI #MCPZeroToHero #DevTools

## Description

Every "build an MCP server" video is a screen recording of an IDE. This one isn't — because the thing that actually matters isn't the code, it's the three conversations a server has: connecting, discovering what's available, and calling a tool.

Built around a concrete example — an AI Developer Assistant that inspects Git repos, reads files, searches code, and runs controlled developer operations — this episode covers what building one looks like against the *current* (July 2026) spec, not the dead handshake model most tutorials still teach.

In this episode:
- Connecting without the old initialize/session-ID handshake
- Tool discovery via tools/list — cacheable, same list for everyone
- The actual mental shift: the server doesn't remember your session, it hands you a stateless handle and you pass it back yourself (SEP-2567)
- Local development, debugging via raw JSON-RPC, and connecting to a real host app
- The new Mcp-Method/Mcp-Name routing headers, and why a Dev Assistant needs them

Episode 2 of MCP: Zero to Hero. Follow for episode 3 — what the client side has to implement.

## Connect

Connect with me:
LinkedIn: https://www.linkedin.com/in/aiops-genai-developer
Medium: https://medium.com/@soumya14041987
AWS Builder Center: https://builder.aws.com/
X: https://x.com/AIWithSoumya

## Recommended slot

**Saturday, 9-10 AM IST** — rule applied: `long-advanced`. Long-form, and while base audience level is Intermediate, the actual content (protocol mechanics, stateless handle-passing, routing headers) is practitioner-depth material closer to the advanced end — picking the closer rule explicitly since long-form-intermediate doesn't cleanly match either named rule.
