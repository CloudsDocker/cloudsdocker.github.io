---
title: Is Your Static Analysis Tool Still Using Outdated Rules?
header:
    image: /assets/images/bg/asdfasdfsadf.jpg
date: 2026-09-29
tags:
 - python
 - ruff
 - linting
 - static-analysis
 - ci
permalink: /blogs/tech/en/static-analysis-outdated-rules
lang: en
layout: single
category: tech
---
> "The competent programmer is fully aware of the limited size of his own skull." — Edsger W. Dijkstra

# Is Your Static Analysis Tool Still Using Outdated Rules?

*How to read Ruff C901 as a design constraint instead of treating it as a line-count complaint.*

“A successful dependency install means CI reached the tests.” It does not.

```text
error[C901]: `_build_outputs` is too complex (12 > 10)
   --> path/to/module.py:310:5
```

That error can arrive after a perfectly successful dependency install and before a single test runs. The installer did its job. The lint gate rejected the control flow.

Run this first:

```bash
ruff check path/to/module.py
```

By the end, you should be able to verify a C901 result by hand, identify the decision block worth extracting, and decide when a suppression or a higher threshold is the more honest choice.

The surprise is that C901 is not charging rent by line count. A short orchestration function can fail after two more branches because it was already near its complexity ceiling.

> 📌 **C901 counts paths through control flow, not lines of code.**

## Read the rule code before you inspect the business object

A CI log often contains plenty of noise before the useful line:

```text
Downloaded a virtual environment
Downloaded ruff
Installed dependencies
error[C901]: function is too complex (12 > 10)
Found 1 error
```

The first three lines report a successful setup. `C901` is the McCabe-complexity rule. `(12 > 10)` says the measured complexity is 12 and the configured ceiling is 10. The source location points at the `def` because the score belongs to the function body, not to a bad assignment on that line.

If the test command is structured like this:

```bash
ruff check app/ && pytest ...
```

then the left side of `&&` failed. `pytest` never ran. Looking through a downstream integration mapping at that point is looking in the wrong building.

| CI evidence | What it establishes | What to do next |
|---|---|---|
| Environment and dependencies installed | Setup succeeded; no application test result exists yet | Stop reading installation output |
| `error[C901]` at a `def` | Ruff rejected the function's control-flow complexity | Inspect the whole function |
| `(12 > 10)` | The score exceeded the threshold by two | Tally decisions, then find a cohesive extraction |
| Exit status 1 after Ruff | The test command was short-circuited | Do not diagnose test failures that did not occur |

This is the reusable debugging habit: name the rule family first. `C901` sends you to control flow. An unused-import rule sends you somewhere else. The code tells you which mental model to load.

## The hand calculation is a check, not a ritual

Thomas McCabe's 1976 model treats a routine as a control-flow graph. A practical hand approximation is:

```text
complexity = 1 + decision points
```

For Ruff's C901, conditional branches, loops, and exception-handling branches are the things to inspect. Do not use a generic complexity checklist blindly: the exact treatment of syntax such as boolean operators, conditional expressions, comprehensions, and pattern matching depends on the analyzer's implementation and version. Check the tool's documentation or reproduce the result with `ruff check` rather than claiming every `and` is automatically another point.

The useful distinction survives that caveat:

```text
200 sequential assignments  -> can still score 1
30 lines with many branches -> can exceed the threshold
```

Nested functions are analyzed as their own functions. A closure inside the flagged routine does not automatically make the enclosing routine's C901 score larger.

Consider this self-contained toy example. A parent routine has accumulated output-specific decisions, and two more guards appear in its record-processing branch:

```python
if "records" in output_groups:
    for record in records:
        if should_emit_record(record):
            if record.get("reference") not in (None, ""):
                add_record_row(outputs, record, references)
```

The policy predicate may already exist as a helper. That does not save the parent if the policy loop and its guards remain in the parent. The hub still owns those paths.

**Paths are the bill; lines are paper.**

## Extract the job, not merely a few lines

The function that assembles outputs has a legitimate orchestration job: decide which output families run, call them, and collect their results. It should not also carry every reason that an individual record is emitted, skipped, or categorized.

That division gives the code a shape worth defending:

| Layer | Question it answers | Typical home |
|---|---|---|
| Policy | Should this record be emitted, skipped, or categorized? | `should_emit_*`, `partition_*` |
| Serialization | How do records become rows in one output? | `add_*_output` |
| Orchestration | Which output families run for this batch? | `build_outputs` |

A partial extraction moves a predicate into `should_emit_*` but leaves the iteration and branch structure in `build_outputs`. It improves naming without reducing the hub's complexity. Policy left the room; the loop stayed.

The better extraction makes the helper own the cohesive output job:

```python
if "records" in output_groups:
    add_records_output(outputs, records, references)
```

The parent keeps one dispatch decision. The helper owns the record-level loop, filtering policy, and row creation for that output group. The point is not to make the parent smaller by moving arbitrary lines. It is to move decisions that belong to one job together.

This is where C901 is useful design pressure. It does not prove that every function above 10 is bad. It makes a growing hub expensive enough that someone has to explain why it should keep knowing one more thing.

## Three ways to make the check green

There are three common responses to C901. They are not interchangeable.

| Move | What you spend | When it is honest |
|---|---|---|
| `# noqa: C901` | This function no longer has this guardrail | A one-shot generator or frozen script whose control flow is clearer left together |
| Raise `max-complexity` | Every function may now grow to the new ceiling | The repository has an intentional baseline and the team can defend the new policy |
| Extract a helper | An additional symbol and a boundary to maintain | The new decisions form one cohesive policy or output job |

My position is plain: do not raise the threshold merely because today's function is 12. The difference between 10 and 12 is not arithmetic. It is whether the next output branch also lands in the same hub.

The strongest counter-case is real. A threshold can become performative when it forces tiny helpers with awkward parameter lists, obscures a linear algorithm, and scatters related logic across files. In that case, a documented suppression or a deliberately higher project threshold is better than extraction theater.

But an orchestrator used by every run is a poor place to spend that exception. If it keeps absorbing policy, it becomes the place where every future rule competes for attention.

Configure the rule explicitly when you want it as a merge contract:

```toml
[tool.ruff.lint]
select = ["C90"]

[tool.ruff.lint.mccabe]
max-complexity = 10
```

Ruff can report C901, but `ruff check --fix` cannot perform a safe architectural extraction for you. Formatting is mechanical. Moving control flow changes ownership, inputs, tests, and sometimes behavior. A human has to make that call.

## Keep the gate visible

A review comment saying “do not make this function bigger” lasts one pull request. A selected C90 rule makes the same preference visible on every pull request.

That is why lint configuration is more than style. It is a merge contract: a small, executable statement about where complexity is allowed to accumulate.

The next time C901 turns CI red, count the decisions before changing the threshold. If the total matches Ruff, ask one narrower question: **which decision block belongs together strongly enough to leave this function?**
