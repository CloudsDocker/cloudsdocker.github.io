---
title: One Error, Five Fates — Anatomy of MWAA Plugin Loading
header:
    image: /assets/images/how_to_save_expect_script_run_output_to_file_locally.jpg
date: 2026-10-07
tags:
 - airflow
 - mwaa
 - aws
 - python
 - devops
permalink: /blogs/tech/en/mwaa-one-error-five-fates
layout: single
category: tech
---

> To see a mountain as a ridge from the front and a peak from the side — near, far, high, low, no two views the same. — Su Shi

# That `ModuleNotFoundError` of yours dies five different deaths across five components

*From reading the error text to reading where the error landed — the one step that separates senior from junior*

A teammate who'd just inherited our new MWAA environment sent me a screenshot of red: **103 lines** of `Failed to import plugin ... ModuleNotFoundError: No module named 'teradatasql'` / `googleapiclient` / `airflow.providers.sftp`, wall to wall on the Airflow UI. He was staring at the `plugins/.airflowignore` we'd merged the day before, and asked a perfectly reasonable question:

> "Did our change break plugin loading?"

I told him to leave the code alone and trigger a few `Test_*` smoke DAGs. That looked worse — **four red in a row**: `Test_snowflake` died on `JWT token is invalid`, `Test_Excel_Ecs` on `TaskDefinition not found`, `CIM__QFF`'s `OPEN_BUSINESS_DATE` on a container `exitCode 1`. He was already reaching for the rollback button.

I stopped him. None of those four reds — nor the 103 lines — was a plugin problem, and not one was caused by that `.airflowignore`. But to explain *why not*, you have to take apart something everyone assumes they understand and almost nobody actually does: **inside MWAA, the single folder `plugins/` is "read" five different ways by five different components. The same line `ModuleNotFoundError` is cosmetic on the WebServer, a heart attack on the Worker, and not even its business inside a Fargate container.**

If you run MWAA — or any system where one codebase is executed by several processes — this one's for you. Three intuitions you'll walk out with:

- **Whether an error is fatal depends on *which component, at which layer* logged it — never on the error text alone.**
- **`.airflowignore` silences the WebServer's *scan*, not execution's *import* — those are two entirely separate loading paths.**
- **To prove a change whose only symptom is "the errors disappear", your evidence has to be anchored on a process restart — otherwise you're measuring air.**

Ordered most-useful-first, not in the order I actually debugged it.

---

## 1. The first screen of red: 103 broken plugins, and not one broken DAG

Here's the raw line — mind the path, and what it's actually missing:

```text
[plugins_manager.py:305] ERROR - Failed to import plugin
  /usr/local/airflow/plugins/plugins/hooks/gdrive_hook.py
ModuleNotFoundError: No module named 'googleapiclient'
...hooks/teradata_ctlfw_hook.py   → No module named 'teradatasql'
...hooks/sftp_hook.py             → No module named 'airflow.providers.sftp'
```

The line comes from `plugins_manager.py` — Airflow's **plugin manager**. At process startup it **walks the entire `plugins/` directory and imports every `.py`**, so it can find classes subclassing `AirflowPlugin` and register them as UI views, menus, timetables, listeners, and so on.

Problem: there isn't a single real `AirflowPlugin` under our `plugins/`. It's all custom hooks / operators / sensors that DAGs pull in directly via `from plugins.hooks.xxx import ...`. They are **not Airflow plugins** — they're **ordinary Python modules that happen to live in the plugins folder**. The plugin manager doesn't know that, eagerly imports each one anyway, and immediately slams into heavy third-party deps like `teradatasql` and `googleapiclient` — which **aren't installed on the WebServer at all**.

**Why is only the WebServer missing deps?** This is the root of the whole thing — a neat case of **broken symmetry**. In `PUBLIC_ONLY` mode the MWAA WebServer runs inside an **AWS-managed VPC with no egress**. When `requirements.txt` installs on the WebServer, the first package fails with `No matching distribution found` and the whole batch aborts. The Scheduler and Workers run in **your own VPC** with egress, so their deps install fine.

> Same `requirements.txt`, same `plugins/` — and because the *network the process lives in* is asymmetric, it collapses on the WebServer and runs clean on the Worker. That's the physical root of "one error, five fates."

The fix isn't to give the WebServer its deps (you can't — it has no network), it's to **tell the plugin manager not to scan those directories at all**. A `plugins/.airflowignore` is enough:

```text
# These are custom hooks/operators imported directly by DAGs, not Airflow plugins.
# Don't let the plugin manager eagerly import their third-party deps and fill the
# WebServer UI with Broken plugin errors.
hooks
operators
sensors
transfers
models
utils
exceptions.py
```

| | The naive read | The seasoned read |
|---|---|---|
| Seeing 103 red lines | "Plugin system is broken, deps missing — go install deps / roll back" | "WebServer is in a no-egress VPC; deps were never going to install. This is scan noise, not a functional fault" |
| What `.airflowignore` does | "Ignores some files" | "Moves non-plugin modules out of the plugin manager's eager-scan range" |
| Blast radius | "It touches plugin loading, might affect DAGs" | "It touches only the WebServer scan; it can't reach the execution path" |

