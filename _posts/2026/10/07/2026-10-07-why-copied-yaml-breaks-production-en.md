---
title: Why Does Copying the AI Gateway's YAML Always Break in Production?
header:
    image: /assets/images/bg_raw/BingWallpaper (12).jpg
date: 2026-10-07
tags:
 - architecture
 - devops
 - llm
 - security
 - infrastructure
permalink: /blogs/tech/en/why-copied-yaml-breaks-production
lang: en
layout: single
category: tech
---
# Why Does Copying the AI Gateway's YAML Always Break in Production?

*It is easy to clone the infrastructure-as-code for an internal AI gateway. It is much harder to survive the first week of production if you do not understand the state machine that generated it.*

If the platform team handed you the infrastructure-as-code for a flagship enterprise AI gateway today, and asked you to stand up a clone, what is the first thing you would change? 

If your answer is the resource prefixes and the region tags, you are about to build a compliance incident.

The hand wants to clone resource names. That is the expensive way to copy an architecture. A reference implementation exists in a specific world: an existing OpenAI VNet, customer conversations that might become compliance records, and business units that want cloud spend billed by team. If your world differs in one place—perhaps data must stay in the EU, or models must be Azure-only—a copied Bicep or Terraform file can look green in a pull request and red in week-one on-call. To survive that first week, you must build a deployment plan based on the original architecture's hard constraints, not its resource names.

## The release state machine outranks the YAML

The `CONTRIBUTING.md` of a mature infrastructure repo usually contains a sentence people skip: a pull request does **not** change the sandbox, dev, or prod environments. 

The deployment workflow for a gateway like LiteLLM is that sentence compiled into code. It enforces a strict state machine: PRs only run a what-if (a diff). Merging to the main branch rolls the sandbox environment, then dev. Production requires a GitHub Environment approval.

```yaml
# .github/workflows/litellm.yaml (structural outline)
on:
  pull_request: { paths: [src/litellm/**] }
  push:         { paths: [src/litellm/**] }

sandbox:  # PRs only
  operation: whatIf | create
dev:
  operation: whatIf | create
dev-test: # merge only
  run: playwright against the new LiteLLM URL
prod:
  needs: dev-test
  if: push && main
  environment: prod # the human gate lives here
```

Local checks and cloud checks use different rulers. Running `make validate` merely diffs configuration snapshots locally. Running `make *-what-if` asks the cloud provider what would actually change. `make local` only proves your docker compose containers can still route traffic. Treat a snapshot as a deploy, or a what-if as a test, and you are using the wrong ruler.

What-if is an opinion. Create is a fact. The human gate is what you are willing to pay for facts.

This distinction reveals itself in stateful container deployments. In one reference architecture, the deployment script deactivates the current revision, runs `sleep 90`, and then applies the new configuration. This looks like a mysterious hack. It is actually a strict constraint: sixty seconds for a graceful stop, thirty more as a buffer, ensuring the single revision and its Redis sessions cannot dual-write.

When you port this setup to Kubernetes, do not translate it as "we also sleep 90". Translate it as the underlying constraint: **the stateful control plane must not be dual-active**. You might implement that via a Job, a PodDisruptionBudget, or a drain. The number is not the constraint. Forbidding two writers is.

## The salt is the only secret you cannot rotate

Identity should be OIDC. The architecture relies on managed identities forwarded into the proxy, with user identity driving per-person budgets rather than a generic "chat container" budget. There are no long-lived service-principal passwords here.

But be aware of multi-cloud asymmetry. Azure models happily use managed identity. AWS Bedrock often requires static access keys. At the next deployment, ask security whether "half the estate still uses long-lived keys" is acceptable. If it is not, you will need a credential proxy in front of Bedrock, or you must delay shipping Claude.

Then there is the salt. LiteLLM encrypts virtual keys in the database using a `LITELLM_SALT_KEY`. This is the least "config-like" config in the entire design. Lose the master database key, and you can still issue emergency keys. Lose the salt, and your historical keys are permanently locked bytes. 

🩸 **血泪提醒**: Custody of the salt needs two people, an offline copy, and a drill date. Do not bury it in the same "remember to put this in Key Vault" bullet point as the frontend UI secret.

