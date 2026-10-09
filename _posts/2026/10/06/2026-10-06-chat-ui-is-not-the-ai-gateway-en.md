---
title: 'The Chat UI Is Not Your AI Gateway: Rethinking the Agent Entry Point'
header:
    image: /assets/images/bg_raw/BB1msMIs.jpg
date: 2026-10-06
tags:
 - architecture
 - llm
 - devops
 - infrastructure
 - api-gateway
permalink: /blogs/tech/en/chat-ui-is-not-the-ai-gateway
lang: en
layout: single
category: tech
---
> "One must learn by doing the thing; for though you think you know it, you have no certainty, until you try." — Sophocles

# The Chat UI Is Not Your AI Gateway: Rethinking the Agent Entry Point

*Draw the control plane first, then hang a user interface on it.*

I keep a note from an early project on AI adoption: *Do not treat AI as a wishing machine; treat it as a workbench.* You do not ask a workbench for a finished product; you use it to design a production line, complete with rules, limits, and controls.

This distinction is exactly what separates an AI demo from an enterprise AI platform. When organizations adopt LLMs, they think they are buying a wishing machine—a chat box that just answers questions. I recently audited the infrastructure repository for a large institution's internal AI platform to understand how it ran in production. The codebase tells a very different story.

By the end of this teardown, you will see why the chat UI is the least important part of the stack, and how to structure the control plane that actually governs your models. Here is the useful order—the opposite of how I discovered it: the request hop, the buyer, why a proxy beats the obvious alternatives, then the four directories that keep it all from colliding.

The reality of the product is nailed down by two lines of Bicep injected into the Open WebUI front-end container:

```bicep
{ name: 'OPENAI_API_BASE_URL', value: 'http://${litellmContainerName}.internal.${containerAppEnv.properties.defaultDomain}' }
{ name: 'OPENAI_API_KEY', secretRef: 'openai-api-key' }
```

The UI never talks to the model provider. It talks to an internal proxy—in this case, LiteLLM—on the environment's internal DNS. The proxy decides whether this call goes to a primary region or falls back to cross-region inference. The UI is just the paint on the wishing machine; the proxy is the workbench's ledger.

## 🧭 1. What actually happens when someone hits send

Users sign in with an institutional mailbox through Entra SSO. Sessions live in Redis. Profiles and history live in Open WebUI's Postgres database. When a user sends a message, it is forwarded to the internal proxy.

Then the path forks. A GPT-4o request hits a provisioned throughput unit in the primary region; a Claude request hits a cross-region AWS Bedrock endpoint. On the way back, the proxy asynchronously writes to two ledgers: roughly 60 days of raw content in a log analytics workspace, and durable usage metadata in its own separate Postgres database. Only then does the UI save the thread and paint the reply.

Document chat is a second, heavier path. The uploaded file lands in cloud storage. The text goes through the proxy to an embedding model. The resulting vectors land in **pgvector** on the UI's database. The next question retrieves those chunks, then builds a prompt.

The identity plumbing is worth seeing in the raw, because it is where most teams quietly leak:

```yaml
# the proxy's production config
user_header_mappings:
  - header_name: X-OpenWebUI-User-Email
    litellm_user_role: customer
user_header_name: X-OpenWebUI-User-Email
```

`ENABLE_FORWARD_USER_INFO_HEADERS=true` lets the chat identity cross the proxy, so spend can be attributed to a real person instead of to one shared service key. And `STORE_PROMPTS_IN_SPEND_LOGS=false` leaves the spend log's `messages` and `response` fields as `"{}"` on purpose.

| | Naive read | Production read |
|---|---|---|
| **What is the product?** | A ChatGPT skin | One OpenAI-compatible door plus budgets and audit logs |
| **Where are the keys?** | An API key in the environment | Managed identity and Key Vault |
| **Who is the user?** | A login name | An HTTP header mapped to a customer ID for billing |
| **Who to blame first?** | "The model is down" | SSO/Redis, the proxy, provider quota, or the chat database |

