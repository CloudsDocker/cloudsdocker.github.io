---
title: The chat box is not the product
header:
    image: /assets/images/hd_containers.png
date: 2026-10-06
tags:
 - azure
 - llm
 - architecture
 - litellm
 - devops
permalink: /blogs/tech/en/chat-ui-is-not-the-ai-gateway
lang: en
layout: single
category: tech
---

> Thirty spokes share one hub. It is the hole that makes the wheel useful. — *Tao Te Ching*, 11

# The chat box is not the product

*What I learned reading Macquarie’s ChatMQ repo as an SME course: you are not buying Open WebUI.*

On 6 October 2026 I sat down with `azure-ai-gateway` to learn it as if I had to own it in production. The README’s first table is a set of doors: OpenWebUI Chat, LiteLLM Admin, three resource groups, sandbox through prod. Your hand goes to chat. That is the wrong door.

The product is nailed down by two lines inside the Open WebUI container:

```bicep
{ name: 'OPENAI_API_BASE_URL', value: 'http://${litellmContainerName}.internal.${containerAppEnv.properties.defaultDomain}' }
{ name: 'OPENAI_API_KEY', secretRef: 'openai-api-key' }
```

The UI never talks to GPT. It talks to LiteLLM on the environment’s internal DNS. LiteLLM decides whether this call goes to Azure OpenAI in Australia East or AWS Bedrock in Sydney / Melbourne. The spokes are pretty. The hole in the hub is what lets the wheel turn.

You should leave with three things:

- Buyers think they are procuring a chatbot. In production the scarce thing is a **control plane priced in dollars, people, and teams**.
- LiteLLM beat APIM here not because “gateway beat gateway”, but because **tokens convert to money**. APIM’s token policies mostly speak Azure OpenAI.
- `src/litellm` is split from `src/openwebui` as information hiding in the Parnas sense: model-list churn must not share a release clock with the chat database.

Discovery order was the opposite of teaching order. The README’s chat links went first; the internal hostname showed up later in Bicep. Below is the useful order: the hop, the buyer, why LiteLLM, then the four directories.

## 1. What actually happens when someone hits send

Staff and students sign in with a Macquarie mailbox through Entra SSO. Sessions live in Redis. Profiles and history live in Open WebUI’s Postgres. The message is forwarded to LiteLLM. Then it forks: GPT-4o hits Azure OpenAI regional PTU; Claude hits Bedrock cross-region inference (`ap-southeast-2` / `ap-southeast-4`). On the way back LiteLLM writes two ledgers asynchronously: roughly 60 days of content in Log Analytics, and durable usage metadata in its own Postgres. Open WebUI saves the thread and paints the reply.

Document chat is a second path: the original file lands in Azure Storage; text goes through LiteLLM to `text-embedding-ada-002`; vectors land in **pgvector** on the Open WebUI database. The next question retrieves chunks, then builds a prompt.

| | Naive read | Production read |
|---|---|---|
| What is the product? | A ChatGPT skin | One OpenAI-compatible door plus budgets plus audit |
| Where are the keys? | An API key in env | Managed identity + Key Vault; Azure Foundry is MI, not a key |
| Who is the user? | A login name | `X-OpenWebUI-User-Email` mapped to a LiteLLM customer for billing |
| Who to blame first? | “The model is down” | SSO/Redis, the proxy, provider quota, or the chat database |

The config is blunt:

```yaml
# src/litellm/litellm-config.prod.yaml
user_header_mappings:
  - header_name: X-OpenWebUI-User-Email
    litellm_user_role: customer
user_header_name: X-OpenWebUI-User-Email
```

`ENABLE_FORWARD_USER_INFO_HEADERS=true` lets chat identity cross the proxy. `STORE_PROMPTS_IN_SPEND_LOGS=false` leaves SpendLogs `messages`/`response` as `"{}"`. When legal asks where the prompt lives, the answer is not “in the spend table”. Body text is mainly in Log Analytics and the Open WebUI database. Name the wrong store and you have a compliance incident, not a documentation nit.

