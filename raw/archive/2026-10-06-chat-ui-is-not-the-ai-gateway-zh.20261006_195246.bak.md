---
title: 聊天框不是产品：大学 AI 网关真正该买的那一层
header:
    image: /assets/images/hd_containers.png
date: 2026-10-06
tags:
 - azure
 - llm
 - architecture
 - litellm
 - devops
permalink: /blogs/tech/zh/chat-ui-is-not-the-ai-gateway
lang: zh
layout: single
category: tech
---

> 三十辐共一毂，当其无，有车之用。 — 《老子》第十一章

# 聊天框不是产品

*从 Macquarie 的 ChatMQ 仓库读出来的第一性原则：你买的不是 Open WebUI。*

2026 年 10 月 6 日，我把 `azure-ai-gateway` 当成一门 SME 课来读。README 第一张表全是入口：Sandbox / Non-Prod / Prod 的 OpenWebUI Chat、LiteLLM Admin、三个资源组。手指会先点聊天。那是错的入口。

真正把产品钉死的，是 Open WebUI 容器里这两行：

```bicep
{ name: 'OPENAI_API_BASE_URL', value: 'http://${litellmContainerName}.internal.${containerAppEnv.properties.defaultDomain}' }
{ name: 'OPENAI_API_KEY', secretRef: 'openai-api-key' }
```

聊天界面不直连 GPT。它连的是环境内部的 LiteLLM。LiteLLM 再决定这次请求去 Azure OpenAI（Australia East）还是 AWS Bedrock（Sydney / Melbourne）。车轮好看，毂中间那块空，才让车转起来。

读完这篇，你该拿走三件事：

- 买方以为在采购聊天产品；生产上真正稀缺的是**按人、按团队、按美元**的控制面。
- LiteLLM 对 APIM 的胜出，不是「网关打赢网关」，是 **token 能换算成钱**，而 APIM 的 token 策略基本只认 Azure OpenAI。
- `src/litellm` 从 `src/openwebui` 拆出去，不是目录洁癖，是 Parnas 意义上的信息隐藏：模型列表的变更频率，不该撞击聊天库的发版节奏。

阅读顺序和发现顺序相反。我先被 README 的聊天链接带着走，后来才在 Bicep 里看见内部 DNS。下面按**对你有用的顺序**写：先讲请求，再讲买方，再讲为什么是 LiteLLM，最后才是四层目录。

## 1. 一次发送，真正经过的跳

用户用 MQ 邮箱走 Entra SSO 进 Open WebUI。会话在 Redis。画像和历史在 OWUI 自己的 Postgres。消息被转到 LiteLLM。按模型分叉：GPT-4o 走 Azure OpenAI 的区域 PTU；Claude 走 Bedrock 跨区推理（`ap-southeast-2` / `ap-southeast-4`）。回来的路上，LiteLLM 异步打两处账：Log Analytics 大约留 60 天内容；Postgres 里留长期用量元数据。Open WebUI 再把对话写进自己的库，然后渲染到浏览器。

上传文档是另一条路：原文件进 Azure Storage；文本经 LiteLLM 打 `text-embedding-ada-002`；向量进 OWUI Postgres 的 **pgvector**。下一次提问，先检索再拼进 prompt。

把「普通人的看法 / 资深的看法」摊开：

| | 普通人 | 把这个仓当生产系统看 |
|---|---|---|
| 产品是什么 | ChatGPT 套壳 | 统一的 OpenAI 兼容入口 + 预算 + 审计 |
| 密钥在哪 | 环境变量里的 API key | 应用托管身份 + Key Vault；Azure 侧甚至不用 API key（Foundry 走 MI） |
| 用户是谁 | 登录名 | `X-OpenWebUI-User-Email` 头，映射成 LiteLLM 的 customer，用来计费 |
| 失败时先怪谁 | 「模型挂了」 | 先分：SSO / Redis、LiteLLM 控制面、供应商配额、还是 OWUI 数据库 |

配置里写得很直白：

```yaml
# src/litellm/litellm-config.prod.yaml
user_header_mappings:
  - header_name: X-OpenWebUI-User-Email
    litellm_user_role: customer
user_header_name: X-OpenWebUI-User-Email
STORE_PROMPTS_IN_SPEND_LOGS: "false"   # 实际写在容器环境变量里
```

