---
title: 'Three Doors to MWAA Permissions: A Deep Dive into Missing Roles'
header:
    image: /assets/images/bg/20251014_150500.jpg
date: 2026-10-22
tags:
 - airflow
 - mwaa
 - iam
 - permissions
 - terraform
permalink: /blogs/tech/en/mwaa-permissions-missing-roles
alt_url: /blogs/tech/zh/mwaa-permissions-triple-door
lang: en
layout: single
category: tech
---
> "What's in a name? That which we call a rose by any other name would smell as sweet." — Shakespeare, *Romeo and Juliet*

*From "permissions open doors for people" to "some permissions exist so the code's books balance"

During last week's health sweep of our SIT Airflow environment, this line kept showing up in the DAG processor logs:

```
airflow.exceptions.AirflowException: The access_control mapping for DAG 'Example_DAG' includes a role named 'team-developers', but that role does not exist
```

The trend looked great. Seventy of these in the previous seven days, down to two in the last three. I wrote "residual, nearly gone, just confirm the timestamps" in my readiness notes and moved on.

A week later, the recheck showed 21 more, the newest from the night before. So I stopped reading the logs and asked the database directly:

```
$ airflow roles list
name
=====
Admin
Op
Public
User
Viewer
```

Nine custom roles, zero present. It wasn't "nearly gone". It had been broken since the day the environment was created.

Then I made a second wrong call. I told the team: "Without those roles, people from the other teams might not be able to see their DAGs." Also wrong. When I read the IAM policies in Terraform, it turned out that **in our MWAA setup, nobody ever logs in as `team-developers`, or as any of the other eight roles.**

So how can a role nobody uses break anything? And if it does break something, why were all the DAGs still running? Answering both means splitting MWAA's access control into three doors.

By the end of this post you’ll know exactly which door to check when a seemingly harmless “role not found” error keeps popping up in your managed Airflow environment, and how to confirm that your runbooks actually create those roles before the DAGs start running.

## 1. The map: three doors

Think of MWAA as an office building where access is controlled at three distinct layers:

| Door | In the building | In MWAA | Where it lives | Who owns it |
|---|---|---|---|---|
| **1: IAM** | Lobby security – you’re let in and a badge is issued for the day. | `airflow:CreateWebLoginToken` policy that maps an IAM principal to an Airflow role name. | AWS IAM (Terraform) | Cloud platform team |
| **2: FAB roles** | Badge level – which doors your badge can open. | Flask‑AppBuilder role → permissions (action × resource). | Airflow metadata database. | Airflow core + the admins who configure it. |
| **3: DAG‑level `access_control`** | The booking sheet for each meeting room – who owns that room. | `access_control={…}` embedded in a DAG’s code, synced into permissions on `DAG:<dag_id>`. | Code repository, then copied into the metadata DB during sync. | Anyone who writes or edits the DAG (the “author”). |

The column that matters for troubleshooting is **"where it lives."** Door 1 sits entirely in AWS – its state never moves when you rename an environment. Doors 2 and 3 live inside Airflow’s own metadata database; if you wipe or recreate that DB, those permissions are lost and reset to the default zero state. The net effect is that users can still log into the UI (door 1 works), but they suddenly find no DAGs or access restrictions where they expect them – a classic “login succeeds, nothing else changes” symptom.

## 2. Door one: IAM decides which badge you wear

MWAA's web UI login goes through `CreateWebLoginToken`. Here’s what our IAM policy looks like (a real Terraform config fragment):

```yaml
- "airflow:CreateWebLoginToken"
resources:
  - "arn:aws:airflow:ap-southeast-2:${aws_account_id}:role/${channel}-${env}/User"
  - "arn:aws:airflow:ap-southeast-2:${aws_account_id}:role/${channel}-${env}-*/User"
```

Look at the last ARN segment: `role/<environment>/<Airflow role name>`. **That segment decides who you are inside Airflow after login.** We have exactly five of these policies, pointing at `Admin`, `Op`, `User`, `Viewer` and `Public`.

That gives us the first counter‑intuitive fact:

| You'd assume | What actually happens |
|---|---|
| EDR engineers log in as `team-developers` | They log in as `User` or `Op` |
| Without `team-developers`, EDR engineers can't see their DAGs | `User` already has global DAG permissions and sees everything |
| Roles are for people | In our setup, the nine custom roles have **zero users** |

Door one has two more traps, and we hit both.