> Chat is the experience. The proxy is the ledger. Ledgers are harder to retrofit than themes.

## 2. What the buyer is actually buying

The 20 May 2025 architecture note is dry on purpose. They needed to stop a cost blowout and still let other teams build tools on the same models. The comparison is not “which chat UI looks nicer”. It is cost control, charge-back, keys, model routing, non-Azure models, and the option to leave Azure.

One first-principles question is enough: **if you swapped Open WebUI for another front end, would this still be an AI gateway?**

Yes. Research jobs, scripts, and internal APIs can mint LiteLLM virtual keys and hit the same `/chat/completions`. Open WebUI is one consumer. Reverse it: drop LiteLLM and let the UI talk to Azure and Bedrock directly — you lose unified `/v1/models`, per-key budgets, and cross-app audit. The classroom chat might survive. The institution’s control plane does not.

That is where the symmetry breaks. In a demo, UI and gateway can share one compose file. In production their clocks diverge: model lists move weekly; chat-product breaking changes must not. Weld them into one deploy unit and each side blocks the other.

| Buyer | What they say | What they sign for |
|---|---|---|
| Staff / students | Chat and PDFs | Do not ship homework overseas; do not run out of quota mid-term |
| Finance / faculties | “Give us AI” | Dollars by team or key, with a kill switch |
| Security / legal | SSO and encryption | Residency, 60-day logs, two-person break-glass |
| Other app teams | Do not force this UI | One internal OpenAI-SDK URL |

Universities have a cut that many companies skip: a conversation can be an education record, and it can be subpoenaed. Macquarie reserves break-glass **only** for lawful access to user data. Rollbacks and key rotation stay on the normal ops path. Mix the two and every Redis repair becomes a data-access event.

> Draw the control plane first. Hang a UI on it. Reverse the order and charge-back becomes homework you do after the invoice.

## 3. Why LiteLLM, not the obvious alternatives

The written decision is `docs/architecture-decisions/2025-05-20-ai-gateway-monitoring.md`. One sentence: LiteLLM. APIM can throttle. It cannot turn tokens into dollars unless you build that math. Their indicative APIM Premium platform cost was about **AU$6,159 / month**. LiteLLM is Container Apps plus Postgres — no that tax.

| Option | What it is good at | Why it was not enough here |
|---|---|---|
| OWUI straight to models | One less hop | No virtual keys, team budgets, or cross-app billing |
| Azure APIM | Enterprise API governance, Azure RBAC | Token/$ is DIY; Bedrock is another backend; no native LLM spend board |
| Azure OpenAI / Foundry only | Region, PTU, Microsoft’s compliance story | Does not cover Claude; they also refused wildcard discovery for control |
| Homegrown proxy | Total control | You now own cost maps, admin SSO, and every provider adapter |

LiteLLM’s wins map onto the buyer table:

- Budgets per key, user, or team, in tokens or dollars; overridable cost maps; remaining quota on response headers.
- One OpenAI-shaped door for Azure and Bedrock. The YAML itself comments that Foundry is managed identity and AWS is access keys.
- Policy in one place: content safety, SIEM syslog, per-key model allow-lists.
- It is a container. The ADR notes it can run on ECS/EKS/Fargate. For a university already standing on Bedrock, that is not a brochure line.

The costs, said fully, or this is a vendor pamphlet:

- **You own the proxy.** Image upgrades, Postgres, Redis, salt/master keys, rollback. APIM is PaaS; you buy less application toil.
- **An extra hop, and a single control plane.** If LiteLLM dies, every model door dies. Open WebUI can still render. There is no brain behind it.
- **Enterprise features ride a license.** Admin SSO wants `LITELLM_LICENSE`.
- **The salt key is the worst operational object in the stack.** Lose `LITELLM_SALT_KEY` and encrypted virtual keys in the database do not come back. APIM subscription keys do not die this way.
- Security may still ask for APIM in front. The ADR’s next steps leave that question open. They did not pretend the room was convinced.

