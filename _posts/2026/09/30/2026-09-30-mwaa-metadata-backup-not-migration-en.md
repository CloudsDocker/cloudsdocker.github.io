---
title: Your Nightly Backup DAG Schedules Nightly Downtime
header:
    image: /assets/images/hd_state_machine.png
date: 2026-09-30
tags:
 - aws
 - airflow
 - terraform
 - devops
 - cloud-infrastructure
permalink: /blogs/tech/en/mwaa-metadata-backup-not-migration
lang: en
layout: single
category: tech
---

> "Hope is not a strategy." — Google, *Site Reliability Engineering*

# Your Nightly Backup DAG Schedules Nightly Downtime

*Every run of your managed Airflow environment lives in a database you have no connection string for.*

Run this against your own `dags/` folder before you read another line:

```bash
grep -rn "is_paused = true" dags/ plugins/ 2>/dev/null
```

If it hits inside the thing you call your metadata backup, then every run of that script pauses every DAG in the environment. It is not a backup tool. It is a migration tool. The day you put it on a schedule, you scheduled recurring downtime.

This post starts from a real incident where an entire Airflow metadata database went to zero. But the root cause is the boring part — two sentences and it's done. The interesting part is the question that comes after: **in a managed service with no database endpoint, who exactly is holding the safety net, at which layer, in whose code?**

Three things to take away:

- A managed service manages **availability**. It does not manage the **durability of your history**. On MWAA that dividing line runs straight through your own `dags/` folder.
- AWS ships you two official metadata export implementations with fundamentally different behavior: one pauses every DAG, one doesn't. `grep is_paused` tells them apart in a second. Pick wrong and your "nightly backup" is nightly downtime.
- Your backup files have a shelf life set by your Airflow version. `task_instance` gained an `executor` column in 2.10; `log` gained `try_number`. Cross-version restore isn't a `COPY` — it's column reconciliation work.

What follows is ordered for teaching, not in the order I found it. The real investigation zigzagged; you don't need to.

(Environment names are anonymized. `etl-sit-251` / `etl-sit-2112` stand in for the real old and new names. Versions, timestamps, and error counts are real.)

---

## 1. The incident is two lines of diff. What it closed was a door.

A routine MWAA upgrade. The Terraform PR touched two lines:

```diff
-airflow_version = "2.10.3"
+airflow_version = "2.11.2"
-name            = "etl-sit-251"
+name            = "etl-sit-2112"
```

`251` is shorthand for 2.5.1, `2112` for 2.11.2 — a convention this repo has followed for years, welding the running Airflow version into the environment's name so anyone can read the deployed version at a glance. It looks like a readability improvement.

Apply finished. Console showed `AVAILABLE`, `LastUpdate: SUCCESS`, clean requirements-install logs, scheduler heartbeating. Ten minutes later the DAG list started going red. One wave was missing permission roles; the other came out to exactly **195**:

```text
airflow.exceptions.AirflowException: The access_control mapping for DAG 'X'
includes a role named 'finance-developers', but that role does not exist
```

```text
KeyError: ''
```

A role that no longer exists, and an Airflow Variable that came back as an empty string. Two symptoms, one cause: this environment's metadata database was brand new and empty. CloudTrail closed the case — not one `UpdateEnvironment`, but two calls 28 minutes apart:

```text
10:58:46  DeleteEnvironment  etl-sit-251
11:26:12  CreateEnvironment  etl-sit-2112
```

And that's the whole root cause: in MWAA's `UpdateEnvironment` API, `Name` appears only in the URL path `/environments/{Name}` — never in the request body. Renaming is not a risky update; at the API level it does not exist as an operation. So Terraform can only reach your declared state by deleting the old environment and creating a new one. That is what CloudFormation's `Update requires: Replacement` means in practice.

**But the thing that turns this from an operator mistake into an architectural gap is a different paragraph — the one in AWS Support's reply.**

I opened a support case asking whether recovery was possible. Support confirmed the root cause, and then gave an answer with no wiggle room in it:

> Unfortunately, AWS does not retain accessible snapshots or backups of deleted/replaced MWAA metadata databases. Once the old environment was destroyed via the Terraform replacement, the metadata is unrecoverable. AWS Support does not have direct access to the managed metadata database and cannot perform restores on behalf of customers.

That paragraph carries far more information than the root cause does. It isn't saying "this one is gone." It's saying:

> In this service model, there is no AWS-side copy of your DAG run history, audit log, Variables, or Connections. The only copy that can possibly exist is one your own code wrote.

If your audit compliance, SLA reporting, or operational forensics depend on that data, then the copy isn't an ops nice-to-have. It is **part of your system**, and it has to live in `dags/`.

| Signal you saw | The question it actually answers | The question it never answers |
|---|---|---|
| `AVAILABLE` | Is this environment healthy right now | Is it the same environment |
| `LastUpdate: SUCCESS` | Did this operation complete | Was it an update or a replacement |
| Clean requirements logs | Did the new environment build | Did the old environment's state come along |
| "It's a managed service" | Who runs it | Who remembers it |

> A managed service manages *it's alive*. Nobody promised to manage *it remembers*.

---

## 2. Why backing up Airflow metadata is a genuinely weird problem

State the weirdness plainly first, or every solution below looks like over-engineering.

Backing up an ordinary Postgres looks like this: enable automated snapshots in the console, take a `pg_dump`, set a PITR retention window. You never touch application code.

On MWAA's metadata database, none of those three exist. No RDS console entry, no endpoint, no connection string, no PITR button. The docs say it outright: **starting from an existing MWAA environment, there is no direct access to the metadata database.**

So what *is* the entrance? One session object, inside your own DAG process:

```python
from airflow import settings
from sqlalchemy import text

session = settings.Session()
result = session.execute(text("select dag_id, run_id, state from dag_run"))
```

Which means the only identity that can reach this database is **"an Airflow task currently running inside this environment."** That single fact determines the shape of everything downstream: backup is a DAG, restore is a DAG, the drill is a DAG — and all of those DAGs live inside the very environment that can be replaced out from under them.

This is the thing I've started calling **the silent half of the managed boundary**. The service made "it runs" perfectly smooth — you never need to know where the Aurora instance sits, how the schema migrates, who watches the heartbeat. It left "it remembers" outside the abstraction, and it won't tell you where that seam is anywhere near the same surface. The shared-responsibility line is never drawn in the console. It's drawn in one line of an API reference nobody reads until afterward.

> **The ceiling rule:** a managed resource's recovery ceiling equals the lowest-level access interface it hands you. MWAA hands you `settings.Session()` — so your backup ceiling is however much SQL you're willing to write.

---

## 3. AWS gave you two scripts. One of them schedules an outage.

This is the most immediately useful section in the post.

Search for "MWAA metadata backup" and you'll land on two pieces of AWS-authored code. Both live under `aws-samples`. Both are described as exporting metadata. They behave **completely differently**.

### 3.1 Script one: `mwaa_export_data.py` (from the start-stop use case)

This is the implementation behind the official migration path. Its first task tells you its personality:

```python
# pause all active dags to have consistent and reliable copy of dag history exports
def pause_dags():
    session = settings.Session()
    session.execute(
        text(f"update dag set is_paused = true where dag_id != '{dag_id}';"))
    session.commit()
    session.close()
```

That isn't an incidental pause. Look at the dependency chain:

```text
back_up_activedags >> pause_dags >> [export_data, export_active_dags,
                                     export_variable, export_connection]
                   >> clean_up >> [activate_dags_on_failure, notify_success]
```

Note that `activate_dags_on_failure` carries `trigger_rule="one_failed"` — the pause is only undone when something **fails**. There is no unpause on the success path, by design: once the export succeeds you're supposed to be moving to the new environment, and the old one is supposed to stay quiet. The docs are honest about this: "During the export and the import process, all other DAGs are paused."

There's a second move that's easier to miss. To remember which DAGs were unpaused, it **writes a table into the database it is backing up**:

```python
def back_up_activedags():
    session = settings.Session()
    session.execute(text(f"drop table if exists active_dags;"))
    session.execute(text(
        f"create table active_dags as select dag_id from dag where not is_paused and is_active;"))
```

