---
title: Your Parity Test Has Never Failed — Because It Can't
header:
    image: /assets/images/bg_raw/BingWallpaper (16).jpg
date: 2026-11-19
tags:
 - data-engineering
 - data-quality
 - dbt
 - snowflake
 - testing
permalink: /blogs/tech/en/parity-test-false-confidence
lang: en
layout: single
category: tech
---

"The first principle is that you must not fool yourself — and you are the easiest person to fool." — Richard Feynman

# Your Parity Test Has Never Failed — Because It Can't

*From "I added a data check" to "I added a light that's wired to stay green" — the line between senior and junior is whether you ever make your own test go red.*

Last week I opened a PR adding a guard to a pipeline that syncs Ascender staff data into Salesforce. The source table `ODS.HRIS.AH_OCCUPANCY` is rebuilt every night. If a rebuild ever lands with only half the rows, the downstream Salesforce models will happily treat a crowd of current employees as "terminated." So I wrote a dbt test: if today's row count drops below 80% of yesterday's, fail the whole build and keep the bad load out of production.

Airtight logic. The test "passed." CI was green.

Then the repo's AI reviewer (`github-dit`) left two comments. The first: your parity branch is dead code, it can never fire. The second: your time-travel query will hard-error on every run and block the entire pipeline.

The two sounded like they contradicted each other — one says "never fires," the other says "fails every time." I was ready to argue. So I connected to Snowflake and actually ran it.

Both were right. And together they exposed the same trap I still fall into after twenty years of building data systems: **a parity test only means something when the two sides it compares are genuinely independent. Otherwise it's a tautology wearing an `assert`'s clothes — and it doesn't score zero, it scores negative.**

If you've ever written a "these two numbers should be equal" check — row-count reconciliation, amount reconciliation, "record counts match before and after the migration" — these three sections are for you:

- **An always-true test isn't neutral.** It keeps flashing green, lulling you into dropping the vigilance you'd otherwise keep. That's worse than no test.
- **Independence is the only thing that makes reconciliation real.** Same statement, same transaction snapshot, same object lineage — three flavors of fake independence that quietly turn a check into a self-proof.
- **Time Travel is not a time machine.** On a table that's `CREATE OR REPLACE`'d daily, it can't reach "yesterday" — because yesterday's object is already dropped.

I won't tell this in the order I debugged it. I'll put the most misleading trap first.

## 1. What a parity test is, and why it's so seductive

A parity test is the most primitive assertion in data engineering: **two things that should be equal, asserted equal.**

- Migration: old table and new table should have the same row count.
- ETL: rows extracted == rows loaded.
- Finance: total debits == total credits.
- My case: the passthrough view `input__ah_occupancy` should have the same row count as its source `ODS.HRIS.AH_OCCUPANCY`.

It's seductive because it looks both cheap and total. You don't have to enumerate what "bad data" means — you just say "the two sides must agree," as if one line of `count(A) = count(B)` fences off every integrity bug at once.

But a parity test carries an assumption everyone understands and almost nobody verifies: **the two sides must be two independent observations.** Two independent tables can check each other. If you check a table against *itself*, you will always get "equal" — that's not a check, that's reading the same number twice.

> The information in a reconciliation isn't "two numbers are equal." It's "two *independent* paths happened to produce the same number." Remove the independence and equality becomes inevitable — and inevitable means zero information.

## 2. Trap one: reconciling inside a single SQL statement is a tautology

Here's the "reconciliation" I wrote first. The heart of it was this branch:

```sql
with counts as (
    select
        (select count(*) from {{ ref('input__ah_occupancy') }})   as input_row_count,
        (select count(*) from {{ source('hris', 'ah_occupancy') }}) as source_row_count,
        ...
)
select ...
from counts
where ...
    or input_row_count <> source_row_count   -- ← meant to catch "the view silently dropped rows"
```

The intent is clear: `input__ah_occupancy` is a passthrough view (`select <fixed columns> from source`, no `where`, no join), and I wanted to assert it hadn't lost rows somewhere in the middle.

**The naive read:** views can have bugs, so add a reconciliation, better safe than sorry.

