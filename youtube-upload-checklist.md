# YouTube Upload Checklist — every episode

Follow this exact sequence in YouTube Studio's upload flow (Details → Video
elements → Initial check → Visibility). Every field below maps to a value
already sitting in that episode's `metadata.md` and `promo-draft.md` — copy,
don't retype.

## Before you start

- File to upload: `episodes/episode-NN-<slug>/episode.mp4`
- Name the upload file something you can recognize in Studio's history —
  `episode-NN-<slug>.mp4` matches the project convention (rename before
  upload if it came out as something generic like this session's
  `MCP-newly-discover.mp4`).

## Step 1 — Details

- **Title**: paste Title option 1 from `metadata.md` (or whichever of the
  2-3 options you prefer — they're pre-written, don't freehand a new one
  mid-upload).
- **Description**: paste the entire `## Description` block from
  `metadata.md`, verbatim, including the `## Connect` footer and the
  hashtag line at the end.
- **Thumbnail**: click **Upload file** (not "Select from video" — the
  channel's thumbnails are purpose-built, not auto-picked frames) → choose
  `thumbnail-final.png` from that episode's folder.
- **Playlist**: add to **MCP: Zero to Hero** (create it once on the first
  upload, then just check the box on every subsequent one — matches
  `playlists/mcp-zero-to-hero.md`).
- **Audience**: "No, it's not made for kids" — standard for this channel's
  content.
- **Age restriction**: no.
- Expand **Show more**:
  - **Tags**: paste the comma-separated list from `metadata.md`'s `## Tags`
    section directly into the tags field.
  - **Category**: Science & Technology.
  - **License**: Standard YouTube License.
  - **Comments**: default (hold potentially inappropriate comments for
    review) unless you want it more/less moderated.
- Ignore **A/B Testing** on title/thumbnail for now — worth using later
  once the channel has enough baseline views to make a test meaningful,
  not on early episodes with low traffic.

## Step 2 — Video elements

- **Subtitles**: do **not** upload a caption file — this pipeline
  deliberately ships with no burned-in captions so YouTube's own
  automatic-captions can generate and sync against the real audio. Leave
  this step empty; captions appear on their own after processing (can take
  longer than the video processing itself — check back later, don't wait
  here).
- **End screen**: optional. Once episode 2+ exists, add a "Video" element
  pointing to the next episode in the series plus a "Subscribe" element.
  On episode 1 (nothing to point to yet), a Subscribe-only end screen is
  fine, or skip entirely and add end screens retroactively once the
  playlist has more entries.
- **Cards**: optional, same logic as end screens — more useful once there's
  a next episode to link to mid-video.

## Step 3 — Initial check

YouTube scans for Content ID / copyright matches automatically. Nothing to
configure — just wait for the check to clear before moving on. If
something flags here on a channel with only original narration + generated
diagrams, it's almost always a false positive on background music (this
pipeline has none) — investigate before dismissing, don't just click past
a real claim.

## Step 4 — Visibility

- Set to **Private** first, click through to finish processing, and copy
  the video link (Studio shows it during processing, top-right area, as
  seen mid-upload — `https://youtu.be/...`).
- Use that private link to do a final personal watch-through (captions
  rendered correctly, thumbnail looks right in context) before it's public.
- Then switch to either:
  - **Public**, immediately, if posting to LinkedIn/Facebook right after, or
  - **Scheduled**, set to the slot in `metadata.md`'s `## Recommended slot`
    section (this channel's rule: Saturday 9-10 AM IST for long-form/
    advanced content, Tue/Thu/Sat/Sun 8-9 PM IST for short-form/beginner).
- Only grab the real link for your LinkedIn/Facebook posts (`promo-draft.md`)
  once it's Public or the Scheduled time has actually passed — a private
  link in a public post is a dead link to everyone else.

## After publishing

- Check YouTube Studio analytics at 24-48h — retention curve and CTR tell
  you whether the hook/thumbnail worked before you promote the next
  episode the same way.
- Log the real published URL somewhere durable if you want it (not
  currently a tracked field in `series-log.md` — add one if this becomes a
  recurring need).
