---
name: ebook-forge
description: Compiles a themed cluster of this blog's published posts (from _posts/) — and optionally not-yet-written material from raw/ — into a coherent ebook manuscript, complete with a real table of contents, an author's-voice preface, and connective tissue between chapters, rather than just concatenating posts back to back. Use this when the user wants to turn a series of blog posts into a book/ebook, asks for a "manuscript", wants to compile posts on a theme (e.g. "the Principal-engineer bash series", "all my AI/agent posts") into one document, or asks how their blog output could become a book. Do NOT use this for writing a single new post from raw notes — that's the raw-to-post skill.
---

# Ebook Forge: posts → manuscript

## Why a straight concatenation doesn't work

Every post in `_posts/` is written to stand alone — each one re-establishes
context, re-introduces the author's recurring frameworks, and ends with its
own action items and teaser. Stapled together unedited, a "book" made of
posts reads as repetitive and un-booklike: the same throat-clearing five
times, no sense of a larger argument accumulating. The actual work of this
skill is building the connective tissue and cutting the redundancy — the
individual chapters (the posts) are already good; assembling them is a real
editorial job, not a file-concatenation job.

Read `raw-to-post/references/voice-profile.md` for the author's voice DNA —
the preface and connective material need to sound like the same person, not
like a table of contents generator.

## Pipeline

### 1. Scope the theme with the user

Ask (if not already clear): what's the theme, and roughly what's the
audience/promise of this book? "A collection of my posts" is too broad to
edit well — "a book that takes a senior engineer from writing scripts that
work to writing scripts that survive on-call" is a real spine to build a TOC
around.

### 2. Gather candidates

Search by tag/category/keyword, e.g.:
```bash
grep -rl "<tag-or-keyword>" _posts/**/*.md
```
Read each candidate's full text, not just the title — confirm it actually
fits the theme and check its "反直觉的洞察" (the one counter-intuitive claim
each post commits to, per the humanity checklist) so you can sequence
chapters by argument, not just by publish date.

Also ask the user whether any `raw/` notes that never became posts should be
folded in as a chapter — sometimes the rawest, most in-progress thinking
is exactly what belongs in a book's final chapter or appendix ("where I'm
still stuck").

### 3. Design the arc, not just the order

Propose a chapter order to the user before writing connective text. Options
worth considering: chronological (shows how the author's thinking evolved —
honest, but not always the strongest read), difficulty-ascending (Senior →
Principal, mirrors this author's own recurring framing), or
problem-clustered (group by the kind of failure mode, e.g. "hidden state",
"declarative vs imperative", "default values"). Get the user's sign-off on
the arc before drafting — restructuring after full connective text is
written is expensive.

### 4. Write the connective tissue

- **Preface**: in the author's voice (see voice-profile.md), a few
  paragraphs on why this cluster of posts belongs together and what the
  reader will be able to do differently by the end. Draw on the author's
  known facts (~20 years in the industry, mentoring background) rather than
  inventing new biography.
- **Chapter transitions**: a short paragraph before each chapter (2-5
  sentences) bridging from the previous chapter's ending to this one's
  opening — reuse the previous chapter's synthesis table/teaser as the
  hook instead of writing a fresh generic intro.
- **Deduplication**: when two posts both re-explain the same background
  concept (e.g. two posts both re-derive what `kubectl wait` is), keep the
  fullest explanation once — in the chapter where it's most load-bearing —
  and replace the repeat in later chapters with a one-line callback
  ("as chapter 2 covered, ..."). Flag any cut to the user rather than
  silently dropping content that might have been load-bearing for that
  specific post's argument.
- **A closing chapter or afterword** that ties the individual chapter
  aphorisms together into the book's single larger claim — this is the
  same synthesis move each individual post makes at its own ending, one
  level up.

### 5. Assemble the manuscript

Write to `ebooks/<book-slug>/manuscript.md` (create the directory; this is
new to the repo, separate from `_posts/` since it's not meant to be served
as web pages directly). Structure:

```markdown
# <Book title>

## Preface
...

## Table of Contents
1. <Chapter title> — from `_posts/.../slug.md`
2. ...

## Chapter 1: <title>
<transition paragraph>
<chapter body, lightly re-edited from the source post: strip frontmatter,
adjust any "in this post" phrasing to "in this chapter", cut the
duplicated background per step 4>

## Chapter 2: <title>
...

## Afterword
...
```

Keep a comment at the top of the manuscript noting the source post file for
each chapter, so future edits to the original posts can be reconciled back
into the book.

### 6. Offer export

This repo already has `docx` and `pdf` skills available for turning a
finished markdown manuscript into a distributable file — offer to hand the
assembled manuscript to one of those once the user confirms the content and
arc are right. Don't run the export until the user has actually reviewed the
manuscript; assembling wrong connective tissue is cheap to redo in markdown,
expensive to redo after a full docx/pdf pass.

### 7. Bilingual books

If the source posts are bilingual pairs, ask whether the user wants one
manuscript per language or a single bilingual edition — don't assume; the
right call depends on the intended audience/publishing channel, which only
the user knows.
