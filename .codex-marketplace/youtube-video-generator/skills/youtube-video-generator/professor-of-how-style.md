
# Professor Of How — Visual Style Blueprint and Prompt Templates

Reference templates for the cinematic 3D short-form educational video style.
Used by the youtube-video-generator skill when the user selects
"Cinematic 3D — Professor of How style" in the visual style gate.

---

## When to Apply This Style

Use when:
- Video format is Short (60-90 seconds)
- Script language is Hinglish or Devnagri Hindi
- User selects "Cinematic 3D" in the visual style elicitation gate
- Topic is science, biology, physics, space, psychology, or "how does it work"

Do not use for:
- Long-form technical tutorials (architecture diagrams suit those better)
- Code walkthroughs or developer content
- Abstract software concepts (Archify diagrams suit those better)

---

## Visual Style Blueprint (Mandatory for Cinematic 3D Mode)

Lighting: Cinematic high-key studio lighting with strong rim-lighting
(backlighting) to define silhouettes. High contrast with deep shadows.
Use caustic light refractions for fluids and subsurface scattering for
organic tissues (skin, cells).

Color Grading: High-saturation palette. Use Teal and Orange or Deep Blue
and Gold cinematic contrast. Biological entities use vibrant reds and pinks.
Technical or environmental elements use cold blues.

Camera: Professional macro-cinematography. 85mm to 100mm focal lengths for
tight shots. Frequent fly-through transitions (moving through skin pores,
bullet holes, eye structures) and orbital pans. Shallow depth of field with
creamy bokeh.

Subjects: Hyper-detailed 3D models with PBR (Physically Based Rendering)
textures. Realistic biological structures (cornea, follicles, bacteria) or
mechanical components that appear tangible and high-fidelity.

Environment: Abstract dark voids or layered cross-sections (anatomical layers,
material layers). Floating micro-particles or dust motes for background depth.

Render Quality: 8K photorealistic output. Sharp focus on textures like metallic
sheen, liquid viscosity, or fibrous weaves. No flat colors.

Animation Style: Fluid, physics-based movement. Slow-motion captures of
high-speed events. Micro-vibrations for microscopic entities.

---

## Topic Ideation Prompt Template

Used when user asks for ideas before providing a topic.

Prompt to feed the research subagent:

"Generate 30 highly engaging YouTube Shorts ideas for an educational channel.
Each idea must trigger strong curiosity and emotional intrigue. Ideas should
cover science, human biology, physics, space, daily life phenomena, history,
or psychology. Each idea must make the viewer think 'Wait, what?' or
'I never knew that.' Write each as a clickable hook-style title. Avoid
generic or overused topics unless you add a fresh angle. Avoid controversial
political topics. Format: numbered list, titles only, no explanations."

---

## Script Style Template (Curiosity Short)

Used when user selects the Curiosity Short script style.

Structure (120-150 words, 60 seconds max):
1. Hook (3-5 seconds) — strong attention-grabbing opening, states the mystery
2. Core explanation — clear, simple, value-packed. Avoid complex jargon.
3. Mind-blowing insight or twist — the reveal the hook promised
4. Memorable ending line — thought-provoking, not generic CTA

Rules:
- Keep sentences short and punchy
- No filler lines
- Tone: curious, fast-paced, slightly dramatic but fact-based
- No generic closing lines like "like and subscribe"
- Target: 16-30 years old

---

## Per-Shot Storyboard Prompt Format

Generated in Step 9b for each script line. Use this exact format:

Scene ID: [Numerical]
Line ID: [Numerical]
Shot ID: [Numerical]

Exact Script Line (FULL): "[Full original line from script]"

Exact Words This Shot Covers:
"[Starting words]" to "[Ending words]"

IMAGE PROMPT: [Subject and environment], [Lighting and mood],
[Camera angle and lens, e.g. 100mm Macro], [Depth of field, e.g. f/2.8 bokeh],
[Composition, e.g. Rule of Thirds], [Color tone], ultra-detailed 8K cinematic
PBR render, Octane render style.

ANIMATION PROMPT: [Camera movement, e.g. orbital pan, slow zoom-in],
[Subject motion, e.g. fluid turbulence, mechanical rotation],
[Background motion, e.g. floating particles],
[Pacing, e.g. 24fps cinematic slow-motion],
[Micro details, e.g. light flicker, subsurface scattering pulse, dust motes].

Forbidden words in prompts: cool, nice, detailed, amazing.
Required technical vocabulary: volumetric lighting, anamorphic flares,
chromatic aberration, tessellated textures, subsurface scattering,
caustic refractions, PBR textures, depth of field, bokeh, parallax.

---

## Auto Whisk Export Format

After all per-shot prompts are generated, export them as a flat text file
called image-prompts-whisk.txt in the episode folder.

Rules:
- One prompt per paragraph
- No headings, no Scene IDs, no numbering, no labels
- Each IMAGE PROMPT as a single continuous paragraph
- Separated by exactly one blank line
- No ANIMATION PROMPT in this file (image generators only)
- No added explanations or metadata

This file is ready to paste into Midjourney, Adobe Firefly, Google Whisk,
or Ideogram for batch image generation.

---

## TTS Conversion Rules (Devnagri Hindi Mode)

When language is set to Devnagri Hindi:
1. Extract only the spoken script from script.md
2. Ignore headings, visual tags, callout tags, labels, formatting
3. Convert Hindi words to Devnagri script
4. Keep all English technical words in English (brain, cells, bacteria, etc.)
5. Do not translate English words to Hindi
6. Smooth natural spoken flow — not translated, not robotic
7. Save as narration-hindi.txt alongside narration.txt
8. Pass narration-hindi.txt to the TTS step instead of narration.txt

For Hinglish mode:
1. Script mixes Hindi and English naturally — do not convert to Devnagri
2. Keep the mix as written
3. Pass narration.txt as-is to TTS step
4. Voice recommendation: use a multilingual voice if available in Gemini TTS
