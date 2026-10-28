---
title: The Lie of Two Clocks — Why Your Incremental Sync Quietly Drops Data Every Night
header:
    image: /assets/images/date_is_most_ignored_treasure_in_macbook.jpg
date: 2026-10-26
tags:
 - data-engineering
 - airflow
 - etl
 - system-design
 - snowflake
permalink: /blogs/tech/en/data-loading-window-two-clocks
lang: en
layout: single
category: tech
---

> “A man with a watch knows what time it is. A man with two watches is never sure.” — Segal’s Law

# The Lie of Two Clocks: Why Your Incremental Sync Quietly Drops Data Every Night

*From “task succeeded” to “data lost” — the line between senior and junior is whether a green log scares you*

A scheduled run fires overnight. Status: `success`. Duration: three minutes. Rows extracted: `0`. The dashboard stays quiet, no alert email, the on-call engineer rolls over and goes back to sleep.

That was the most expensive incident I chased this month, and the reason it was expensive is simple: **it never threw an error.**

The setup is one you’ve probably built a version of: take behavioural learning signals out of an LMS (Moodle-based), clean them through a Snowflake ODS layer, and incrementally push them into a CRM (Salesforce Education Cloud) that feeds an academic-risk dashboard for student advisors. One day the business flagged it: a batch of grades had definitely been changed, but the CRM didn’t have them. Not late — missing.

First place I looked was the dead-letter queue. Empty. Then the control table — every row for that time window read `SUCCESS`, `records_extracted = 0`. The task didn’t fail, nothing landed in the DLQ, the data simply vanished.

If you maintain any pipeline that pulls from an upstream in daily batches and pushes downstream incrementally, this one is for you. Three intuitions to walk away with:

- In a batch pipeline, **the most dangerous log line isn’t a red error — it’s a green `success, rows=0`**;
- “What time is it?” has **two contradictory answers** inside a cross-system pipeline, and most of these bugs live in the gap between them;
- An idempotent upsert isn’t just dedup insurance — it’s **what earns you the right to re-read**.

The order below is the reverse of how I debugged it: I’m putting the useful conclusion (two clocks) first, not narrating the detective work (DLQ, then control table).

---

## 1. The scene: a pipeline that never errors

Here’s the skeleton of the extract SQL — every incremental pipeline has a version of this:

```sql
SELECT ...
FROM   ods.lms.grade_grades gg
WHERE  gg.timemodified >  :watermark_from
  AND  gg.timemodified <= :watermark_to
```

`watermark_from` is the previous run’s `watermark_to`; windows are back-to-back and never overlap. The bug is in how `watermark_to` is chosen:

```python
# the line that decides the right edge of the window
watermark_to = conf.get("watermark_to") or now_epoch
```

`now_epoch` — the wall clock, the UTC second the task happened to start. Looks obvious: I’m pulling “everything since last time until now,” what could be wrong?

What’s wrong is that **this SQL queries the ODS, and the ODS is not real-time.**

---

## 2. The mechanism: two clocks live inside one pipeline

The `lms` schema in the ODS isn’t a live mirror — it’s a snapshot the upstream loads once a night. The ingestion DAG’s cron is `52 22 * * *`: it only pulls from the source at 22:52, and on the day I checked, the freshest `timemodified` sitting in the ODS stopped around 01:40 in the morning.

So one pipeline now carries two clocks running at different speeds:

| | What it represents | How it moves |
|---|---|---|
| **Source clock** | `grade_grades.timemodified` — the moment a grade was actually changed | Real-time, always ticking |
| **ODS snapshot clock** | the max `timemodified` visible in the ODS | Jumps once a day (that nightly load) |

The sync task’s `watermark_to = now` is the **wall clock**; the data it queries comes from the **lagging snapshot clock**. Two watches — and you trusted the wrong one.

**This is symmetry breaking.** The “use `now` for the watermark” abstraction is elegant only because of a hidden assumption: *the ODS already holds data up to this instant.* The moment upstream becomes a daily snapshot, that symmetry breaks — the wall clock marches forward, the data clock advances one notch a day, and window and data drift apart.

Walk the timeline and it’s obvious. Say a grade is changed on **Monday 10:00** (`timemodified = Mon 10:00`):

| Time | What happens | Is the grade in the ODS? |
|---|---|---|
| Mon 10:00 | grade changed in the source | ❌ ODS hasn’t pulled yet |
| Mon 12:00 | sync runs, window `(Mon 08:00, Mon 12:00]` | ❌ queries ODS, not there → window wasted |
| Mon 15:00 | sync runs, window `(Mon 12:00, Mon 15:00]` | ❌ still not there |
| **Mon 22:52** | **ODS load**, the grade lands in the ODS | ✅ now present |
| Tue 01:00 | sync runs, window `(Mon 15:00, Tue 01:00]` | ✅ in ODS, but… |

