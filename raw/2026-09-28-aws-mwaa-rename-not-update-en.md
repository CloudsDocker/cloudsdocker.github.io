---
title: You Thought You Renamed It. AWS Heard "Demolish and Rebuild."
header:
    image: /assets/images/hd_aws_certificat.png
date: 2026-09-28
tags:
 - aws
 - airflow
 - terraform
 - devops
 - cloud-infrastructure
permalink: /blogs/tech/en/aws-mwaa-rename-not-update
layout: single
category: tech
lang: en
---

> "No man ever steps in the same river twice, for it's not the same river and he's not the same man." — Heraclitus

---

# You Thought You Renamed It. AWS Heard "Demolish and Rebuild."

*A two-line Terraform diff, and how a managed Airflow environment's entire history quietly disappeared*

---

Last week we upgraded a managed Airflow environment (AWS MWAA) from 2.10.3 to 2.11.2. Dev went first and came through clean — not a single broken DAG. When it was SIT's turn, the Terraform PR I opened touched exactly two lines:

```diff
-airflow_version: "2.10.3"
+airflow_version: "2.11.2"
-name: ${channel}-${env}-251
+name: ${channel}-${env}-2112
```

`251` is shorthand for 2.5.1, `2112` for 2.11.2 — a naming habit this repo has followed for years, baking the running Airflow version straight into the environment's name so anyone can tell at a glance what's deployed. It reads as harmless as a diff can get.

After apply, the console showed `Status: AVAILABLE`, `LastUpdate: SUCCESS`. I checked CloudWatch out of habit — clean requirements install logs, scheduler heartbeating normally. I closed my laptop thinking the upgrade was done.

Ten minutes later the DAG list started filling with red. `Broken DAG` after `Broken DAG` — one wave was a permissions error, another was a variable error. Once I actually queried the logs, the second wave came out to an exact **195**:

```
airflow.exceptions.AirflowException: The access_control mapping for DAG 'X'
includes a role named 'finance-developers', but that role does not exist
```

```
File "db_context_hook.py", line 32, in get_database_name
    mapper = context_database_map[self.environment][self.database_context]
             ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
KeyError: ''
```

One error is a permission role that no longer exists. The other is an Airflow Variable that came back as an empty string. Two different symptoms, one shared cause: **this environment's metadata database was brand new and completely empty.**

While I was staring at the wall of errors, a teammate — I'll call him Dean — dropped a one-liner in chat:

> "There's no history in the interface. It has to be a new database."

That's the moment it landed: I thought I'd upgraded a version number. AWS heard something closer to "tear the building down and put up a new one on the same lot."

This post is about untangling exactly that. Once you see it clearly, you won't just dodge the mistake we made — you'll walk away with an intuition about what "identity" actually means for a cloud resource, one that travels well beyond MWAA to RDS, EKS, or any resource whose Update API you've never actually read line by line.

**Three things to take with you, in 30 seconds:**

- In most systems, renaming is a free metadata operation. In the world of cloud resources, the name is often the identity itself — and once that equivalence breaks, the loss is permanent.
- If a resource's Update API doesn't accept a field in its request body at all, that field isn't "technically updatable but risky" — it's immutable by design. That distinction should change how you read docs and how you review a PR.
- A Terraform diff only tells you "this line changed." It will never tell you that the change just crossed an identity boundary that only the cloud provider's own API contract knows exists.

This is written in the order that teaches best, not the order I discovered things in — the real investigation zigzagged; you don't need to zigzag with me.

---

### Chapter 1: The Detective Work — Two Calls, Not One Update

`Status: AVAILABLE` isn't lying to you. It's telling the truth about a narrow question: is this environment healthy right now? The problem is that "this environment" and "the environment I thought I was upgrading" turned out to be two different individuals wearing the same badge.

Confirming that took evidence, not a hunch — pulling both API calls out of CloudTrail by timestamp:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=DeleteEnvironment \
  --query 'Events[*].[EventTime,Resources[0].ResourceName]' --output text

aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=CreateEnvironment \
  --query 'Events[*].[EventTime,Resources[0].ResourceName]' --output text
