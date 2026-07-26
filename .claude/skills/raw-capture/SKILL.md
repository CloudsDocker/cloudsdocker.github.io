---
name: raw-capture
description: Captures a fast, low-friction note into raw/ when the user has a half-formed idea, a realization from a debugging session, or a brain dump they want saved before it evaporates — without expanding it into a full blog post yet. Use this when the user says things like "记一下这个想法", "add this to raw", "capture this before I forget", "笔记一下", or dumps a stream-of-consciousness technical insight and just wants it saved, not published. Do NOT use this for turning a raw note into an actual blog post — that's the raw-to-post skill's job.
---

# Raw Capture

## Why this is a separate skill from raw-to-post

输出倒逼输入 only works if both ends of the loop are cheap. If capturing an
idea takes as much effort as writing the finished post, ideas stop getting
captured at all, and the `raw/` well runs dry. This skill's only job is to
get a real idea onto disk, in the author's own compressed shorthand, as fast
as possible — polish and structure happen later, in `raw-to-post`.

## What to preserve vs. what to clean up

Look at the existing files in `raw/` before writing a new one — they range
from tightly structured (`claude_inside.md` uses the author's own 根-干-枝-叶
— root/trunk/branch/leaf — framework) to a three-line fragment
(`stdout_vs_stderr.md`). Both are valid. Your job:

- **Preserve**: the user's own phrasing, their shorthand terms, any
  half-finished thought marked as unresolved. Don't smooth this into
  finished prose — that's premature and it's not your call to make the
  content sound more confident than the user actually is right now.
- **Clean up**: only mechanical things — fix garbled dictation/OCR-style
  artifacts, deduplicate an accidentally-repeated line, add markdown
  structure (headers, lists) if the note is long enough to need
  navigation. When unsure whether something is signal or noise, ask rather
  than deleting silently.
- **Never add**: content the user didn't say. If you see an interesting
  angle while capturing, you can mention it back to the user as a question,
  but don't fold your own elaboration into their raw note as if they'd said
  it.

## The one thing to always add: a gap marker

Before finishing, ask (briefly, don't force a long reflection if the user's
in a hurry): *"What's the part of this you couldn't yet explain simply to
someone else?"* Add their answer as a short marked line at the end of the
file, e.g.:

```markdown
> 待验证 / 未想清楚：<their answer, verbatim or lightly cleaned up>
```

This is the actual mechanism of 输出倒逼输入 on the input side — the gap is
what makes the eventual post worth writing, and it's what `raw-to-post`
should look for first when it's time to distill this note. If the user says
there's no gap, that's fine — not every note needs one, but always ask once.

## Mechanics

- File: `raw/<topic-slug>.md`, lowercase, kebab-case, matching the existing
  naming style (`langgraph_astream_explained.md` uses underscores — either
  underscore or hyphen is fine, match whichever the user already leans
  toward, don't mix within one filename).
- No frontmatter needed — `raw/` files aren't Jekyll content, they're just
  the author's working notes.
- If a file on the same topic already exists, append to it (with a
  timestamped or clearly separated section) rather than creating a
  near-duplicate file — check `ls raw/` and grep for the topic first.
- Do not touch `_posts/` from this skill. Capture is one-way into `raw/`;
  promoting something to a published post is a distinct, deliberate step the
  user asks for separately (via `raw-to-post`).
