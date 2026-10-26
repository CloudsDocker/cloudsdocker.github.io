---
title: Three Designs for Incremental Extract Windows — Overlap, High-Water-Mark, and Poison-Window Breakers
header:
    image: /assets/images/cdc_booster.png
date: 2026-10-26
tags:
 - data-engineering
 - airflow
 - etl
 - idempotency
 - system-design
permalink: /blogs/tech/en/incremental-extract-window-design
lang: en
layout: single
category: tech
---

> “No man ever steps in the same river twice.” — Heraclitus

# Three Designs for Incremental Extract Windows: Overlap, High-Water-Mark, and Poison-Window Breakers

*From “pull a time range of data” to “design a trustworthy temporal contract”*

The previous post, [The Lie of Two Clocks](/blogs/tech/en/data-loading-window-two-clocks), was the disease: a pipeline where the wall clock and the data clock drift apart, the window aligns to the wrong one, and data quietly leaks through the gap. This post is the cure — treating the incremental extract window as a **design problem** instead of reflexively typing `watermark_to = now`.

Heraclitus said you can’t step into the same river twice. That’s the whole difficulty of an incremental pipeline: the river of source data you “step into” each run is always at a different level — and *when* the upstream lets you see new water is often not up to you. Window design is, at bottom, answering one question: **what gives me the right to claim “I’ve seen everything from A to B”?**

You’ll walk away with:

- why binding the right edge of an incremental window to the wall clock is **always a latent bug**, even if it hasn’t blown up yet;
- look-back overlap vs. high-water-mark alignment, and where each one fits;
- why **idempotent upsert isn’t an optimization but a precondition** — without it you can’t safely use either fix;
- how a circuit breaker lets the pipeline “skip and advance” when one window is permanently poisoned, instead of jamming forever on a single bad row.

---

## 1. The right edge: which clock are you trusting?

Compress the last post into one sentence: **the right edge of an incremental window should be “the boundary of the data I can reliably see,” not “the moment I ran the task.”**

```python
# anti-pattern: right edge = wall clock
watermark_to = now_epoch

# two fixes, both pulling the right edge back to the data's clock
# A. high-water-mark alignment
watermark_to = min(now_epoch, source_max_timemodified)
# B. look-back overlap (move the left edge back, tolerate an eager right edge)
watermark_from = max(0, last_watermark_to - overlap_seconds)
```

**The naive take:** `now` is natural — “pull up to now,” obviously.
**The seasoned take:** `now` equals the data boundary only under the assumption that the source is real-time. That assumption holds for real-time CDC and fails for **every** daily snapshot, scheduled load, or read replica with replication lag. So `watermark_to = now` isn’t “wrong” — it’s a buried fuse. The day upstream switches to batch loading, or replica lag grows, it detonates.

> First principle: a window’s boundary is a property of the data, not of the scheduler. Binding it to `now` mortgages data correctness against “upstream is always real-time,” an assumption you don’t own.

---

## 2. Where each fix fits: high-water-mark vs. overlap

Both are correct, for different situations. Don’t memorize — remember their costs:

| Dimension | High-water-mark (`watermark_to = MIN(now, MAX(src))`) | Look-back overlap (`watermark_from` back by overlap) |
|---|---|---|
| Correctness | Exact — reads only arrived data, nothing lost or missed | Eventually consistent — misses get re-caught in later windows |
| Extra reads | Almost none, one `MAX()` per source | Re-reads already-synced data within each overlap window |
| Dependency | Needs a queryable, trustworthy source watermark column | Needs an idempotent downstream (else duplicate writes) |
| Blast radius | Touches extract core logic, wire it per source | One parameter + a one-line change to the watermark start |
| Bonus | None | Auto-backfills data dropped before the fix shipped |
| Failure mode | Source has no trustworthy “last updated” column | Overlap shorter than the real lag — still misses |

**Decision heuristic:**
- Can get a trustworthy source watermark, want zero redundant reads + exactness → high-water-mark.
- Downstream is already an idempotent upsert, want minimal change plus a free backfill → overlap.
- Doing both is fine too: high-water-mark for correctness, a small overlap to absorb the second-order error that the watermark timestamp *itself* can lag.

My last case chose overlap: the downstream was a Bulk upsert keyed on an external unique ID, the change was one line, and I got a historical backfill for free. Overlap = 48h (“worst-case upstream lag ~1 day + 1 day of slack”).

