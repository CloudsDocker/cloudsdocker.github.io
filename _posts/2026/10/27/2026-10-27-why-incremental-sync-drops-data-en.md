---
title: 'The Lie of Two Clocks: Why Incremental Sync Drops Data'
header:
    image: /assets/images/angular_no.png
date: 2026-10-27
tags:
 - data engineering
 - etl
 - data pipelines
 - debugging
 - database synchronization
permalink: /blogs/tech/en/why-incremental-sync-drops-data
lang: en
layout: single
category: tech
---
> "A man with a watch knows what time it is. A man with two watches is never sure." — Segal’s Law

# Why Your "Success" Log Lies About Your Data Integrity

*From “task succeeded” to “data lost” — the line between senior and junior is whether a green log scares you*

A scheduled run fires overnight. You check the logs. Status: `success`. Duration: three minutes. Rows extracted: `0`. The dashboard stays quiet, no alert email is triggered, and the on-call engineer rolls over to sleep, satisfied that the system is healthy. 

That was the most expensive incident I chased this month, and the reason it was so costly is simple: **it never threw an error.**

In the world of production data engineering, we are conditioned to hunt for the red text. We have built our monitoring, our paging, and our peace of mind around the

## 1. The scene: a pipeline that never errors

Every production-grade incremental data pipeline eventually hits the same architectural crossroads: how do you define "the present"? To move data from a source system into a downstream analytical store without double-counting records or missing events, we use a "watermark" or "high-water mark." It is the boundary line of our knowledge—the point where we know the data is complete and where the unknown begins.

Here is the skeleton of the extract SQL that serves as the backbone for almost every incremental sync job in our stack. It is a standard pattern for ensuring we only pull what we haven't seen before:

```sql
SELECT ...
FROM   ods.lms.grade_grades gg
WHERE  gg.timemodified >  :watermark_from
  AND  gg.timemodified <= :watermark_to
```

The logic here is mathematically clean. `watermark_from` is the value of `watermark_to` from our last successful execution. By ensuring our windows are perfectly back-to-back—where the end of the previous window is the start of the next—we create a contiguous stream of data with zero overlap and zero gaps. It feels like a perfect loop.

However, the integrity of that stream relies entirely on how we calculate the upper bound. In my initial implementation, the logic for `watermark_to` looked like a standard best practice. It was designed to be dynamic, adapting to the current moment of execution:

```python
# the line that decides the right edge of the window
watermark_to = conf.get("watermark_to") or now_epoch
```

On the surface, this is perfectly intuitive. `now_epoch` is the wall clock—the UTC second the task actually began. The mental model is simple: "I am pulling everything that happened since the last time I checked, right up until this very second." It feels like a safe, moving target that guarantees we are always up to date.

But this is where the abstraction of "now" collapses when it meets the messy reality of distributed systems. 

**The fundamental flaw is a mismatch of temporal truth: this SQL queries the ODS, and the ODS is not a real-time reflection of the source.**

In a distributed data architecture, the Operational Data Store (ODS) is rarely a synchronous mirror. It is an asynchronous downstream consumer. Whether it's due to Kafka replication lag, batch processing intervals, or database write pressures, there is always a "delta" between the moment an event occurs in the source system and the moment it becomes queryable in the `ods.lms` schema.

When we use the wall clock (`now_epoch`) as our upper bound, we create what I call a "Phantom Window." If the ODS is lagging by even a few seconds, our query asks for data that hasn't landed yet. Because the SQL returns an empty set for that "missing" time, the pipeline assumes the work is complete. The watermark then successfully advances to the current wall clock time.

The next time the pipeline runs, it starts from that new, advanced watermark. The data that arrived during that lag period—the data that was "in flight" but not yet visible—is skipped entirely. We haven't just experienced a delay; we've created a permanent hole in our data integrity. We have successfully moved the goalpost past the data we were trying to catch, leaving a gap that will never be filled because the watermark has already moved on.