**In one line: those 103 lines are the WebServer doing something it shouldn't (scanning non-plugin modules) in a no-network environment — not your code breaking.**

---

## 2. Why `.airflowignore` can shut the WebServer up without touching execution

The teammate's real fear: "If you tell the plugin manager not to load `operators/`, won't `from plugins.operators.xxx import` in the DAG also fail to resolve?"

No. Because **plugin loading has two entirely independent paths**, and `.airflowignore` cuts only one:

| | Path A: plugin-manager scan | Path B: `sys.path` import |
|---|---|---|
| Triggered by | `plugins_manager` walking `plugins/` at startup | `from plugins.x import Y` in DAG/task code |
| Purpose | Find `AirflowPlugin` subclasses to register UI/macros/timetables | Actually get the hook/operator class to use it |
| Honors `.airflowignore`? | **Yes** — ignored dirs aren't scanned | **No** — `plugins/` is on `sys.path`; imports resolve as always |
| Failure mode | WebServer UI shows Broken plugin (cosmetic) | DAG fails to parse / task import error (fatal) |

`.airflowignore` affects **Path A** only. Path B is plain Python import: MWAA puts `plugins/` on `sys.path`, so `from plugins.operators.xxx import Foo` works in any process, regardless of whether the plugin manager scanned it.

Evidence? After our change went live, I grepped the dev **DAGProcessing** (DAG parser) logs for import/parse errors:

```text
filter-pattern: ?"ModuleNotFoundError" ?"ImportError" ?"Broken DAG"
result: 0
```

And in this environment, **262 of 263 DAGs `import` `plugins.utils` and `plugins.operators`**. If `.airflowignore` had severed execution-side imports, this would be a sea of `ModuleNotFoundError: No module named 'plugins....'`. It's 0 — Path B is untouched.

> `.airflowignore` is a pair of scissors that only cuts "Path A". You're trimming the WebServer's eager scan, not the DAG's import — the two share a directory but run on two different mechanisms.

A buried **code-archaeology** landmine worth naming: I deliberately wrote a comment in that `.airflowignore` — "**if a real Airflow plugin (UI view / timetable / listener) is ever added, it must be excluded from these patterns or it will be silently ignored**." Because three months from now nobody will remember why this file exists, and it is exactly the thing that would make a *real* plugin silently not register. Writing the *why* into the file is the cheapest possible move to turn tribal knowledge into an engineering artifact.

---

## 3. Proving "the red is gone": anchor time on the gunicorn restart

The hard part of a change like `.airflowignore` is that **it has no positive output**. There's no "success" screenshot to take — its success *is* those 103 lines **disappearing**. And "proving something no longer exists" is the easiest kind of verification to fool yourself with.

I walked the teammate through three traps; each one you clear raises how much the conclusion is worth:

**Trap 1: deployed to S3 ≠ live on the environment.** MWAA **pins** `PluginsS3ObjectVersion` — it does not "pull S3-latest". Pushing to S3 is step one; terraform has to bump the version, `UpdateEnvironment` has to finish, and `get-environment` has to show the **new version id + Status=AVAILABLE + LastUpdate=SUCCESS** before you're running new code. `LastUpdate.CreatedAt` is your before/after dividing line.

**Trap 2: plugin import errors are logged exactly once — at WebServer (gunicorn) boot.** 99% of the WebServer log group is ELB `/health` access logs; `plugins_manager.py:305` red only appears when gunicorn re-scans `plugins/`. My first attempt took a fixed "last 12h" window — **0 hits** — not because there were no errors, but because the WebServer hadn't restarted in those 12h. **You have to anchor on the gunicorn restart first:**

```bash
aws logs filter-log-events --log-group-name airflow-edr-dev-2112-WebServer \
  --filter-pattern '"Starting gunicorn"' --query 'events[*].timestamp'
```

**Trap 3: an AFTER "0" only counts when paired with a real restart.** Otherwise the 0 is a false negative — the WebServer never re-scanned, so of course no new errors. So the AFTER window must both count errors (expect 0) and prove gunicorn actually did `Booting worker` after the update.

Line up all three, pull before/after, and it's airtight:

| Window | Time (UTC) | plugins.zip | broken-plugin import errors |
|---|---|---|---|
| **BEFORE** | last pre-update WebServer boot | old, no `.airflowignore` | **103** |
| env update | 2026-10-06 22:13 | → new (with `.airflowignore`) | — |
| **AFTER** | 22:19 WebServer restart | new | **0** |

> Rule of thumb: **find the gunicorn restart first, then count errors at it; a 0 is evidence only when paired with a real restart; MWAA always runs the pinned version, never S3's latest.**

---

## 4. Four `Test_*` reds, zero plugin problems: the world beyond the component boundary

Back to the four smoke reds that panicked the teammate. They're the perfect specimens for this post's spine — **all four ran past the plugin boundary and died in different components, under different identities, in different logs.**