> Rule of thumb: high-water-mark says “I only take what I’ve fully seen”; overlap says “I’d rather take some twice — the write won’t duplicate anyway.”

---

## 3. Idempotent upsert: the precondition for any re-read

Of the two fixes, overlap explicitly re-reads data, and high-water-mark re-reads the same window on retry. The moment you re-read, **the downstream must be idempotent**, or every “look back” manufactures duplicate rows.

Idempotency comes from an **external unique key** — the source record’s own natural, stable ID, not an autoincrement PK or a hash:

```text
upsert externalId = the source grade record's grade_id
→ however many times the same grade is synced, it hits the same downstream
  row and overwrites it with the same value
```

| Without an external unique key | With an external unique key |
|---|---|
| re-read = duplicate rows, data rots as it accumulates | re-read = idempotent overwrite, harmless |
| can’t overlap, can’t retry, can’t backfill | overlap / retry / backfill all become safe operations |
| “run exactly once” becomes a hidden correctness premise | correctness no longer depends on exactly-once |

**Interview-worthy point:** “exactly-once” is extremely expensive and fragile in distributed systems; what’s actually achievable in practice is “at-least-once delivery + idempotent receipt.” You move the dedup responsibility from the *transport* to the *receiver’s unique key*, and the whole pipeline’s fault-tolerance design gets an order of magnitude simpler. That’s why I call idempotency a precondition, not an optimization — it’s the license that lets you use every “re-read” technique above.

> Chapter aphorism: idempotency isn’t for preventing duplicates — it’s for **buying the right to retry and re-read.**

---

## 4. Poison windows: let the breaker make the trade-off

The last real problem: what if a window simply contains a row the downstream will reject forever (a field too long, a foreign key that won’t resolve, an illegal picklist value)?

Naive implementation: window fails → next run retries the same window → fails again → stuck here forever, watermark never advances. One bad row deadlocks the whole pipeline.

The mature implementation is a **circuit breaker + dead-letter isolation**:

```text
window fails → retry_count + 1 → retry the same window
on reaching max_retry → stop grinding:
    · write the failed rows to the DLQ (keep evidence, fix offline)
    · mark this window PARTIAL (partial success / skipped)
    · advance the watermark as usual, so one bad row can't block the rest
```

| Without a breaker | With a breaker |
|---|---|
| one bad row = whole pipeline permanently halted | the bad row is isolated to the DLQ, the mainline keeps moving |
| watermark stuck forever before the poison window | watermark steps over the poison window, downstream data keeps syncing |
| incidents mean someone woken at 2am to skip it by hand | incidents degrade to an async ticket: “N rows in the DLQ to triage” |

The design philosophy here is turning tribal knowledge into an engineering artifact: **“this window has bad data, skip it manually” used to live only in some veteran’s head; the breaker freezes it into a deterministic rule in code.** The cost is accepting “eventual consistency + manual DLQ triage”; the payoff is that no single bad row can permanently kill the pipeline.

> Rule of thumb: a good pipeline isn’t one that never fails — it’s one where **failure is isolated and doesn’t block the healthy data.**

---

## What you can do today

1. Audit your incremental pipelines; for each, answer two questions: is the right edge bound to `now` or to the data’s watermark? Is the downstream an idempotent upsert on an external unique key? Those two answers decide whether you can safely re-read.
2. If the downstream isn’t idempotent yet, that’s higher priority than “fixing the window” — build the external unique key first, or any re-read fix will create duplicates.
3. Add a breaker to every pipeline: define `max_retry`, and on reaching it, DLQ the failures + mark PARTIAL + advance the watermark. Don’t let a single bad row block forever.
4. Make values like overlap / max_retry configuration (variables, not hardcoded) — they’re your future tuning knobs, and the vehicle for turning tribal knowledge into an engineering artifact.

## Next up

These two posts drilled into the single point of “the window.” One layer out is the full architecture of the whole LMS→CRM pipeline — grade-tree weight validation, the twice-a-year daylight-saving breakage, the four-state machine, the “data poison pill” of group assignments — all in [this enterprise integration write-up](/blogs/tech/en/enterprise-lms-crm-integration-architecture).

---

*The maturity of an incremental pipeline isn’t how fast you move the data across — it’s whether you can honestly answer one question: “from A to B, what makes me say I’ve seen it all?”*
