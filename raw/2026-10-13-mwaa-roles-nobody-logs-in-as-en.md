---
title: "The Roles Nobody Logs In As: MWAA's Three Doors of Access Control"
header:
    image: /assets/images/hd_kerberos.png
date: 2026-10-13
tags:
 - airflow
 - mwaa
 - aws
 - security
 - devops
permalink: /blogs/tech/en/mwaa-roles-nobody-logs-in-as
layout: single
category: tech
---

> "What's in a name? That which we call a rose by any other name would smell as sweet." — Shakespeare, *Romeo and Juliet*

# Nine Roles Nobody Uses, and You Can't Lose a Single One

*From "permissions open doors for people" to "some permissions exist so the code's books balance"*

During last week's health sweep of our SIT Airflow environment, this line kept showing up in the DAG processor logs:

```
airflow.exceptions.AirflowException: The access_control mapping for DAG 'Insurance__Wellbeing'
includes a role named 'edr-developers', but that role does not exist
```

The trend looked great. Seventy of these in the previous seven days, down to two in the last three. I wrote "residual, nearly gone, just confirm the timestamps" in my readiness notes and moved on.

A week later, the recheck showed 21 more, the newest from the night before. So I stopped reading the logs and asked the database directly:

```
$ airflow roles list
name
======
Admin
Op
Public
User
Viewer
```

Nine custom roles, zero present. It wasn't "nearly gone". It had been broken since the day the environment was created.

Then I made a second wrong call. I told the team: "Without those roles, people from the other teams might not be able to see their DAGs." Also wrong. When I read the IAM policies in Terraform, it turned out that **in our MWAA setup, nobody ever logs in as `edr-developers`, or as any of the other eight roles.**

So how can a role nobody uses break anything? And if it does break something, why were all the DAGs still running? Answering both means splitting MWAA's access control into three doors.

What you'll take away:

- **IAM is the front door, FAB roles are the badge, and `access_control` is the booking sheet on each meeting room.** Each one covers a different part of access, and mixing up any two of them leads to the wrong diagnosis.
- **A falling error count doesn't mean you're nearly fixed.** This error only fires when a DAG changes, so the count measures how much code moved, not how much of the problem is left.
- **On a managed service, verify every command in your runbook actually runs.** The role-creation command in ours is one MWAA refuses to execute.

A note on order: first what each door is (the intro), then a walk through the third door's source code along the real error (the deep dive), then the fix and how to prove it actually worked.

---

## 1. The map: three doors

Think of MWAA as an office building:

| Door | In the building | In MWAA | Where it lives | Who owns it |
|---|---|---|---|---|
| **1: IAM** | Lobby security: are you let in, and which badge do you get | `airflow:CreateWebLoginToken` policy mapping an IAM principal to an Airflow role name | AWS IAM (Terraform) | Cloud platform team |
| **2: FAB roles** | Badge level: which doors your badge opens | Flask-AppBuilder role → permissions (action × resource) | Airflow metadata DB | Airflow + admins |
| **3: DAG-level `access_control`** | The booking sheet on each meeting room: which department owns it | `access_control={...}` in DAG code, synced into permissions on `DAG:<dag_id>` | Code, synced into the metadata DB | Whoever writes the DAG |

The column that matters is "where it lives". **Door 1 lives in AWS. Doors 2 and 3 live in Airflow's metadata DB.** When an environment rename wipes the metadata DB (I covered why a rename does that in [*DeleteEnvironment Is More Honest Than UpdateEnvironment*](/blogs/tech/en/mwaa-name-is-identity)), door 1 is untouched and doors 2 and 3 reset to zero. The symptom: everyone can still log in, and nothing looks wrong.

---

## 2. Door one: IAM decides which badge you wear

MWAA's web UI login goes through `CreateWebLoginToken`. Here's what our IAM policy looks like (a real Terraform config fragment):

```yaml
- "airflow:CreateWebLoginToken"
resources:
  - "arn:aws:airflow:ap-southeast-2:${aws_account_id}:role/${channel}-${env}/User"
  - "arn:aws:airflow:ap-southeast-2:${aws_account_id}:role/${channel}-${env}-*/User"
```

