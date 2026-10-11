# To setup for a new blog

To run below command setup folder and files

```shell
mkdir -p ~/dev/ws/todd/cloudsdocker.github.io/_posts/2025/"10"/"1011"
```

Then use your keyword to create a file 
```shell
touch ~/dev/ws/todd/cloudsdocker.github.io/_posts/2025/"10"/"1011"/"2026-10-11-fix-annoying-fake-security-prompt-in-docker-desktop-in-macbook.md"
```

Then download the blog source to clipboard
```shell
cat ~/Downloads/docker-desktop-security-fix.md | pbcopy
```

# AI-assisted workflow (raw idea → post → book)

This repo uses `raw/` as a scratchpad for technical ideas, and Antigravity / Claude Code skills to turn raw material into publication-ready output in this blog's authoritative voice without generic AI filler:

- **`chat-to-blog`** — captures the active AI conversation (or specific solutions) directly into a markdown draft under `raw/`.
- **`raw-capture`** — quickly saves a new idea into `raw/` (low friction, unpolished notes).
- **`raw-to-post`** — distills a rough idea into an initial bilingual draft in `raw/` for review.
- **`raw-to-blog`** — **promotes & rewrites a `raw/*.md` note into publication-grade bilingual (`zh` + `en`) posts under `_posts/YYYY/MM/DD/`**:
  - **Zero material loss**: Output length is strictly $\ge$ input note; preserves 100% of technical details, formulas, tables, and code.
  - **Authoritative stance**: Transforms interview/exam framing into a Lead AI Engineer perspective in enterprise production (Aegis / tier-1 carrier).
  - **Language-specific opening quotes**: Enforces authentic Chinese quotes (`> “...”`) on Line 1 of Chinese articles (never English quotes), and matching English quotes for English articles.
  - **Zero banned phrases**: Deterministically eliminates AI cliches and kill-list words (especially `闭环`).
  - **Deterministic validation**: Auto-validates output via `editorial_policy.validate_post` and backs up the original note to `raw/archive/`.
- **`ebook-forge`** — compiles a themed cluster of published posts into an ebook manuscript under `ebooks/`.

### How to trigger `raw-to-blog`:
Simply say to the AI assistant (Antigravity or Claude):
> *"raw to blog"*
> *"publish raw blog from raw/2026-10-09-ai-observability-cost-control.md"*

The assistant acts as the LLM engine directly without external API calls, writing the final bilingual posts to `_posts/` and running automated validation.
