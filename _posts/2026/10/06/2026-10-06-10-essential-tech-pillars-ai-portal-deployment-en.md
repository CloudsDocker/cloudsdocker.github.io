---
title: 10 Essential Tech Pillars for Rapid AI Portal Deployment
header:
    image: /assets/images/bg_raw/BingWallpaper (12).jpg
date: 2026-10-06
tags:
 - infrastructure-as-code
 - github-actions
 - llm-gateway
 - devops
 - security
permalink: /blogs/tech/en/10-essential-tech-pillars-ai-portal-deployment
lang: en
layout: single
category: tech
---
# 10 Essential Tech Pillars for Rapid AI Portal Deployment

*You can clone the IaC templates, but if you don't understand the compliance and state constraints beneath them, your deployment will fail on week one.*

When a platform team is asked to stand up a private enterprise AI portal, the industry consensus is to find an open-source reference architecture and clone its infrastructure-as-code templates. It feels like a shortcut: the Terraform or Bicep is already written, the Docker containers are mapped, and the network is drawn.

I keep a note from a podcast about the width of modern train tracks. They are sized the way they are because English rail engineers copied the width of pre-railway tramways, which were built to match the wheel spacing of horse-drawn wagons—spacing dictated by the width of two horses. We are still building high-speed rail constrained by the dimensions of a 19th-century horse.

Cloning an AI portal's repository without understanding its constraints is the same mistake.

The original institution built their architecture for a specific world: a designated local Azure region, strict student privacy requirements, and faculties that charge back by the team. If your world differs in one place—perhaps your data must stay in the EU, or you rely on AWS Bedrock instead of Azure OpenAI—a blindly copied Bicep template will look green in a pull request and red during your first week on-call.

This teardown of a production AI gateway architecture will show you the exact constraints you must copy, and the superficial configurations you must discard.

## The Release State Machine Is the Real Architecture

The repository's `CONTRIBUTING.md` contains a structural rule that developers often skip: a pull request does **not** change the sandbox, dev, or production environments. It only shows the diff.

The GitHub Actions workflow for the LiteLLM gateway is that rule compiled into code:

```yaml
# .github/workflows/litellm.yaml (structural shape)
on:
  pull_request: { paths: [src/litellm/**] }
  push:         { paths: [src/litellm/**] }

sandbox:                      # PRs only
  operation: whatIf | create  # whatIf on the PR
dev:
  operation: whatIf | create
dev-test:                     # merge only
  playwright against the new LiteLLM URL
prod:
  needs: dev-test
  if: push && main
  environment: prod           # the human gate lives here
```

Local checks and cloud checks use different rulers. Running `make validate` locally only diffs your Bicep snapshots. Running `make local` only proves your Docker compose file still routes chat requests on `:3000` and `:4000/ui`. But an infrastructure `what-if` asks the cloud provider what would actually change. Treat a snapshot as a deployment, or a what-if as a test, and you are using the wrong ruler.

If you look at the deployment script for the stateful containers, you will see a command to deactivate the current revision, followed by a mysterious `sleep 90`, and then the Bicep execution. Sixty seconds allow for a graceful stop; thirty more provide a buffer. 

When you port this to Kubernetes, do not translate this as "we also need to sleep for 90 seconds." Translate it as a structural rule. The number is not the constraint. Forbidding two writers is. Implementation can be a Kubernetes Job, a PodDisruptionBudget, or a node drain. The goal is ensuring the stateful control plane is never dual-active against the Redis session store.

## 🔐 Identity, Secrets, and the Salt You Must Not Lose

Authentication in this architecture relies on OIDC, not long-lived service-principal passwords. GitHub holds the OIDC tokens and environment secrets, allowing the container to pull from Key Vault at startup.

```yaml
permissions:
  id-token: write
  contents: read
# azure/login relies on client-id / tenant-id / subscription-id 
# fetched dynamically from GitHub Environment vars
```

But look closely at the model onboarding configuration. Azure models use Managed Identity (MI), but AWS Bedrock uses static access keys. This is the multi-cloud asymmetry: Microsoft can kill static keys for Azure OpenAI; AWS, in this specific design, has not. At your organization, ask security whether "half the estate still uses long-lived keys" is acceptable. If it is not, you will need a credential proxy in front of Bedrock, or you cannot ship Claude yet.

