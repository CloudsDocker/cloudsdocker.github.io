---
title: "Why Your curl -d JSON Blows Up When You Paste in Multi-line CSV"
date: 2026-08-12
categories: [engineering, shell, debugging]
tags: [curl, json, jq, salesforce, zsh, debugging]
---

While debugging the `bulk-load` endpoint of a local `ditapi-s-salesforce-v1` service, a seemingly normal `curl -d '...'` command blew up the JSON parsing. The root cause is a classic, easy-to-hit trap — here's the debugging trail and a small zsh function that came out of it.

## The offending command

```bash
curl -sv -X POST http://localhost:8003/bulk-load \
  -H "x-salesforce-org: S360UAT" \
  -H 'Content-Type: application/json' \
  -d '{"csv_data":"StaffId__c,FirstName,LastName,
    RecordType.Name\n999999901,TESTASC,STAFFEXTID,Staff","salesforce_object":"Account","external_id_field_name":"StaffId__c"}' \
  2>&1 | tail -30
```

Intent is simple: call the local service to bulk-upsert into the `Account` object in the **S360UAT** Salesforce org, using `StaffId__c` as the external ID field to match/create records.

## The gotcha: a real newline is not the same as a literal `\n`

The `-d` payload mixes two different things inside a single JSON string:

1. After `LastName,` there's an **actual newline character** typed into the terminal (from multi-line pasting), not the escape sequence `\n`. JSON strings **do not allow raw, unescaped newline characters** inside them — a strict parser will throw something like "Invalid control character."
2. That newline is followed by 4 spaces of indentation (leftover from pretty-formatted pasting), which leak into the CSV header, producing `"    RecordType.Name"` with a leading space. Even if the JSON somehow parsed, the backend's column-name mapping would likely fail to match it.
3. The one before `999999901` is the actual literal `\n` escape — that's the correct way to encode a newline-separated CSV row inside a JSON string.

Root cause: cramming multi-line CSV directly into a single-line `-d '...'` string is the easiest way to fall into this — a real newline and an escaped `\n` are visually indistinguishable in a terminal.

## Fix #1: write to a temp file with heredoc

```bash
cat > /tmp/payload.json <<'EOF'
{
  "csv_data": "StaffId__c,FirstName,LastName,RecordType.Name\n999999901,TESTASC,STAFFEXTID,Staff",
  "salesforce_object": "Account",
  "external_id_field_name": "StaffId__c"
}
EOF

curl -sv -X POST http://localhost:8003/bulk-load \
  -H "x-salesforce-org: S360UAT" \
  -H 'Content-Type: application/json' \
  --data @/tmp/payload.json 2>&1 | tail -30
```

`<<'EOF'` (with quotes around `EOF`) makes the heredoc write content **verbatim, without variable expansion**. You still have to type the JSON-internal newline as a literal `\n` — no real line breaks inside the string.

## Fix #2: let `jq -Rs` / `jq -n --arg` escape real multi-line text for you (safer)

```bash
CSV=$(cat <<'EOF'
StaffId__c,FirstName,LastName,RecordType.Name
999999901,TESTASC,STAFFEXTID,Staff
EOF
)

jq -n --arg csv "$CSV" \
  '{csv_data: $csv, salesforce_object: "Account", external_id_field_name: "StaffId__c"}' \
  > /tmp/payload.json

curl -sv -X POST http://localhost:8003/bulk-load \
  -H "x-salesforce-org: S360UAT" \
  -H 'Content-Type: application/json' \
  --data @/tmp/payload.json 2>&1 | tail -30
```

The key move is `jq -n --arg csv "$CSV" '{...}'`: hand jq the real, multi-line string and let it produce valid escaping automatically. Whenever you're stuffing CSV or multi-line text into JSON, default to this instead of hand-escaping.

## curl flags, decoded

| flag | what it does |
|---|---|
| `-s` (silent) | suppresses the progress meter |
| `-v` (verbose) | prints the full request/response exchange — `>` lines are the request headers sent, `<` lines are the response headers received, useful for spotting 4xx/5xx or header mismatches |
| `-X POST` | explicitly sets the method (curl infers POST automatically when `-d` is present, but being explicit is clearer) |
| `2>&1 \| tail -30` | `-v` output goes to stderr, so `2>&1` redirects it to stdout before `tail` can capture it; `tail -30` avoids flooding the terminal |

## Wrapping it into a zsh function: dcurl

"Fire a request, then check the tail of the service log" is a pattern worth naming — same spirit as `gacp` / `klog`:

```bash
# usage: dcurl <endpoint> <json-file> [logfile]
dcurl() {
  local endpoint="$1"
  local payload="$2"
  local logfile="${3:-/tmp/ditapi-s-salesforce-v1.log}"

  command -v jq >/dev/null || { echo "jq required"; return 1; }

  curl -sv -X POST "http://localhost:8003${endpoint}" \
    -H "x-salesforce-org: S360UAT" \
    -H 'Content-Type: application/json' \
    --data @"$payload" 2>&1 | tail -30

  echo "---LOG---"
  tail -40 "$logfile"
}
```

Natural next steps: support arbitrary endpoints/headers and auto-pretty-print the JSON response; parameterize `x-salesforce-org` to switch between UAT/PROD; or reuse the same payload-construction logic inside an Airflow DAG instead of duplicating it across bash and Python.

## Takeaway

Never hand-cram multi-line text into a single-line shell string. Let `jq -Rs` / `jq -n --arg` handle the escaping — it's far more reliable than trying to eyeball whether something is a real newline or a literal `\n`.
