# Voice Profile — Highly Distinguish / todzhang.com

Extracted by reading the actual published posts in `_posts/`, not invented. Every
pattern below was pulled from at least two real posts (mainly the 2026 batch,
which is the most mature form of the voice — `every-sleep-is-a-lie`,
`cognitive-scaffolding-ai-memory-skills`, `tianren-wushuai-philosophy`,
`minikube-windows-path-pitfall`). When in doubt, go re-read one of those rather
than trust this summary blindly — this doc will drift out of date faster than
the posts do.

## Known author facts (already public — reuse, don't re-invent)

- ~20 years in the industry ("我入行二十年", stated in `every-sleep-is-a-lie-zh`).
- Writes/reviews production code and does code review / mentoring for other
  engineers (the "Alex" stories are framed as real mentoring sessions).
- Comfortable in bash, Kubernetes, Terraform, Airflow, Spark, dbt, LLM
  internals (Claude/LangChain/LangGraph) — the raw/ folder is the reliable
  source of truth for what topics are real expertise vs. speculation.
- Draws as easily on Chinese classical philosophy (王阳明, 孟子的"知人论世",
  庄子/道家的"天人五衰") as on Western sources (Steve Jobs, Thomas Reid, SRE
  folklore) and CS theory (Parnas information hiding, Occam's razor, the free
  energy principle). This cross-domain mixing is a core signature — do not
  flatten it into "just tech quotes."

If a draft needs a biographical claim not listed here (a company name, a
specific year, a specific incident), **do not invent it** — ask the user, or
leave a clearly marked placeholder (see `humanity-checklist.md`).

## The structural skeleton

Not every post uses every element, and that's correct — forcing all of them
into every post is exactly the kind of formulaic sameness to avoid. Treat this
as the toolbox this author reaches into, not a template to fill in
mechanically.

1. **Frontmatter** (see Mechanics below).
2. **Opening quote** — a real, attributable quote, one line, from a source
   *outside* the immediate tech topic when possible (philosophy, history, a
   craft maxim). This is the single most consistent element across every era
   of this blog (present even in 2016-era posts).
3. **Title (H1)** — often more vivid/provocative than the frontmatter
   `title:`, sometimes identical. Chinese titles lean toward a concrete
   image + stakes ("你脚本里的每一个 sleep 都在说谎", "花冠不败是幻觉，山静日长是出路").
4. **Optional italic subtitle promise** — one line, `*From X to Y — what
   separates senior from principal*` style. Names the transformation the
   reader will undergo, not just the topic.
5. **The hook** — a concrete, specific, real-feeling scene: a named person
   (often "Alex", but vary this — a first-person confession or an
   unembellished incident description work just as well and should be used
   sometimes instead), a timestamp ("凌晨两点", "11pm"), a real artifact (an
   error message, a diff, a log line). Ground it in sensory/situational
   specifics, never "imagine a developer who...".
