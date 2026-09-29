---
title: C901 taxes independent paths, not line count
header:
    image: /assets/images/hd_mvn_skip_tests.png
date: 2026-09-15
tags:
 - python
 - lint
 - ci-cd
 - ruff
 - github-actions
permalink: /blogs/tech/en/ruff-c901-is-paths-not-lines
layout: single
category: tech
---
> “The competent programmer is fully aware of the limited size of his own skull.” — Edsger W. Dijkstra

# C901 taxes independent paths, not line count

*From one red ruff line to being able to score a function by hand — and knowing what to extract.*

Tuesday morning. The UAC → Salesforce PR — `ditapi-p-domestic-student-recruitment-v1` #41 — went red. Pytest never got a turn. Ruff spoke first:

```
error[C901]: `_build_csvs` is too complex (12 > 10)
   --> app/services/sync_uac.py:310:5
```

These three lines are a successful install, not the failure:

```
Downloaded virtualenv
Downloaded ruff
Installed 89 packages in 68ms
```

First reflex is SAS, Bulk, Salesforce. Wrong room. This is a **static-analysis gate**: too many independent paths through one function. Cap is 10. We had 12.

The counter-intuitive line: **C901 does not count how long a function is. It counts how many ways you can walk out of it.** Two new `if`s can fail CI when the orchestrator is already sitting on the cap.

What to take with you is not another ruff manual. Three portable ideas:

- **McCabe cyclomatic complexity** — independent paths on a control-flow graph, not LOC
- **Orchestrator vs policy** — new rules go in helpers, not in a hub that is already at the limit
- **Lint as a merge contract** — extract / `noqa` / raise the cap — pick one, with a stance

Teaching order, not discovery order: read the log, score by hand, then change the code.

## 1. How to read the log: rule code + numbers + the `def` line

| Log line | What it actually means |
|---|---|
| `Downloaded virtualenv` / `Downloaded ruff` | `uv` installed an isolated env and ruff. **No business test has run.** |
| `Built mq-canonical-models` / `ditapi-common` | Private git deps compiled. Install succeeded. |
| `Installed 89 packages` | Environment is fine. The failure is next. |
| `error[C901]` | Ruff rule family: McCabe / mccabe |
| `_build_csvs` is too complex **(12 > 10)** | Measured 12, ceiling 10 |
| `--> app/services/sync_uac.py:310:5` | Arrow points at **`def`**, not a wrong assignment |
| `Found 1 error` / exit 1 | The whole job dies on this one lint |

CI chain: PR into `dev` → `feature.yaml` → `ci-test.yaml` → `uv run scripts/run-test`. First line of that script:

```bash
ruff check app/ && pytest ...
```

Left side of `&&` went red. Pytest never ran. Hunting Salesforce mappings in the test job is looking in the wrong building.

Where the rule lives: `pyproject.toml`, `[tool.ruff.lint] select` includes `"C90"`. There is **no** `[tool.ruff.lint.mccabe] max-complexity`, so the default is 10. `C90` is not in `fixable`: `ruff check --fix` **will not save you from C901**.

> Naive take: the function is too long; delete comments.
> Seasoned take: name the rule family first, then check whether the numbers add up. Only then touch code.

> 📌 **This section:** the rule code decides whether you count branches or chase a business object.

## 2. Deep dive 1: McCabe, paths on a graph

In 1976 Thomas McCabe treated a program as a directed graph: statements are nodes, `if` / `for` / `and` are decisions. **Cyclomatic complexity = number of linearly independent paths.** Hand formula:

```
CC = 1 + decision points
```

Count: `if` / `elif` / `for` / `while` / `except`, plus **each `and` / `or`**, ternaries, and the `if` inside a comprehension. **Do not count lines.** Two hundred sequential assignments can score 1. Thirty lines of branches can score 15.

A nested `def` is scored **separately** in ruff / mccabe. The `_finalize` closure inside `_build_csvs` does not contribute to the parent's 12.

PR #41 stuffed Study Application filtering into the orchestrator and added two decision points:

```python
if not _should_emit_study_application(...):   # +1
    if applicant.get('refnum') not in (None, ''):  # +1
```

The parent was already near 10 (Account / ContactPoint / Application / Preference orchestration). 10 + 2 = **12**. That matches CI.

