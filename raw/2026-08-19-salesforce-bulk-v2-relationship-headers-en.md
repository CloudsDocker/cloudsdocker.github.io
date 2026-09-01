---
title: "The Error Message Was Right All Along: Salesforce Bulk API v2 Relationship Headers"
date: 2026-08-19
categories: [engineering, salesforce, debugging]
tags: [salesforce, bulk-api, csv, polymorphic, data-integration, debugging]
---

A data pipeline had been silently failing for three weeks. Every run, one object loaded fine and the next one died with the same message:

```
InvalidBatch : type is not needed for non polymorphic foreign key references: Parent
```

We read that message dozens of times. We queried org metadata. We escalated to the Salesforce team. We drafted a case. What we never did — until the very end — was **take the sentence literally**.

The fix was deleting eight characters.

## The setup

The pipeline syncs applicant data into Salesforce via Bulk API v2 upsert. Two objects, loaded in sequence:

1. `Account` (Person Account) — keyed on `ApplicantId__c`
2. `ContactPointEmail` — keyed on `ExternalId__c`, and each row must link back to its parent Account

Because we load by **business key** rather than Salesforce Id, the parent link is expressed as a special CSV column. That column was:

```
Account:Parent.ApplicantId__c
```

Account loaded every time — 784 records, zero failures. ContactPointEmail failed every time, with zero records processed *and* zero records failed.

That last detail is the first real clue, and we skated past it.

## Reading a Bulk v2 failure correctly

Bulk API v2 ingest is three calls:

```
POST  /services/data/v65.0/jobs/ingest              → create job
PUT   /services/data/v65.0/jobs/ingest/{id}/batches → upload CSV
GET   /services/data/v65.0/jobs/ingest/{id}         → poll status
```

The trap: **the CSV upload returns `201 Created` even when the header is garbage.** Salesforce doesn't validate column names at upload time. You get a cheerful 201, then the job flips to `Failed` seconds later.

```json
{
  "id": "750XXXXXXXXXXXXXXX",
  "object": "ContactPointEmail",
  "state": "Failed",
  "numberRecordsProcessed": 0,
  "numberRecordsFailed": 0,
  "errorMessage": "InvalidBatch : type is not needed for non polymorphic foreign key references: Parent"
}
```

Learn to read those two counters together:

| processed | failed | Meaning |
|---:|---:|---|
| 0 | 0 | **Header/batch rejected.** No row was ever evaluated. |
| 700 | 84 | Rows were evaluated; 84 hit validation rules. Fetch `failedResults`. |
| 784 | 0 | Clean load. |

`0 / 0` means the problem is structural — the schema of your CSV, not the contents. There is no `failedResults` CSV to fetch, because Salesforce never got as far as looking at a row. If you find yourself hunting for bad data when you see `0 / 0`, stop; you're in the wrong layer.

## Wrong turn #1: the metadata "paradox"

Since the error said "non polymorphic," we asked the org what it thought. Two Tooling API objects describe a field, and they seemed to disagree:

```sql
-- What kind of field is this?
SELECT QualifiedApiName, DataType, IsPolymorphicForeignKey, RelationshipName
FROM FieldDefinition
WHERE EntityDefinition.QualifiedApiName = 'ContactPointEmail'
  AND QualifiedApiName = 'ParentId'
```
```
DataType                = Master-Detail(Account)
IsPolymorphicForeignKey = true          ← "it IS polymorphic"
RelationshipName        = Parent
```

```sql
-- What can it actually point at?
SELECT QualifiedApiName, DataType, ReferenceTo
FROM EntityParticle
WHERE EntityDefinition.QualifiedApiName = 'ContactPointEmail'
  AND QualifiedApiName = 'ParentId'
```
```
ReferenceTo = { referenceTo: ["Account"] }   ← exactly one target
```

A flag saying "polymorphic," a list with one entry. We built a whole theory on this contradiction: Bulk v2 must be gating on the *count* of `referenceTo` entries rather than the flag, so the org config is inconsistent and Salesforce needs to fix it at source.

That theory was **correct on the mechanics and useless as a conclusion.** Yes, Bulk v2 gates on the entry count. But that's not a bug to be fixed — it's the documented rule, and it was already telling us the answer. `referenceTo` has one entry ⇒ don't send a type prefix. Full stop.

We turned a plainly worded instruction into a metadata mystery because the word "polymorphic" appeared in two places and we anchored on the one that was easier to blame.

## Wrong turn #2: trusting a claim without reproducing it

The Salesforce team replied that they had successfully created a record with this header:

```
ExternalId__c    Parent:Account:ApplicantId__c    EmailAddress    UsageType__c
```