When legal asks where a user's prompt lives, the answer is not "in the spend table"—that table was deliberately gutted of body text. The prompt itself lives in the analytics workspace and the UI database. Name the wrong store during an audit and you have a compliance incident, not a documentation nit.

> 📌 **Chat is the experience. The proxy is the ledger.** Ledgers are far harder to retrofit than themes—so draw the ledger first.

## 2. What the buyer is actually buying

The institution's architecture decision records are dry on purpose. They needed to stop a cost blowout while still allowing other internal teams to build tools on the same models. The procurement criteria strictly prioritized cost control, charge-back, model routing, and the option to leave a specific cloud provider over the aesthetics of the chat UI.

One first-principles question settles it: **if you swapped the chat UI for a completely different front end, would this still be an AI gateway?** Yes. Research jobs, CI/CD scripts, and internal APIs can mint virtual keys from the proxy and hit the exact same `/chat/completions` endpoint. The chat UI is just one consumer.

Reverse it: drop the proxy and let the UI talk to the cloud providers directly. You instantly lose unified model routing, per-key budgets, and cross-app auditing. The classroom chat might survive, but the institution's control plane does not.

| Buyer | What they say | What they sign for |
|---|---|---|
| **End Users** | "We need chat and PDF reading." | Do not ship data overseas; do not run out of quota mid-month. |
| **Finance** | "Give the teams AI." | Track dollars by team or key, and provide a kill switch. |
| **Security** | "Use SSO and encryption." | Enforce data residency, 60-day logs, and two-person break-glass. |
| **Other App Teams** | "Do not force this UI on us." | Provide one internal OpenAI-SDK-compatible URL. |

There is one cut that regulated institutions carry and most product teams never think about: in a university, a hospital, or a bank, a single conversation can itself be a record that must be retained and can be lawfully compelled. That reframes "break-glass." Reserve the two-person emergency access path **only** for lawful access to user data, and keep ordinary operations—rollbacks, key rotation, a Redis repair—off it. Mix the two and every routine maintenance touch becomes a reportable data-access event.

> Draw the control plane first. Hang a UI on it. Reverse the order and charge-back becomes homework you do after the invoice has already landed.

## 🛠️ 3. Why a proxy—and why not the obvious alternatives

Enterprise API management tools (like Azure APIM) are the default corporate choice for gateways. They are the wrong default here. The decision was not "which chat UI looks nicer"; it was which layer can turn tokens into dollars. Here is the shortlist the team actually weighed:

| Option | What it is good at | Why it was not enough here |
|---|---|---|
| **UI straight to the model providers** | One less hop to run | No virtual keys, no team budgets, no cross-app billing |
| **Enterprise API management (APIM)** | REST governance, cloud-native RBAC | Tokens→dollars is DIY; a second vendor is just another backend; no native LLM spend board |
| **A single provider's own gateway** | Region control, provisioned throughput, the vendor's compliance story | Does not cover a second vendor's models; ties you to one cloud |
| **A hand-rolled proxy** | Total control | You now own cost maps, admin SSO, and every provider adapter yourself |

APIM can throttle requests. It cannot natively turn tokens into dollars unless you build that math yourself—and the architectural notes put the indicative APIM Premium platform cost in the thousands of dollars a month. The containerized proxy runs on basic container apps and Postgres, avoids that tax entirely, and natively reports remaining quota on response headers. Its wins map one-to-one onto the buyer table: budgets per key, user, or team, in tokens or dollars; one OpenAI-shaped door for two different clouds; and content safety, SIEM syslog, and per-key model allow-lists all enforced in a single layer.

To be clear about the limits of this approach, this is not a free lunch. You own the proxy. You are responsible for image upgrades, the Postgres database, Redis, and rollback procedures. An extra hop also means a single brain: if the proxy dies, every model door dies with it—the UI can still render, but there is nothing behind it.

🩸 **Warning**: The salt key is the single worst operational object in this stack. Lose the master salt key, and the encrypted virtual keys in the proxy's database do not come back. Enterprise API management platforms do not die this way. You are trading managed-platform resilience for deep control over LLM economics—a trade worth making only once money is denominated in tokens.