```

The answer left no room for ambiguity:

```
10:58:46  DeleteEnvironment  etl-sit-251
11:26:12  CreateEnvironment  etl-sit-2112
```

Two records, two distinct API names, 28 minutes apart. That's not one `UpdateEnvironment` call logging itself twice — an actual update leaves a completely different trail. This was a genuine delete, followed by a genuine create. Not Theseus's ship, patched plank by plank while staying itself the whole time. Scuttled, and a lookalike launched under the same flag half an hour later.

> **What most people assume:** the console is green, no errors fired, so the upgrade must have worked.
> **What the senior engineer actually knows:** a health check answers "is it alive right now," never "is it still the thing I think it is." Those are two entirely different questions, and one cannot answer the other.

---

### Chapter 2: Digging to First Principles — Identity Fields Aren't Symmetric With Config Fields

The mystery's solved, but the more useful question is the one underneath it: **why does changing one string trigger a full teardown?** That's the layer that actually saves you next time.

The answer doesn't live in Terraform's docs. It lives in AWS's own MWAA API reference. I went and read the request body for the `UpdateEnvironment` action, and found something genuinely counter-intuitive:

```
PATCH /environments/{Name} HTTP/1.1
{
   "AirflowConfigurationOptions": {...},
   "AirflowVersion": "...",
   "DagS3Path": "...",
   "EnvironmentClass": "...",
   "ExecutionRoleArn": "...",
   "MaxWorkers": ...,
   "NetworkConfiguration": {...},
   "WorkerReplacementStrategy": "...",
   ... (a dozen more fields)
}
```

`Name` only ever appears in the URL path — it's how you tell AWS *which* existing environment to update. **It never appears in the request body.** Which means renaming isn't a degraded, higher-risk operation you were warned away from. It's an operation that does not exist at the API design level. You cannot ask AWS to rename an environment. You can only ask it to create one and delete another — which is exactly the pair of CloudTrail entries above.

There's a mental model worth naming here on its own: **broken symmetry.**

Terraform lays `name`, `airflow_version`, and `max_workers` out at the same indentation level, as if they were an interchangeable set of config knobs. That's a clean abstraction, and it's exactly the kind that lies to you. It paints "configuration property" and "identity property" as the same category of thing. In the real world they aren't symmetric at all — changing `max_workers` is a configuration tweak; changing `name` is rewriting the resource's ID card. The point where a clean abstraction quietly stops being smooth is where the symmetry breaks, and it never announces itself on the README's front page — it's buried in the one line of API reference nobody reads until after the incident.

> **First principle:** never ask "does this field sound like config or like identity." Read the Update API's request body. Whether the field is there is the only fact that matters.

**Worth remembering for an interview**: if someone asks "how do you tell whether a cloud resource property can be changed in place," "check if the docs say immutable" is a passing answer. "Go read the corresponding Update API's request body and see if the field is actually in it" is the answer that gets remembered — because it replaces a guess with a verifiable fact.

---

### Chapter 3: Code Archaeology — This Had Already Happened Before

Dean's "no history in the interface" sent me digging through CloudWatch log groups, and what I found was more unsettling than the incident itself:

```
airflow-etl-sit-243-*
airflow-etl-sit-251-*
airflow-etl-sit-306-*
airflow-etl-sit-DATA-9395-*
airflow-etl-sit-rollback-*
airflow-etl-sit-2112-*
```

Six log groups, the oldest dating back three years. Every suffix is a fossil from some past "upgrade" — `243`, `251`, `306`... this same version-in-the-name convention had already staged the identical destroy-and-rebuild at least five times over three years, silently wiping the Postgres metadata each time, and nobody had ever needed the old history badly enough afterward to notice it was gone. Which is exactly why nobody had ever flagged it as an incident instead of a routine upgrade.

This is the uncomfortable part of code archaeology: it doesn't only live in old code nobody's brave enough to delete — it lives in an operational habit repeated for years. Nobody wrote down "this naming convention destroys data" because whoever designed it probably had no idea they were building a time bomb. They just wanted the environment's name to be legible at a glance.

| | What it looked like | What actually happened |
|---|---|---|
| The PR diff | Two string fields changed | A full resource teardown and rebuild |
| Console status | `AVAILABLE` / `SUCCESS` | A brand-new, empty metadata database |
| The naming convention's intent | Make the current version obvious | Welded the version number into the resource's identity |
| Times this fired in the last 3 years | 0 (never reported as an incident) | At least 5 (the log groups are the receipts) |

---

### Chapter 4: The Path That Doesn't Draw Blood

The most ironic part: AWS explicitly supports an in-place upgrade path, and it automatically snapshots the metadata database before the change and restores it after — Variables, connections, DAG run history, pause state, all preserved with zero manual work. The one condition: **don't touch `Name`. Change `AirflowVersion` only.**

And if you genuinely do need a new environment name for some other reason, AWS has a documented, non-improvised path for that too: run a `db_export` DAG on the **old** environment — while it's still alive — to push `variable`, DAG run history, `xcom`, and related tables to S3; then run a `db_import` DAG on the new environment to pull them back in. The one hard constraint that makes or breaks this: **the export has to finish before the old environment is deleted. Once it's gone, this door is closed for good, with no recovery path on the other side.**

| Scenario | What to do | Outcome |
|---|---|---|
| Just bumping the Airflow version | Change `AirflowVersion` only, leave `Name` untouched | AWS auto-snapshots and restores — nothing lost |
| A new environment name is genuinely required | Run `db_export` on the old env first, `db_import` on the new one | Data moves over; all DAGs auto-pause during the migration window |
| What we actually did | — (already too late) | Metadata gone for good; CloudWatch logs are the only partial recovery |

That last row deserves a footnote: task and scheduler logs in CloudWatch live independently of the MWAA environment itself. Deleting the environment doesn't delete them, and they're never auto-linked into the new environment's UI. So we could still pull a specific task's raw output back out of `airflow-etl-sit-251-*` — we just couldn't get back the graphical run-history timeline the UI used to show. That's not luck. CloudWatch Logs and the MWAA metadata database are two entirely unrelated storage systems; one happened to survive, the other didn't.

---

### Closing: Two Questions, One Answer

Compress the whole incident into two questions worth asking yourself before any similar change:

1. **Is this an update, or a replacement?** Don't guess from intuition — go read the field list in the corresponding Update API's request body and check whether the field you're changing is actually in it.
2. **If it's unavoidably a replacement, is the data packed for the move?** The official export/import path only works while the old resource is still alive. There's no grace period after.

**Do this today:**

1. Open your own project's Terraform/CloudFormation definitions and walk every field that would trigger a force-replace — flag them now, don't wait for a diff to teach you the hard way.
2. Before the next "version bump" PR, go read the request body of the relevant cloud service's Update API and confirm the field you're changing is actually listed there.
3. If your own naming convention also bakes a version number into an identity field, go check how long it's been running, and whether every past "upgrade" quietly destroyed something nobody ever went back to look for.
4. For every stateful resource your team depends on, build an enforced "export before you touch this" checklist — don't rely on institutional memory, because tribal knowledge always outlives the person who remembers why it matters.

---

*Cloud providers never lie to you. They just never volunteer which fields are merely names, and which names are actually identities — that line only reveals itself the moment you walk into it.*