Three sections. Ours had three sections too, just in a different order. Close enough to sound authoritative, different enough to explain a discrepancy. Tempting.

So we ran it. Not a variant of it — the exact string, against the exact org, through the exact code path our pipeline uses.

## The experiment

The whole investigation collapses into one loop. A small bash function, one CSV row, five header spellings:

```bash
run() {
  python3 - "$1" > /tmp/p.json <<'PY'
import json, sys
h = sys.argv[1]
print(json.dumps({
  "csv_data": f"ExternalId__c,{h},EmailAddress,UsageType__c\n"
              f"APPLICANT-001,APPLICANT-001,test@example.edu,Personal",
  "salesforce_object": "ContactPointEmail",
  "external_id_field_name": "ExternalId__c",
}))
PY
  printf '%-40s ' "$1"
  curl -s -X POST http://localhost:18080/bulk-load \
    -H 'Content-Type: application/json' \
    -H 'x-salesforce-org: SANDBOX' \
    -d @/tmp/p.json \
  | python3 -c "
import json,sys
d = json.load(sys.stdin)
print('SUCCESS  %d processed' % d['data']['records_processed']) if d.get('success') \
  else print('FAILED   ' + d['error']['details'].split('Debug Info')[0].strip())
"
}

run 'Parent:Account:ApplicantId__c'    # the SF team's claim
run 'Account:Parent:ApplicantId__c'
run 'Account:Parent.ApplicantId__c'    # what our code sent
run 'Parent:Account.ApplicantId__c'
run 'Parent.ApplicantId__c'
```

Results:

| Header column | Result |
|---|---|
| `Parent:Account:ApplicantId__c` | `InvalidBatch : Field name not found : Parent:Account:ApplicantId__c` |
| `Account:Parent:ApplicantId__c` | `InvalidBatch : Field name not found : Account:Parent:ApplicantId__c` |
| `Account:Parent.ApplicantId__c` | `InvalidBatch : type is not needed for non polymorphic foreign key references: Parent` |
| `Parent:Account.ApplicantId__c` | `InvalidBatch : Unable to find relationship: Account` |
| **`Parent.ApplicantId__c`** | **SUCCESS — 1 processed, 0 failed** |

The claimed-working header doesn't work. Not in that order, not in the reverse order.

Three weeks of theorising, answered in ninety seconds by varying one string.

## Reverse-engineering the grammar from the errors

Here's the part worth sharing with your team, because it generalises far beyond this bug. **The three failures are different from each other, and each difference tells you how the parser works.**

Compare rows 3 and 4:

- `Parent:Account.X` → *"Unable to find relationship: **Account**"*

  Salesforce read the token between the colon and the dot as the relationship name. So the grammar is `ObjectType:RelationshipName.MatchField`.

- `Account:Parent.X` → *"type is not needed..."*

  This parsed **correctly** — type `Account`, relationship `Parent`. Salesforce understood exactly what we meant and refused it on policy, not on syntax.

And rows 1 and 2, both all-colons:

- → *"Field name not found: `<entire string>`"*

  With no dot, there's nothing to split on. Salesforce gave up on relationship parsing and treated the whole thing as one literal field name. **A three-section header without a dot is not a relationship reference at all.**

So the error messages were never inconsistent. They were three precise reports from three different stages of one parser: tokenizing, resolving, then policy-checking. We just weren't reading them as a sequence.

> **Takeaway for debugging generally:** when a system gives you *different* errors for *similar* inputs, that difference is free documentation. Deliberately perturbing the input to harvest more error messages is often faster than reading the docs — and it's authoritative, because it's the actual implementation talking.

## The underlying model: every lookup has two names

Now the concept the whole bug rests on.

Every lookup or master-detail field in Salesforce carries **two** names. CSV relationship headers use the second one:

| Field API name (stores the Id) | Relationship name (use this in headers) |
|---|---|
| `ParentId` | `Parent` |
| `AccountId` | `Account` |
| `OwnerId` | `Owner` |
| `RecordTypeId` | `RecordType` |
| `ParentApplication__c` *(custom)* | `ParentApplication__r` |

The rule: **standard** lookups drop the trailing `Id`; **custom** lookups swap `__c` for `__r`.

Both conventions usually coexist in the same file. From our record builders:

```python
{
    'Parent.ApplicantId__c':                  parent_id,   # standard → no suffix
    'RecordType.Name':                        'Student',   # standard → no suffix
    'Account.ApplicantId__c':                 parent_id,   # standard → no suffix
    'ParentApplication__r.ExternalId__c':     parent_app,  # custom   → __r
}
```

