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

By the end of this teardown, you will see why the chat UI is the least important part of the stack, and how to structure the control plane that actually governs your models.

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

| | Naive read | Production read |
|---|---|---|
| **What is the product?** | A ChatGPT skin | One OpenAI-compatible door plus budgets and audit logs |
| **Where are the keys?** | An API key in the environment | Managed identity and Key Vault |
| **Who is the user?** | A login name | An HTTP header mapped to a customer ID for billing |
| **Who to blame first?** | "The model is down" | SSO/Redis, the proxy, provider quota, or the chat database |

When legal asks where a user's prompt lives, the answer is not "in the spend table". The configuration explicitly leaves the spend log's `messages` and `response` fields as `"{}"`. The body text lives in the analytics workspace and the UI database. Name the wrong store during an audit and you have a compliance incident, not a documentation nit.

## 2. What the buyer is actually buying

The institution's architecture decision records are dry on purpose. They needed to stop a cost blowout while still allowing other internal teams to build tools on the same models. The procurement criteria strictly prioritized cost control, charge-back, model routing, and the option to leave a specific cloud provider over the aesthetics of the chat UI.

The architecture's defining trait is its decoupled front-end: you could swap the chat UI for a completely different application, and the AI gateway would remain intact. Research jobs, CI/CD scripts, and internal APIs can mint virtual keys from the proxy and hit the exact same `/chat/completions` endpoint. The chat UI is just one consumer.

Reverse it: drop the proxy and let the UI talk to the cloud providers directly. You instantly lose unified model routing, per-key budgets, and cross-app auditing. The classroom chat might survive, but the institution's control plane does not.

| Buyer | What they say | What they sign for |
|---|---|---|
| **End Users** | "We need chat and PDF reading." | Do not ship data overseas; do not run out of quota mid-month. |
| **Finance** | "Give the teams AI." | Track dollars by team or key, and provide a kill switch. |
| **Security** | "Use SSO and encryption." | Enforce data residency, 60-day logs, and two-person break-glass. |
| **Other App Teams** | "Do not force this UI on us." | Provide one internal OpenAI-SDK-compatible URL. |

## 🛠️ 3. The economics of the proxy

Enterprise API management tools (like Azure APIM) are the default corporate choice for gateways. They are the wrong default here. APIM is strong at REST governance, but it is weak at LLM economics.

APIM can throttle requests. It cannot natively turn tokens into dollars unless you build that math yourself. The architectural notes revealed an indicative APIM Premium platform cost of thousands of dollars a month. The containerized proxy runs on basic container apps and Postgres, avoiding that tax entirely, while natively tracking remaining quota on response headers.

To be clear about the limits of this approach, this is not a free lunch. You own the proxy. You are responsible for image upgrades, the Postgres database, Redis, and rollback procedures.

🩸 **Warning**: The salt key is the single worst operational object in this stack. Lose the master salt key, and the encrypted virtual keys in the proxy's database do not come back. Enterprise API management platforms do not die this way. You are trading managed platform resilience for deep control over LLM economics.

## 4. Information hiding by directory

The most revealing part of the repository is its directory structure. It is split into four distinct stacks: `src/network`, `src/ai-platform`, `src/litellm`, and `src/openwebui`.

This separation is information hiding in the classic Parnas sense. In a local demo, the UI and the gateway can share a single Docker Compose file. In production, their operational clocks diverge.

The model list in the proxy changes weekly as new models drop. The chat product, heavily laden with stateful Redis sessions and user history, cannot tolerate breaking changes at that frequency. Weld them into a single deployment unit, and each side blocks the other.

> 📌 **The Two-Clock Principle**
> 
> **Mechanism**: When two components in a system operate on fundamentally different rhythms (e.g., model deprecation vs. database schema stability), they must not share a deployment unit.
> **Limit**: This only applies when state or external dependencies force the clocks out of sync. If both components can safely deploy together without friction, splitting them is just premature microservice overhead.
> **Generalize**: Which two components in your stack are currently sharing a pipeline despite running on different operational clocks?

You pick a proxy because money is denominated in tokens; you split the repository because money changes faster than the chat chrome.

## Do this today

If you are running an AI entry point for your team, check your assumptions against the workbench model:

1. Search your current "AI chat" deployment for `OPENAI_API_BASE` or its equivalent. If it points directly at a public cloud provider's endpoint, you operate a client, not a gateway.
2. Ask finance whether they can name last month's AI expenditure **by person or by team**. If they cannot, you are pretending charge-back lives in vendor rate limits.
3. Split the git path for your model list from the git path for your UI release. Even if they stay in one repository, separate the directories and workflows today.
4. Write down who holds the salt or master key for your virtual budgets. If you cannot name a person, you are not in production yet.

A wishing machine only knows how to grant one type of request. A workbench is where you build the tools to handle any request. Stop staring at the UI, and start building the workbench.
