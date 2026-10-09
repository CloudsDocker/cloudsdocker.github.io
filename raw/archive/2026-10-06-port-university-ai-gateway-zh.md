---
title: 别抄资源名，抄约束：把大学 AI 网关搬到下一所学校
header:
    image: /assets/images/hd_kubenetes_bamboo_deployment.png
date: 2026-10-06
tags:
 - azure
 - github-actions
 - llm
 - devops
 - security
permalink: /blogs/tech/zh/port-university-ai-gateway
lang: zh
layout: single
category: tech
---

> 颂其诗，读其书，不知其人可乎？是以论其世也。 — 《孟子·万章下》

# 别抄资源名，抄约束

*ChatMQ 能教你的不是 `prd-auea-opui-rg-01`。是一所大学为什么必须 sandbox → non-prod → 人工闸 prod。*

上一篇把毂讲清楚了：聊天框是辐条，LiteLLM 是空心。这篇给平台工程师——你被叫去「我们也搞一套 ChatGPT」。手指会去复制资源名。那是最贵的抄法。

孟子说读诗要论世。Macquarie 的「世」是：Australia East、Entra、已有 OpenAI VNet、师生对话可能成为教育记录、财务要按团队算钱。你的「世」只要有一条不同——数据必须出欧盟、没有 ExpressRoute、模型只许 Azure——抄来的 Bicep 会在 what-if 里看起来很绿，在第一周值班里很红。

读完你该能：

- 画出三环境状态机：PR 只 what-if，合入后 sandbox → dev，prod 要 GitHub Environment 批准。
- 分清 **break-glass**（合法碰用户数据）和 **ops**（回滚、轮换、扩容），混用是合规事故。
- 带着一份「抄 / 改编 / 扔掉」清单走进另一所学校的架构会，而不是带着一份资源名对照表。

## 1. 发版状态机，比资源名更值得抄

`CONTRIBUTING.md` 有一句别人容易跳过的话：Pull Request **不会**改 sandbox、dev、prod。what-if 只显示差异。合入之后 Actions 才部署，sandbox 先，然后 dev，prod 要人工批准。

LiteLLM 的 workflow 把这句话写成了代码：

```yaml
# .github/workflows/litellm.yaml（结构，不是全文）
on:
  pull_request: { paths: [src/litellm/**, ...] }
  push:         { paths: [src/litellm/**, ...] }

sandbox:  # 仅 PR
  operation: whatIf | create   # PR 上是 whatIf
dev:
  operation: whatIf | create
dev-test:                     # 仅合入后
  playwright against the new LiteLLM URL
prod:
  needs: dev-test
  if: push && main
  environment: prod           # 这里有人工闸
```

身份是 OIDC，不是长期服务主体密码：

```yaml
permissions:
  id-token: write
  contents: read
# azure/login
#   client-id / tenant-id / subscription-id 来自 GitHub Environment 的 vars
```

本地验证和云验证不是同一把尺子。`make validate` 比的是 Bicep snapshot；`make *-what-if` 问的是 Azure 里会不会真变；`make local` 只证明 docker compose 还能聊。把 snapshot 当部署，或把 what-if 当测试，都是在用错尺子。

有状态容器还有一段容易被当成「神秘 sleep」的脚本：部署前 deactivate 当前修订，`sleep 90`，再跑 Bicep。60 秒给优雅退出，多 30 秒缓冲。单修订加上 Redis 会话，不能两份修订同时写。抄这套到 Kubernetes 时，不要翻译成「我们也 sleep 90」——要翻译成 **有状态控制面禁止双活**。实现可以是 Job、可以是 PDB、可以是明确的 drain。数字不是约束，禁止双活才是。

| 抄这个 | 别抄这个 |
|---|---|
| PR = 只读差异；prod = 人工闸 | `prd-auea-opui-rg-01` 这种前缀 |
| 三个 GitHub Environment，secret 按环境隔离 | 把 sandbox 密钥复用到 prod |
| 模型变更走 LiteLLM workflow，UI 变更走 OWUI workflow | 一个 mega-pipeline 部署全世界 |
| 镜像先改 `local/docker-compose-*.yaml` 再改 Bicep | 直接在 prod 参数里改 tag |

模型上架也是状态机：`make update-models-from-azure` 写 YAML，Actions 先让 sandbox 看见，non-prod 再看见，prod 批准后才全校可用。他们关掉 LiteLLM 的 wildcard discovery，注释里写着和 Richard 聊过、为了更好的控制。另一所学校如果打开通配符，等于让 Azure 控制台里的一次误部署，立刻变成全校模型列表。那是产品决策，不是 YAML 口味。