The part **after the dot** is *which field to match on*. So `Parent.ApplicantId__c` reads as: "find the parent record whose `ApplicantId__c` equals this cell, and link to it." You're joining on a business key instead of a Salesforce Id — which is the entire reason this syntax exists, and what makes idempotent re-runnable loads possible without storing Salesforce Ids on your side.

## The three header shapes

```
FieldApiName                             ← plain scalar column
RelationshipName.MatchField              ← single-target lookup    (2 sections)
ObjectType:RelationshipName.MatchField   ← polymorphic lookup      (3 sections)
```

The critical rule, and the one that cost us three weeks:

> The 3-section form is **not** an optional, more-explicit style. Salesforce accepts it *only* when the relationship genuinely has more than one possible target type, and **rejects it** when it doesn't.

Being more explicit is not free. Specifying a type that couldn't have been ambiguous is an error, not helpful redundancy.

## Which relationships are actually polymorphic

These are the ones that genuinely need the `ObjectType:` prefix:

| Relationship | Field | Can point to | Where you meet it |
|---|---|---|---|
| `Owner` | `OwnerId` | User **or** Group (queue) | Nearly every object |
| `Who` | `WhoId` | Contact **or** Lead | Task, Event |
| `What` | `WhatId` | Account, Opportunity, Case, custom… | Task, Event |
| `Parent` | `ParentId` | almost anything | Note, Attachment, ContentDocumentLink |

Valid 3-section headers look like `Owner:User.Username` or `What:Account.MyExtId__c`. `Owner` is the one you'll hit most in practice — assigning to a queue versus a user is the classic case.

Notice that `Parent` is in that table. That's why our confusion was reasonable rather than stupid: on `Note` and `Attachment`, `Parent` really is wildly polymorphic. On `ContactPointEmail` it isn't. **The relationship name tells you the semantics ("my owning record"), not the cardinality.** Never infer the header shape from the name.

`RecordType.Name` is the same mechanism, just so common it stops looking like a relationship traversal: `RecordTypeId` is a single-target lookup to `RecordType`, matched on `Name` instead of an external Id. Two sections, no prefix — because RecordType is the only thing it can point at.

## The 30-second check

The question to ask before adding any lookup column is **not** "is this field described as polymorphic anywhere?" It's:

> **How many object types can this specific relationship point to, in this specific org?**

And you never have to guess:

```sql
SELECT QualifiedApiName, RelationshipName, DataType, ReferenceTo
FROM EntityParticle
WHERE EntityDefinition.QualifiedApiName = 'ContactPointEmail'
  AND QualifiedApiName = 'ParentId'
```

`ReferenceTo` gives you the list. **One entry → 2 sections, no prefix. Two or more → 3 sections, prefix required.**

Note the "in this specific org" caveat. Feature enablement and licensing can change a relationship's target list between orgs. A header that works in one sandbox can legitimately fail in another — which is exactly what happened to us when the pipeline was repointed to a new org, and why the breakage looked like it came from nowhere.

## The fix

```diff
-# Bulk v2 polymorphic relationship header:
-# ObjectType:RelationshipName.IndexedFieldName
-CONTACT_POINT_PARENT_EXT_ID = 'Account:Parent.ApplicantId__c'
+# Bulk v2 relationship header: RelationshipName.IndexedFieldName
+CONTACT_POINT_PARENT_EXT_ID = 'Parent.ApplicantId__c'
```

One constant, shared by the email, phone, and address builders. Three weeks, eight characters.

## Takeaways

**Believe the error message before you believe your model of the system.** "type is not needed for non polymorphic foreign key references" is not cryptic. It names the field, states the fact, and tells you what to remove. We treated it as a symptom to be explained away rather than an instruction to be followed, because we'd already decided the field *was* polymorphic.

**`0 processed / 0 failed` is a schema error, not a data error.** Different counters mean different investigations. Don't go looking for bad rows when no row was ever read.

**Reproduce a claim before you act on it — or before you let it stall you.** "We inserted it successfully" was offered in good faith and was almost certainly true *in some tool*. Data Loader, Workbench, and Bulk v1 accept header grammar that Bulk v2 REST rejects. A success in a different mechanism is not evidence about yours.

**Perturb the input to harvest error messages.** Five variants took ninety seconds and gave us the parser's grammar directly from the implementation. That beats three weeks of reading metadata and drafting escalations.

**Escalate with a reproduction, not a theory.** We nearly filed a platform case about a metadata inconsistency that was, in the end, entirely irrelevant to the failure. One test matrix would have prevented that — and would have saved another team the time too.