## 2. The mechanism: two clocks live inside one pipeline

The `lms` schema in our ODS (Operational Data Store) is not a live, high-fidelity mirror of the source system. Instead, it functions as a snapshot—a periodic "freeze frame" of the source state that the upstream ingestion DAG loads once every 24 hours. The ingestion DAG is configured with a specific cron expression: `52 22 * * *`. This means the pipeline only wakes up to pull new data at 10:52 PM. On the day I conducted the investigation, the freshest `timemodified` timestamp sitting in the ODS had stalled out around 01:40 in the morning, confirming that the data was lagging significantly behind the real-time source.

Because of this architecture, one pipeline now carries two distinct clocks running at different velocities:

| | What it represents | How it moves |
| --- | --- | --- |
| **Source clock** | `grade_grades.timemodified` — the exact moment a grade was actually changed in the source system. | Real-time, always ticking forward with every user action. |
| **ODS snapshot clock** | The maximum `timemodified` value currently visible in the ODS. | Jumps in discrete increments once a day (the nightly load). |

The sync task's logic relies on `watermark_to = now`. In this context, `now` represents the **wall clock**—the actual current time of the system executing the job. However, the data it queries is pulled from the **lagging snapshot clock**. You are essentially using a high-resolution stopwatch to measure a clock that only updates once a day. The system was built on the assumption that these two watches were perfectly synchronized.

**This is a classic case of symmetry breaking.** The “use `now` for the watermark” abstraction is elegant only because of a hidden, unstated invariant: *the ODS must already hold all data up to this exact instant.* When you use a live mirror, the wall clock and the data clock move in lockstep, and the abstraction holds.

The moment the upstream source becomes a daily snapshot, that symmetry breaks. The wall clock marches forward linearly, but the data clock advances only one notch a day. This creates a "dead zone" where the processing window for the current sync task moves forward, but the data it needs to process hasn't arrived yet. This is a leaky abstraction; the simplicity of the `now()` call masks the underlying complexity of the data's staleness.

Walking through the timeline makes the failure mode obvious. Consider a grade that is changed in the source system on **Monday at 10:00 AM** (`timemodified = Mon 10:00`):

| Time | What happens | Is the grade in the ODS? |
| --- | --- | --- |
| Mon 10:00 | Grade changed in the source system. | ❌ ODS hasn’t pulled the update yet. |
| Mon 12:00 | Sync runs, processing window `(Mon 08:00, Mon 12:00]`. | ❌ Queries ODS, but data is missing → window is "processed" and closed. |
| Mon 15:00 | Sync runs, processing window `(Mon 12:00, Mon 15:00]`. | ❌ Data is still missing from the ODS. |
| **Mon 22:52** | **ODS load occurs.** The grade finally lands in the ODS. | ✅ Now present in the snapshot. |
| Tue 01:00 | Sync runs, processing window `(Mon 15:00, Tue 01:00]`. | ✅ Present in ODS, but... |

The final row is the trap. By the time the Tuesday early-morning sync runs, the grade *is* physically present in the ODS—but its `timemodified` value is still **Monday 10:00**. Because the sync task's current window has a left edge of **Monday 15:00**, the SQL `WHERE` clause filters the grade out as "old" data.

The window it *should* have belonged to—`(Mon 08:00, Mon 12:00]`—closed with a `SUCCESS` status at Monday noon and pushed the watermark past it. Because the data was missing at that specific moment in time, the system moved on, and the window never returned.

> This grade didn’t fail to sync. In every window that should have caught it, it was either not yet in the ODS or already behind the watermark. It fell into the gap between the two clocks.

## 3. Why it’s harder to catch than an error

A junior engineer’s debugging instinct is usually reactive: *something’s wrong, check the error log, peek at the Dead Letter Queue (DLQ), and verify the retry count.* Every one of those reflexes **fails here**, because there is no anomaly signal to trigger them. In a healthy-looking system, the "fire" isn't burning; it's just that the oxygen has been cut off. The system is technically

