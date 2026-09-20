# Episode 02 — Metadata

## Title options

1. **MCP: Server, Client, Tools, Resources, Prompts & Discovery (Recommended)**
2. What an MCP Server Exposes and How Clients Find It — 2026 Spec
3. The Three Primitives of MCP: Tools, Resources, Prompts

## Tags

MCP, Model Context Protocol, tools, resources, prompts, tool discovery, stateless MCP, JSON-RPC, stdio transport, caching, handles, API design, protocol design, local development, July 2026 spec, intermediate audience

## Hashtags

#MCP #ModelContextProtocol #Stateless #Tools #Resources #Prompts #APIDesign #DeveloperTools

## Description

You know MCP exists. Here's what it *actually* does — all three primitives, how they fit together, and why the 2026 stateless spec changes everything.

An MCP server exposes three things:
- **Tools** — callable actions (functions) with schemas
- **Resources** — read-only context data (files, docs, database records)
- **Prompts** — reusable instruction templates the server composes

The client discovers all three via cacheable list requests. Then it calls tools, passing stateless handles back as ordinary arguments — the server never remembers your session, you carry proof of state explicitly through every request.

Local development: stdio transport, JSON-RPC 2.0 messages, no handshake, no session IDs. Scales horizontally behind plain load balancers.

In this episode:
- What servers expose (tools, resources, prompts) and why three primitives
- How clients discover (cacheable lists with TTL hints)
- The mental shift: stateless handles instead of session IDs
- Why that matters for scaling, load balancing, and developer simplicity
- Building and debugging locally via stdio JSON-RPC

Episode 2 of MCP: Zero to Hero. Next: what the client side implements.

## Connect

Connect with me:
LinkedIn: https://www.linkedin.com/in/aiops-genai-developer
Medium: https://medium.com/@soumya14041987
AWS Builder Center: https://builder.aws.com/
X: https://x.com/AIWithSoumya
GitHub (series code + episode assets): https://github.com/Soumya14041987/mcp-zero-to-hero

## Recommended slot

**Saturday, 9-10 AM IST** — rule applied: `long-intermediate`. Long-form (5–7 min), Intermediate level. Technical depth (protocol mechanics, stateless design, handles) but explained for intermediate audience — some jargon with glosses, no hand-holding on basics. Consistent with EP01 timing.