**The seasoned read:** those two `count(*)`s live in the *same SQL statement*. Snowflake — like any ACID database — resolves one statement against *one consistent snapshot*: the transaction timestamp at statement start. Inside this statement, `input_row_count` and `source_row_count` read the *same data at the same instant*. And since the view is an unfiltered passthrough, its count is necessarily equal to the source.

So `input_row_count <> source_row_count` is *physically impossible* to be true. Not "unlikely to fire" — never fires. No compiler error, the test passes cheerfully, CI goes green, and what it validated was whether 1 equals 1.

| | Looks like it's doing | Actually doing |
|---|---|---|
| `count(view) <> count(source)`, same statement | Detecting dropped rows in the view | Reading one number twice and comparing it to itself |
| View with a `where`, same-statement reconcile | Detecting filter drift | Still one snapshot — drift is invisible too |
| A real reconciliation | Readings from two independent paths | Needs an **independent point-in-time** count to compare against |

The point isn't "does the view have a bug." It's **what you check it against.** To actually catch "the view lost rows relative to the source," you have to compare it to a count produced *across time, across objects, independently* — not re-count the source inside the same pair of parentheses.

> Check yourself against yourself and you always pass. The face in the mirror never tells you it's dirty.

What to do with this test? Delete it. The one valid assertion it was reaching for — "today's count shouldn't be far below yesterday's" — is already another test's job. And that other test walked straight into the second trap.

## 3. Trap two: on a daily-rebuilt table, time travel can't reach "yesterday"

The other test had the right idea: compare today's count to *yesterday's*. Snowflake offers time-travel syntax that looks made for the job:

```sql
select count(*)
from {{ model }}
at (offset => -86400)   -- 86400 seconds = 24 hours ago
```

`AT(OFFSET => -86400)` means "query this table as it looked 24 hours ago." Use that as "yesterday's snapshot," compare to today, alarm if it dropped too far. The config said `offset_seconds: 86400`.

Looks beautiful. I ran it against dev06:

```
000707 (02000): Time travel data is not available for table AH_OCCUPANCY.
The requested time is either beyond the allowed time travel period
or before the object creation time.
```

A **hard error**, not an empty result. Under `dbt build`, this error fails the source test and therefore **blocks every downstream staff-EC model** — whether or not today's load was actually incomplete. I set out to add a guard against incomplete data, and the guard itself takes the pipeline down every single day. Backwards.

Why? I pulled the table's metadata:

```sql
show tables like 'AH_OCCUPANCY' in schema ODS.HRIS;
-- rows: 572000   retention_time: 1

select max(CREATED), max(LAST_ALTERED) from ODS.INFORMATION_SCHEMA.TABLES ...;
-- CREATED:      2026-11-19 02:30:49
-- LAST_ALTERED: 2026-11-19 02:32:38
```

Two facts nailed the coffin shut:

1. **retention_time = 1 day.** Snowflake's default time travel keeps only 1 day, so `-86400` sits exactly on the boundary. A little clock drift at compile time and the requested instant slides right out of the retention window.
2. More fatal — `CREATED` and `LAST_ALTERED` are *both* from this morning, and `CREATED` moves every day. That's the signature of `CREATE OR REPLACE TABLE`: **the daily rebuild doesn't load rows into the table, it drops the whole object and builds a new one.**

That second point is the real killer. `AT(OFFSET => -86400)` queries the history of *this current object* 24 hours ago. But this object was only created at 2:30 this morning — it has no "yesterday." Yesterday's table was a *different, already-dropped object*; its time-travel history lives under that old object, and no `AT(OFFSET)` on the new object's name will ever reach it.

I checked smaller offsets to find the boundary:

| offset | meaning | result |
|---|---|---|
| `-7200` | 2 hours ago | ✅ 572000 (within this object's lifetime) |
| `-86400` | 24 hours ago | ❌ hard error (before object creation) |

The conclusion is hard: **on a daily `CREATE OR REPLACE` + 1-day-retention table, no offset can both avoid the error and actually point at the previous load.** The reviewer's two suggested mitigations — "use a safer offset" and "degrade gracefully when the snapshot is missing" — don't rescue this table: a safe offset can only reach "earlier today" (useless for catching an incomplete rebuild), and graceful degradation turns the guard into a no-op that never fires — right back to trap one.

> Time travel isn't a time machine, it's an object's medical chart. When the object dies, the chart is buried with it. You think you're revisiting yesterday; you're flipping through the old checkups of someone born this morning.

## 4. The fix: persist your own snapshot, compare against an independent point in time

Both traps share one root cause: **I kept trying to conjure "yesterday's count" out of "today's table" — but a table that gets wholesale-replaced every day carries none of its own history.** So stop asking it to. If you want an independent reference point, store one yourself.

The dbt-idiomatic way: an append-only audit model that appends one row per run — "this is what I counted today":

```sql
-- models/audit/audit__ah_occupancy_row_count.sql
{{ config(materialized='incremental') }}

select
    current_timestamp()                                        as snapshot_ts,
    current_date()                                             as snapshot_date,
    (select count(*) from {{ source('hris', 'ah_occupancy') }}) as row_count
```

Then the reconciliation test takes today's source count and compares it to the *most recent audit row whose date is strictly before today*:

```sql
-- tests/assert_ah_occupancy_row_count_guard.sql
with current_count as (
    select count(*) as row_count from {{ source('hris', 'ah_occupancy') }}
),
prior_snapshot as (
    select row_count
    from {{ ref('audit__ah_occupancy_row_count') }}
    where snapshot_date < current_date()      -- the key: strictly before today
    order by snapshot_ts desc
    limit 1
)
select current_count.row_count, prior_snapshot.row_count
from current_count cross join prior_snapshot
where prior_snapshot.row_count > 0
    and current_count.row_count < prior_snapshot.row_count * 0.8
```

`dbt build` runs the model first (appending today's count), then the test. The test's `snapshot_date < current_date()` excludes the row it just wrote and compares only against yesterday. On a cold start the audit table has no history, the `cross join` yields the empty set, and the test passes — no false kill on day one.

Line up what the three versions are actually comparing:

| version | reference comes from | independent? | result |
|---|---|---|---|
| same-statement `count(view)<>count(source)` | one statement, one snapshot | ❌ the same number | always green, zero info |
| `AT(OFFSET => -86400)` | the same object's time travel | ❌ object rebuilt daily, history gone | hard error, blocks pipeline |
| append-only audit table | **yesterday's run** left an independent record | ✅ across runs, across time, persisted | actually catches an incomplete rebuild |

Only in the third row are the two numbers being compared produced by *two genuinely independent paths*: one counted now, one counted and stored by yesterday's run. Them being equal is meaningful; them being unequal is a real signal.

> To check today, you have to leave an anchor in yesterday that today can't overwrite. A comparison with no anchor is just talking to yourself.

This pairs with my previous post, *[Why Your Incremental Sync Is Silently Losing Data](/blogs/tech/en/why-incremental-sync-drops-data)*: that one was about "the job succeeded but the data quietly shrank"; this one is about "the test you wrote to prevent that is itself lying to you." Silent data loss is frightening — but a guard that's wired to stay green makes you believe you're already protected. That's the deeper silence.

## What you can do today

1. **Pull up every "two numbers should be equal" test in your repo** and ask one question of each: are these two numbers from *two independent paths*? If they come from the same SQL, the same transaction, the same object — delete or rewrite it. All it gives you is false confidence.
2. **Manually make every guard you care about fail at least once.** Change the threshold, feed it a bad load, cut the source — and watch whether it actually goes red. A test that has never gone red is, evidentially, the same as no test.
3. **For anything leaning on time travel / `AT(OFFSET)`, check two things first:** what's the table's `retention_time` in days, and is it loaded via `CREATE OR REPLACE` or `MERGE`/`TRUNCATE+INSERT`? The former caps how far back you can reach; the latter wipes the history clean on every rebuild. `show tables like '...'` and `INFORMATION_SCHEMA.TABLES.CREATED` tell you both at a glance.
4. **If you need a cross-day comparison, persist it yourself.** Don't expect a table that's rebuilt every day to remember yesterday for you — it doesn't even remember its own.

---

*The value of an assertion equals the information it carries when it fails. If it can never fail, its value is zero — and if it fools you into feeling protected, its value is negative. When you finish a test, don't rush to watch it go green; find a way to make it go red once. That's how you know it's alive.*
