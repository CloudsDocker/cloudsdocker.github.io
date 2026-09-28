---
title: "Zero Rows, Zero Errors: How Snowflake Silently Ate Our Regex Backslashes"
date: 2026-09-28
categories: [tech]
tags: [Snowflake, SQL, Regex, Production-Incident, Data-Engineering]
header:
  image: /assets/images/bg/20251014_150500.jpg
---

> "The most dangerous bugs are the ones that succeed."

# Zero Rows, Zero Errors: How Snowflake Silently Ate Our Regex Backslashes

## The Scene

Fifteen consecutive DAG runs. All SUCCESS. Zero rows extracted. Zero rows upserted. No alerts. No errors in the control table. Salesforce had no attendance data. The watermark cursor kept advancing, window after window, over a week of real data that was sitting right there in Snowflake.

This is the story of a one-character class that never reached the regex engine.

## The Code That Looked Fine

Our Python DAG extracts Moodle gradebook rows from Snowflake and upserts them to Salesforce. The attendance filter matches grade items named "Week 1", "Week 2", etc.:

```python
cur.execute("""
    ...
    AND REGEXP_LIKE(gi."itemname", '^Week\\s+[0-9]+$', 'i')
    ...
""")
```

If you read Python, this looks correct. `\\s` is a single backslash followed by `s` — the `\s` whitespace class. And in Python's `re` module, it *would* work.

But this SQL doesn't run in Python. It runs in Snowflake.

## Two Parsers, One Lost Backslash

Between your Python source and Snowflake's regex engine, a string passes through **two** parsing layers. Each one can strip a backslash:

```
Layer 1: Python string literal
    '\\s'  →  \s  (Python resolves \\ to one backslash)

Layer 2: Snowflake SQL string literal
    '\s'  →  s   (Snowflake doesn't recognize \s — drops the backslash)

Layer 3: Regex engine
    Receives: '^Weeks+[0-9]+$'
    Matches: "Weekssss4" but not "Week 4"
```

### Why Snowflake Drops the Backslash

Snowflake's SQL string parser recognizes a small set of escape sequences:

| Escape | Recognized? | Result |
|--------|:-----------:|--------|
| `\\` | ✅ | literal `\` |
| `\'` | ✅ | literal `'` |
| `\n` | ✅ | newline |
| `\s` | ❌ | **backslash dropped**, keeps `s` |
| `\d` | ❌ | **backslash dropped**, keeps `d` |
| `\w` | ❌ | **backslash dropped**, keeps `w` |

This is by design. SQL string literals predate regex by decades. Undefined escapes are silently dropped for backward compatibility — no error, no warning. PostgreSQL in strict mode is the exception; most databases (Snowflake, Oracle, MySQL) follow the "drop and move on" convention.

This means `REGEXP_LIKE` never sees your `\s`. It sees the letter `s`.

## Proving It: The Smoking Gun

Snowflake's `GET_QUERY_OPERATOR_STATS` shows the *compiled* filter condition for any query:

```sql
SELECT operator_type, operator_attributes
FROM TABLE(GET_QUERY_OPERATOR_STATS('<query_id>'))
WHERE operator_type = 'Filter';
```

Our attendance query showed:

```
filter_condition: GI."itemname" REGEXP_LIKE '^Weeks+[0-9]+$'
```

There it is. `\s` became `s`. The regex was matching "one or more letter s after Week" — not whitespace.

Same time window, two patterns, two very different row counts:

| Pattern | Rows |
|---------|------|
| `^Weeks+[0-9]+$` (eaten) | **0** |
| `^Week[[:space:]]+[0-9]+$` (POSIX) | **1,887** |

## The Fix: POSIX Character Classes

```sql
-- Before: backslash eaten by Snowflake string parser
AND REGEXP_LIKE(gi."itemname", '^Week\s+[0-9]+$', 'i')

-- After: POSIX class — no backslash to eat
AND REGEXP_LIKE(gi."itemname", '^Week[[:space:]]+[0-9]+$', 'i')
```

`[[:space:]]` is a POSIX character class. It means the same thing as `\s` (any whitespace character), but it doesn't contain a backslash. No backslash means no layer can strip it.

### The Translation Table

| Intent | ❌ Don't use in Snowflake SQL | ✅ Use instead |
|--------|------------------------------|----------------|
| Whitespace | `\s` | `[[:space:]]` |
| Digit | `\d` | `[[:digit:]]` or `[0-9]` |
| Word char | `\w` | `[[:alnum:]]` |

You *can* get `\s` to the regex engine by quadruple-escaping in Python (`'\\\\s'` → `\\s` in SQL → `\s` in value), but that's fragile. One refactor, one f-string change, and it breaks again. POSIX classes are zero-backslash by construction.

## Why This Is Worse Than a Crash

A failed DAG run is loud:
- Alerts fire
- Watermark doesn't advance (next run retries the same window)
- Error message in the control table

A zero-row SUCCESS is silent:
- **No alerts** — the run "succeeded"
- **Watermark advances** — the data window is permanently skipped
- **Looks healthy** — dashboards show all green

By the time we noticed, 15 windows of attendance data had been skipped. Fixing the SQL wasn't enough — we also had to replay the missed window:

```json
{"jobs": ["attendance"], "watermark_from": 1789633681, "watermark_to": 1790238481}
```

Crucially, replaying *before* fixing the SQL just writes another SUCCESS with 0 rows. The replay is only useful after the regex is corrected on the live branch.

## Why Tests Didn't Catch It

Our test asserted:

```python
assert 'REGEXP_LIKE' in sql  # Checks the function name exists. That's it.
```

It didn't check *what pattern* the function received. The fix:

```python
assert "REGEXP_LIKE(gi.\"itemname\", '^Week[[:space:]]+[0-9]+$', 'i')" in sql
assert '\\s' not in sql  # No backslash shorthand survives into Snowflake SQL
```

## The Checklist I Wish I'd Had

For any `REGEXP_LIKE` / `REGEXP_REPLACE` / `REGEXP_SUBSTR` in Python code that targets Snowflake:

- [ ] Does the SQL text contain `\s`, `\d`, or `\w`? → Replace with POSIX class
- [ ] Does the test assert the **exact pattern string**, not just the function name?
- [ ] After a zero-row run, did I check `GET_QUERY_OPERATOR_STATS` for the compiled filter?
- [ ] In a raw `.sql` file (no Python layer), `\\s` *is* safe — SQL parser reduces `\\` to `\`. But `[[:space:]]` is still cleaner.

## The Takeaway

This bug wasn't "I wrote the wrong regex." In Python, `'^Week\\s+[0-9]+$'` matches `Week 4` perfectly. The bug was **assuming one parser when there are two**.

Your Python string literal has its own escape rules. Snowflake's SQL string literal has different escape rules. The regex engine has a third set. When you write regex in SQL in Python, you're threading a needle through three layers — and any one of them can silently eat the backslash you're depending on.

POSIX character classes sidestep the entire problem. No backslash, no layers to survive, no silent failure.

In data engineering, the scariest outcome isn't an error — it's a pipeline that successfully does nothing.

---

*Check your Snowflake regex patterns. Your backslashes might already be gone.*
