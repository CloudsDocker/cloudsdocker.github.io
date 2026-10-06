---
title: Don't copy the resource names. Copy the constraints
header:
    image: /assets/images/hd_kubenetes_bamboo_deployment.png
date: 2026-10-06
tags:
 - azure
 - github-actions
 - llm
 - devops
 - security
permalink: /blogs/tech/en/port-university-ai-gateway
lang: en
layout: single
category: tech
---

> When you recite their poems and read their books, can you do so without knowing what they were? You must discuss the world they lived in. — Mencius

# Don't copy the resource names. Copy the constraints

*ChatMQ does not teach you `prd-auea-opui-rg-01`. It teaches why a university has to walk sandbox → non-prod → a human gate on prod.*

The previous post named the hub: the chat box is a spoke, LiteLLM is the hole. This one is for the platform engineer who has just been asked to “stand up our own ChatGPT”. The hand wants to clone resource names. That is the expensive way to copy.

Mencius’s point is context. Macquarie’s world is Australia East, Entra, an existing OpenAI VNet, student conversations that might become education records, and faculties that want dollars by team. If your world differs in one place — data must stay in the EU, there is no ExpressRoute, models must be Azure-only — a copied Bicep can look green in what-if and red in week-one on-call.

After this you should be able to:

- Draw the three-environment state machine: PRs only what-if; merge rolls sandbox then dev; prod needs a GitHub Environment approval.
- Separate **break-glass** (lawful access to user data) from **ops** (rollback, rotation, scale). Mixing them is a compliance incident.
- Walk into another university’s architecture review with a copy / adapt / discard list, not a resource-name cheat sheet.

## 1. The release state machine is more worth copying than the names

`CONTRIBUTING.md` has a sentence people skip: a pull request does **not** change sandbox, dev, or prod. What-if shows the diff. After merge, Actions deploy — sandbox first, then dev, then prod with a human approval.

LiteLLM’s workflow is that sentence compiled:

```yaml
# .github/workflows/litellm.yaml (shape, not the full file)
on:
  pull_request: { paths: [src/litellm/**, ...] }
  push:         { paths: [src/litellm/**, ...] }

sandbox:  # PRs only
  operation: whatIf | create   # whatIf on the PR
dev:
  operation: whatIf | create
dev-test:                     # merge only
  playwright against the new LiteLLM URL
prod:
  needs: dev-test
  if: push && main
  environment: prod           # the human gate lives here
```

Identity is OIDC, not a long-lived service-principal password:

```yaml
permissions:
  id-token: write
  contents: read
# azure/login
#   client-id / tenant-id / subscription-id from GitHub Environment vars
```

Local checks and cloud checks are different rulers. `make validate` diffs Bicep snapshots. `make *-what-if` asks Azure what would actually change. `make local` only proves docker compose still chats. Treat a snapshot as a deploy, or a what-if as a test, and you are using the wrong ruler.

Stateful containers have a script that looks like a mysterious sleep: deactivate the current revision, `sleep 90`, then run Bicep. Sixty seconds for a graceful stop, thirty more as buffer. Single revision plus Redis sessions cannot dual-write. When you port this to Kubernetes, do not translate it as “we also sleep 90”. Translate it as **the stateful control plane must not be dual-active**. Implementation can be a Job, a PDB, a drain. The number is not the constraint. Forbidding two writers is.

| Copy this | Do not copy this |
|---|---|
| PR = read-only diff; prod = human gate | Prefixes like `prd-auea-opui-rg-01` |
| Three GitHub Environments, secrets isolated | Sandbox secrets reused in prod |
| Model changes on the LiteLLM workflow, UI on OWUI | One mega-pipeline that deploys the world |
| Change the image in `local/docker-compose-*.yaml` before Bicep | Bump the tag only in prod parameters |

Model onboarding is a state machine too: `make update-models-from-azure` writes YAML; Actions show it in sandbox, then non-prod, then prod after approval. They turned off LiteLLM wildcard discovery — the comment says they talked to Richard and wanted control. Turn wildcards on in another school and a mistaken deploy in the Azure console becomes the campus model list. That is a product decision, not a YAML taste.