Look at the last ARN segment: `role/<environment>/<Airflow role name>`. **That segment decides who you are inside Airflow after login.** We have exactly five of these policies, pointing at `Admin`, `Op`, `User`, `Viewer` and `Public`.

That gives us the first counter-intuitive fact:

| You'd assume | What actually happens |
|---|---|
| EDR engineers log in as `edr-developers` | They log in as `User` or `Op` |
| Without `edr-developers`, EDR engineers can't see their DAGs | `User` already has global DAG permissions and sees everything |
| Roles are for people | In our setup, the nine custom roles have **zero users** |

Door one has two more traps, and we hit both.

**Trap one: wildcard width.** SIT's early policy used `${env}-???`. In IAM, `?` matches exactly one character, so the pattern matched `-251` but not `-2112`. When the new environment went live, the console's link to the web UI just showed "Oops, something went wrong", while the environment reported `AVAILABLE` and its last update `SUCCESS`. It looked like MWAA was broken. The cause was three question marks in a policy file.

**Trap two: three entry points, three separate grants.**

| Entry point | IAM action | Our result |
|---|---|---|
| Web UI | `airflow:CreateWebLoginToken` (mapped to a role) | ✅ maps to Admin |
| MWAA CLI | `airflow:CreateCliToken` (granted per environment) | ✅ works, but many subcommands are disabled by MWAA |
| REST API | `airflow:InvokeRestApi` (also needs a role mapping) | ❌ `No Airflow role granted in IAM` |

This table comes back in section 5, when we get to the fix.

> The front door answers "who are you and which badge do you get". It doesn't answer "which rooms can you enter".

---

## 3. Door two: a FAB role is a set of actions on resources

Airflow 2.x's web UI is built on Flask-AppBuilder (FAB). Its permission model has three concepts:

- **action**: `can_read`, `can_edit`, `can_create`, `can_delete`, ...
- **resource**: `DAGs`, `DAG Runs`, `Connections`, `Variables`, ...
- **permission**: one action × resource pair. A **role** is a set of permissions.

The five default roles roughly stack on top of each other:

| Role | Roughly what it can do |
|---|---|
| `Public` | Nothing (anonymous) |
| `Viewer` | Read-only: DAGs, runs, logs |
| `User` | Viewer + operate DAGs (pause/unpause, trigger, clear, mark state) |
| `Op` | User + operational config (Connections, Variables, Pools, ...) |
| `Admin` | Everything, including managing users and roles |

**Worth knowing for interviews:** resources come in two scopes. `DAGs` is global: `can_edit on DAGs` lets you operate every DAG. `DAG:FF__CHARM__Core` is per-DAG and covers just that one. The default roles all hold the global permissions, which is why `User` sees everything. Per-DAG permissions only carve out territory for a role that **lacks** the global ones.

All of this lives in metadata DB tables prefixed `ab_` (`ab_role`, `ab_permission_view`, `ab_permission_view_role`, ...). When an MWAA environment gets replaced, these tables go with the old metadata DB, and there's nowhere to restore them from.

> Badge levels are written in the building's register. Demolish the building and the register goes with it.

---

## 4. Door three: `access_control`, a ledger that has to balance (deep dive)

### 4.1 What it looks like in code

Almost every one of our 200-plus DAGs has this:

```python
with DAG(
    dag_id="FF__CHARM__Core",
    schedule="15 0 * * *",
    access_control={"edr-developers": {"can_edit"}},
    ...
) as dag:
```

In plain terms: grant the `edr-developers` role `can_edit` on `DAG:FF__CHARM__Core`. Each team uses its own role, folder by folder:

| Role | Folder | SIT refs | PRD refs |
|---|---|---|---|
| `edr-developers` | `edr/` | 133 | 210 |
| `tds-developers` | `tds/` | 70 | 69 |
| `cim-developers` | `cim/` | 49 | 46 |
| `fraud-developers` | `fraud/` | 1 | 5 |
| `air-developers` / `airflow-developers` / `edr-test-developers` | other | a few | a few |
| `fst-developers` / `loy-commercial-ops-developers` | PRD only | 0 | 1 / 2 |