This exposes a critical boundary. Key rotation is operations. Custody of the salt is continuity. Extracting chat logs for a legal request is break-glass. **Mixing break-glass (lawful access to user data) with ops (rollback, rotation, scale) is a compliance incident.** Production database access must be mediated by data or ops teams, time-boxed (under two hours), and backed by a legal ticket.

## Inconsistent backups will break the application on restore

If you do not write down the data stores on one page, the architecture meeting will end on the vague consensus that "we encrypt things."

| Data Type | Location | Retention | Access |
|---|---|---|---|
| Chat body / history | Open WebUI Postgres | Until user deletes, or 90-day idle cleanup | App + lawful break-glass |
| Original uploads | Cloud Storage | Same; orphans deleted | Same |
| RAG vectors | pgvector (same DB) | Same | Same |
| Prompt telemetry | Log Analytics Workspace | ~60 days | Table-level RBAC only |
| Usage (tokens, dollars) | LiteLLM Postgres | Durable | Finance/platform |
| Sessions | Redis | While session lives | Not an archive |

Disk configuration is a constraint. Production databases might be provisioned at 64 GiB, with sandbox defaulting to 32 GiB. Copy the SKU but skip the alerts, and "disk full" moves from a dashboard warning to a Monday incident. When peak seasonal traffic starts, file uploads and concurrency arrive simultaneously. The SKU is just the result; the calendar is the cause.

The disaster-recovery script must coordinate file-share snapshots with Postgres point-in-time recovery (PITR), laying down points nightly. A deployment with database backups but no file snapshots will restore into an inconsistent state: vectors that point at missing files. Drill an inconsistent timestamp on purpose and watch the application fail.

Residency is equally strict. "We are deployed in the local region" is an insufficient defense. A cloud provider might process prompts locally but use cross-region inference for specific models. Legal wants a data-flow map, not a cloud provider's logo.

## The constraint-based porting list

Divide the reference architecture into three piles. Ship the first pile to start. Treat the third pile as scripture and you will spend a month arguing about naming conventions.

**Copy (The Constraints)**
* Control plane and UI in separate directories, workflows, and databases.
* Three environments; a human gate on prod; what-if by default on PRs.
* GitHub OIDC; no long-lived passwords.
* Single-active sessions / no dual-write on the control plane.
* Explicit TTLs on content logs; durable storage for usage metadata.
* Model onboarding goes through progressive environments; no wildcards.

**Adapt (To Your World)**
* **Region:** An EU deployment may require a region pair plus an explicit ban on certain cross-region APIs.
* **Network:** You may have to hang the gateway on a zero-trust network rather than a pre-existing VNet.
* **Compute:** Swap serverless containers for managed Kubernetes if you keep internal DNS, but ensure you replicate the single-revision drain.
* **Alerts:** Alert receivers live in platform parameters, not in a hero's phone. Changing who gets paged is a PR, not a direct message.

**Discard (Their Leaves)**
* The specific resource dictionaries (e.g., `prod-region-app-*`). Build your own `{env}-{region}-{workload}` taxonomy.
* Treating web search or dynamic sessions as MVP requirements.
* Turning on `LITELLM_LOG_PAYLOADS=true` in production "for debugging." That copies full plaintext from a 60-day log policy into a durable usage database.

## Elevation: Infrastructure-as-Code is Serialized Scar Tissue

Infrastructure-as-code is not an architecture. It is the serialized output of a specific organization's constraints, compliance boundaries, and budget.

When we copy YAML, we assume the code is the solution. But the code is often just the scar tissue of a previous incident. The 90-second sleep is there because dual-writing corrupted the session store. The isolated Log Analytics table is there because the security team refused to grant workspace-level read access. 

This principle has a limit: it applies strictly to stateful planes, identity perimeters, and data lifecycles. Pure stateless compute—like the frontend web container—can often be copied blindly without consequence.

> Generalize: Before porting a configuration block, ask: what specific failure mode or organizational policy forced this block to exist? 

## Do this today

Open your infrastructure repository. Look at the last deployment script you copied from a reference architecture. Can you name the constraint that forced it to be written that way? 

If you cannot, whose world are you currently running in?