> What-if is an opinion. Create is a fact. The human gate is what you are willing to pay for facts.

## 2. Identity, secrets, and the salt you must not lose

Each app gets a user-assigned managed identity. Key Vault access policies let it read secrets. LiteLLM’s identity is also Cognitive Services User against Azure OpenAI, and it publishes into a custom log table. GitHub holds OIDC plus environment secrets. The container pulls from Key Vault at start.

Azure models use managed identity; Bedrock uses access keys — the header of `litellm-config.prod.yaml` says so. That is the multi-cloud asymmetry: Microsoft can kill static keys; AWS has not, in this design. At the next university, ask security whether “half the estate still has long-lived keys” is acceptable. If not, put a credential proxy in front of Bedrock, or do not ship Claude yet.

The salt is the least “config-like” config in the design. LiteLLM encrypts virtual keys in the database with `LITELLM_SALT_KEY`. Lose the master key and you can still issue emergency keys. Lose the salt and historical keys are bytes you cannot open. Backup of the salt needs two people, an offline copy, and a drill date. Do not bury it in the same “remember to put this in KV” bullet as `WEBUI_SECRET_KEY`.

Three mistakes other campuses will make because they look cheap:

| Mistake | Why it looks cheap | What it actually costs |
|---|---|---|
| One MI for everything | Fewer role assignments | Cleanup job and chat UI share blast radius |
| Secrets in `.bicepparam` | Pretty what-if | Parameters enter git; people will paste webhooks into Bicep |
| API keys against Azure OpenAI | Local docker is smoother | Rotation touches every consumer; MI turns rotation into a role change |

Postgres and Storage sit behind firewalls. The repo’s `docs/connecting-to-firewalled-services.md` is: add a rule, do the work, remove the rule. A standing laptop IP as “developer experience” is break-glass as the default route.

> Key rotation is operations. Custody of the salt is continuity. Do not put them on the same line of the same runbook.

## 3. Where data lives, who may see it, what you restore first

Write the stores on one page or the architecture meeting will end on “we encrypt”:

| What | Where | How long | Who |
|---|---|---|---|
| Chat body / history | OWUI Postgres (Australia East) | Until the user deletes or the cleanup job (idle > 90 days by default) | The app + lawful break-glass |
| Original uploads | Azure Storage | Same; orphans go too | Same |
| RAG vectors | pgvector on that same OWUI database | Same | Same |
| Prompt bodies (telemetry) | Log Analytics `LiteLLM_CL` | ~60 days | Table-level RBAC, not the workspace skeleton key |
| Usage metadata (tokens, dollars, email) | LiteLLM Postgres | Durable | Finance/platform; spend bodies may be empty |
| Sessions | Redis | While the session lives | Not an archive |

Disk is a constraint too: production Open WebUI Postgres is P6 / 32 GiB; LiteLLM is P6 / 64 GiB; sandbox/dev default to P4 / 32. Copy the SKU and skip the alerts, and “disk full” moves from a dashboard to a Monday incident.

The disaster-recovery script coordinates **file-share snapshots and Postgres PITR**, with a nightly job laying down points. A campus with disk backups and no file snapshots will restore into “database yes, files no” — vectors that point at ghosts. Drill an inconsistent timestamp on purpose and watch the app complain.

The first cut in the break-glass doc is the useful one: it is **not** for rollback, rotation, or deploy. Two people, time-boxed (default ≤ two hours), read-only preferred, legal basis on the ticket. Production database access is mediated by CloudOps or data. With `STORE_PROMPTS_IN_SPEND_LOGS=false`, fishing the LiteLLM spend table for chat text returns empty — operators must already know whether to go to the OWUI database or Log Analytics.

Do not dismiss residency with “we are on Azure in Australia”. Standard / Regional PTU Azure OpenAI processes prompts and responses inside the customer geography; they may still move between regions inside that geography. Bedrock Claude uses AU cross-region inference — Sydney and Melbourne. Legal wants a map, not a logo. If your campus forbids any non-Azure processing, Claude is not “one more `model_list` row”. It is a procurement.