🩸 **血泪提醒 (The Salt Trap)**: The most dangerous piece of configuration is the `LITELLM_SALT_KEY`. LiteLLM uses this to encrypt virtual keys in the database. If you lose the master database password, you can issue emergency keys. If you lose the salt, your historical keys are permanently locked bytes you cannot decrypt. Custody of the salt requires two people, an offline copy, and a scheduled disaster recovery drill. Do not bury it in the same casual "remember to put this in Key Vault" checklist as the UI theme string.

## Where the Data Lives (And Who Can See It)

Before you write a single line of infrastructure code, you must document the data stores. If you don't, your architecture review will end with a vague "we encrypt it" and fail the audit.

| Data Type | Storage Location | Retention (TTL) | Access Custody |
|---|---|---|---|
| Chat body / history | Postgres (Open WebUI) | Until user deletes or 90-day idle cleanup | The app + lawful break-glass |
| Original uploads | Azure Storage | Same as chat (orphans purged) | Same |
| RAG vectors | pgvector (Open WebUI DB) | Same as chat | Same |
| Prompt bodies (telemetry) | Log Analytics `LiteLLM_CL` | ~60 days | Table-level RBAC only |
| Usage metadata (tokens/$) | Postgres (LiteLLM) | Durable | Finance/Platform teams |
| Active Sessions | Redis | While session lives | App only (Not an archive) |

Disk capacity is a hard constraint here. The production Open WebUI Postgres database runs on a P6 / 32 GiB SKU; LiteLLM needs P6 / 64 GiB. If you copy the SKUs but skip importing the disk-space alerts, "disk full" moves from a Grafana dashboard directly to a Monday morning incident. When the academic term starts, uploads and concurrency arrive simultaneously. The SKU is just the result; the academic calendar is the cause.

Disaster recovery requires coordinating file-share snapshots with Postgres Point-in-Time Recovery (PITR). A team with database backups but no file snapshots will restore into a split-brain state: vectors pointing at ghost files. Drill an inconsistent timestamp on purpose and watch the application panic.

## 💡 The 10 Essential Tech Pillars

When you copy the exact naming convention of the upstream repository—like `<env>-<region>-<workload>-rg-01`—you are just measuring the 19th-century horse. Discard the names. Copy these 10 constraints instead:

1. **PRs are Read-Only:** Pull requests run `what-if` diffs. Only merges mutate state.
2. **Human Gates on Production:** Sandbox and dev roll automatically; production requires a GitHub Environment approval.
3. **OIDC Identity:** No long-lived service-principal passwords. User identity is forwarded into the proxy.
4. **Single-Active Control Plane:** Sessions cannot dual-write. Enforce drains or single-revision limits.
5. **Granular Data Retention:** Content logs require a strict TTL (e.g., a 17:00 UTC cleanup job). Usage metadata remains durable.
6. **Strict Model Onboarding:** Model additions go through progressive environment scripts. Never enable wildcard model discovery.
7. **Salt Custody Continuity:** The database salt is treated as a continuity asset, not a standard operational secret.
8. **Budgets Tied to Identity:** Budgets are applied to human identities, not "the chat container."
9. **Segregate Break-Glass from Operations:** Key rotation is operations. Accessing a user's chat history is lawful break-glass. Do not put them in the same runbook. 
10. **Discard Upstream Topology:** Build your own `{env}-{region}-{workload}` taxonomy. Discard the upstream Teams webhooks, subscription IDs, and assumptions about internal DNS.

> 📌 **The Principle of Conservation of Constraints**
> You cannot copy an architecture without copying the organizational boundaries that shaped it. If you adopt a strict three-tier release pipeline, you are adopting the compliance requirement that mandated it. Form follows failure.
> **Limit:** This applies to structural topology (networks, state, identity), not to stateless application logic where standard libraries abstract the organization away.
> **Generalize:** Which of our infrastructure configurations is actually just an org chart in YAML?

A standing laptop IP firewall rule framed as "developer experience" is just break-glass access configured as the default route. If you turn on `STORE_PROMPTS_IN_SPEND_LOGS=true` in production "for debugging," you just expanded full-text user data from a volatile 60-day log policy into a durable financial database.

What happens if legal asks to pull one specific conversation tomorrow morning? If you cannot answer that without guessing which database to query, you aren't ready to deploy.

Open your own infrastructure repository right now. Pick the largest configuration file, find the most oddly specific timeout or retry value, and ask the person who wrote it what incident caused it. I bet you find a constraint you didn't know you had.