### 4.2 How one line of config becomes an error

Here's the call chain from the SIT stack trace (Airflow 2.11.2):

```
DAG processor parses the DAG file
 └─ DagBag._serialize_dag_capturing_errors      dagbag.py:693
     └─ DagBag._sync_perm_for_dag               dagbag.py:749
         └─ security_manager.sync_perm_for_dag  fab/.../override.py:1153
             └─ _sync_dag_view_permissions      fab/.../override.py:1220  ← raise
```

And the code that throws (quoted from fab provider 2.4.1; the logic matches what 2.11 runs, only the line numbers differ):

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

It's very plain: look the role name up in `ab_role`, and throw if it isn't there. It does not create the role for you.

### 4.3 Why the DAGs kept running and the errors stayed rare

This is exactly where my first call went wrong. The order of the stack trace and the observed behaviour show two things:

1. **Permission sync happens after serialization.** The DAG is already serialized into the DB, and the scheduler reads the serialized version, so scheduling and execution are untouched. The CHARM and QBR batches ran in SIT every day, and not one task failed because of this.
2. **Permission sync only runs when a DAG's content changes.** No change, no sync, no error. Each file reports once, at the moment it's edited or its content shifts.

So the count measures "how many DAGs were re-serialized recently", not "how much of the problem is left". The drop from seventy in seven days to two in three days just meant less code was changing. It said nothing about whether the problem was fixed.

| Signal | What I thought it measured | What it actually measures |
|---|---|---|
| Count of "role does not exist" | How much of the problem is left | How many DAGs were re-serialized recently |
| Count going down | Self-healing | Less code churn |
| A reliable test | — | Does `roles list` show the role, and how many DAG permissions does it hold |

### 4.4 It also takes permissions away

The first half of the same function has a part people tend to miss:

```python
# Revoking stale permissions for all possible DAG level resources
for perm in existing_dag_perms:
    non_admin_roles = [role for role in perm.role if role.name != "Admin"]
    for role in non_admin_roles:
        ...
        if perm.action.name not in target_perms_for_role:
            self.remove_permission_from_role(role, perm)
```

For any non-Admin role, **a DAG-level permission that isn't declared in `access_control` gets revoked on the next sync.** A DAG-level grant you add by hand in the UI won't survive the next sync. `access_control` is the single source of truth for DAG-level permissions, which is why it behaves like a ledger rather than a switch.

> Every name the code writes down needs a matching entity in the database. Whether anyone uses it is a separate question.

---

## 5. The fix: the runbook command MWAA won't run

Missing roles, so create them. Our runbook said to use the MWAA CLI:

```bash
curl -X POST "https://$HOST/aws_mwaa/cli" -H "Authorization: Bearer $CLI_TOKEN" \
  --data-raw "roles create edr-developers ..."
```

When I actually ran it, MWAA replied:

```
HTTP/1.1 400 BAD REQUEST
this sub command is not allowed: create
```

MWAA's CLI endpoint only allows some subcommands. `roles list` runs; `roles create` doesn't. That explains why the nine roles had been missing since the cutover: **the runbook contained a step nobody had ever verified. Someone followed it, it failed, and nobody noticed.** This is tribal knowledge that never became an engineering artifact: everyone "knew" the roles had to be created, and nothing checked that they actually were.

The three-entry-points table from section 2 now comes in handy:

| Attempt | Result |
|---|---|
| MWAA CLI `roles create` | ❌ 400, subcommand not allowed |
| `aws mwaa invoke-rest-api` | ❌ `No Airflow role granted in IAM` |
| Web UI login (mapped to Admin) → Security → List Roles → add | ✅ |

In the end I used `create-web-login-token` to get an Admin session and submitted FAB's `/roles/add` form. It does exactly what clicking through the UI does, but it can be scripted and repeated:

```bash
J=$(aws mwaa create-web-login-token --name "$ENV" --output json)
W=$(echo "$J" | jq -r .WebToken); H=$(echo "$J" | jq -r .WebServerHostname)
curl -s -c jar -b jar -X POST "https://$H/aws_mwaa/login" --data-urlencode "token=$W"
for r in edr-developers tds-developers cim-developers ...; do
  CSRF=$(curl -s -c jar -b jar "https://$H/roles/add" \
         | grep -o 'name="csrf_token" type="hidden" value="[^"]*' | sed 's/.*value="//')
  curl -s -c jar -b jar -X POST "https://$H/roles/add" \
       -H "Referer: https://$H/roles/add" \
       --data-urlencode "csrf_token=$CSRF" --data-urlencode "name=$r"
done   # 302 = created
```

Each role only needs a name and no base permissions, since nobody logs in as these roles anyway.

Once the roles exist, the DAGs that only sync on change still need a forced sync. Our repo already had a DAG for exactly that:

```python
RESERIALIZE_DAGS = BashOperator(bash_command="airflow dags reserialize", task_id="RESERIALIZE_DAGS")
SYNC_PERM = BashOperator(bash_command="airflow sync-perm", task_id="SYNC_PERM")
RESERIALIZE_DAGS >> SYNC_PERM
```

Unpause it, trigger it, wait about a minute and a half, then pause it again.

---

## 6. Proving it's actually fixed

After the falling-count mistake, I stopped using the error count as evidence and looked for three independent checks instead:

| Check | Result |
|---|---|
| `does not exist` in the `RESERIALIZE_DAGS` task log (580 lines) | 0 |
| `"role named"` in DAG processor logs after the roles were created | 0 |
| `can edit on DAG:*` permissions held by each role | `edr` 133, `tds` 70, `cim` 49 |

The third is the one that settles it: **133, 70 and 49 match the number of `access_control` references to those roles in the code exactly.** The first two only show the error stopped. The third shows the code's ledger and the database's ledger balance.

---

## Three doors, one table

| | IAM (front door) | FAB roles (badge) | `access_control` (booking sheet) |
|---|---|---|---|
| Question it answers | Who are you, which badge do you wear | Which doors that badge opens | Which team owns this room |
| Where it lives | AWS IAM | Metadata DB | Code → metadata DB |
| After an env rename | Untouched | **Wiped** | Code survives, ledger wiped |
| Typical failure | `???` wildcard too narrow | Everything beyond the defaults is gone | References a role that doesn't exist |
| Typical misread | "MWAA is broken" | "People log in with these" | "Fewer errors means nearly fixed" |

My position: **on MWAA with IAM-mapped login, `access_control` has largely stopped doing its job of keeping people out, but you still shouldn't delete these roles or leave them missing.** The reason isn't access control, it's the ledger: if the code names a role, the database has to have it. Getting rid of the ledger means editing 200-plus DAG files to strip `access_control`, just to avoid creating nine empty roles. That's a bad trade. The better move is to put "create the roles, force a sync, reconcile the counts" on the checklist for every environment cutover.

---

## What you can do today

1. Run `roles list` on your MWAA environment, then run
   `git grep -hoE '"[a-z-]+-developers"' -- dags/ | sort | uniq -c` in your repo, and compare the two lists line by line.
2. Open your `CreateWebLoginToken` policies and check which roles the last ARN segment maps to. If they're all defaults, stop telling people "they won't see their DAGs without the custom roles".
3. Search your IAM policies for fixed-width wildcards like `???`: `git grep -n '???' -- <iam-policy-dir>`. The next time an environment name gets longer, they'll break.
4. Actually run every managed-service command in your runbooks. MWAA's CLI has a subcommand allowlist, and being written in a doc doesn't mean a command is allowed.
5. When you verify a permissions fix, don't count errors. Count the DAG permissions each role holds and compare that with the references in your code.

---

*Not every name in a permission system has a person behind it. But every name your code writes down needs something in the database that answers to it.*