### Trap one: wildcard width.
SIT's early policy used `${env}-???`. In IAM, `?` matches exactly one character, so the pattern matched `-251` but not `-2112`. When the new environment went live, the console’s link to the web UI just showed "Oops, something went wrong", while the environment reported `AVAILABLE` and its last update `SUCCESS`. It looked like MWAA was broken. The cause was three question marks in a policy file.

### Trap two: three entry points, three separate grants.

| Entry point | IAM action | Our result |
|---|---|---|
| Web UI | `airflow:CreateWebLoginToken` (mapped to a role) | ✅ maps to Admin |
| MWAA CLI | `airflow:CreateCliToken` (granted per environment) | ✅ works, but many subcommands are disabled by MWAA |
| REST API | `airflow:InvokeRestApi` (also needs a role mapping) | ❌ `No Airflow role granted in IAM` |

This table comes back in section 5, when we get to the fix.

> The front door answers "who are you and which badge do you get". It doesn't answer "which rooms can you enter".

## 3. Door two: a FAB role is a set of actions on resources

Airflow 2.x’s web UI is built on Flask‑AppBuilder (FAB). Its permission model has three fundamental concepts:

- **action** – the verbs that can be performed, e.g. `can_read`, `can_edit`, `can_create`, `can_delete`, and many more.
- **resource** – the objects those actions apply to: `DAGs`, `DAG Runs`, `Connections`, `Variables`, `Pools`, etc.
- **permission** – a single action‑on‑resource pair. A *role* is simply a collection of permissions.

The five default roles that ship with Airflow stack on top of each other, each inheriting the previous set plus new capabilities:

| Role | Roughly what it can do |
|---|---|
| `Public` | Nothing (anonymous) |
| `Viewer` | Read‑only: DAGs, runs, logs |
| `User` | Viewer + operate DAGs (pause/unpause, trigger, clear, mark state) |
| `Op` | User + operational config (Connections, Variables, Pools, …) |
| `Admin` | Everything, including managing users and roles |

### Scope matters: global vs per‑DAG permissions

Resources can be *global* or *per-object*. For example:

- `DAGs` is a **global** resource. Granting `can_edit on DAGs` lets the holder edit every DAG in the cluster.
- `DAG:Example_DAG` is a **per‑DAG** resource, scoped to a single DAG named `Example_DAG`. Permissions on this target only that one DAG.

The default roles all contain the global permissions. That’s why a `User` sees every DAG—because it inherits `can_read` and `can_edit` on the global `DAGs` resource. If you want to restrict a role to *only* a subset of DAGs, you must explicitly remove the global permission and add per‑DAG permissions for the desired DAGs.

### Where the data lives

All of this information is stored in the Airflow metadata database under tables prefixed with `ab_`: `ab_role`, `ab_permission_view`, `ab_permission_view_role`, etc. When you upgrade or replace an MWAA environment, these tables are carried over with the old metadata DB; there’s no separate backup mechanism for them.

> Badge levels are written in the building's register. Demolish the building and the register goes with it.

## 4. Door three: `access_control`, a ledger that has to balance (deep dive)

### 4.1 What it looks like in code

Almost every one of our 200‑plus DAGs has this:

```python
with DAG(
    dag_id="Example_DAG",
    schedule="15 0 * * *",
    access_control={"team-developers": {"can_edit"}},
    ...
) as dag:
```

In plain terms: grant the `team‑developers` role the `can_edit` permission on the DAG identified by `DAG:Example_DAG`. Each team owns its own role, scoped to a folder hierarchy:

| Role | Folder | SIT refs | PRD refs |
|---|---|---|---|
| `team-developers` | `team/` | 133 | 210 |
| `other-developers` | `other/` | 70 | 69 |
| `third-developers` | `third/` | 49 | 46 |
| `fourth-developers` | `fourth/` | 1 | 5 |
| `air‑developers` / `airflow‑developers` / `team-test‑developers` | other | a few | a few |
| `special-developers` | PRD only | 0 | 1 / 2 |

The table is more than a curiosity: it tells us how many distinct roles exist across environments and gives a rough idea of how many DAGs each team owns. Notice the asymmetry between SIT (staging) and PRD (production); some teams have dozens of DAGs in production but barely any in staging, which hints at the life‑cycle practices we’ll discuss later.

### 4.2 How one line of config becomes an error

Here’s the call chain that surfaces when a role referenced in `access_control` is missing (Airflow 2.11.2 stack trace):