`drop table if exists` plus `create table as`. For a one-shot migration that's a defensible engineering tradeoff. For something you run nightly, it's repeatedly creating and dropping tables in your production metadata store.

### 3.2 Script two: `mwaa-dr` (the PyPI package — the actual backup tool)

Also AWS-authored (`aws-samples/mwaa-disaster-recovery`), `mwaa-dr` wraps export/import in a DAG factory. Here is the `setup` step of its backup DAG:

```python
def setup_backup(self, **context):
    print("Executing the backup workflow setup ...")
    if self.storage_type == S3:
        print("No local file system setup necessary!")
        return
    # ...(only creates a directory in LOCAL_FS mode)
```

**No pause. Not one line.** The DAG is `setup >> export_tables >> teardown` — pure reads plus writes to S3. And it explicitly expects to be scheduled:

```python
def schedule(self) -> str:
    return Variable.get("DR_BACKUP_SCHEDULE", default_var=None)
```

Default `None`, meaning manual trigger only. Set a `DR_BACKUP_SCHEDULE` variable and it becomes periodic. *That* is a thing you can put on a schedule.

> **What most people assume:** both are official AWS metadata export scripts, so pick either — they do roughly the same job.
>
> **What the senior engineer knows:** they answer two different questions. One answers "I need to move history to another environment." The other answers "I need a copy without disturbing anyone." The first is allowed to take an outage, because the outage *is* the migration window. The second self-destructs the moment it accepts one — **a backup you wouldn't casually run at peak hours is not a backup**, because the moment you actually need it, you won't dare run it either.

### 3.3 One table to keep them straight

| Dimension | `mwaa_export_data.py` (migration) | `mwaa-dr` backup DAG (backup) |
|---|---|---|
| Pauses all DAGs | Yes (`update dag set is_paused = true`) | No |
| Unpauses after success | No (only on `one_failed`) | N/A |
| Writes to the production metadata DB | Yes (`create table active_dags`) | No (reads + writes S3) |
| Safe to schedule | It shouldn't be | Yes (`DR_BACKUP_SCHEDULE`) |
| `trigger` table | Explicitly excluded | Included by default |
| Requires an empty DB to restore | No (`COPY` into a fresh env) | Yes (ships a `cleanup` DAG) |
| Built for | Renames, cross-version migration, blue/green | Periodic backup, DR drills, same-env rollback |

**The one-line test:** `grep -n "is_paused" <your backup script>`. Present means migration tool. Absent means it might actually be a backup.

---

## 4. Four things you only learn by reading the source

This is the section worth saving. None of it is in the docs, and all of it decides outcomes on the day you actually need a restore.

### 4.1 `variable.csv` and `connection.csv` hold decrypted plaintext

Here's how Variables get exported:

```python
query = session.query(Variable)
for y in query.all():
    w.writerow({k[0]: y.key, k[1]: y.get_val(), ...})
```

And on the Connections side, `y.get_password()`.

`get_val()` and `get_password()` return **decrypted** values — necessarily so, because the Fernet key is per-environment and ciphertext moved to a new environment can't be opened. So the price of this path is that **your backup bucket is now a credential store**: plain CSV, one production secret per line.

The official docs leave one Note about this, suggesting you "enable default encryption" on the bucket if you're migrating sensitive data. That wording is light relative to the actual exposure. A production setup needs at minimum:

- A dedicated bucket encrypted with a KMS CMK (not SSE-S3), key policy scoped to the MWAA execution role
- Bucket policy denying non-TLS and cross-account access; Block Public Access on
- A short lifecycle expiry — a backup's value decays with time, its leak risk doesn't
- **Better: make those two tables not worth backing up at all.** Move Variables and Connections to the Secrets Manager backend and there's nothing left in the metadata DB to leak. `mwaa-dr` has a switch for exactly this case — set the restore strategy to `DO_NOTHING` and it skips both tables

### 4.2 `active_dags.csv` has an asymmetric header contract

The export streams the `active_dags` table to CSV using `csv.writer(...).writerows(chunk)` — **no header row is written.**