## 4. First principles: what should the window align to?

To build a robust incremental sync, you have to strip the problem down to its first principles. We need to ask a fundamental question: what *is* the correct right-hand boundary for an incremental window? 

In most production systems, the answer isn't the time on your watch. It is: **"How far does the data I can reliably see actually extend?"** 

We need to distinguish between two distinct types of time: 

1.  **The Wall Clock:** The absolute time of execution (e.g., `now()`). This is what most engineers default to because it's easy to reason about in a vacuum.
2.  **The Data Clock:** The timestamp of the latest record successfully persisted in the source system. 

In a true real-time streaming source (like a Kafka topic with strictly ordered offsets), these two clocks often coincide, which is why many engineers never notice the underlying architectural debt. However, the moment your source becomes a snapshot—such as a database table, a file storage bucket, or a downstream Operational Data Store (ODS)—the two clocks diverge. 

If you align your window to the wall clock but the data source is lagging or being updated in batches, you create a "non-deterministic window." You might end up skipping data that was mid-transit during your last run, or worse, double-counting records that were committed just as your query finished. 

Once you recognize this divergence, there are three ways to solve it. I’ve categorized them by their trade-offs in terms of architectural purity and operational overhead:

| Option | Mechanism | Engineering Cost |
| :--- | :--- | :--- |
| **Align to the Data Clock** | `watermark_to = MIN(now, source MAX(timemodified))` | Requires a high-performance query to find the `MAX` timestamp before every extract; requires consistent `timemodified` updates at the source. |
| **Look-back Overlap** | `watermark_from = max(0, last_watermark_to − overlap)` | Re-reads a window of already-synced data (e.g., 48h overlap) on every run. Requires **idempotent upserts** (e.g., `ON CONFLICT DO UPDATE`) in the destination. |
| **Stretch the Schedule** | Only trigger the sync once the source snapshot load is confirmed complete. | Low logic complexity, but creates a brittle circular dependency. If the load time drifts, your sync window drifts with it. |

For this specific implementation, I chose the **Look-back Overlap**. 

Here is the technical reasoning: The ODS we are targeting is a daily snapshot. While it is generally reliable, it can experience significant lag—sometimes up to 24 hours during periods of high volume or maintenance. By using a look-back overlap, we decouple our sync logic from the specific latency of the source. We don't need to know *exactly* when the data arrived; we just need to ensure that the window we grab is large enough to capture any "late" arrivals.

The one-line change to the core logic looks like this:

```python
# Later windows start `overlap` seconds before the last watermark_to.
# The ODS is a daily snapshot, so changes arrive a night late; the
# overlap re-catches them, and the upsert makes the repeat harmless.
watermark_from = max(0, int(last_watermark_to) - watermark_overlap_seconds)
```

I set `watermark_overlap_seconds` to 48 hours. This isn't an arbitrary number. I calculated it based on the ODS's worst-case lag (approx. 24 hours) plus a 24-hour "slack" buffer. This buffer covers the period of the actual change, the time it takes to propagate to the ODS, and any potential retries or late-arriving records.

There is a significant "hidden" benefit to this approach that I didn't initially account for in the initial design: **Automatic Back-filling.** 

Because `watermark_from` is calculated relative to the last *successfully processed* `watermark_to`, this logic is self-healing. If the pipeline breaks for three days and you fix it, the next run will look back from the last successful watermark. If that watermark was three days old, the next window will automatically encompass those missing three days. It "heals" the gap in the data without requiring a manual intervention to reset pointers or run a one-off migration script. 

> Rule of thumb: Align the window to the data’s clock, not to your wristwatch.

## What you can do today

If you’re currently grappling with inconsistent data or suspected gaps in your stream processing, the fix usually lies in the intersection of state management and idempotency. To move from reactive firefighting to a robust architecture, follow this four-step audit and hardening checklist:

### 1. Audit your watermark logic
Start by pulling up every "incremental" pipeline you own and asking a single, critical question: **Does its `watermark_to` parameter use `now` (the wall-clock time of the runner), or the source’s actual maximum timestamp?**

This is a classic source of non-deterministic behavior and a primary cause of "ghost" data loss. If your pipeline uses `now()`, it assumes the world is perfectly synchronous. However, if your data source is loaded on a schedule (e.g., a batch job that pushes data to a storage bucket every hour) rather than being a true real-time stream, using `now()` will almost certainly result in dropped data. You are effectively creating a "blind spot" between the moment the data was produced and the moment your runner decided to check for it.

*   **Action:** Identify all pipelines where `now` is the default. Move toward using a high-water mark derived from the source metadata (such as a `max(created_at)` or a monotonically increasing sequence ID) to ensure the pipeline only consumes what is actually committed and available.

### 2. Turn silence into a signal
One of the most dangerous failure modes in data engineering is the "successful empty." A task completes with a `200 OK` status and no errors, but it processed zero records. This usually happens because of a source hiccup, a network partition, or a logic error in your filtering layer.

You need to change your monitoring posture from "is the job running?" to "is the job actually doing work?" Add an alert to tasks that should consistently have data: fire a warning when `extracted=0` for $N$ consecutive windows. By doing this, you turn a silent data gap into a proactive signal, allowing you to catch "soft failures" before the downstream stakeholders notice the missing metrics.

### 3. Verify downstream idempotency
Before you attempt any "fix-forward" strategy, you must confirm that your downstream write is idempotent. Specifically, you want to ensure your sink is performing an `upsert` based on an external, unique key (like a `transaction_id` or a `uuid`), rather than a blind `append`.

Without idempotency, you cannot safely use a "re-read for safety" fix like the overlap—where you intentionally grab a bit of extra data from the past to ensure the current window is fully saturated. If you re-run a job to fill a gap and the sink doesn't handle duplicates, you’ll end up with double-counted records, which is often harder to clean up than missing data.

### 4. Execute a controlled backfill
Once you have confirmed that your sink is idempotent (Step 3), you can safely recover what fell into the gap. If you’ve identified a specific time window where data was dropped, perform a one-off, wide-window backfill.

Set the `watermark_from` parameter far enough back to encompass the entire duration of the gap. Because you've verified idempotency, this "sweep" will populate the missing records without creating duplicates. If you haven't verified idempotency yet, **do not do this**. A wide-window backfill on a non-idempotent sink is a recipe for a data integrity nightmare that can take weeks to untangle.

## Next up

This post addressed the immediate disease: a window aligned to the wrong clock. Solving that alignment is the first step, but the real challenge for a production system is building a cure—a robust architectural framework that prevents these discrepancies from recurring. 

To understand how to move from a manual fix to a systemic design, read: [design patterns for incremental extract windows](/blogs/tech/en/incremental-extract-window-design). That post explores the fundamental trade-offs of data synchronization, specifically:

*   **Overlap vs. High-Water-Mark Alignment**: Deciding between the safety of redundant data overlap and the precision of a strict high-water-mark pointer.
*   **Idempotent Upserts**: Why idempotency is the non-negotiable precondition for a reliable pipeline; if you cannot rerun a job without side effects, your system is fundamentally fragile.
*   **Circuit Breakers for Poison Windows**: How to implement safeguards that catch a single malformed record before it can jam the entire pipeline in an infinite retry loop.

For a broader view of the ecosystem this pipeline inhabits, see [this enterprise LMS→CRM integration write-up](/blogs/tech/en/enterprise-lms-crm-integration-architecture). It provides the full architectural context, detailing how we manage complex grade-tree weights, handle multi-region time zone shifts, and maintain the state machine logic required to keep the entire flow consistent.


*Errors shout; dropped data is silent. Half of engineering maturity is in how you handle exceptions — the other half is whether you’re willing to distrust a green log.*
