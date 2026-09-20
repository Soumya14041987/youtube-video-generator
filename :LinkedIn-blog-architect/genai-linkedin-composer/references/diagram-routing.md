# Diagram routing

Every post ships with one visual. Which tool builds it depends on what
the post is actually claiming.

## Route to `archify` skill when the post is about a real system

The post names actual components with a real topology: a Kubernetes
cluster, an AWS service call chain, a Terraform-provisioned stack, an
agent orchestration graph (LangGraph nodes/edges, Bedrock AgentCore
runtime + tools), a CI/CD pipeline, a data pipeline.

Signals: the draft or source material names specific services/resources
("EKS", "Bedrock AgentCore runtime", "an ALB in front of two ASGs",
"a LangGraph state machine with three tool nodes"), or describes a
request/data flow between named components.

Output: architecture, sequence, or dataflow diagram, dark/light theme,
exportable to PNG for the LinkedIn post attachment.

## Route to image-gen (infographic) when the post is a concept or a stat

The post makes an abstract point, a comparison, or leads with a number:
"why agentic AI needs memory," "cost of running X vs Y," a before/after
claim, a definition post, a myth-busting post.

Output: a clean infographic — big number or comparison as the visual
anchor, minimal text (the post copy carries the explanation, the image
carries the one number or contrast a scroller catches in half a second).

## Ambiguous cases

A "we migrated from X to Y" post is architecture (route to archify) if
the value is in what changed structurally; it's an infographic (route to
image-gen) if the value is in the outcome number (cost, latency, time
saved). When both are true, default to architecture — this skill's whole
differentiator is that the visual shows the real mechanism, not a stat
card. Save the stat for the post copy's opening line instead.

## Never

Never ship a post with no visual, and never ship a stock-photo-style
generic AI image with no technical content — it reads as filler and
undercuts every claim in the post above it.

## Authoring with archify (learned from the first end-to-end run)

archify is a separate skill, not bundled here. It needs Node 18+, and PNG
export needs Google Chrome or Chromium. Write the spec, then run
`archify validate` (showcase quality, all 9 checks), `archify deliver`, and
`archify visual-check`, then export the PNG with `scripts/export_png.py`.
visual-check's own screenshots include the viewer toolbar, so don't post them.

Rules that cost a wasted round each the first time:

- **Put numbers in `sublabel` or edge `label`, never only in `tag`.** Node tags
  are drawn at "fine" detail and stay invisible until the viewer is zoomed, so a
  static PNG loses them. The cold-start figures in the first attempt vanished.
- **Set `meta.legend.mode` to `hidden`** when your node types don't match the
  workflow legend's built-in names ("Tool action", "Cloud service"), which would
  mislabel them.
- **Skip `cards` for an image.** They push the page past the viewport and fail
  visual-check. Put the source and any vendor-benchmark caveat in the title,
  for example "(AWS-reported P75)".
- **Keep labels short.** The validator rejects a label wider than its node
  (about 13 characters at the default width); shorten the label and move detail
  into the sublabel, or set `width`.
- **Only draw what the source states.** Don't invent internal steps for a
  system the announcement doesn't describe.
- Known cosmetic quirk: node icons can overlap the first letter of a label.