The import side reads it like this:

```python
cursor.copy_expert(
    "COPY active_dags FROM STDIN WITH (FORMAT CSV, HEADER TRUE)", f)
```

`HEADER TRUE`. PostgreSQL discards the first line as a header. The first line is a real `dag_id`.

The consequence: after migration `active_dags` is one DAG short, so `UPDATE dag SET is_paused=false FROM active_dags` never releases it — **one DAG that was running before will stay paused in the new environment**, with no error anywhere.

That's a conclusion from reading the code, not from running it. Verify it in your own environment:

```bash
# after export: how many rows does the CSV have
aws s3 cp "s3://$BUCKET/data/active_dags.csv" - | wc -l
# after import: how many rows in active_dags — the delta should be 0, not 1
```

A bug that silently drops a row and a bug that raises an exception are an order of magnitude apart in cost.

### 4.3 The CSV's column names lie — and it still works

This is the subtle one. The Connections export declares these column names:

```python
k = ["conn_id", "conn_type", "host", "schema", "login", "password",
     "port", "extra", "is_encrypted", "is_extra_encrypted", "description"]
```

The values actually written are shifted:

| CSV column N | Declared name | Value actually written |
|---|---|---|
| 3 | `host` | `description` |
| 4 | `schema` | `host` |
| 7 | `port` | `schema` |
| 8 | `extra` | `port` |
| 9 | `is_encrypted` | `extra` |

At this point you'd assume you've found a data-corruption bug. But the import reads it this way:

```python
rows.append(Connection(row[0], row[1], row[2], row[3], row[4],
                       row[5], row[6], port, row[8]))
```

**Positional arguments.** And `Connection.__init__` happens to be `(conn_id, conn_type, description, host, login, password, schema, port, extra)` — which lines up exactly with the write order. The round trip is correct.

The real problem is that this file's contract isn't its column names — it's `Connection.__init__`'s **parameter order**. The names exist only in the exporter's source, and they're wrong. Anyone who writes their own importer from those names (or feeds this CSV into an audit, a diff, or another system) will swap host with description and slide schema into port, silently.

> **Rule of thumb:** a data file with a positional contract and no header doesn't carry its schema in the file. It carries it in the code that reads it. A backup format that depends on someone remembering the field order has already started to rot.

### 4.4 The `trigger` table: the two official tools disagree

`mwaa_export_data.py` carries an unusually honest comment:

```python
# NOTE: The trigger table is intentionally excluded from export.
# Starting in Airflow 2.9.0, trigger.kwargs is Fernet-encrypted with a per-environment key.
# Exporting and importing these rows into a different environment causes
# cryptography.fernet.InvalidToken errors that crash the triggerer and scheduler.
```

Meanwhile `mwaa-dr`'s default table list **includes** `trigger`: `variable`, `connection`, `slot_pool`, `log`, `job`, `dag_run`, `trigger`, `task_instance`, `task_fail`, `xcom`.

Two official AWS tools, opposite answers on the same table — and **both are right**, because their recovery targets differ:

| Recovery scenario | Fernet key | Can `trigger` travel |
|---|---|---|
| Same environment (accidental deletion, rollback, DR drill back into the origin) | Same | Yes — `kwargs` decrypts fine |
| Cross environment (rename, blue/green, cross-Region DR) | Different | No — `InvalidToken` takes down the triggerer and scheduler |

**Worth remembering for an interview:** asked "which Airflow metadata tables can't be migrated directly," answering "the `trigger` table" is a pass. Answering "`trigger.kwargs` has been Fernet-encrypted with a per-environment key since 2.9.0, so a cross-environment import raises `InvalidToken` and crashes the triggerer — and since triggers are ephemeral in-flight state for deferred tasks that get recreated on the next run anyway, the correct move is to exclude the table, not to fix it" is the answer that gets remembered, because it delivers mechanism, consequence, and tradeoff in one breath.

The other tables have personalities too, all of them checkable in the source:

| Table | Does it travel | Why |
|---|---|---|
| `dag`, `dag_tag`, `dag_code`, `serialized_dag` | Not needed | Rebuilt automatically when the scheduler parses the DAG files from S3 |
| Permission / role tables | Not carried (but must be rebuilt) | Generated from the IAM execution role and FAB config — that wave of `access_control` errors is exactly this not coming along |
| `dataset` / `asset` tables | Explicitly excluded | Auto-generated since 2.9.2; importing collides on primary keys |
| `slot_pool` | Yes, but excluding `default_pool` | The new environment creates its own `default_pool` |
| `task_instance` | Yes, but non-terminal states filtered out | Export filter is `state NOT IN ('running','restarting','queued','scheduled','up_for_retry','up_for_reschedule')` — **in-flight tasks are not in your backup** |
| The export DAG's own `dag_run` row | Special-cased | Otherwise it re-runs itself after restore, like `catchup=True` |

Those last two rows deserve a note. The `task_instance` filter means your backup's semantics are "history that has finished," not "the full state at this instant." After any restore, the batch of tasks that was mid-flight at backup time has to be rerun by hand — an extra bill on top of your RPO, and AWS's own DR blog writes "interrupted DAG runs need to be manually rerun" in as an explicit step.

---

## 5. The official runbook's `cd` target is a 404

This is the most time-sensitive section, and the best illustration of why copying a runbook verbatim goes wrong.

As of today (2026-09-30) the official AWS migration guide still tells you:

```bash
git clone https://github.com/aws-samples/amazon-mwaa-examples.git
cd amazon-mwaa-examples/usecases/metadata-migration/{existing-version}-{new-version}/
```

Then edit `S3_BUCKET` in `export_data.py`, upload it, and unpause a DAG called `db_export`.

Check it yourself:

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  https://raw.githubusercontent.com/aws-samples/amazon-mwaa-examples/main/usecases/metadata-migration/2.5.1-2.10.1/export_data.py
# 404
```

`usecases/metadata-migration/` now contains exactly two files: `.airflowignore` and `README.md`. The README's entire technical content is one sentence:

> Metadata import and export scripts are now part of the [MWAA Disaster Recovery project](https://pypi.org/project/mwaa-dr/).

The scripts moved. The documentation didn't. So if you follow the official guide on incident day, you stall on a directory that doesn't exist — while the old environment may still be alive and your export window is closing.

The new home's support matrix matters even more. `mwaa-dr` is currently at 2.2.0, and its README badge lists:

```text
MWAA 2.10.3 | 2.10.1 | 2.9.2 | 2.8.1 | 2.7.2 | 2.6.3 | 2.5.1 | 2.4.3
```

**No 2.11.** Which is precisely the version this upgrade targeted.

That's not a conspiracy — one look at a factory class explains it:

```python
class DRFactory_2_10(DRFactory_2_9):
    def task_instance(self, model):
        return BaseTable(
            name="task_instance",
            columns=[..., "executor",  # New Field
                     ...],
            export_filter="state NOT IN ('running', ...)",
        )