6. **Reader-value preview** — a short bullet list of 2-3 things the reader
   will walk away with, each phrased as an intuition, not a topic
   ("`sleep` 是说谎的注释，`kubectl wait` 是会执行的注释" — not "we'll cover
   kubectl wait").
7. **An explicit ordering note** — pedagogical order (most useful first) is
   called out as different from chronological/discovery order. A small but
   recurring signal of intentional teaching design.
8. **Numbered chapters**, each roughly:
   - A concrete code/config/error anchor — real syntax, not pseudocode.
   - Sometimes a "普通人的看法 / 资深工程师的洞察" (naive take vs. seasoned
     take) contrast — use when there's a genuine gap in understanding to
     expose, skip it when the chapter doesn't have one.
   - A table contrasting symptoms/anti-patterns/defaults against fixes —
     tables are a heavy signature of this voice, used for anything
     comparable (bug vs cause, tool vs hidden state, before vs after).
   - A named mental-model callout — pick from the vocabulary bank below,
     don't reuse the same one twice in one post unless it's the post's
     explicit throughline.
   - A one-line, boxed/quoted "chapter philosophy" — an aphorism that
     could stand alone outside the post. Vary the label wording
     ("一句话哲学", "直觉口诀", "第一性原则", or no label, just a blockquote) —
     don't let this become a mechanical `## 一句话哲学` heading every single
     time.
9. **Ending**:
   - A synthesis table or diagram pulling the chapters' threads together
     under one abstraction (e.g. "三张地图").
   - **"立刻可以做的事"** — a short numbered list of concrete actions the
     reader can do *today*, tied to their own codebase/team, not generic
     advice.
   - **"预告"** — a teaser for the next post, ideally a real thing the
     author intends to write, creating series continuity. Don't invent a
     teaser that won't be followed up — check with the user.
   - A closing italicized aphorism, original (not the opening quote
     repeated), that reframes the whole post in one sentence.

## Vocabulary bank — the author's mental-model toolbox

These terms recur across `raw/` notes and published posts. They are the
author's actual intellectual signature, distilled from real thinking habits —
not tech-blog decoration. Reach for the one that's *true* for the insight at
hand; don't sprinkle them for flavor.

| Term | What it's for |
|---|---|
| 第一性原理 (first principles) | Stripping a "everyone knows X" belief down to the actual mechanism underneath. |
| 根-干-枝-叶 (root-trunk-branch-leaf) | The author's personal note-taking framework for going from a core question → mechanism → sub-topics → concrete facts. Visible in raw notes; rarely surfaces literally in finished posts, but its logic (root question first) shapes the hook + preview. |
| 知人论世 (Mencius) | Understanding a decision requires knowing both the actor's context ("世") and their method ("事") — used for framing why a default/design choice makes sense given its era or constraints. |
| 对称性破缺 (symmetry breaking) | Naming the specific asymmetry that turns a clean abstraction into a leaky one. |
| 自由能原理 / 最小化惊讶 (free energy principle) | Framing a design as reducing surprise/uncertainty for the reader or the system, rather than adding raw capability. |
| 奥卡姆剃刀 (Occam's razor) | Justifying why the simpler mechanism is the right explanation. |
| 五个为什么 (5 whys) | Drilling from a symptom to a root cause, shown as a literal Q/A chain. |
| Parnas information hiding | Justifying scoping/encapsulation choices (e.g. why an env var should only apply to one command, not the whole script). |
| 信息单向性 (information directionality) — coined | Every context boundary (host↔guest, frontend↔backend, ORM↔SQL) rewrites information according to its own assumptions; semantics live in the human's head, syntax lives in the tool. |
| 代码考古学 (code archaeology) — coined | The trap of "magic" fixes nobody remembers the reason for three months later. |
| 部落知识 → 工程产物 | The Principal-vs-Senior dividing line: turning something only remembered by word of mouth into a documented/enforced artifact (a flag, a README line, a check). |

Feel free to name a *new* framework if the raw material genuinely calls for
one — this bank should grow, not fossilize.

## Recurring rhetorical devices

- Direct reader address at a pivot point: "如果你也遇到过类似 ... 下面这一节就是为你准备的。"
- "面试拿分点" — flagging a detail as specifically interview-worthy, rewarding readers who want to level up, not just fix today's bug.
- Seniority framing as a throughline: Senior vs Principal, "普通人" vs "资深工程师" — used to make the stakes about the reader's own growth, not just the bug.
- Quotes and mental models pulled from *outside* the tech domain into a tech problem, and vice versa (Wang Yangming next to `kubectl wait`). This juxtaposition is a deliberate part of the voice, not a quirk to sand off.
- Tables over prose whenever two or more things are being compared.
- Real, runnable code blocks with realistic variable names (`WAIT_TIMEOUT`, `HOST_MOUNT_SRC`) — never `foo`/`bar` placeholders in the final fix.

## Mechanics (file layout, frontmatter, naming)

Confirmed by grepping every post under `_posts/`:

- **Path**: `_posts/YYYY/MM/DD/YYYY-MM-DD-<slug>.md` (year/month/day are real
  nested directories, matching `date:` in the frontmatter).
- **Bilingual pair**: two files, same slug, language suffix on the *filename*:
  `<slug>-zh.md` and `<slug>-en.md` (this is the current, consistent
  convention as of the 2026 posts — older posts used a bare filename for one
  language plus `_en` for the other, which is legacy and shouldn't be copied
  for new posts). If the topic is inherently English-first (e.g. quoting
  English source material throughout), it's fine to have only one file, but
  default to producing both languages unless the user says otherwise — the
  point of this whole pipeline is reach across both audiences.
- **Frontmatter fields**, in this order:
  ```yaml
  ---
  title: <string, matches or slightly softer than the H1>
  header:
      image: /assets/images/<existing-file>.{png,jpg,jpeg}
  date: YYYY-MM-DD
  tags:
   - lowercase-kebab-topics (3-5 of them)
  permalink: /blogs/<category>/<lang>/<slug>
  layout: single
  category: tech   # or life, for personal/philosophical posts
  ---
  ```
- **`category`**: `tech` for engineering content, `life` for
  philosophy/career/personal-growth posts (rare, but the pattern exists —
  `tianren-wushuai-philosophy`). It drives the first path segment of
  `permalink`, so keep them consistent within a bilingual pair.
- **`permalink` lang segment**: use `zh` and `en` (not `cn` — that's a legacy
  value from older posts, don't propagate it into new ones).
- **`header.image`**: reuse an existing file under `assets/images/` — do not
  invent a new binary asset. Prefer files already prefixed `hd_` (a small
  library of thematic illustrations already used across many posts) that
  loosely match the topic; if nothing fits well, it's acceptable to reuse a
  generic evocative image (this blog already reuses e.g. `swan.jpg` across
  unrelated posts) rather than block the post on finding a perfect image.
  List candidates with `ls assets/images | grep -i <keyword>` and
  `ls assets/images | grep '^hd_'` before picking.
- **Tags**: lowercase, kebab-case where multi-word, 3-5 per post, drawn from
  what's actually used elsewhere (`grep -rh '  - ' _posts | sort | uniq -c |
  sort -rn` to see the existing tag vocabulary before inventing new ones).