```
DAG processor parses the DAG file
 └─ DagBag._serialize_dag_capturing_errors      dagbag.py:693
     └─ DagBag._sync_perm_for_dag               dagbag.py:749
         └─ security_manager.sync_perm_for_dag  fab/.../override.py:1153
             └─ _sync_dag_view_permissions      fab/.../override.py:1220  ← raise
```

And the exact snippet that raises the exception (excerpted from the FAB provider 2.4.1; line numbers differ in production but logic is identical):

```python
# Adding the access control permissions
for rolename, resource_actions in access_control.items():
    role = self.find_role(rolename)
    if not role:
        raise AirflowException(
            f"The access_control mapping for DAG '{dag_id}' includes a role named "
            f"'{rolename}', but that role does not exist"
        )
```

The code is explicit: look up the role in the database (`ab_role`) and abort if it’s missing. There is no implicit creation or fallback logic.

### 4.3 Why the DAGs kept running and the errors stayed rare

My initial interpretation of the error frequency was misleading. The stack trace order and the real‑world behaviour point to two key facts:

1. **Permission sync runs *after* the DAG is serialized into the database.** Once a DAG file has been parsed, its representation is persisted as a JSON blob in the `dag` table. The scheduler later reads that blob; therefore, missing permissions do not prevent scheduling or task execution.
2. **Sync only triggers on content change.** Airflow monitors file timestamps and content hashes. If nothing changes, the DAG is considered unchanged and the permission sync step is skipped entirely.

Because of (1) and (2), a DAG that once had an invalid `access_control` mapping can keep running for days or weeks if no one edits it again. The count of *"role does not exist"* errors thus reflects how many DAGs were recently re‑serialized, not the health of the permission subsystem.

| Signal | What I thought it measured | What it actually measures |
|---|---|---|
| Count of "role does not exist" | How much of the problem is left | How many DAGs were re‑serialized recently |
| Count going down | Self‑healing | Less code churn |
| A reliable test | — | Does `roles list` show the role, and how many DAG permissions does it hold |

The first two checks merely confirm that no new errors surface; they do not speak to correctness. The third check shows that every role’s permission count is what we expect, and the system will reject any future attempt to grant or revoke permissions in a way that would break this balance.

### 4.4 It also takes permissions away

A second half of the same function, often overlooked, performs revocation:

```python
# Revoking stale permissions for all possible DAG level resources
for perm in existing_dag_perms:
    non_admin_roles = [role for role in perm.role if role.name != "Admin"]
    for role in non_admin_roles:
        ...
        if perm.action.name not in target_perms_for_role:
            self.remove_permission_from_role(role, perm)
```

For any non‑Admin role, **any DAG‑level permission that isn’t explicitly declared in `access_control` is removed on the next sync**. A hand‑granted permission applied through the UI will be stripped away once the DAG file is parsed again.

In other words, `access_control` functions as a *ledger* rather than an ad‑hoc switch: it is the single source of truth for DAG‑level permissions. The code’s comment captures this nuance:

> Every name the code writes down needs a matching entity in the database. Whether anyone uses it is a separate question.

This design choice explains why permission errors can be silent and why they reappear after seemingly innocuous edits: the ledger enforces consistency, but at the cost of accidental revocation if a role or action is omitted.

## 5. The fix: creating roles and forcing a sync

Missing roles, so create them. Our runbook said to use the MWAA CLI:

```bash
curl -X POST "https://$HOST/aws_mwaa/cli" -H "Authorization: Bearer $CLI_TOKEN" \
  --data-raw "roles create team-developers ..."
```

When I actually ran it, MWAA replied:

```
HTTP/1.1 400 BAD REQUEST
the sub command is not allowed: create
```

MWAA's CLI endpoint only allows a limited set of subcommands; `roles create` is not one of them. That explains why the nine roles had been missing since the cutover: **the runbook contained a step that never succeeded, and nobody noticed.**

The three‑entry‑points table from section 2 now comes in handy:

| Attempt | Result |
|---|---|
| MWAA CLI `roles create` | ❌ 400, subcommand not allowed |
| `aws mwaa invoke-rest-api` | ❌ `No Airflow role granted in IAM` |
| Web UI login (mapped to Admin) → Security → List Roles → add | ✅ |

In the end I used AWS CLI to create the roles directly in IAM, then logged into the MWAA web UI as an Admin and submitted FAB's `/roles/add` form. It does exactly what clicking through the UI does, but it can be scripted and repeated:

```bash
aws iam create-role \
  --role-name team-developers \
  --assume-role-policy-document file://trust.json
# repeat for each missing role
```

Each role only needs a name; no base permissions are required because nobody logs in as these roles.

Once the roles exist, the DAGs that only sync on change still need a forced sync. Airflow does not expose a `sync-perm` command, so we trigger a re‑serialization and let the scheduler pick up the new permissions:

```python
RESERIALIZE_DAGS = BashOperator(bash_command="airflow dags reserialize", task_id="RESERIALIZE_DAGS")
# After running this task, the scheduler will automatically sync permissions on next run.
```

Unpause it, trigger it, wait about a minute and a half, then pause it again.

## 6. Proving it's actually fixed

After I realized that the falling‑count bug was a false alarm, I stopped treating the error counter as proof and instead ran three independent sanity checks to verify that the system behaved correctly.

| Check | Result |
|---|---|
| `does not exist` in the `RESERIALIZE_DAGS` task log (580 lines) | 0 |
| "role named" in DAG processor logs after the roles were created | 0 |
| `can edit on DAG:*` permissions held by each role | `team` 133, `other` 70, `third` 49 |

The third check is decisive. The numbers **133, 70 and 49** exactly match the count of `access_control` entries that reference those roles in the source code, meaning the database’s permissions ledger and the code‑level ledger are perfectly aligned.

## Three doors, one table

| | IAM (front door) | FAB roles (badge) | `access_control` (booking sheet) |
|---|---|---|---|
| **Question it answers** | Who are you, which badge do you wear? | Which doors that badge opens? | Which team owns this room? |
| **Where it lives** | AWS IAM | Metadata DB | Code → metadata DB |
| **After an env rename** | Untouched | **Wiped** | Code survives, ledger wiped |
| **Typical failure** | `???` wildcard too narrow | Everything beyond the defaults is gone | References a role that doesn't exist |
| **Typical misread** | "MWAA is broken" | "People log in with these" | "Fewer errors means nearly fixed" |

> *“You must be careful not to delete what you don’t understand.”* — Unknown

My position: **on MWAA with IAM‑mapped login, `access_control` has largely stopped doing its job of keeping people out, but you still shouldn't delete these roles or leave them missing.** The reason isn't access control itself; it's the ledger. If the code names a role, the database must have that entry. When you strip the ledger—say after an environment rename—you end up editing 200‑plus DAG files just to avoid creating nine empty roles. That’s a bad trade. A cleaner move is to *create the roles, force a sync, reconcile the counts* on the checklist for every environment cutover.

## What you can do today

1. **Run `roles list` on your MWAA environment** – this command pulls the IAM roles that Airflow is configured to use. Then, in the repository that contains the DAG code, run:
   ```bash
   git grep -hoE '"[a-z-]+-developers"' -- dags/ | sort | uniq -c
   ```
   The two outputs are lists of role names: one from the runtime environment and one inferred from the source code. Compare them line‑by‑line to spot any mismatches or missing roles.

2. **Inspect your `CreateWebLoginToken` policies** – locate the policy files that grant the token‑creation capability. For each statement, resolve the ARN suffix (the part after the last colon). If every ARN resolves to a default role that you know is present in MWAA’s configuration, then the issue isn’t a missing custom role; it’s a misunderstanding of what the policies actually allow.

3. **Search for fragile wildcards in IAM policy files** – patterns like `???` are syntactically legal but break as soon as an environment name grows beyond three characters. Run:
   ```bash
   git grep -n '???' -- <iam-policy-dir>
   ```
   and review each hit. Replace them with explicit prefixes or longer wildcard ranges (e.g., `*` or `?`) that match the real naming scheme.

4. **Execute every managed‑service command listed in your runbooks** – just because a CLI subcommand is documented does not guarantee it will work in MWAA’s sandboxed environment. For each command, try it against the live environment and verify the expected side effect (e.g., creating an S3 bucket, invoking a Lambda). If any fail, document the failure path and update the runbook accordingly.

5. **Validate permission coverage quantitatively** – after applying fixes, don’t simply look for "no errors". Count the permissions that each role actually holds using `aws iam list-attached-role-policies` or equivalent CLI calls, then compare those counts against the reference set you derived from your DAG code. This ensures that every role has exactly the rights it needs and no more.

---

> *Not every name in a permission system has a person behind it. But every name your code writes down needs something in the database that answers to it.*
