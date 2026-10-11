---
name: raw-to-blog
description: >-
  Promotes and rewrites raw notes from cloudsdocker.github.io/raw/ into publication-grade
  bilingual (Chinese + English) technical blog posts under _posts/YYYY/MM/DD/.
  Implements the full editorial policy and post-assembly logic of post_publisher.py
  and editorial_policy.py without calling external LLM APIs (the agent acts as the
  LLM engine). Enforces that output length is not less than the input note, eliminates
  interview framing in favor of an authoritative Lead AI Engineer perspective,
  enforces Chinese opening quotes for Chinese articles, enforces zero banned phrases
  (especially 闭环), and validates deterministically via editorial_policy.validate_post.
  Use when the user asks to "raw to blog", "publish raw blog", "publish raw note",
  "turn raw into blog", "rewrite raw note into blog", "push raw to post",
  "run push_raw_to_post_folder", or points to a raw/*.md file to publish.
---

# Raw to Blog: Enterprise Tech Blog Publishing Workflow

## Why This Exists

The user writes dense, aggregated technical notes under `cloudsdocker.github.io/raw/` (e.g. `2026-10-09-*.md`). While `post_publisher.py` contains automated pipelines, running them through external local/cloud LLMs often causes unwanted lossy summarization, dropped code snippets, or rate limit failures.

Instead of calling external LLMs, **the agent (Antigravity / Claude) executes the LLM rewrite job directly**, adhering strictly to the author's house style, architectural depth, and editorial constraints.

---

## Non-Negotiable Hard Rules

### 1. Zero Material Loss & Expansion Guarantee (Strict)
- **Output length must NOT be less than the input**: `len(output_post) >= len(raw_note)`.
- **100% Substance Preservation**: Every observation, argument, calculation table, diagram, code block, error message, and nuanced aside from the raw note must be retained.
- **Enrichment, Not Scaffolding**: Add architectural context, historical mechanisms, and deep technical grounding that the author left implicit. Do not pad with generic filler; expand with genuine engineering rigor.

### 2. Language-Specific Opening Quotes (Front of the Page)
- **Chinese Articles (`*-zh.md`) MUST USE A CHINESE QUOTE**:
  - Line 1 of the body MUST be in Chinese, enclosed in full-width CJK quotation marks `“”` (or Chinese dash `——`).
  - **NEVER use an English quote at the front of a Chinese article.**
  - If the raw note has an English quote, translate it into polished, authoritative Chinese aphorism prose, or select a classic Chinese quote that resonates with the core engineering principle (e.g. from 《论语》, 庄子, or translated technical aphorisms like 《Python 之禅》).
  - *Example*: `> “我们衡量我们所珍视的，也珍视我们所衡量的。在人工智能的无声广袤中，一次未被观测的失败不仅是一场技术故障，更是对真实性的悄然侵蚀。”`
- **English Articles (`*-en.md`)**: Line 1 uses the corresponding English quote:
  - *Example*: `> "We measure what we value, and we value what we measure. In the silent expanse of artificial intelligence, an unobserved failure is not merely a technical glitch—it is a quiet erosion of truth."`

### 3. Tone: Authoritative Lead AI Engineer Perspective
- **Purge All Interview Framing**: Completely strip out "面试", "面试官", "面试题", "如果面试官问", "面试拿分点".
- **Replace With Enterprise Engineering Context**:
  - "面试官可能追问" → "在日常技术评审与架构深究中常触及的核心细节 / 老板或 Team Lead 会深入提问的"
  - "在某公司 Lead AI Engineer 面试中" → "作为 Lead AI Engineer，在日常系统架构演进中"
  - "面试回答建议" → "架构方案设计与生产实施路径"
- **Enterprise Anonymization**:
  - Zurich / named insurer → **Aegis** (a global Tier-1 insurance & financial carrier / Fortune Global 100)
  - AWS → **the cloud provider** (or Amazon Bedrock when discussing public APIs)
  - APRA → **local regulators**

### 4. Banned Phrases Kill-List (Zero Tolerance)
`editorial_policy.py` checks these deterministically. Any hit fails the build:
- ❌ **Strictly Banned Chinese Words**: `"在当今"`, `"众所周知"`, `"让我们一起来看看"`, `"总而言之"`, `"值得一提的是"`, `"不难发现"`, `"赋能"`, **`"闭环"`**, `"打法"`, `"抓手"`
- ⚠️ **CRITICAL GOTCHA**: The two-character word **`"闭环"`** is on the kill list! Never use "闭环" in Chinese prose! Instead use:
  - `"数据回流"` / `"反馈链路"` / `"工程回路"` / `"自适应循环"` / `"全链路协同"`
- ❌ **Strictly Banned English Phrases**: `"fast-paced world"`, `"picture this"`, `"let's dive in"`, `"game-changer"`
- ❌ **No Dry Openings**: The post must never open with `"在现代"`, `"在当今"`, `"随着"`, `"众所周知"`, `"In today's"`, `"In modern"`, `"As ..."`.

### 5. Structural Disciplines
- **Line 1 of Body**: Must be a blockquote containing an attributable opening quote: `> "..." — Author` (Chinese for `zh`, English for `en`).
- **Single H1 Title**: Exactly one `# <Title>` in the entire body.
- **Opening Hook**: Must execute an active hook from `HOOK_RULES` (The Indictment Question, The False Consensus, or Artifact First).
- **Visual Artifacts**: Must include comparison tables (`| ... |`), Mermaid diagrams (````mermaid`), flowchart code blocks (````flowchart`), and complete runnable code snippets.
- **Callout Quotas**:
  - At most **two** `📌` takeaways in the entire post.
  - At most **one** `🩸` warning in the entire post.
- **Front Matter Assembly**: Standard Jekyll front matter outside the body:
  ```yaml
  ---
  title: "..."
  header:
      image: /assets/images/<chosen_image>.jpg
  date: YYYY-MM-DD
  tags:
   - tag1
   - tag2
  permalink: /blogs/tech/<lang>/<slug>
  lang: <lang>
  layout: single
  category: tech
  ---
  ```

---

## Step-by-Step Execution Pipeline

### Step 1: Read and Profile the Raw Note
1. Read the target raw file:
   `/Users/toddzhang/ws/todd/cloudsdocker.github.io/raw/<filename>.md`
2. Profile the content:
   - Check character count, lines, existing code blocks, and diagrams.
   - Record the baseline size: the final output must exceed this baseline.
   - Extract the core theme, tags, and date (default to filename date or `date.today()`).

### Step 2: Select Quotes, Imagery & Front Matter Metadata
1. **Opening Quotes**:
   - For `zh`: Craft/translate an evocative, profound Chinese quote. Must contain CJK characters and full-width quotes `“”`.
   - For `en`: Craft/maintain the matching English quote.
2. Resolve the shared slug (e.g. `ai-observability-cost-control`).
3. Pick an appropriate header image from `cloudsdocker.github.io/assets/images/`:
   - Examples: `Cheap_and_flexible_computing.jpg`, `Python-expert-write-code-like-this.jpg`, `AI-basics-talk-about-searches.jpg`.
4. Plan titles for both languages:
   - Chinese: Specific, professional, and authoritative.
   - English: Direct, impactful, matching international engineering blogs.

### Step 3: Modular Generation via Scratch Workspace
> [!TIP]
> Generating a 30k+ character technical post directly inside a Python string literal often causes escaping errors with markdown code blocks and triple-quotes (`"""`). Use the modular scratch approach.

1. Create a build scratch directory:
   `scratch/blog_build/<lang>/` (e.g. `scratch/blog_build/zh/` and `scratch/blog_build/en/`)
2. Write individual chapters as pure `.md` files (e.g. `00_header.md`, `01_section1.md`, ..., `10_qa.md`).
   - For `zh/00_header.md`: ensure Line 1 after front matter is `> “<中文格言>”`
   - For `en/00_header.md`: ensure Line 1 after front matter is `> "<English quote>"`
3. Ensure every section from the raw note is mapped, organized into a clean 8–10 chapter narrative arch, and expanded with technical mechanics.

### Step 4: Assemble and Write Posts
Assemble all chapter `.md` files in order and write directly to:
- Chinese: `cloudsdocker.github.io/_posts/YYYY/MM/DD/YYYY-MM-DD-<slug>-zh.md`
- English: `cloudsdocker.github.io/_posts/YYYY/MM/DD/YYYY-MM-DD-<slug>-en.md`

### Step 5: Archive the Raw Note
Preserve transactional safety by backing up the original raw file:
```python
backup_path = raw_dir / "archive" / f"{raw_stem}.{timestamp}.bak.md"
shutil.copy2(raw_path, backup_path)
```

### Step 6: Deterministic Validation
Run validation against `editorial_policy.py`:
```python
import sys
from pathlib import Path
import re, yaml

sys.path.insert(0, "/Users/toddzhang/ws/todd/effectiveCodingBase/ai/mcp/servers/output-learn-agent")
import editorial_policy

# Split front matter and body
m = re.match(r"^(---\n.*?\n---\n)(.*)$", full_text, re.DOTALL)
assert m, "Missing front matter"
front_matter, body = m.group(1), m.group(2).strip()

# Check quote language
quote_line = body.splitlines()[0]
if lang == "zh":
    assert any('\u4e00' <= ch <= '\u9fff' for ch in quote_line), "Chinese post Line 1 quote must be in Chinese, not English!"
else:
    assert quote_line.startswith("> \""), "English post Line 1 quote must start with > \""

# Run policy checks
issues = editorial_policy.validate_post(body)
assert not issues, f"Validation issues: {issues}"

# Run custom safety checks
assert "面试" not in body, "Found interview tone"
assert "闭环" not in body, "Found banned word 闭环"
assert full_text.count("📌") <= 2, "Too many takeaways"
assert len(full_text) >= len(raw_text), "Output is shorter than raw note!"
```

---

## Quick Reference / Commands

To run validation on generated posts:
```bash
uv run python /Users/toddzhang/ws/todd/effectiveCodingBase/scripts/verify_posts.py
```
