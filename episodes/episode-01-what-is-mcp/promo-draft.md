# Episode 01 — Promo Draft (YouTube + LinkedIn + Facebook)

## 1. Thumbnail

File: `thumbnail-final.png` (currently a copy of `thumb-a.png` — headline "MCP ALREADY CHANGED ONCE").
Alternative: `thumbnails/thumb-b.png` — headline "THE REWRITE MOST EXPLAINERS MISS".
Both are 1280x720. Pick whichever headline you think earns more clicks — `thumb-b` leans harder into the differentiated angle, `thumb-a` is the more universal hook.

## 2. YouTube upload draft

**Title** (pick one):
1. MCP Fundamentals, Components, and the Rewrite Most Explainers Skip
2. What is MCP? The 2026 Update Every Tutorial Missed
3. MCP: How It Actually Works Now (Not in 2024)

**Description:**
```
Almost every "MCP explained" video still teaches November 2024's stateful handshake — the initialize/initialized exchange, the session ID pinning a connection to one server instance. That version of MCP doesn't exist anymore.

This episode covers MCP as it works today: fundamentals, the three core components (host, client, server — plus tools, resources, prompts), why MCP exists (the M×N integration problem, explained with a concrete 5-app/5-tool example), and how the July 2026 spec rewrite went stateless — removing the handshake entirely so MCP servers can finally sit behind a normal load balancer.

In this episode:
- What MCP is and why it exists (the M×N problem: 5 apps × 5 tools = 25 integrations → MCP makes it 5+5 = 10)
- The three architecture roles and three server primitives
- The original stateful handshake vs. the current stateless request model
- Why mass 2025 adoption is what forced the 2026 rewrite
- What's now an extension (Tasks, MCP Apps) vs. deprecated (Roots, Sampling, Logging)

Episode 1 of the MCP: Zero to Hero series. Follow for the next one.

Connect with me:
LinkedIn: https://www.linkedin.com/in/aiops-genai-developer
Medium: https://medium.com/@soumya14041987
AWS Builder Center: https://builder.aws.com/
X: https://x.com/AIWithSoumya

#MCP #ModelContextProtocol #AgenticAI #AITools #MCPZeroToHero
```

**Tags (comma-separated, paste into YouTube's tags field):**
```
MCP, Model Context Protocol, MCP fundamentals, MCP architecture, AI agents, Agentic AI, Anthropic, AI tooling, MCP tutorial, stateless MCP, MCP 2026, AI protocol, LLM tools, MCP components
```

**Category:** Science & Technology
**Visibility on publish:** Public (or Scheduled for Saturday 9-10 AM IST per the slot recommendation)
**Captions:** Don't upload a caption file — enable YouTube's automatic captions in Studio after processing finishes (this pipeline deliberately doesn't burn in captions).
**Playlist:** Add to (or create) "MCP: Zero to Hero" playlist on your channel — matches `playlists/mcp-zero-to-hero.md`.

## 3. LinkedIn announcement draft

```
Most "MCP explained" content out there — including a lot of what I've watched — still teaches the version of the Model Context Protocol that launched in November 2024. Session handshakes. Sticky connections. A model that Anthropic itself rewrote in July 2026.

I put together Episode 1 of a new series, MCP: Zero to Hero, to cover MCP as it actually works today — not as a footnote update, but as the baseline.

What's in it:
→ The M×N integration problem, with a real example: 5 AI apps × 5 tools = 25 custom integrations to hand-build and maintain. MCP turns that into 5+5 = 10.
→ The three architecture roles (host, client, server) and three server primitives (tools, resources, prompts)
→ Why the original stateful handshake got replaced — mass 2025 adoption exposed a scaling problem (sticky sessions don't work behind a normal load balancer)
→ What's now a first-class extension (Tasks, MCP Apps) vs. what's being deprecated (Roots, Sampling, Logging)

If you're building with AI agents — or explaining MCP to your team — this is the version worth knowing.

📺 Watch: [YouTube link once uploaded]

Would genuinely value thoughts from anyone in the GenAI, CNCF, and AWS Community Builders spaces here — especially if you've hit the stateful→stateless migration in practice.

#MCP #ModelContextProtocol #GenAI #AgenticAI #CNCF #AWSCommunityBuilders #AIOps #DevOps #CloudComputing
```

## 4. Facebook announcement draft

```
New video: MCP: Zero to Hero, Episode 1 🎬

If you learned MCP (Model Context Protocol) any time before mid-2026, the version in your head is probably out of date — the handshake and session-ID model from launch got replaced with a stateless rewrite in July 2026.

This episode covers MCP as it actually works right now: what it is, why it exists (the classic M×N integration problem — 5 apps × 5 tools = 25 integrations, down to just 10 with MCP), the 3 architecture roles, and what changed in the rewrite.

Built for anyone working with AI agents, tooling, or just trying to keep up with how fast this space moves.

🔗 [YouTube link once uploaded]

Tag someone who's still explaining the old handshake model 👀

#MCP #ModelContextProtocol #AI #GenAI #AgenticAI
```

## 5. Step-by-step: getting this in front of your network

1. **Upload to YouTube first, unlisted.** Use the title/description/tags/thumbnail above. Don't publish public yet — you need the real video link for the LinkedIn/Facebook posts.
2. **Add captions**: in YouTube Studio, wait for automatic captions to generate (can take 10-30 min after upload), spot-check the first minute for accuracy (jargon like "MCP," "Anthropic" is where auto-captions most often mangle).
3. **Switch visibility to Public** (or schedule for Sat 9-10 AM IST per the metadata recommendation — YouTube Studio's schedule option lets you set this and share the link before it's technically live, though the page won't be watchable until then; simplest is to just publish public when ready and post the real link to socials right after).
4. **Copy the real video URL.**
5. **Post to LinkedIn** using the draft above with the real link swapped in. Post it as your own update, not just a share — original text posts outperform link-only shares in LinkedIn's feed algorithm.
6. **Cross-post into relevant LinkedIn Groups/communities manually** — AWS Community Builders and CNCF-affiliated groups typically have their own LinkedIn Group or community feed distinct from your personal post; if you're a member, share the post there too (LinkedIn doesn't let you auto-crosspost to groups from a personal post, it's a separate manual share).
7. **Post to Facebook** using that draft, into your own timeline and into any GenAI/CNCF Kolkata Facebook groups you're a member of (community groups often have their own posting rules — check if they want a text summary + link vs. a native video upload; some groups' algorithms favor native uploads over external YouTube links).
8. **CNCF Kolkata / AWS Community Builders specifically**: these usually also have Slack or Meetup community channels separate from Facebook/LinkedIn — if you're active there, a short manual note with the link tends to land better than a copy-pasted promo post, since these are practitioner communities that respond to a personal "here's something I built, thought this group would find it useful" framing over a broadcast-style announcement.
9. **First 24-48h**: watch retention/CTR in YouTube Studio's analytics — this tells you whether the hook and thumbnail are working before you invest in episode 2's promotion the same way.

I can't post any of this for you — no LinkedIn/Facebook/YouTube API access from here, and that's also not something I'd do without you reviewing the live post first. Everything above is ready to copy-paste; steps 1-9 are the manual sequence.