> Backups prove you can go back. Residency proves you did not go to the wrong place. Audit proves you know who went. Those are not one control.

## 4. Week one at another campus: copy, adapt, discard

Split ChatMQ into three piles. Ship the first pile and you can start. Treat the third pile as scripture and you will spend a month on naming.

**Copy (constraints)**

- Control plane and UI in different directories, workflows, and databases.
- Three environments; a human gate on prod; what-if by default on PRs.
- GitHub OIDC; no long-lived SP passwords.
- User identity forwarded into the proxy; budgets on people, not “the chat container”.
- Single-active sessions / no dual-write on the control plane.
- Content logs have a TTL; usage metadata is durable; the cleanup job has a clock (theirs is 17:00 UTC).
- Model adds go through a script and progressive environments; no wildcards.
- Break-glass and ops as separate booklets.

**Adapt (to your world)**

- Region. They bound Australia East because students and counsel live on that map. An EU campus may be a region pair plus an explicit Bedrock ban.
- Network. Their VNet is a pre-existing asset. You may draw from scratch, or you may have to hang on campus zero-trust. `src/network` is documentation, not “apply to rebuild”.
- Front end. Open WebUI is replaceable. Do not write “must be this UI” into architecture principles.
- Compute. Swap ACA Consumption for AKS / ECS if you keep internal DNS, MI/IRSA, and single revision or an equivalent drain.
- Alert receivers live in **ai-platform parameters**, not in a hero’s phone. Changing who gets paged is a PR, not a chat message.

**Discard (their leaves, not your root)**

- The whole `prd-auea-opui-*` dictionary. Build your own `{env}-{region}-{workload}` and put it in types. Do not keep it oral.
- Their Teams webhooks, mailboxes, subscription IDs.
- Treating syslog relay, SearXNG, Speech, or dynamic sessions as MVP. ChatMQ’s own data-flow note says web search was off for go-live.
- APIM Premium “because enterprises have a gateway layer”. Prove the token-to-dollar problem is still unsolved by the proxy before you buy a second gateway.
- Turning on `STORE_PROMPTS_IN_SPEND_LOGS=true` in production “for debugging”. That expands full text from a 60-day log policy into a durable database.

Week one is four jobs, in this order, with UI polish deliberately last:

1. Draw your three maps (request / purchase / change). Get security, finance, and the registrar on the same page.
2. Stand up a minimum proxy: one model, OIDC or a throwaway MI, a per-person budget of $N, spend logs without bodies.
3. Hang a front end whose `OPENAI_API_BASE` points at the proxy’s **internal** address.
4. Write two pages: what happens if the salt is lost; what happens if legal wants one conversation. Dry-run both.

Locally they use `make local`: OWUI on `:3000`, LiteLLM on `:4000/ui`. You can start on those two ports. Do not treat the local Jupyter code interpreter as the production shape — the comment says it is local only.

On capacity, copy alerts before SKUs. CPU and memory alerts already sit on Postgres; uploads show up on the Storage dashboard. When term starts, uploads and concurrency arrive together. SKU is the result. The calendar is the cause.

> Know the person, discuss their world: discuss this campus’s world before you copy Macquarie’s deeds. Deeds can change. Worlds do not become the same because the YAML did.

## Do this today

1. On one architecture page, write the **GitHub Environment names** for three environments and who can approve prod. If you cannot name a person, do not write Bicep yet.
2. Fill a user-data grid: body, files, vectors, telemetry, metadata. Every cell gets a system name and a TTL. Empty cells mean you are not ready for students.
3. Promote salt-key custody from “it is in KV” to “two people, offline copy, drill date”.
4. Put the next model change in its own PR. Do not bundle it with an Open WebUI bump. That is information hiding at the lowest price.
5. Book a 30-minute tabletop: a bad LiteLLM image, single revision already fully live. What is the rollback? Who approves? What do students see?

The last post was the hub. This one is which bolt pattern you must measure when you mount that hub on a different car, and which hubcap you can throw away.

*Resource names are leaves. Constraints are the root. Leaves photograph well. Roots decide whether the next campus survives the first term.*