> **Interview point**: do not recite the proxy's feature list. Say the institution needed *LLM economics and multi-vendor control*. API management is strong at REST; it is weak at "how many dollars does this key have left this month."

## 4. Information hiding by directory

The most revealing part of the repository is its directory structure. It is split into four distinct stacks, and the split is information hiding in the classic Parnas sense—each stack hides a volatile decision behind a stable boundary.

| Stack | What it hides | What actually churns |
|---|---|---|
| `src/network` | Existing VNet, subnets, routing | Almost never—the IaC is a documented replica of hand-built infra |
| `src/ai-platform` | Logging, monitoring, storage, Key Vault, alerting | Alert receivers, shared SKUs |
| `src/litellm` | The proxy, spend DB, cross-cloud routing, content safety | The model list, the license, the image tag |
| `src/openwebui` | Chat, pgvector, file store, SSO, cleanup job | UI version, retention policy, uploads |

In a local demo, the UI and the gateway can share a single Docker Compose file. In production, their operational clocks diverge. The model list in the proxy changes weekly as new models drop; the chat product, heavy with stateful Redis sessions and user history, cannot tolerate breaking changes at that frequency. Weld them into one deployment unit and each side blocks the other.

The chat stack carries a Bicep comment that does not lie:

```bicep
activeRevisionsMode: 'Single' // Change this from 'Multiple' to support sticky sessions
```

They moved **from** Multiple **to** Single for WebSockets and sticky sessions. The cost: no percentage traffic split—a release replaces the active revision outright. So the deploy pipeline deactivates the stateful container, sleeps ninety seconds, then applies the new Bicep, specifically to avoid a dual-write window. That is not cloud romance; it is symmetry breaking after a chat product grew a Redis session. A separate cleanup job runs daily and drops idle data older than 90 days plus orphaned files—knowing *that* is more SME than reciting resource names, because someone will arrive on Monday asking where Friday's knowledge base went.

> 📌 **The Two-Clock Principle**
> 
> **Mechanism**: When two components operate on fundamentally different rhythms (model deprecation vs. database schema stability), they must not share a deployment unit.
> **Limit**: This only applies when state or external dependencies force the clocks out of sync. If both components can safely deploy together without friction, splitting them is just premature microservice overhead.
> **Generalize**: Which two components in your stack are currently sharing a pipeline despite running on different operational clocks?

You pick a proxy because money is denominated in tokens; you split the repository because money changes faster than the chat chrome.

## Three maps to keep

Strip away the specific cloud and the specific chat app, and three maps are what remain. Another institution can skip these tools; it should not skip these maps.

| Map | The question it answers | The answer here |
|---|---|---|
| **Request** | What happens after send? | Browser → UI → (internal) proxy → provider A or B → two ledgers + the chat DB |
| **Purchase** | Where does the budget actually go? | The control plane—proxy, identity, logs—not the skin |
| **Change** | Which folder does this PR touch? | Models or money → the proxy stack; UX or files → the chat stack; an alert email → the platform stack |

Skip the maps and you ship a fluent demo plus a quarter-end invoice with no sending user attached to it.

## Do this today

If you are running an AI entry point for your team, check your assumptions against the workbench model:

1. Search your current "AI chat" deployment for `OPENAI_API_BASE` or its equivalent. If it points directly at a public cloud provider's endpoint, you operate a client, not a gateway.
2. Ask finance whether they can name last month's AI expenditure **by person or by team**. If they cannot, you are pretending charge-back lives in vendor rate limits.
3. Split the git path for your model list from the git path for your UI release. Even if they stay in one repository, separate the directories and workflows today.
4. Write down who holds the salt or master key for your virtual budgets. If you cannot name a person, you are not in production yet.

A wishing machine only knows how to grant one type of request. A workbench is where you build the tools to handle any request. Stop staring at the UI, and start building the workbench.

*Next up: the porting guide—which constraints are worth copying (OIDC, what-if deploys, single-revision, data residency), and which resource names will embarrass you on day one.*
