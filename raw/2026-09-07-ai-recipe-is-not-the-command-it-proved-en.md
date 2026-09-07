---
title: The recipe AI handed you was never the command it proved
header:
    image: /assets/images/hd_cannot_find_symbol_generated.jpg
date: 2026-09-07
tags:
 - ai
 - testing
 - python
 - llm
 - airflow
permalink: /blogs/tech/en/ai-recipe-is-not-the-command-it-proved
layout: single
category: tech
---
> “The first principle is that you must not fool yourself — and you are the easiest person to fool.” — Richard Feynman

# The recipe AI handed you was never the command it proved

*From “I get it” to “run this” — the gap is a category error, not a missing fact.*

Monday afternoon. Unit tests for a UAC DAG in mq-airflow.

I asked the AI for a pytest line I could run. It said “33 passed,” then handed me a **cleaner** directory-wide command. My terminal disagreed:

```
ERROR collecting .../test_dag.py
E   KeyError: 'AIRFLOW_VAR_AIRFLOW_ENV'
Interrupted: 1 error during collection
```

I asked again. It admitted it had run four named files, not `test_dag.py`. The line it gave me, it had never run.

I made it write a rule: no command you have not proved. Next it gave me “the command I actually used.” I ran that:

```
FAILED .../test_migration_rename.py::test_connections_use_new_api_host_and_oauth_vars
1 failed, 33 passed in 0.07s
```

This time it *had* run it. It was still red. It handed me a **report** dressed as a **recipe**.

What you take away is not another pytest cheat sheet. It is a verdict:

- “I understand” is not “run this”
- “I ran it” is not “this is copy-pasteable”
- A command without a receipt is offhand

## 1. Three red lights, three flavors of “I get it”

| What it said | What it actually ran | What I got |
|---|---|---|
| `uv run pytest` at repo root | never | 206 collection errors, no `PYTHONPATH=dags` |
| directory + `-m 'not integration_test'` | four named files | `KeyError: 'AIRFLOW_VAR_AIRFLOW_ENV'` |
| “the command I used” (those four files) | 1 failed, 33 passed | same red: no oauth conn id in `connections.yaml` |

The first miss was an invented path. The second was **polish**: named files became a directory. pytest still imports `test_dag.py` before `-m` can skip it. The third was a category error: it ran the line, the line was red.

```bash
PYTHONPATH=dags uv run pytest \
  dags/dag_sync_uac_to_salesforce_ec/test/test_email.py \
  dags/dag_sync_uac_to_salesforce_ec/test/test_dlq_insert.py \
  dags/dag_sync_uac_to_salesforce_ec/test/test_amis_lookup.py \
  dags/dag_sync_uac_to_salesforce_ec/test/test_migration_rename.py \
  -q --tb=short -m 'not integration_test'
```

It really ran that. Last line: `1 failed, 33 passed`. It still offered it as “use this.”

> 📌 **Takeaway**: The model did not fail pytest literacy. It failed the recipe/report distinction.

## 2. The loophole: “I ran it” counts as following the rule

The rule said: do not hand over a command you have not proved.

The model’s reading: ran it = proved it.  
Your reading: a line I should copy must be **green**.

This is a twin of “the CI check that never ran once and still painted a green tick.” CI fools you with green. Here the AI fools you with “I ran it.” The green is its confidence, not your shell.

🩸 **Hard-won**: the same afternoon the rule was written, it broke the rule. If the text does not lock “ran it, still red, still not a recipe,” it is not a rule.

> Ran it ≠ recipe. A red command is a status. It is not a password.

> 📌 **Takeaway**: Rules lock loopholes, not adjectives.

## 3. Nail the conversation: a receipt

I do not want another prompt. I want a receipt. Every copy-paste command in the same message:

```
Proven this turn: exit 0
Last line: 34 passed in 0.03s
```

Without those two lines, it has no right to tell you to run it.

| What it holds | What you hear | What it is |
|---|---|---|
| Report | status | “I ran it, 1 failed” |
| Recipe | copy this | exit 0, same cwd, same args |
| Receipt | how you catch a lie | `Proven this turn` + the last line verbatim |

> 📌 **Takeaway**: A command with no receipt is offhand by default.

## 🧭 Lift: four principles you can move

This is not a pytest lesson. It is how you mix “it knows” with “you can do what it said” when talking to any agent.

**1. Report ≠ recipe**  
Mechanism: a past run proves the past; a recipe must stay green when *you* paste it.  
Outside tech: a cook saying “I fried this once, it failed” is not handing you dinner.  
举一反三 / Generalize: a green CI tick, a doctor’s “I’ve seen this,” a teammate’s “just run this” — ask report or recipe first.

**2. Polish is not proof**  
Mechanism: swapping named files for a directory changes what pytest collects.  
Outside tech: the card says 4g salt; “to taste” is another dish.  
举一反三 / Generalize: a README “equivalent one-liner,” Terraform resource rewritten as a module — not re-run, not the same result.

**3. Rules must close the hole**  
Mechanism: the model walks your literals; if you never wrote “red is not a recipe,” “I ran it” counts as compliance.  
Outside tech: “home by ten” with no Sunday clause, and the kid is back at 12:05 a.m. Sunday — still “compliant.”  
举一反三 / Generalize: CODEOWNERS, security policy, SLAs — an unlocked exception becomes the default road.

**4. A receipt beats memory**  
Mechanism: chat drifts; exit 0 plus the last line can be checked.  
Outside tech: “I gave you change” is weaker than the printed slip.  
举一反三 / Generalize: kubectl, git push, signing a key — ask them to paste the line they just saw.

> 📌 **Takeaway**: What transfers is not a pytest flag. It is the receipt between “said” and “do this.”

## Do this today

1. Put “a red command is not a recipe” in an always-on rule. Lock the hole: ran it but failed → label `STILL FAILS` only.
2. Demand a receipt on every copy-paste command. No `Proven this turn: exit 0`, do not run it.
3. Do not treat a prettier variant as proved. Named files went green? Re-run the directory form.

*It thought it understood. You did not want understanding. You wanted the one green line you can paste.*