The last row is the trap. By Tuesday’s early run the grade *is* in the ODS — but its `timemodified` is **Monday 10:00**, and this window’s left edge is Monday 15:00. `10:00 < 15:00`, so the `WHERE` filters it out.

And the window it *should* have belonged to, `(Mon 08:00, Mon 12:00]`, closed `SUCCESS` at Monday noon and pushed the watermark past it — never to return.

> This grade didn’t fail to sync. In every window that should have caught it, it was either not yet in the ODS or already behind the watermark. It fell into the gap between the two clocks.

---

## 3. Why it’s harder to catch than an error

A junior engineer’s debugging instinct: something’s wrong, check the error, read the DLQ, look at retries. Every one of those reflexes **fails here**, because there is no anomaly signal at all:

| The naive take | The seasoned take |
|---|---|
| No error = no problem | No error is the worst class of bug: it slipped past all your alarms |
| `rows=0` means that window genuinely had no data | `rows=0` can equally mean “data not arrived yet / already skipped” — identical in the log |
| Task `SUCCESS` means the data is correct | `SUCCESS` only means this code didn’t raise; whether the data is right is a separate question |

The real evidence I had (anonymised): in one daytime span, 47 in-scope grades had been changed in the source; in the CRM, zero; in the DLQ, zero; every matching control-table window read `SUCCESS / extracted=0`. Looking back a week, across 26 scheduled grade runs only 1–2 ever pulled any data — because every daytime window was querying “last night’s snapshot,” which didn’t contain that day’s changes, and by the time the snapshot refreshed, the window had already slid past.

**Interview-worthy point:** if someone asks how you monitor an ETL pipeline’s health and your answer is only “task success rate + error alerts,” you’ll miss this entire class of failure. The monitor that actually catches it: *a task that should always have data showing `extracted=0` for N consecutive windows should alert.* Silence is itself a symptom.

> Chapter aphorism: in batch, the scary thing isn’t a red Exception — it’s a green `success, rows=0` nobody reads.

---

## 4. First principles: what should the window align to?

Strip it to first principles: what *is* the right edge of an incremental window, really?

It should be **“how far does the data I can reliably see extend”** — the **data clock** — not **“what time did I happen to run”** — the wall clock. In a real-time source the two coincide, which is why most people never notice which one they depend on; the moment the source becomes a snapshot, the two diverge.

Once you see that, there are two clean fixes plus one cheap stopgap:

| Option | How | Cost |
|---|---|---|
| **Align to the data clock** | `watermark_to = MIN(now, source MAX(timemodified))` | one extra MAX query per source before each extract; touches core logic |
| **Look-back overlap** | `watermark_from = max(0, last_watermark_to − overlap)`, overlap = 48h | re-reads some already-synced data each run; dedup via idempotent upsert |
| Stretch the schedule | only run after the snapshot load completes | worse freshness, still brittle — change the load time and it drifts again |

I chose the look-back overlap this time; the next post explains why. Here’s the conclusion and the one-line change:

```python
# Later windows start `overlap` seconds before the last watermark_to.
# The ODS is a daily snapshot, so changes arrive a night late; the
# overlap re-catches them, and the upsert makes the repeat harmless.
watermark_from = max(0, int(last_watermark_to) - watermark_overlap_seconds)
```

48 hours isn’t arbitrary: the ODS lags about a day in the worst case, plus a day of slack, covering both “the day of the change” and “the day it reaches the ODS.” This change has a bonus: it **back-fills the data dropped before the fix shipped**, automatically, on the next run — because those stranded old `timemodified`s now land back inside the window.

> Rule of thumb: align the window to the data’s clock, not to your wristwatch.

---

## What you can do today

1. Pull up every “incremental” pipeline and ask one question: **does its `watermark_to` use `now`, or the source’s actual max timestamp?** If it’s `now`, then ask: is that source real-time, or loaded on a schedule? If it’s the latter, you’re very likely dropping data.
2. Add an alert to tasks that should always have data: fire when `extracted=0` for N consecutive windows. Turn silence into signal.
3. Confirm your downstream write is idempotent (upsert on an external unique key). Only idempotency lets you use a “re-read for safety” fix like the overlap.
4. If you are dropping data, do a one-off wide-window backfill (set `watermark_from` far enough back) to recover what fell into the gap — once point 3 holds.

## Next up

This post was the disease: the window aligned to the wrong clock. The next one is the cure — [design patterns for incremental extract windows](/blogs/tech/en/incremental-extract-window-design): overlap vs. high-water-mark alignment, why idempotent upsert is the precondition for everything, and how a circuit breaker keeps one poison window from jamming the pipeline forever. For the full architecture this pipeline sits inside (grade-tree weights, time zones, state machine), start with [this enterprise LMS→CRM integration write-up](/blogs/tech/en/enterprise-lms-crm-integration-architecture).

---

*Errors shout; dropped data is silent. Half of engineering maturity is in how you handle exceptions — the other half is whether you’re willing to distrust a green log.*
