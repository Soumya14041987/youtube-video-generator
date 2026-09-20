# voice.md

<!-- Section layout adapted from templates/voice.md in Jakeschincariol/linkedin-agent-skill (MIT). See THIRD_PARTY_NOTICES.md. -->

Copy this to `~/.claude/linkedin/voice.md` (or pass a path with `--voice`)
and fill it in before running `/lin-blog-architect`. Every step in the
pipeline reads this file — the discovery ranking, the draft, and the QA
gate all check against it. Ten minutes here is the difference between a
post you paste and a post you rewrite from scratch.

If you'd rather not fill it in by hand, paste three of your own LinkedIn
posts into Claude and say "write my voice.md from these."

---

## Who I am

- **Name:**
- **Role, in one sentence:** (e.g. "Sr GenAI Developer building agentic
  systems on AWS Bedrock and EKS")
- **Focus areas:** (e.g. AIOps, Kubernetes, Terraform, Bedrock, Agentic AI,
  LangGraph — list the ones that are actually yours, discovery only pulls
  from these)
- **Who I'm writing for:** (be specific: "platform engineers running LLM
  workloads on k8s", not "tech professionals")
- **What I sell, if anything:** (a product, a service, my own credibility —
  or "nothing, this is a personal brand" is a valid answer)

## What I sound like

- **Three of my own posts that sound most like me:** (paste them, or link them)
- **Words I actually use:**
- **Words I would never use:**
- **Sentence length:** (short and punchy / mixed / long and considered)
- **Do I use emoji:** (never / one, rarely / freely)
- **Contractions:** (yes — almost always yes)
- **Q&A or narrative, as a default:** (per-post override is always allowed)

## My positions

Three to five technical opinions some of my audience doesn't share yet.
This is where the good posts come from, and it's also what discovery
ranks new source material against — a Kubernetes release that doesn't
touch any of these is a low-priority pull, not a post.

1.
2.
3.

## Off limits

- **Topics I don't post about:**
- **Employers, clients, or numbers I can't name publicly:**
- **Claims I'm not allowed to make:** (NDA, employer policy, vendor
  certification rules, anything that reads as investment or compliance
  advice)
- **Phrases the QA gate should hard-fail on, beyond the standard slop
  lexicon:** (anything specific to your industry that reads as fake to
  your audience — e.g. "AI-powered" if you build the AI, "seamless
  integration" if you've ever debugged one)

## Proof I can use

Real numbers, outcomes, incidents, and postmortems you're happy to put
your name on. The pipeline never invents one — if this section is empty,
every draft comes back with `{{your number}}` where a number should be.

-
-
-