> what-if 是意见。create 是事实。中间那道人闸，是你愿意为事实付的钱。

## 2. 身份、密钥、那把不能丢的盐

每个应用一块 User-assigned MI。Key Vault 用 access policy 读 secret。LiteLLM 的 MI 还要当 Cognitive Services User 去打 Azure OpenAI，并往自定义日志表送数。GitHub 只持有 OIDC 和 Environment secret；容器启动时从 KV 拉。

Azure 模型走托管身份，Bedrock 走 access key——`litellm-config.prod.yaml` 文件头就写了。这是多云的不对称：微软侧可以消灭静态 key，AWS 侧还没有在这套设计里消灭。搬到下一所学校时，先问安全团队能否接受「半边没有长期密钥」。不能接受，就要在 Bedrock 前加一层你们自己的凭证代理，或先不上 Claude。

盐是这套设计里最不像「配置」的配置。LiteLLM 用 `LITELLM_SALT_KEY` 加密库存里的虚拟 key。master key 丢了，你还能转紧急签发；salt 丢了，历史 key 是一堆解不开的字节。备份 salt 的流程要写成两人、离线、定期演练，不要写在和 `WEBUI_SECRET_KEY` 同一段「记得放进 KV」里。

另一所学校常见的三种错法：

| 错法 | 看起来省事 | 实际账单 |
|---|---|---|
| 一个 MI 打天下 | 少写 role assignment | 清理 Job 和聊天 UI 权限搅在一起，blast radius 变成整仓 |
| secret 写在 `.bicepparam` | what-if 好看 | 参数和 Bicep 都会进 Git；URL 一旦提交就是永久历史 |
| 用 API key 打 Azure OpenAI | 本地 docker 最顺 | 轮换时要碰每个消费者；MI 把轮换从「改密钥」变成「改角色」 |

防火墙里的 Postgres 和 Storage 不能从笔记本直接连。仓里有 `docs/connecting-to-firewalled-services.md`：临时加规则，用完拆掉。把「我的 IP 常驻白名单」当成开发体验，等于把 break-glass 做成了默认路由。

> 密钥轮换是运维。盐的保管是业务连续性。两件事不要放进同一张 runbook 的同一行。

## 3. 数据住哪、谁能看、灾难时先救谁

把落点写成一张表，架构会才不会被「我们加密了」三个字结束：

| 东西 | 住哪 | 多久 | 谁能碰 |
|---|---|---|---|
| 聊天正文 / 历史 | OWUI Postgres（Australia East） | 直到用户删或清理 Job（默认 90 天闲置） | 应用 + 合法 break-glass |
| 上传原文件 | Azure Storage | 同上；孤儿文件一并清 | 同上 |
| RAG 向量 | 同一套 OWUI Postgres 的 pgvector | 同上 | 同上 |
| Prompt 全文（遥测） | Log Analytics `LiteLLM_CL` | 约 60 天 | 表级 RBAC，不是工作区大门钥匙 |
| 用量元数据（token、美元、邮箱） | LiteLLM Postgres | 长期 | 财务/平台；注意 SpendLogs 里正文可能是空的 |
| 会话 | Redis | 活着的会话 | 不是归档 |

生产磁盘也是约束：OWUI Postgres P6 / 32 GiB，LiteLLM P6 / 64 GiB；sandbox/dev 默认 P4 / 32。抄 SKU 而不抄告警，等于把「库满」从仪表盘问题变成周一早晨的事故。

Disaster recovery 脚本协调的是 **文件共享快照 + Postgres PITR**，夜间 Job 打点。另一所学校如果只有磁盘备份、没有文件快照，RAG 会恢复成「库在、文件不在」——向量指向幽灵。演练时要故意恢复到「库和文件时间点不一致」，看应用是否会吵。

Break-glass 文档的第一刀最有用：它 **不是** 给回滚、轮换、发版用的。两人、限时（默认 ≤ 2 小时）、只读优先、工单里写法律依据。生产库访问由 CloudOps/数据团队中介。`STORE_PROMPTS_IN_SPEND_LOGS=false` 时，去 LiteLLM spend 表找聊天正文会空手而归——操作者必须事先知道该去 OWUI 库还是 Log Analytics。