`ENABLE_FORWARD_USER_INFO_HEADERS=true` 让聊天身份穿过代理。`STORE_PROMPTS_IN_SPEND_LOGS=false` 让 SpendLogs 里的 messages/response 变成 `"{}"`。法务问「prompt 存在哪」时，答案不是「都在 LiteLLM 那张 spend 表」——正文主要在 Log Analytics 和 OWUI 库。说错地方，就是一次合规事故。

> 聊天是体验。代理才是账本。账本比体验更难补。

## 2. 买方到底在买什么

2025-05-20 的架构记录写得很克制：要避免费用爆炸，又要允许别人用这些模型做工具。决策者名单里有工程也有平台。他们比的不是「哪个聊天框更好看」，是 **cost control、charge-back、keys、model routing、非 Azure 模型、迁云**。

第一性原理问一句就够：**如果把 Open WebUI 换成别的前端，这套系统还是不是 AI Gateway？**

还是。研究项目、脚本、内部服务都可以拿 LiteLLM 虚拟 key 打同一个 `/chat/completions`。Open WebUI 只是其中一个消费者。反过来：如果拿掉 LiteLLM，让 UI 直连 Azure 和 Bedrock——你立刻失去统一 `/v1/models`、按 key 预算、跨应用审计。教室里的聊天可能还在，学校的控制面没了。

这就是对称性破缺发生的位置。Demo 阶段，UI 和网关可以糊成一个 docker compose。一进生产，变更频率就不对称了：模型列表每周都可能动；聊天产品的 breaking change 必须小心。把它们焊在同一个部署单元里，两边会互相卡住。

| 买方 | 他们口头要的 | 他们签字时真正要的 |
|---|---|---|
| 师生 | 能聊天、能传 PDF | 别把作业内容漂到外国、别突然没额度 |
| 财务 / 院系 | 「AI 给我们用用」 | 按团队/key 能算美元，能切断超支 |
| 安全 / 法务 | SSO、加密 | 数据驻留、60 天日志、break-glass 两人制 |
| 其他应用团队 | 别强迫他们用这个 UI | 一条 OpenAI SDK 兼容的内部 URL |

大学场景还有一刀，企业常常没有：对话是教育记录，可能被传票。Macquarie 把 break-glass **只**留给合法访问用户数据，日常回滚和轮换密钥走普通运维。这不是流程洁癖——混用之后，每一次修 Redis 都会被当成一次数据调阅。

> 先画控制面，再挂界面。顺序反了，charge-back 会变成事后补课。

## 3. 为什么是 LiteLLM，不是「别人」

仓里的正式选择写在 `docs/architecture-decisions/2025-05-20-ai-gateway-monitoring.md`。结论一句：选 LiteLLM。APIM 能限流，不能把 token 翻译成美元，除非你自己写一层。当时 APIM Premium 的指示性平台成本大约 **每月 AU$6,159**；LiteLLM 是 ACA 加上一套 Postgres，没有这笔固定税。

| 方案 | 它擅长 | 在这个项目里为什么不够 |
|---|---|---|
| OWUI 直连模型 | 少一跳 | 没有虚拟 key、团队预算、跨应用计费 |
| Azure APIM | 企业 API 治理、Azure RBAC | token/$ 要自研；Bedrock 要另开 backend；没有原生 LLM spend 看板 |
| 只吃 Azure OpenAI / Foundry | 区域、PTU、微软合规叙事 | 盖不住 Claude；他们还故意关掉 wildcard discovery，要可控上架 |
| 自研代理 | 完全可控 | 成本表、SSO Admin、provider 适配都要养团队 |

LiteLLM 的利，都贴着上面那张买方表：

- 按 key / 用户 / 团队做 token 或美元预算；成本表可覆盖；响应头能带剩余额度。
- 一个 OpenAI 兼容入口打 Azure 和 Bedrock。`model_list` 里 Azure 走托管身份，AWS 走 access key——配置自己都写了这句注释。
- 策略集中：Content Safety、SIEM syslog、按 key 限模型，都挂在代理上。
- 容器可移植。ADR 写过以后迁 AWS 也能原样跑——对一所已经一只脚踩在 Bedrock 上的学校，这不是空话。

它的弊，也必须说满，否则这篇文章只是厂商小册子：

- **你拥有这台代理。** 镜像升级、Postgres、Redis、salt/master key、发版回滚，都是值班面。APIM 是 PaaS，少一块应用运维。
- **多一个跳，而且是单点控制面。** LiteLLM 挂了，所有模型入口一起挂。OWUI 还活着，只是后面没有脑。
- **企业能力绑许可。** Admin SSO 要 `LITELLM_LICENSE`。
- **salt key 是最高危运维物件。** `LITELLM_SALT_KEY` 丢了，库里加密的虚拟 key 解不开。APIM 订阅密钥没有这个死法。
- 安全团队仍可能问「要不要再套一层 APIM」。ADR 的 Next Steps 把这句留着，没有假装已经说服所有人。

