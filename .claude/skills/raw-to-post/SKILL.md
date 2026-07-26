---
name: raw-to-post
description: Turns a raw idea/notes file from raw/ (or a rough idea the user just typed out) into a publish-ready bilingual (Chinese + English) technical blog post for this Jekyll site (todzhang.com), matching the blog's established house voice — narrative hook, chapter structure with tables and mental-model callouts, philosophy-quote framing, and an action-items/teaser ending. Use this whenever the user wants to draft, write up, turn into a post, distill, or publish a blog entry from something in raw/, wants to convert notes/ideas/a brain dump into a blog post for this repo, or asks "help me write this up" / "把这个写成博客" about a technical or personal-growth topic. Also use it when the user wants feedback on whether a draft post sounds like them or sounds like generic AI writing.
---

# Raw → Post: distilling ideas into this blog's voice

## Why this exists

The user's theory of learning here is 输出倒逼输入 — writing forces real
understanding, and it also builds their name in the industry. Both goals die
if the output reads like generic AI-blog filler. Your job is not "write a
blog post about X" — it's "help this specific author turn their own raw
thinking into the sharpest, most recognizably-theirs version of that
thinking, in the exact shape their readers already expect from them."

Read `references/voice-profile.md` in full before drafting anything — it's
the distilled house style, extracted from real published posts, not a
generic "how to write a tech blog" guide. Read `references/humanity-checklist.md`
before calling any draft finished — it's the gate that keeps output from
drifting into AI sameness.

## Pipeline

### 1. Find and read the source material

- If the user points at a `raw/*.md` file, read it in full. These files are
  dense, compressed personal notes (often using the author's own shorthand
  frameworks like 根干枝叶, 第一性原理, 五个为什么) — they are the real
  intellectual content, just not yet shaped into prose. Don't treat them as
  a rough draft to lightly edit; treat them as ore to smelt.
- If the user just typed an idea inline with no raw file, that's fine too —
  treat their message as the raw material, and consider offering to save a
  distilled version back into `raw/` first (see the `raw-capture` skill) so
  the knowledge base grows even if this particular idea doesn't become a
  post today.
- Skim 2-3 *existing* posts close to this topic (`grep -rl <keyword>
  _posts/`) so you don't repeat an argument the author has already made, and
  so you can cross-link or explicitly build on a previous post if relevant.

### 2. Find the spine

Before writing a single line of the post, identify out loud (to the user,
briefly) what you think:

- **The one counter-intuitive claim** the post is actually making. If the
  raw notes contain several, ask the user which one is the spine — a post
  that tries to carry three equally-weighted insights usually ends up
  saying none of them memorably.
- **What kind of hook fits**: a real incident the user can confirm happened,
  a first-person confession, or a more essayistic/philosophical opener (see
  `tianren-wushuai-philosophy` for the non-incident-driven mode). Don't
  default to "Alex" reflexively — check `humanity-checklist.md`'s interview
  questions first.
- **tech vs life category** — most posts are `tech`; use `life` when the
  core content is career/philosophy/personal-growth rather than a technical
  mechanism.

### 3. Run the required interview

Per `humanity-checklist.md`, ask the user the few sharp questions about real
details, real opinions, and real anecdotes *before* drafting the hook. This
is the step most likely to get skipped under time pressure — don't skip it.
It's fine to batch these into one short message.

### 4. Draft the Chinese version first

Chinese is this blog's primary voice — the English version is an adaptation,
not the source. Follow the structural skeleton in `voice-profile.md`:
frontmatter → opening quote → hook → reader-value preview → chapters (code
anchors, tables, one named mental model each, a one-line chapter closer) →
synthesis → action items → teaser → closing aphorism.

Concretely:
- Pick a real, attributable opening quote (ask the user if unsure, or
  propose 2-3 candidates that fit the spine).
- Write the hook using only real or user-confirmed details.
- For every comparison (bug vs. fix, default vs. override, before vs.
  after), reach for a table before reaching for prose — that's this
  author's default move, not decoration.
- Pull at most 1-2 terms from the vocabulary bank in `voice-profile.md` per
  post. Repeating the same framework in every post is the fastest way to
  make this voice start sounding like a template.
- End with "立刻可以做的事" (concrete, tied to the reader's own repo/team —
  not generic advice) and a "预告" only if there's a genuine next post in
  mind; ask the user rather than inventing a series commitment they didn't
  make.

### 5. Adapt (don't translate) the English version

Re-derive the hook and idiom for an English-reading audience while keeping
the same argument, code, and tables. A phone call at "凌晨两点" and one at
"11pm" carry different connotations in each culture — pick what lands, don't
transliterate. Confirm both versions reach the same stance in the synthesis
section.

### 6. Mechanics — file placement and frontmatter

Follow `voice-profile.md`'s "Mechanics" section exactly:
- `_posts/YYYY/MM/DD/YYYY-MM-DD-<slug>-zh.md` and `...-en.md` (create the
  date directories if they don't exist).
- Frontmatter fields in the documented order and format, `permalink:
  /blogs/<category>/<lang>/<slug>` with `zh`/`en` (never `cn`).
- Pick `header.image` from existing files under `assets/images/` — search
  first (`ls assets/images | grep -i <keyword>`, and check the `hd_*`
  library), never invent a new image file.
- Pick tags from the existing tag vocabulary where reasonable
  (`grep -rh '  - ' _posts | sort | uniq -c | sort -rn` to check), 3-5 tags.

### 7. Run the humanity checklist before presenting the draft

Walk through every item in `references/humanity-checklist.md`'s "What every
draft must have" and "Phrases and moves to never use" sections explicitly.
Fix anything that fails rather than presenting a draft you know is weak on
one of these axes. If something can't be fixed without more input from the
user (a missing real anecdote, an unconfirmed number), say so plainly
instead of quietly filling the gap with something invented.

### 8. Hand back to the user

Tell the user where the files were written, what's still a placeholder that
needs a real detail from them, and ask whether they want it committed. Do
not commit/push without being asked — publishing to a public blog is a
visible action, treat it like one.

## Reference files

- `references/voice-profile.md` — the structural skeleton, the mental-model
  vocabulary bank, recurring rhetorical devices, and the exact file/frontmatter
  mechanics. Read this before drafting.
- `references/humanity-checklist.md` — the anti-genericness gate and the
  required-interview questions. Read this before drafting and again before
  declaring a draft finished.