Interview point: do not recite LiteLLM’s feature list. Say the school needed **LLM economics and multi-vendor control**. APIM is strong at REST. It is weak at “how many dollars does this key have left this month”.

> You pick a proxy because money is denominated in tokens. You split the repo because money changes faster than the chat chrome.

## 4. Four stacks: directories doing information hiding

This repository is not LiteLLM or Open WebUI application source. Those neighbouring checkouts are read-only from here. This repo is the Azure source of truth: Bicep, environment parameters, model YAML, Actions, runbooks.

| Stack | Path | What it hides | What churns |
|---|---|---|---|
| network | `src/network/` | Existing VNet / subnets / NSG / UDR | Almost never; the Bicep is a documented replica |
| ai-platform | `src/ai-platform/` | CAE, Log Analytics, App Insights, Storage, Key Vault, action group | Alert receivers, shared SKUs |
| litellm | `src/litellm/` | Proxy, spend DB, `LiteLLM_CL`, Bedrock, content safety | Model list, license, `-stable` image |
| openwebui | `src/openwebui/` | Chat, pgvector, files, cleanup job, SSO | UI version, retention, uploads |

Names encode environment: `{sbx\|npd\|prd}-auea-opui-...`. `auea` is Australia East. `opui` is this workload family. Production’s VNet does not even live in the app resource group; it is `prd-auea-infra-openai-vnet-01`. The network README admits the VNet was built by hand. The Bicep exists so the subnets are written down.

Open WebUI carries a comment that does not lie:

```bicep
activeRevisionsMode: 'Single' // Change this from 'Multiple' to support sticky sessions
```

They changed **from** Multiple **to** Single because of WebSockets / sticky sessions. The cost: no percentage traffic split. A release replaces the active revision. Stateful containers are deactivated in `reusable-deploy.yaml`, then the job sleeps 90 seconds, then Bicep runs — to avoid dual-write. That is not Azure romance. It is symmetry breaking after a chat product grew a Redis session.

A cleanup job runs daily at 17:00 UTC (03:00 / 04:00 in Sydney) and drops idle data older than 90 days, plus orphaned files. Knowing that is more SME than reciting resource names. Someone will arrive on Monday asking where Friday’s knowledge base went.

> You split directories so two clocks do not share one spring.

## Three maps

| Map | Question | Answer |
|---|---|---|
| Request | After send? | Browser → OWUI → (internal) LiteLLM → Azure or Bedrock → ledger + chat DB |
| Purchase | Where does budget go? | Control plane (proxy + identity + logs), not the skin |
| Change | Which folder does this PR touch? | Models/money → `src/litellm`; UX/files → `src/openwebui`; alert email → `src/ai-platform` |

Another university, another company, can skip Azure Container Apps. They can skip Open WebUI. They should not skip these three maps. Skip them and you ship a fluent demo, plus a quarter-end invoice with no sending user on it.

## Do this today

1. Search your current “AI chat” deploy for `OPENAI_API_BASE` or the equivalent. If it points at a public Azure OpenAI endpoint, you have a client, not a gateway.
2. Ask finance whether they can name last month’s dollars **by person or by team**. If they cannot, you are still pretending charge-back lives in APIM rate limits or a vendor console.
3. Split the git path for the model list from the git path for the UI release. Even if they stay in one repo, split directories and workflows first.
4. Write down who holds the salt/master key. If you cannot name a person, you are not in production yet.

The next post is the porting guide: which constraints to copy (OIDC, what-if, single revision, residency), and which resource names will embarrass you on day one.

*The hub is empty. Emptiness is not a defect. It is the layer that lets the spokes work.*