数据驻留不要用「我们在 Azure 澳洲」一句打发。Azure OpenAI 用 Standard / Regional PTU 时，提示和回复在客户指定的地理内处理，地理内部仍可能换区。Bedrock Claude 走澳区 cross-region，Sydney 和 Melbourne。法务要的是地图，不是供应商 Logo。你的学校若禁止任何非 Azure 处理，Claude 不是「加一行 model_list」的事，是一次采购决策。

> 备份证明你能回到过去。驻留证明你没有去错地方。审计证明你知道谁去过。三件不是一件。

## 4. 另一所学校的第一周：抄、改编、扔掉

把 ChatMQ 拆成三堆。只搬第一堆，也能开工；把第三堆当圣经，会在命名规范上耗掉一个月。

**抄（约束）**

- 控制面与 UI 分目录、分 workflow、分数据库。
- 三环境，prod 人闸；PR 默认 what-if。
- GitHub OIDC，不用长期 SP 密码。
- 用户身份用头传递进代理，预算打在人上，不是打在「那个聊天容器」。
- 单活会话 / 禁止控制面双写。
- 内容日志有 TTL；用量元数据长期；清理 Job 有明确时钟（他们是 17:00 UTC）。
- 加模型走脚本和渐进环境，不打开 wildcard。
- break-glass 与 ops 分册。

**改编（按你的世）**

- 区域。他们绑 Australia East，因为师生与法务都在这张地图上。欧盟学校可能是一对区域 + 明确禁止 Bedrock。
- 网络。他们的 VNet 是既有资产。你可能要从零画，或必须挂上学校的零信任。`src/network` 是文档，不是「apply 即重建」。
- 前端。Open WebUI 可换。不要把「必须用这个 UI」写进架构原则。
- 计算。ACA Consumption 换成 AKS / ECS，只要保住：内部 DNS、MI/IRSA、单修订或等价 drain。
- 告警接收人写在 **ai-platform 参数** 里，而不是某个英雄的手机。换人是 PR，不是微信。

**扔掉（他们的叶，不是你的根）**

- `prd-auea-opui-*` 整套命名。建自己的 `{env}-{region}-{workload}` 词典，写进 types，不要口语化。
- 他们的 Teams webhook、具体邮箱、订阅 ID。
- 把 syslog relay、SearXNG、Speech、dynamic sessions 当成 MVP。ChatMQ 自己的数据流文档都注明 go-live 时搜索是关掉的。
- APIM Premium「因为企业就该有一层」。先证明 token-美元问题还没被代理解决，再买第二层网关。
- 在生产打开 `STORE_PROMPTS_IN_SPEND_LOGS=true` 只为了「调试方便」。那是把全文从 60 天日志策略，扩成数据库长期存档。

第一周建议只做四件事，按这个顺序，故意不先做 UI 美化：

1. 画出你的三张地图（请求 / 购买 / 变更），让安全、财务、教务在同一页上签字。
2. 起一个最小代理：一个模型、OIDC 或临时 MI、按人预算 $N、SpendLogs 不存正文。
3. 再挂一个前端，把 `OPENAI_API_BASE` 指到代理的**内部**地址。
4. 写两页 runbook：salt 丢了怎么办；法务要一份对话怎么办。演练一次空跑。

本地他们用 `make local`：OWUI `:3000`，LiteLLM `:4000/ui`。你也可以从这一对端口开始。但不要把本地 Jupyter 代码解释器当成生产形状——注释写了那是 local only。

容量方面，先抄告警再抄 SKU。CPU/内存告警在 Postgres 上已经有了；文件上传看 Storage 仪表盘。学校一开学，上传和并发会同时来。SKU 是结果，日历才是原因。

> 知人论世：先论这所学校的「世」，再搬 Macquarie 的「事」。事可改，世不可假装相同。

## 立刻可以做的事

1. 在架构一页纸上写下三个环境的 **GitHub Environment 名** 和谁有 prod 批准权。写不出人名，先别写 Bicep。
2. 列一张「用户数据表」：正文、文件、向量、遥测、元数据。每一格填系统名和 TTL。有空格就还不能上师生。
3. 把 salt key 的保管从「在 KV 里」升级成「两人、离线副本、演练日期」。
4. 下一次模型变更走独立 PR，禁止和 Open WebUI 改版绑在同一个 commit。这是最低成本的信息隐藏。
5. 约一次 30 分钟桌面演练：LiteLLM 镜像坏了、单修订已经全量。回滚命令是什么？谁批准？师生看到什么？

上一篇是毂。这篇是把毂装进另一辆车上时，哪些孔距必须量，哪些轮毂罩可以换。

*资源名是叶。约束是根。叶好看，根决定下一所学校能不能活过第一个学期。*