```

Each version's factory subclasses the previous one and overrides only **the tables whose columns changed**: `task_instance` gained `executor` in 2.10, `log` gained `try_number`. Which means **the backup file's schema is pinned one-to-one to an Airflow version.** A `task_instance.csv` exported on 2.10.3 and `COPY`-ed into a 2.11.2 database either fails on column count, or — worse — matches on count and misaligns on meaning.

> **Documentation has a shorter half-life than the dependencies it describes.** So the test for whether a runbook still works isn't "it's on the official site." It's whether every path and every package version it references still resolves under `curl` today. During an incident, a stale runbook is more expensive than no runbook, because what it consumes is your tightest twenty minutes.

---

## 6. So what do you actually run in production

To be clear up front: **we haven't shipped this yet.** It's the design that came out of the incident. I'm writing it down because the tradeoffs are worth more than the code, and I've marked the parts that still need real-world validation.

### 6.1 The first step isn't writing a backup. It's shrinking what needs backing up.

The cheapest backup is the data you don't have to back up. Classify every table before deciding how much code to write:

| Tier | Contents | Disposition |
|---|---|---|
| **L0 — don't back up** | `dag`, `dag_tag`, `dag_code`, `serialized_dag`, `dataset`/`asset` | Rebuilt automatically from S3 by the scheduler. Backing them up only creates primary-key collisions on restore |
| **L1 — shouldn't live here** | `variable`, `connection` | Move to the Secrets Manager backend. One change removes both the plaintext-in-S3 problem and most of the backup scope |
| **L2 — must back up** | `dag_run`, `task_instance`, `task_fail`, `log`, `job`, `slot_pool`, `xcom` | These seven carry audit trail, SLA reporting, and run history — exactly what the incident destroyed |
| **L3 — deliberately don't** | `trigger` in cross-environment scenarios; permission/role tables | The Fernet key won't travel; permissions should be rebuilt by IaC, not restored from CSV, or your access model drifts somewhere nobody can reproduce |

L1 deserves an extra line. Moving Variables and Connections out of the metadata database isn't only a security improvement — it changes the shape of the incident. `KeyError: ''` was fatal because application config lived in the metadata database. Had it lived in Secrets Manager, the same environment replacement would have cost history only, not working DAGs.

### 6.2 The backup DAG (code that actually runs)

```python
# dags/backup_metadata.py
from airflow import DAG
from mwaa_dr.v_2_10.dr_factory import DRFactory_2_10

factory = DRFactory_2_10(
    dag_id="dr_backup_metadata",
    path_prefix="data",
    storage_type="S3",
)

# Must be assigned to a global, or DAG detection won't see it
dag: DAG = factory.create_backup_dag()
```

Three prerequisites, none optional:

1. A dedicated S3 bucket (KMS CMK encrypted) the MWAA execution role can read and write
2. An Airflow variable `DR_BACKUP_BUCKET` set to the bucket **name** (not the ARN)
3. An Airflow variable `DR_BACKUP_SCHEDULE` set to the cron matching your RPO. Leave it unset and the DAG is manual-trigger only — and "I'll run it by hand when I need it" is the complete script of this incident

Add `mwaa-dr` to `requirements.txt` (it pulls `smart-open>=7.0.4`).

**Upgrading to 2.11 means writing the next link yourself.** There is no `v_2_11` factory yet, so either subclass `DRFactory_2_10` and override the tables whose columns changed, or diff the 2.11 schema on [aws-mwaa-local-runner](https://github.com/aws/aws-mwaa-local-runner) first. There's no shortcut, and don't expect the docs to help — they haven't caught up to the 2.10 scripts moving yet.

### 6.3 A restore drill, not a restore plan

`mwaa-dr`'s restore **requires an empty database**, which is why it ships a `cleanup` DAG. That makes "let's just try a restore in prod" a dangerous sentence. The right rehearsal venue is the local runner:

```python
factory = DRFactory_2_10(
    dag_id="dr_restore_metadata",
    path_prefix="data",
    storage_type="LOCAL_FS",   # drill against local FS, never touch S3
)
dag: DAG = factory.create_restore_dag()
```

Two strategy variables control what happens to Variables and Connections on restore; the default is `APPEND`:

| `DR_VARIABLE_RESTORE_STRATEGY` / `DR_CONNECTION_RESTORE_STRATEGY` | Behavior | When |
|---|---|---|
| `DO_NOTHING` | Skip both tables entirely | You're on the Secrets Manager backend (the recommended end state) |
| `APPEND` (default) | Add missing entries, never overwrite | Filling history into an already-configured new environment |
| `REPLACE` | Overwrite existing entries from backup | When the backup is more authoritative than the live environment |

What the drill has to prove isn't "the DAG went green." It's four things: **Variable counts match, Connections actually connect, `dag_run` row counts match the last N days of history, and unpause state matches what it was before** — that last one incidentally verifies the header inference from §4.2.

### 6.4 Turn the lesson into a gate, not a verbal rule

The least useful artifact any postmortem produces is "be careful next time." The artifact worth keeping here is a CI check: no plan that replaces a stateful resource gets merged unattended.

```bash
terraform plan -out=tfplan
terraform show -json tfplan | jq -e '
  [ .resource_changes[]
    | select(.change.actions == ["delete","create"]
          or .change.actions == ["create","delete"])
    | select(.type | test("mwaa_environment|db_instance|rds_cluster|elasticache|msk_cluster"))
  ] | length == 0