First, a criterion: **for an ECS-backed task, "plugins are fine" means the log shows the custom operator successfully `import`-ed and entered `execute()`** — not that the task turned green. Once it's in `execute()`, the plugin side is cleared; wherever it dies after that is some other component's problem.

| Smoke task | Where it actually died | What's missing | Identity / log location |
|---|---|---|---|
| `Test_snowflake` | `250001 (08001) JWT token is invalid` — connected to host, rejected at auth | Snowflake user's key-pair public key not registered / rotated | Airflow Task log (rejected server-side by Snowflake) |
| `Test_Excel_Ecs` | `botocore ClientException: RunTask ... TaskDefinition not found` | ECS task definition not registered in the new account | Airflow Task log (rejected by AWS API) |
| `CIM__QFF / OPEN_BUSINESS_DATE` | container **started**, `exitCode 1` | ECS **task role** lacks `secretsmanager:GetSecretValue` | **the container's own CloudWatch log**, not in Airflow |

The third one teaches the most. The Airflow Task log gives you only a flat `This task is not in success state ... exitCode 1` — **the root cause isn't in Airflow at all**. It's in the Fargate container's own log group `dev/edr/ecs/edr-dev-teradata-utilities`:

```text
botocore.exceptions.ClientError: AccessDeniedException when calling GetSecretValue
User: arn:aws:sts::...:assumed-role/edr-dev-teradata-utilities/...
is not authorized to perform: secretsmanager:GetSecretValue
on resource: /edr/airflow/connections/teradata__ARM
```

Two of the most-confused identity concepts hide right here:

- **This is the ECS _task role_, not the _execution role_.** The execution role is for the ECS agent (pull image, create log group); the task role is the identity **the code inside the container** uses (read Secrets Manager, hit S3). The one failing `GetSecretValue` is the task role.
- **Airflow's execution role and this ECS task role are two different crews.** The MWAA Worker uses MWAA's role to `RunTask`, but once the container is up it uses its **own** task role to fetch the secret. Two boundaries, two identities.

Put the four together and the conclusion closes in one line: **they're all wiring gaps in the new `edr-dev-2112` environment (Snowflake public key, ECS task def, task-role permissions) — zero DAG/plugin problems. And they prove in reverse that `.airflowignore` broke nothing: every operator imported and ran right up to the external call before an external system rejected it.**

---

## 5. Three maps: component, identity, log

Collapse the four chapters into one abstraction. Debugging MWAA — or any "one codebase, many processes + downstream containers" system — means keeping three maps open at once:

| Map | The question it asks | The answer this time |
|---|---|---|
| **Component map** | Who's running this code? Who "reads" `plugins/`? | WebServer scan (no egress, collapses) / Scheduler·Worker import (egress, fine) / Fargate container (a separate runtime) |
| **Identity map** | Whose permissions does this step use? | MWAA execution role / ECS task role / ECS execution role / Snowflake JWT — four identities |
| **Log map** | Which log group holds the truth? | WebServer = the gunicorn boot moment / DAGProcessing = parsing / Airflow Task = the outcome / container CloudWatch = the actual cause |

The teammate's mistake wasn't a skill gap — it was having only the "error text" map open: `ModuleNotFoundError` reads as a deps problem, a red task reads as a change problem. Open all three maps and the 103 red lines immediately file under "WebServer cosmetic", the four smoke reds under "new-env wiring gaps", and `.airflowignore`'s innocence is provable in thirty seconds.

### Do this today

1. Walk your own `plugins/`: how many are *real* `AirflowPlugin` subclasses, and how many are plain modules DAGs import directly? If it's mostly the latter and your WebServer is `PUBLIC_ONLY`, that pile of Broken plugin errors in your UI is almost certainly this — curable with one `.airflowignore`.
2. Give every ECS-backed operator a debugging bookmark: **check `exitCode` in the container's own CloudWatch log group first; don't guess from the Airflow Task log.**
3. Separate **task role vs execution role** in your environment, and pin "container failed to fetch a secret" straight to the task role's policy instead of digging through Airflow connections.
4. Next time you ship a change whose only proof is "errors disappear", write down your before/after anchor (which process, which restart, which log group) *before* you start. A "0" with no anchor is not a verification.

### Next up

This `edr-dev-2112` playbook ports straight to the **stg/prd 2.11 cutover** next. That side hides a dirtier class of landmine: the new environment's metadata DB is empty — FAB roles, Airflow Variables, task history, all gone. I dug into the root cause in ["Rename Means Demolish: in MWAA the name *is* the identity"](/blogs/tech/en/mwaa-name-is-identity), and the "things you must run against the old environment *before* you cut over" list lives in ["Backup Is Not Migration"](/blogs/tech/en/mwaa-metadata-backup-not-migration). The next post is the debrief of actually cutting stg/prd over, with all three posts' bills coming due at once.

---

*The error text tells you where it hurts; where the error landed tells you what's actually wrong. Senior and junior are often separated by a single question: which component printed this line?*