面试拿分点：别背「LiteLLM 功能多」。要能说——学校要的是 **LLM 经济与多供应商控制面**，APIM 管 REST 很强，管「这个 key 这个月还能花多少美元」很弱。

> 选代理，是因为钱的单位是 token；选拆分，是因为钱的变更频率高于聊天框。

## 4. 四层栈：目录在执行信息隐藏

仓库不是 LiteLLM 或 Open WebUI 的应用源码仓。邻仓在这里应当只读。本仓是 Azure 部署的真相源：Bicep、环境参数、模型 YAML、Actions、运维剧本。

| 栈 | 路径 | 藏起来的细节 | 高频变更 |
|---|---|---|---|
| network | `src/network/` | 已有 VNet / 子网 / NSG / UDR | 几乎不该动；Bicep 是文档化复刻 |
| ai-platform | `src/ai-platform/` | CAE、Log Analytics、App Insights、Storage、Key Vault、Action Group | 告警接收人、共享底座 SKU |
| litellm | `src/litellm/` | 代理、用量库、`LiteLLM_CL`、Bedrock、Content Safety | 模型列表、许可、镜像 `-stable` |
| openwebui | `src/openwebui/` | 聊天、pgvector、文件、清理 Job、SSO | UI 版本、留存、上传体验 |

命名一眼能读环境：`{sbx\|npd\|prd}-auea-opui-...`。`auea` 是 Australia East，`opui` 是这族工作负载。生产 VNet 甚至不在应用资源组里，而在 `prd-auea-infra-openai-vnet-01`。网络栈的 README 自己承认：网络是手工建的，Bicep 是为了把子网写下来。

Open WebUI 还有一行不会说谎的注释：

```bicep
activeRevisionsMode: 'Single' // Change this from 'Multiple' to support sticky sessions
```

他们从 Multiple **改回** Single，因为 WebSocket / 粘性会话。单修订的代价是：没有百分比切流。发版等于新修订替换旧修订。有状态容器在 `reusable-deploy.yaml` 里会先 deactivate，睡 90 秒，再部署——防的是双写。这不是 Azure 的默认浪漫，是聊天产品用 Redis 会话之后的对称性破缺。

清理 Job 每天 17:00 UTC（悉尼 03:00 / 04:00）跑，默认清 90 天闲置数据和孤儿文件。知道这件事，比会背资源名更像 SME：有人会在周一早上说「我上周五的知识库没了」。

> 拆目录，是为了让两种时钟不要共用一个发条。

## 合成：三张地图

| 地图 | 问题 | 答案 |
|---|---|---|
| 请求地图 | 用户点发送之后？ | 浏览器 → OWUI →（内部）LiteLLM → Azure 或 Bedrock → 账本 + 聊天库 |
| 购买地图 | 预算该打给谁？ | 控制面（代理 + 身份 + 日志），不是聊天皮肤 |
| 变更地图 | 这次 PR 该碰哪？ | 模型/钱 → `src/litellm`；体验/文件 → `src/openwebui`；告警邮箱 → `src/ai-platform` |

另一所大学、另一家公司，可以不用 Azure Container Apps，甚至可以不用 Open WebUI。不该省的是这三张地图。省掉之后，你会得到一个很会聊天的 demo，以及一封财务部在季度末发来的、没有发送人的账单。

## 立刻可以做的事

1. 打开你现在的「AI 聊天」部署，搜 `OPENAI_API_BASE` 或等价项。如果它指向 Azure OpenAI 的公网 endpoint，你还没有网关，只有一个客户端。
2. 问财务：能否按**人**或按**团队**说出上月的美元数。说不出，就还在 APIM 限流或供应商控制台里假装有 charge-back。
3. 把模型列表的 Git 路径和 UI 发版的 Git 路径拆开。即使今天还是同一个 repo，也先拆目录和 workflow。
4. 写下 salt/master key 的保管人。写不出名字的，等价于还没上生产。

下一篇写搬迁：哪些约束该抄（OIDC、what-if、单修订、数据驻留），哪些资源名抄了会当场出丑。

*毂是空的。空不是缺陷，是让辐条能工作的那一层。*