' || { echo "Stateful resource will be replaced: needs sign-off + an export window"; exit 1; }
```

It doesn't stop you from replacing a resource — sometimes you genuinely need to. It only forces "replacement" to be seen by a human once. That's the senior-to-principal line: take knowledge that survives only by word of mouth and turn it into a check that can fail.

### 6.5 The log groups, and the dark joke in that naming convention

One aside, and the only good news. Task logs live in CloudWatch under `airflow-{environment-name}-Task`, a storage system entirely independent of the MWAA environment. Deleting the environment doesn't delete them. So the old environment's task output is still sitting in `airflow-etl-sit-251-*`, queryable through Logs Insights.

But the log group name is derived from the environment name. A new environment writes to new groups, and the old groups are never linked into the new UI. The docs carry a bolded **Important** about it: changing the environment name means historical task logs aren't reachable from the new environment's Airflow UI.

Here's the dark joke: **if the version number had never been welded into the environment name, neither the log groups nor the metadata database would have been lost.** The convention designed so anyone could see which version was running took out both.

Listing the log groups for this environment shows `243`, `251`, `306`, a `rollback` marker, one ad-hoc change marker, and now `2112` — stacked like strata. This scene has played out more than once over the past few years. Nobody ever needed that history badly enough afterward to notice, which is exactly why it was never filed as an incident.

A process that doesn't page you isn't a process without a cost. Sometimes it's just a cost nobody has had to pay yet.

---

## Synthesis: three failure modes, and who catches each

The whole thing compresses into one table. The columns are "what AWS did for you" and "what's unavoidably yours" — and that dividing line is the answer to how much code you need to write:

| Failure mode | What AWS manages | What's left to you |
|---|---|---|
| **In-place version upgrade** (name unchanged) | Snapshots the metadata DB first, upgrades components, runs the schema migration, auto-rolls-back on failure (up to ~2 hours unavailable) | Validating DAG and `requirements.txt` compatibility on the local runner; manual DAG edits are not reverted by the rollback |
| **Environment replacement** (rename / blue-green / cross-Region) | Nothing | All of it: export while the old environment is still alive, import, handle log groups, verify afterward |
| **Regional disaster / accidental deletion / corruption** | Multi-AZ fault tolerance (auto-recovery from a single AZ failure) | Periodic backup + cross-Region replication + SchedulerHeartbeat alarms + regular drills |

Row one is the only row with a safety net under it, and its only condition is: **don't touch `Name`.**

---

## Do this today

1. **`grep -rn "is_paused = true" dags/`.** If your "backup" script contains it, it's a migration tool. Take it off any schedule it's currently on.
2. **`aws s3 ls` your backup bucket and open one `connection.csv`.** If there are plaintext passwords in it, move to a KMS CMK and tighten the bucket policy today, and put "Variables and Connections to Secrets Manager" on the backlog.
3. **`curl` every GitHub path and package version your runbook references.** Nobody notifies you when documentation goes stale. While you're there, confirm your target Airflow version is in `mwaa-dr`'s support matrix — if it isn't, that's part of the upgrade's scope, not something to discover after the upgrade.
4. **Add the `jq` check from §6.4 to CI**, pointed at every stateful resource you own: MWAA, RDS, ElastiCache, MSK. Make "replacement" something a human has to see once.
5. **Run a full backup → cleanup → restore on the local runner**, then check four things: Variable counts, Connection reachability, `dag_run` row counts, unpause state. The difference between an unrehearsed recovery plan and no recovery plan is only in what you expect on the day.

The first thing I'm verifying myself is the `active_dags.csv` off-by-one from §4.2 — the code says it should happen, but I haven't yet counted those two numbers in a live environment.

---

*Your cloud provider took over keeping the thing alive. It never agreed to keep the thing's memory. The line between those two never shows up in the console — it shows up in whether you wrote it as a DAG that runs.*