The matcher itself already lived in `_should_emit_study_application` and `_partition_mq_preferences`. Those functions were each under 10. **What blew up was the hub swallowing another layer of business `if`s.**

| Looks like | Actually is |
|---|---|
| Function too long | Too many independent paths |
| Line 310 is wrong | Scoring starts at `def` and covers the whole body |
| We should disable C90 | The gate exists so this hub cannot grow forever |

Interview point: “Why isn’t 12 just ‘too long’?” Answer with the table above.

> More paths, more tests. The gate counts roads, not pages.

## 3. Deep dive 2: orchestrator and policy do not share a skull

Parnas information hiding: a module exposes one stable question. `_build_csvs` answers: **which CSVs does this batch emit?** It should not know *why* a given applicant skips Study Application.

| Layer | Job | Who owns it here |
|---|---|---|
| Policy | MQ course family / emit or skip / cancel still ships | `_should_emit_*`, `_partition_*` |
| Serialize | Rows → tagged Bulk CSV | `_add_study_application_csv`, `_add_preference_csvs` |
| Orchestrate | Call by entity, tally stats | `_build_csvs` |

#41 did not get the policy wrong. Policy was already extracted. What was wrong: **the policy loop still sat inside the orchestrator**, so the parent still paid for those two `if`s.

This repo hit the same wall last month: `_build_csvs` at **14 > 10**. The fix was an AMIS overlay helper — not `noqa`, not a new ceiling. Same river.

After the extract:

```python
if ENTITY_APPLICATION in entities:
    study_skipped_no_mq = _add_study_application_csv(
        csvs, applicants, library, category, pref_refnums, mq_refnums,
    )
```

The parent keeps one `if`. Paths drop from 12 to about 7. Salesforce behaviour is unchanged: same CSV key, same skip counter, Cancelled still upserts.

What I ran locally:

```
uv run ruff check app/services/sync_uac.py
# All checks passed!

uv run pytest tests/test_services/test_sync_uac.py \
  tests/test_services/test_sync_uac_masking.py \
  tests/test_services/test_uac_transforms.py -q --tb=short
# 71 passed in 0.26s
```

> Policy left the room. The loop stayed. That is only half of information hiding.

## 4. Deep dive 3: three fixes, one stance

| Move | Cost | What you spend | When it is honest |
|---|---|---|---|
| `# noqa: C901` | One line | The gate dies for this function forever | Generators, one-shot scripts, confirmed frozen |
| `max-complexity = 12` | A toml edit | The whole repo may now pile to 12 | Baseline already sits at 11 and you can explain why |
| **Extract a helper** | One rename | One more symbol; tests keep the old entry | The new decisions are already one cohesive job |

This repo’s `scripts/render.py` has `noqa:C901`. That is a script. `_build_csvs` is the **hub every UAC sync walks**. The new rule is days old, not a historical tumour.

Raising the cap sounds like “12 is basically 10.” The gap is not 2. The gap is **who splits the next AMIS or entity branch**. The gate exists because this function is already a hub.

Ruff puts C90 in `select` and keeps it out of `fixable` on purpose: **this is design pressure, not formatting.** Formatting can rewrite quotes. Path count needs a human.

Tribe knowledge → engineering artifact: “don’t fatten `_build_csvs`” said once in review will be ignored by the next PR. Written as `select = ["C90"]`, it is a contract on every PR.

> A lint `--fix` cannot touch is the one asking about your design.

## 5. Three maps, one picture

| Idea | Root question | Answer this time |
|---|---|---|
| McCabe | More paths, bigger test surface | 12 = old orchestration + two new ifs |
| Orchestrator vs policy | The hub should not know why we skip | Loop moves into `_add_*_csv` |
| Merge contract | Is the gate pressure or decoration? | Extract. No `noqa`. Do not raise 10. |

The fix commit is `438b8ad`, pushed to #41.

## Do this today

1. Next red CI: read the rule code first. `C901` → count `if`s. `F401` → delete an import. Only a business exception sends you to the object model.
2. Score the flagged function by hand: `1 + decision points`. When the number matches CI, you know which block to extract.
3. New rules join the existing helper family: `_should_*` / `_add_*`. Do not leave the loop in the orchestrator and pay the path tax twice.
4. Do not set `max-complexity` to whatever number would make today green. That is deleting the gate.

*Lines are paper. Paths are the bill.*
