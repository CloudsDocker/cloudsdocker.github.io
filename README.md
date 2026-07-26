# To setup for a new blog

To run below command setup folder and files

```shell
mkdir -p ~/dev/ws/todd/cloudsdocker.github.io/_posts/2025/"$(date +%m)"/"$(date +%m%d)"
```

Then use your keyword to create a file 
```shell
touch ~/dev/ws/todd/cloudsdocker.github.io/_posts/2025/"$(date +%m)"/"$(date +%m%d)"/"$(date +%Y-%m-%d)-fix-annoying-fake-security-prompt-in-docker-desktop-in-macbook.md"
```

Then download the blog source to clipboard
```shell
cat ~/Downloads/docker-desktop-security-fix.md | pbcopy
```

# AI-assisted workflow (raw idea → post → book)

This repo also uses `raw/` as a scratchpad for half-formed ideas and
`.claude/skills/` for Claude Code skills that turn that raw material into
publish-ready output in this blog's own voice, without flattening it into
generic AI writing:

- **`raw-capture`** — quickly saves a new idea into `raw/` (low friction, no
  polishing yet).
- **`raw-to-post`** — distills a `raw/*.md` file (or a fresh idea) into a
  bilingual (zh/en) blog post matching this blog's established structure,
  tables, and recurring frameworks. Reads `raw-to-post/references/voice-profile.md`
  and `humanity-checklist.md` to keep the output sounding like a specific
  person, not an AI template — it will ask for real anecdotes/opinions
  rather than inventing them.
- **`ebook-forge`** — compiles a themed cluster of published posts (plus,
  optionally, unpublished `raw/` material) into an ebook manuscript under
  `ebooks/`, with real connective tissue between chapters instead of a
  straight concatenation.

Point Claude Code at a file in `raw/` and ask it to write the post — the
skills trigger automatically.