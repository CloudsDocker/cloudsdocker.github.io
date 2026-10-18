---
title: 全球顶尖团队如何平衡AI可观测性与成本？
header:
    image: /assets/images/stress-test-concurrency-JPA-entity-random-update.jpg
date: 2026-10-18
tags:
 - ai
 - observability
 - opentelemetry
 - cost-engineering
 - architecture
permalink: /blogs/tech/zh/ai-observability-cost-telemetry-opentelemetry
lang: zh
layout: single
category: tech
---
> “不要把AI当成许愿机，而是要把它当成工作台。” — 《AI是工作台》

# 全球顶尖团队如何平衡AI可观测性与成本？

*在高并发、强监管的企业级生产环境中，构建基于 OpenTelemetry 语义约定、动态级联路由与持续反哺评测体系的工程治理方案。*

如果你的线上多智能体（Agent）系统昨晚因为一次偶发的非收敛死循环，无声无息地在几个小时内烧掉了数千美元的 Token 预算，你能在五分钟内指认出是哪一个业务功能（Feature）、哪一个租户（Tenant）、哪一次工具执行（Tool Call），还是哪一次未受控的 Prompt 版本迭代导致的吗？

在很多团队的例会上，类似的问题往往只能得到一张来自云厂商的聚合账单和几张模糊的调用计数看板。商业顾问刘润曾转述过一个关于微软前 CEO 史蒂夫·鲍尔默（Steve Ballmer）的故事：在微软的高管年度述职中，鲍尔默对业务数据有着近乎苛刻的审视。如果汇报者列出的关键财务或业务数字出现错漏且自己无法自圆其说，述职往往会演变成当场解职的危机。在鲍尔默的逻辑里，如果你连业务运转底层的核心数字都看不清，你根本就不理解自己的系统。数字化不是购买了一套昂贵的监控 SaaS，而是经营者骨子里对数据的敬畏。

面对大语言模型（LLM）与智能体系统，绝大多数研发团队正陷入类似的认知陷阱：他们误以为成本优化是一次性的财务削减，误以为可观测性只是在事后拉几张可视化图表。本文给出的核心承诺是：**读完本文，你将获得一套经过顶级金融与保险级生产验证的完整工程体系——从底层 OpenTelemetry Span 的规范设计、动态级联路由模型，到 PII 深度脱敏与线上失败用例的自收敛反馈回路。**

真正的工程现实是反直觉的：

> 成本优化真正的前提是 eval。没有评估体系,你不敢把模型换小——因为你不知道质量掉了多少。所以我一般先建 eval,成本优化是它的副产品。

> **【案例背景与代称说明 / Enterprise Context Note】**
> 本文探讨的生产级架构与工程实践中，**Aegis**（源自古典神话中的庇护之盾，寓意稳健承保与严密风控）为作者在深度技术特稿中使用的虚构企业代称，指代某世界顶级跨国金融与保险巨擘（Global Tier-1 Carrier / Fortune Global 100）。此举旨在恪守商业隐私与合规边界，同时为读者完整呈现高并发、严监管生产环境下的顶级 AI Native 系统工程实战。

先摆框架，再给手段——技术负责人和核心团队真正看重的是你把成本当工程约束管，不是事后省钱。

---

## 第一步:成本必须可归因

没有归因谈优化都是猜。工程团队必须在接入层与运行时落实四项刚性纪律：

- 每次 tool 调用必须独立为一个 span，强制挂载 input/output token、模型名、真实耗时。
- 成本必须能够精准归到 **feature / 租户 / 用户**三个正交维度，严禁系统只有一个大盘汇总总账单。
- 核心度量指标是 **cost per successful task**，而不是 cost per call。失败的调用同样在真实烧钱，只看单价会严重欺骗自己——多次重试成功的所谓“便宜模型”，其累加成本往往远超一次成功的高单价大模型。
- 在 eval 评测体系中，把 cost 和 latency 当作**一等公民指标**，与准确率（Accuracy）并列对齐。任何 prompt 版本的线上变更，都必须联立观察这三个数字的动态平衡，而不是只盯单一质量分。

---

## 按杠杆大小排序的手段

面对算力成本失控，不同层次的工程手段所带来的杠杆效应有着数量级的差距：

```text
+-------------------------------------------------------------------------+
| 架构层 (收益杠杆: 10 倍，最该首先落地)                                    |
| - 大部分请求根本不该进 agent: 前置意图分类/路由，确定性流程走规则 API      |
| - 砍掉多余的 agent 跳数: 每一跳都是一次全量上下文的重新灌入与重放          |
| - 结果缓存: 对高确定性知识检索、文档特征抽取、分类标签做内容寻址持久化缓存  |
+-------------------------------------------------------------------------+
                                     │
                                     ▼
+-------------------------------------------------------------------------+
| 模型层 (收益杠杆: 3–5 倍)                                               |
| - 分层路由: 小模型做抽取、分类、判路; 旗舰大模型只做最终逻辑推演          |
| - 基于 eval 证明降级安全性: 无严谨评测集守门严禁拍脑袋降配模型            |
| - 结构化输出强约束: 压减非必要输出 token (输出单价远高于输入单价)        |
+-------------------------------------------------------------------------+
                                     │
                                     ▼
+-------------------------------------------------------------------------+
| Token 层 (收益杠杆: 30%–60%)                                            |
| - Prompt caching: 系统前缀字节严格静态不可变，严禁在前缀塞入动态时间戳    |
| - Tool 描述瘦身: 裁撤臃肿 Schema，从 20+ 个工具收敛至 7 个正交工具       |
| - 上下文压缩: 长会话定期 compact，子任务通过 sub-agent 隔离只回传精炼结论 |
| - 检索重排: 严谨 rerank 取 Top-5 高精上下文，胜过粗暴塞入 Top-50 片段     |
+-------------------------------------------------------------------------+
                                     │
                                     ▼
+-------------------------------------------------------------------------+
| 运行层 (工程兜底)                                                       |
| - 离线非实时任务走批处理模式 (Batch API 通常享受半价折扣)                  |
| - 租户与特性级别熔断: 强制设置单任务硬上限，超时超限就地截断             |
| - 流式输出 (Streaming): 改善交互感知延迟，替代盲目的“换更快更贵模型”     |
+-------------------------------------------------------------------------+
```

---

## 防失控的护栏(保险公司会特别在意)

在严监管与强合规场景下，智能体决不能任由其自由循环。单次任务的 **max steps / max tokens / max tool calls** 三个上限必须由底层框架强制锁定，否则一个偶发的非收敛死循环就能在一夜之间烧掉整个季度的财务预算。在此之上，必须配套设置租户级动态限流与预算告警水位线。这不仅是财务合规要求，更是核心系统的可靠性（Reliability）基石。

---

## 一句收尾

> 成本优化真正的前提是 eval。没有评估体系,你不敢把模型换小——因为你不知道质量掉了多少。所以我一般先建 eval,成本优化是它的副产品。

---

# 深入模型级联与动态路由：从架构模式到 Python 实战

在生产级 LLM 系统中，“Small Model First, Large Model When Needed”（小模型优先，复杂任务再升级到大模型）绝不仅仅是一个节省 Token 的编码技巧，而是一个集成了 LLM Routing、Model Cascading 与 Cost Optimization 的系统级架构方案。

其核心哲学非常克制：**不要让最贵的模型处理每一个请求。先用便宜、低延迟的模型或确定性规则判断任务类型、复杂度和风险，再选择最合适的处理路径；只有小模型能力不足或任务复杂时，才升级到大模型。**

### 1. 业界常见的四种架构

- **模式 A：意图分类路由（Intent Classification + Routing）**：常见生产模式。小模型先识别用户意图，再分流到不同处理器：
  - FAQ → RAG + 小模型
  - 复杂推理 → 大模型
  - 计算 → Python / 确定性工具
  - 无关请求 → 拒绝或引导
  该模式最适合保险客服、企业知识助手与 IT Helpdesk。
- **模式 B：模型级联（Model Cascading）**：先由小模型生成答案并进行质量检查；不达标时，再转交大模型重新处理。适合摘要提取、单据抽取与事实问答等具备明确验证逻辑的任务。
- **模式 C：基于复杂度的动态选型（Complexity-Based Routing）**：根据问题复杂度阶梯选择模型：简单问题打给小模型，中等问题分配中型模型，高难推理直通旗舰大模型。适合多步骤长程分析与代码生成平台。
- **模式 D：语义缓存前置（Semantic Cache + Routing）**：请求进入模型前先检索高频相似问题库，命中即返回，未命中才进入路由。适合政策查询与内部高频咨询。

### 2. 真实业界案例：Amazon Bedrock Intelligent Prompt Routing

以 Aegis 面向的云原生生产环境为例，Amazon Bedrock 的 Intelligent Prompt Routing 提供了托管式路由器，可在支持的同系列模型之间依据预测响应质量动态调配流量。

```text
Application
     │
     ▼
Bedrock Prompt Router
     │
     ├── Simple query ──► Smaller model
     │
     └── Complex query ─► More capable model
                              │
                              ▼
                         Final response
```

- **选用托管路由的时机**：希望免运维底层打分网关；模型组合完全落在托管列表内；需要深度融合云端 IAM 审计。
- **坚持自建路由的时机**：路由决策必须深度结合保险险种、理赔免赔额、用户授信等级等业务上下文；某些请求受法律约束必须强制走确定性规则；需要融合实时 RAG 检出率与前序工具报错历史。

在实际工程中，推荐采用混合设计：业务规则控制安全边界，自建/托管路由优化成本，评估系统验证端到端质量。

### 3. 先看一份具体路由配置

在构建 Aegis 保险助手时，路由策略必须声明式外置为配置，严禁硬编码在业务逻辑中：

```yaml
models:
  classifier: ${CLASSIFIER_MODEL}
  small: ${SMALL_MODEL}
  large: ${LARGE_MODEL}
routing:
  rules_first: true
  classifier_timeout_ms: 800
  default_route: large
  intents:
    greeting:
      route: small
    policy_faq:
      route: small
    policy_comparison:
      route: large
    complex_claim_analysis:
      route: large
    calculation:
      route: tool
  escalation:
    on_low_confidence: large
    on_invalid_output: large
    on_small_model_error: large
    on_safety_uncertainty: human_review
  limits:
    max_retries: 1
    max_input_tokens: 12000
    max_output_tokens: 1500
```

三大设计原则：
- **规则优先**：确定性的算式不必先调用 LLM 分类；
- **复杂任务升级**：小模型遇到不确定输入、格式校验失败或异常时，走明确的 fallback；
- **高风险请求隔离治理**：不能因为小模型报出高置信度就越权放行重大理赔核准。

### 4. 可运行思路的 Python 示例：小模型分类，大模型处理复杂任务

```python
import json
import os
import time
from typing import Literal
from openai import OpenAI
from pydantic import BaseModel, Field

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "<YOUR_API_KEY>"))
CLASSIFIER_MODEL = os.environ.get("CLASSIFIER_MODEL", "gpt-4o-mini")
SMALL_MODEL = os.environ.get("SMALL_MODEL", "gpt-4o-mini")
LARGE_MODEL = os.environ.get("LARGE_MODEL", "gpt-4o")


class RouteDecision(BaseModel):
    intent: Literal[
        "greeting",
        "policy_faq",
        "policy_comparison",
        "complex_claim_analysis",
        "calculation",
        "unknown",
    ]
    complexity: Literal["low", "medium", "high"]
    confidence: float = Field(ge=0.0, le=1.0)


def classify_request(question: str) -> RouteDecision:
    """Use a small model to classify the request, not answer it."""
    response = client.chat.completions.create(
        model=CLASSIFIER_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify the user request for an insurance assistant. "
                    "Return JSON only. Do not answer the question. "
                    "Use unknown when the intent is unclear. "
                    "Confidence must reflect classification confidence."
                ),
            },
            {"role": "user", "content": question},
        ],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=100,
    )
    raw = response.choices[0].message.content or "{}"
    return RouteDecision.model_validate_json(raw)


def answer_with_model(model: str, question: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an insurance assistant. "
                    "Do not invent policy terms. "
                    "If policy evidence is missing, say so. "
                    "Do not make binding claim eligibility decisions."
                ),
            },
            {"role": "user", "content": question},
        ],
        temperature=0,
        max_tokens=800,
    )
    return response.choices[0].message.content or ""


def handle_request(question: str) -> dict:
    started = time.perf_counter()
    # Deterministic fast path: avoid classifier calls when possible.
    if question.strip().lower() in {"hi", "hello", "hey"}:
        route = "small"
        reason = "greeting_rule"
        answer = answer_with_model(SMALL_MODEL, question)
    else:
        try:
            decision = classify_request(question)
        except Exception:
            # Fail closed to the more capable model; log the failure.
            decision = None

        if decision is None:
            route = "large"
            reason = "classifier_error"
        elif decision.confidence < 0.80:
            route = "large"
            reason = "low_classifier_confidence"
        elif decision.intent in {
            "policy_comparison",
            "complex_claim_analysis",
            "unknown",
        } or decision.complexity == "high":
            route = "large"
            reason = "complex_or_unknown"
        elif decision.intent == "calculation":
            # In production, dispatch to a validated calculator/tool.
            route = "tool"
            reason = "calculation_intent"
        else:
            route = "small"
            reason = "simple_intent"

        if route == "tool":
            answer = "A validated calculation tool is required."
        elif route == "small":
            answer = answer_with_model(SMALL_MODEL, question)
        else:
            answer = answer_with_model(LARGE_MODEL, question)

    return {
        "answer": answer,
        "route": route,
        "reason": reason,
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
    }


if __name__ == "__main__":
    question = "My laptop was stolen overseas. Can I claim under my travel policy?"
    print(json.dumps(handle_request(question), indent=2))
```

工程注意点：
- 示例中的 `confidence` 仅是小模型自我打分，并不等同于真实准确概率，生产中需依赖人工标注集校准标定阈值。
- 分类器本身具有耗时与开销，若简单问题级联多次反而增加总体延迟。

### 5. 如何计算是否真的省钱？

假设周期内处理 100,000 次请求（基准数值仅用于推导演示）：

| 参数 | 假设设定值 |
|---|---|
| 小模型处理单次请求 | $0.001 |
| 大模型处理单次请求 | $0.020 |
| 分类器处理单次请求 | $0.0002 |
| 实际被路由到大模型的比例 | 20% |

全量使用大模型成本：
$$100{,}000 \times \$0.020 = \$2{,}000$$

分类 + 动态路由成本（80% 走小模型，20% 走大模型）：
$$\begin{aligned}
C &= 100{,}000 \times 0.0002 + 80{,}000 \times 0.001 + 20{,}000 \times 0.020 \\
&= \$20 + \$80 + \$400 = \$500
\end{aligned}$$

基准对比：全量大模型 $\$2{,}000$，路由方案 $\$500$，综合成本降幅达 **75%**（若按原始简单模型估算约为 71%）。最核心的启示是：**路由系统本身的调用与潜在重试开销，必须完整纳入全局财务模型，严禁脱离系统架构单纯对比两家单价。**

### 6. 另一种架构：先回答，再判断是否升级

即 Model Cascading：先由小模型作答，再由强检验器断言质量：

```text
用户问题 ──► 小模型生成答案 ──► 质量验证 ──┬──► (通过) 返回答案
                                          └──► (未通过) 大模型重新处理
```

例如用户询问：“What is the excess on my policy?”
小模型从条款中抽取免赔额，随后由确定性校验器断言：
- 是否定位到了明确的保单条款？
- 金额是否真实出自该条款？
- 币种与适用条件是否对齐？
- 是否存在多个适用的冲突免赔额？

严禁把小模型自我宣称的“我拥有 95% 把握”作为质检合格的充分条件。对于高风险理赔，必须强依赖确定性规则校验与专家复核。

### 7. Lead Engineer 应该如何评估这套路由系统？

技术负责人必须全面盘点以下七个监控维度：

| 核心指标 | 试图回答的工程问题 |
|---|---|
| **Cost per request** | 平均每次真实请求花费多少？ |
| **Escalation rate** | 有多少请求从小模型升级到了大模型？ |
| **Task success rate** | 用户的真实业务意图是否真正达成？ |
| **Quality by route** | 小模型路径是否比大模型更容易产生合规偏差？ |
| **p50 / p95 latency** | 路由逻辑是否显著恶化了用户的交互等待？ |
| **Fallback rate** | 分类器自身超时、输出崩溃强制走兜底的比例是多少？ |
| **Safety violation rate** | 是否发生越权操作、错误条款引用或安全违规？ |

切记规避 Selection Bias：简单请求天然易于处理，不能直接拿小模型路径的胜率与大模型直接对比，必须在同一批基准评测集上进行双盲对照。

### 8. 在日常工程实践中可以这样总结

I would use a combination of rule-based routing, model-based classification and quality-driven escalation. First, I would handle deterministic cases without an LLM where possible. For other requests, a lightweight classifier would identify the intent, complexity and risk level, and route the request to the most cost-effective model that meets the required quality threshold. For tasks where quality can be verified, I would consider a cascading approach: start with a smaller model and escalate when validation fails. For high-risk insurance decisions, however, I would enforce deterministic controls and human approval rather than relying on model confidence alone. I would evaluate the routing policy against a representative dataset, measuring task success, cost per request, p95 latency, escalation rate and safety violations. I would deploy it gradually and continuously monitor quality by route and business risk. The objective is not simply to maximise the percentage of requests handled by a small model. It is to minimise total cost while meeting explicit quality, latency and safety requirements.

---

## 最小心智模型

把一次请求的执行过程想成函数调用栈，**但是把它完整录制下来并打上毫秒级时间轴**。

```text
trace                                  ← 一次完整的请求/会话
└── span: invoke_agent  claims_bot      [0ms ────────────── 4200ms]  父
    ├── span: execute_tool lookup_policy   [40ms ── 160ms]           子
    ├── span: chat  claude-sonnet          [170ms ──────── 2300ms]   子
    └── span: execute_tool calc_excess     [2310ms─2318ms]           子
```

- **Trace** = 整棵调用拓扑树，代表一件完整业务（一次完整的用户提问理赔）。
- **Span** = 树上的一个工作单元节点，代表这件事情中的独立一步。
- 每个 span 必须内嵌 `trace_id`（声明我属于哪棵树）和 `parent_span_id`（声明我的直接父节点是谁）——有了这两个指针，采集器才能将离散在各微服务进程中的数据还原为因果树。

---

## 一个 span 实际装着什么

```json
{
  "name": "execute_tool lookup_policy",
  "trace_id": "4bf92f3577b34da6",
  "span_id":  "00f067aa0ba902b7",
  "parent_span_id": "a3ce929d0e0e4736",
  "start_time": "2026-10-08T01:22:14.120Z",
  "end_time":   "2026-10-08T01:22:14.240Z",
  "status": "OK",
  "attributes": {
    "gen_ai.tool.name": "lookup_policy",
    "app.tenant": "zurich_au",
    "app.feature": "claims_triage"
  }
}
```

**属性是价值的真正所在。** Span 的起止耗时只能粗暴地说明系统“慢了”，而内嵌的属性才能清晰解释“为什么慢、究竟花了多少钱、属于哪一个业务租户”。

---

## 和 log / metric 的区别

| 信号维度 | 试图回答的核心问题 | 呈现形态 |
|---|---|---|
| **Log** | “这一刻具体发生了什么孤立事件” | 一个时间点，一行扁平文本 |
| **Metric** | “大盘宏观趋势水位如何” | 聚合数字，丢弃了个体因果上下文 |
| **Span / Trace** | “**这一次**具体请求里，时间和资金花在哪一步” | 时间区间 + 树状层级拓扑关系 |

典型排障场景对照：
- Metric 报警：P95 延迟升至 8 秒，大盘恶化；
- Log 打印：14:22:14 执行了 lookup_policy；
- **Trace 还原真相：这次慢的 8 秒里，整整 6.2 秒卡在第二次 chat，因为输入 token 是平时的 4 倍，因为前序检索返回了 50 个高维切片而非 5 个。**

只有 Trace 具备解释因果链的能力，这就是它不可被替代的根本理由。

---

## 为什么 agent 特别需要它

传统 Web 请求的链路通常是 3–4 步静态确定的，翻看日志尚可人工拼接。自主 Agent 完全颠覆了这一现状：

- 步数在运行时才动态收敛（可能 3 步结束，也可能震荡 15 步才退出）；
- 同一个工具可能在思维链中被重复唤起多次，日志排布完全相同，无法辨析属于哪一轮思考；
- 资金消耗离散分布在多轮调用中，缺少层级聚合就无法厘清总账；
- 子 Agent 往往分发在独立的异步容器中执行，跨进程日志彻底断裂。

Span 的父子嵌套关系天然解决了这些痛点：完整记录了谁调用了谁、第几次重试、各自耗时与精确花费。

---

## 代码里长什么样

在代码中，Span 表现为一个优雅的上下文管理器，进入时启动计时，退出时自动记录结束时间：

```python
with tracer.start_as_current_span("execute_tool lookup_policy") as span:
    span.set_attribute("gen_ai.tool.name", "lookup_policy")
    result = lookup_policy(policy_id)
    span.set_attribute("app.rows_returned", len(result))
```

`start_as_current_span` 内部的 **current** 是精妙之处：在当前块内开启的新 Span，会自动将其作为父节点完成绑定，开发者完全不需要手动穿透传递父子 ID。

---

## 怎么决定“什么该是一个 span”

工程实用判据：**当这一步发生异常、静默超时或成本过高时，你是否需要在调用链与看板中单独审查它？**

- ✅ 每次 LLM 推理调用（系统中最昂贵、最慢的环节）；
- ✅ 每次外部 Tool 执行（最容易发生权限和网络故障）；
- ✅ 每次知识库 Retrieval 检索（直接决定生成质量）；
- ✅ 整个 Agent 的顶层调度生命周期（作为根 Span 汇总总账）；
- ❌ 纯内存计算的小函数（无外部依赖，增加 Span 只会制造无谓的内存开销与日志噪音）。

---

## 落到你的项目上

许多资深开发者在早期单体项目中使用的“追加写 JSONL（Append-only JSONL）结合内容寻址缓存”，其本质就是手写版的 Span 记录：每一行记录一个交互 Turn，包含耗时、Token 用量与可重放参数。

两者只有两个本质差别：
1. 手写版本没有树状父子拓扑（单进程同步调用不需要）；
2. 手写版本不具备跨网络进程的上下文传播机制（所有状态都在本地进程内）。

在日常架构沟通中可以这样清晰表达：

> “我自己手写过一版 span——每个 turn 一条记录,带时长、token、成本,输入可重放。OTel 在那之上加的是**跨进程的因果关联**和**标准化的属性名**。前者在单进程里没有需求,后者在多团队、多工具链的环境里才值钱。Aegis 两个条件都满足,所以在那边我会直接用 OTel。”

---

## 一、词源与谱系

**“Span”并非 OpenTelemetry 所生造。** 它在 2010 年 Google 发表的 Dapper 论文中被正式定型，OTel 的历史功绩在于将其推向全行业标准。

- **史前期（2002–2007）**：分布式服务拆分后，单机日志失效。学术界先后涌现了 Pinpoint（2002）、微软研究院的 Magpie（2004）以及伯克利的 X-Trace（2007），彼时概念五花八门，被称作 Request Track 或 Task Tree。
- **Dapper（2010）定型**：Google 正式发表 *Dapper, a Large-Scale Distributed Systems Tracing Infrastructure*，确立了 Trace Tree 拓扑、Span 节点概念、Parent-Child 引用、分布式 RPC 上下文传递与采样理论。英文中“span”本意即为“跨度”，精确映射了“一段有开始和结束的工作”。
- **商业 APM 并行割裂（2012–2017）**：Twitter 开源了复刻 Dapper 的 Zipkin；Uber 开源了 Jaeger 并注入 CNCF。同期 Dynatrace 推出 PurePath，AppDynamics 主打 Business Transaction，各家探针互不兼容，行业陷入严重分裂。
- **标准统一之争（2016–2019）**：CNCF 主推的 OpenTracing（定 API 标准）与 Google/MS 主推的 OpenCensus（给具体实现）陷入对立。最终在 2019 年 5 月两者宣布合并为 **OpenTelemetry**，提供 Traces、Metrics、Logs 规范、通用 API 与统一采集器 Collector。
- **配套底层协议**：W3C Trace Context 推动确立了跨 HTTP 传递的标准标头（`traceparent` 与 `tracestate`），彻底夯实了跨系统串联链路的通信地基。

---

## 二、所以 span 到底被谁定义

| 标准解耦分层 | 核心定义方 | 具体规定内容 |
|---|---|---|
| **概念模型** | Dapper (2010) | Span 本质定义、父子拓扑、上下文跨进程传递哲学 |
| **数据模型与 API** | OpenTelemetry | Span 生命周期、字段结构、SDK 导出规范 |
| **跨网络传播格式** | W3C Trace Context | HTTP 标头中 `traceparent` 序列化格式 |
| **线上传输协议** | OTLP (OTel) | Span 在网线上通过 Protobuf 进行 gRPC/HTTP 传输的二进制协议 |
| **语义命名约定** | OTel Semantic Conventions | `http.*`、`db.*` 以及 `gen_ai.*` 属性命名字典 |

OpenTelemetry 终结了专有探针的垄断壁垒，将全行业的指标埋点与传输协议彻底标准化，其价值远超单纯的 SDK 实现。开发者只需插桩一次，后端换成任何平台仅仅是修改导出配置。

---

## 三、现在的行业状态(2026)

**OpenTelemetry 已经彻底告别了“新兴标准”的早期阶段。** 2026 年 5 月 21 日，OpenTelemetry 正式取得 CNCF 毕业状态（Graduated），项目汇聚了全球 1,200 家企业的上万名贡献者。

**行业采用率现状**：
- CNCF 官方年度调查数据显示：**49% 的受访企业已在核心生产中全面运行 OTel，另有 26% 正在评估推进**；
- 在新建云原生工程中，默认采用率已突破 90%；
- 几乎所有主流观测厂商（Datadog、Grafana Tempo、Honeycomb、CloudWatch）均已原生接纳 OTLP 协议，传统 APM 探针壁垒瓦解，竞争重心全面转向下游分析。

**信号成熟度的结构性分层（至关重要）**：

| 信号类型 | 当前成熟度状态 | 生产工程应对策略 |
|---|---|---|
| **Traces** | 成熟稳定，行业事实标准 | 全面压注为底层调用链骨架 |
| **Metrics** | 成熟稳定 | 全面用于用量与费用指标聚合 |
| **Logs** | 稳定推进中 | 逐步接替传统日志打点 |
| **Profiles** | 2026 年 3 月 26 日进入公开 Alpha 阶段 | 暂不适合用于生产级强依赖告警 |
| **GenAI 语义约定** | **全线挂起 Development 状态，无一核心属性 Stable** | **必须在业务代码与 SDK 间封装 Adapter 防腐层** |

核心认知：**核心 Tracing 已经彻底成熟毕业，但 GenAI 语义约定仍处于快速演化的移动靶标阶段。**

---

## 四、日常工作中如何落地应用与向上沟通

在架构评审与管理层汇报中，用清晰的技术判断展示深度：

> "Span 这个概念来自 2010 年 Google 的 Dapper,OTel 把它标准化了。到 2026 年 OTel 已经 CNCF 毕业,大约一半的组织在生产里跑,几乎所有厂商都原生收 OTLP——所以**在仪表化层面它已经没有真正的竞品了**,争论点只剩后端选谁。
>
> 但要分清成熟度:核心的 trace/metric/log 是稳的,**GenAI 的语义约定全部还是 Development 状态,一个 Stable 属性都没有**,而且今年 6 月还从主仓库拆到了独立仓库,就是为了能跑得比核心稳定性门槛更快。
>
> 所以我的做法是:**底层仪表化押 OTel,这是安全的;但 `gen_ai.*` 的属性名不直接写进业务代码,夹一层 adapter。** 稳定的部分照标准来,不稳定的部分留退路——这是我对所有未成熟依赖的默认姿势。"

---

## 一、先讲现状(这本身就是加分项)

截至 2026 年年中，官方 Registry 里的每一个 `gen_ai.*` 属性、Span、Metric 与 Event 依然悬挂着 "Development" 稳定性标签（即早期 experimental）。当前 GenAI Span 上唯一达到 Stable 状态的属性，只有从核心规约继承来的 `error.type`、`server.address` 与 `server.port`。

更关键的架构分水岭是 2026 年 6 月 12 日发布的 v1.42.0：所有 GenAI conventions（包含 OpenAI 专属及 MCP 规范）被正式从主库剥离，独立迁移至 `open-telemetry/semantic-conventions-genai` 仓库，专门以高频周期进行迭代升级。

**在日常工程中这样落地应用：**

> "我会按 OTel GenAI conventions 埋,但我清楚它整套还是 Development 状态,属性名可能无预警变。所以我**不会让业务代码直接写 `gen_ai.*` 字面量**——中间夹一层我们自己的 adapter,spec 变了只改 adapter。这是我对所有未稳定标准的默认做法。"

---

## 二、Span 树长什么样

一次理赔问答的真实 Trace 拓扑呈现如下：

```text
trace: conversation_id=conv_7f3a
└── invoke_agent  claims_assistant                    [4.2s]  $0.031
    ├── execute_tool  lookup_policy                   [120ms]
    ├── execute_tool  search_policy_documents         [340ms]
    │     retrieval.top_score=0.81  retrieval.k=5  retrieval.hits=5
    ├── chat  claude-sonnet-4-6                       [2.1s]
    │     input_tokens=8420  cache_read=6100  output_tokens=310
    ├── execute_tool  calculate_excess                [8ms]
    └── chat  claude-sonnet-4-6  (final)              [1.4s]
          confidence=0.62  grounding_rate=0.93
          → routed_to_human=true  (confidence < 0.7)
```

关键胜负手在**最后一行**：把“分流给人工坐席”直接固化为一个 Span 属性（`routed_to_human=true`），原本静默的用户体验降级就变成了看板上可量化、可告警的明确业务事件。

---

## 三、属性怎么埋(代码样例)

OTel 规范涵盖 `gen_ai.request.model`、`gen_ai.usage.input_tokens` 等核心字段，Metric 侧对应 `gen_ai.client.token.usage` 与 `gen_ai.client.operation.duration`。业务代码通过 Adapter 隔离落地：

```python
from contextlib import contextmanager
from functools import wraps
import hashlib
import os
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer("aegis.claims", "1.0.0")
PROMPT_VERSION = "claims_triage_v2.4"


class GenAIAttrs:
    OPERATION   = "gen_ai.operation.name"
    REQ_MODEL   = "gen_ai.request.model"
    RES_MODEL   = "gen_ai.response.model"
    FINISH      = "gen_ai.response.finish_reasons"
    CONV_ID     = "gen_ai.conversation.id"
    IN_TOKENS   = "gen_ai.usage.input_tokens"
    OUT_TOKENS  = "gen_ai.usage.output_tokens"
    CACHE_READ  = "gen_ai.usage.cache_read.input_tokens"
    TOOL_NAME   = "gen_ai.tool.name"


@contextmanager
def llm_span(model: str, conversation_id: str, *, feature: str, tenant: str):
    span_name = f"chat {model}"
    with tracer.start_as_current_span(span_name) as span:
        span.set_attribute(GenAIAttrs.OPERATION, "chat")
        span.set_attribute(GenAIAttrs.REQ_MODEL, model)
        span.set_attribute(GenAIAttrs.CONV_ID, conversation_id)
        # 注入多维归因属性
        span.set_attribute("app.feature", feature)
        span.set_attribute("app.tenant", tenant)
        span.set_attribute("app.prompt_version", PROMPT_VERSION)
        yield span


def record_usage(span, resp):
    u = resp.usage
    span.set_attribute(GenAIAttrs.IN_TOKENS, u.input_tokens)
    span.set_attribute(GenAIAttrs.OUT_TOKENS, u.output_tokens)
    span.set_attribute(GenAIAttrs.CACHE_READ, getattr(u, "cache_read_input_tokens", 0))
    span.set_attribute(GenAIAttrs.RES_MODEL, resp.model)
    span.set_attribute(GenAIAttrs.FINISH, [resp.stop_reason])
    # 成本在运行时就地计算，严禁事后粗暴使用均价估算
    span.set_attribute("app.cost_usd", price(resp.model, u))
```

> 📌 **本节要点**：必须将 `app.prompt_version` 随 Span 持久化，Prompt 改动而代码未更新是排查线上模型质量突发劣化最核心的线索。

针对新演进出的 `gen_ai.usage.cache_read.input_tokens` 与 `gen_ai.usage.reasoning.output_tokens` 必须独立建账，否则推理模型的账单在财务上永远无法对齐。

### 工具调用的 span

```python
IRREVERSIBLE_TOOLS = {"execute_payout", "modify_policy", "revoke_coverage"}


def hash_args(kwargs_dict):
    return hashlib.sha256(str(sorted(kwargs_dict.items())).encode()).hexdigest()


def traced_tool(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with tracer.start_as_current_span(f"execute_tool {fn.__name__}") as span:
            span.set_attribute(GenAIAttrs.OPERATION, "execute_tool")
            span.set_attribute(GenAIAttrs.TOOL_NAME, fn.__name__)
            span.set_attribute("app.tool.args_hash", hash_args(kwargs))
            try:
                out = fn(*args, **kwargs)
            except Exception as e:
                span.set_attribute("error.type", type(e).__name__)
                span.set_status(Status(StatusCode.ERROR))
                raise
            if fn.__name__ in IRREVERSIBLE_TOOLS:
                span.set_attribute("app.irreversible", True)
            return out
    return wrapper
```

---

## 四、PII 脱敏——在 SDK 层,不是后端

在标准规范中，记录交互明文的 `gen_ai.input.messages`、`gen_ai.output.messages`、`gen_ai.system_instructions` 与 `gen_ai.tool.definitions` 均为 **Opt-In**（默认关闭）。这个默认设置对高度重视客户隐私的金融保险场景是天然适用的。

脱敏必须在客户端 SDK 导出通道内就地完成：

```python
import re
from opentelemetry.sdk.trace.export import BatchSpanProcessor

CAPTURE_CONTENT_ENABLED = os.environ.get("CAPTURE_CONTENT", "false").lower() == "true"
PII_PATTERNS = re.compile(r"(?P<POLICY>[A-Z]{2}\d{7})|(?P<PHONE>\+?\d{10,12})|(?P<EMAIL>[\w\.-]+@[\w\.-]+)")


class RedactingSpanProcessor(BatchSpanProcessor):
    CONTENT_KEYS = {
        "gen_ai.input.messages",
        "gen_ai.output.messages",
        "gen_ai.system_instructions",
    }

    def on_end(self, span):
        if hasattr(span, "_attributes") and span._attributes:
            current_attrs = dict(span._attributes)
            for k in self.CONTENT_KEYS:
                if k in current_attrs:
                    if not CAPTURE_CONTENT_ENABLED:
                        current_attrs.pop(k, None)
                    else:
                        current_attrs[k] = redact(str(current_attrs[k]))
            span._attributes = current_attrs
        super().on_end(span)


def redact(text: str) -> str:
    text = PII_PATTERNS.sub(lambda m: f"<{m.lastgroup}>", text)
    return ner_redact(text)
```

三条安全工程铁律：
1. **默认严禁采集，按需动态开启**：开关基于租户与特性配置，严禁全局硬编码放行；
2. **明文内容走物理独立通道**：短生命周期（TTL 7–30 天）、挂载独立 KMS 密匙、查询行为全流程留痕；
3. **可复现排障不等于留存明文**：依托入参哈希（SHA-256）与 Mock 固件重放复现，无须持久化用户隐私对话。

---

## 五、成本归因:维度设计才是难点

```python
token_counter = meter.create_counter("gen_ai.client.token.usage")
token_counter.add(u.input_tokens, {
    "gen_ai.operation.name": "chat",
    "gen_ai.request.model": model,
    "gen_ai.token.type": "input",
    "app.feature": "claims_triage",
    "app.tenant": tenant_id,
    "app.outcome": "success",
})
```

`app.outcome` 维度的注入是系统的分水岭。有了它才能准确核算 **cost per successful task**，而不是只看单次调用的单价。

```text
[方案 A: 廉价小模型级联重试]
调用 1 (小模型):  花费 $0.001  --> 格式崩溃 (Fail)
调用 2 (小模型):  花费 $0.001  --> 验证失败 (Fail)
调用 3 (升级大模型):花费 $0.020  --> 成功生成 (Success)
----------------------------------------------------
该任务总耗费: $0.022 | 累计耗时: 6.8s | 体感: 极差

[方案 B: 旗舰模型直出]
调用 1 (大模型):  花费 $0.020  --> 一次成功完成 (Success)
----------------------------------------------------
该任务总耗费: $0.020 | 累计耗时: 1.8s | 体感: 优秀
```

只看单次调用价格，方案 A 的单次名义均价只有 $\$0.0073$，但按有效任务统计，方案 A 不仅费用超额，还严重吞噬了并发吞吐。团队必须固化三张核心分析表：**按业务特性（哪个 Feature 烧钱）、按租户（哪个客户在倒贴）、按最终结局（多少预算浪费在失败路径上）**。

---

## 六、工具路线取舍

| 选型路线 | 适合场景 | 关键妥协与代价 |
|---|---|---|
| **纯 OTel + 现有 APM** (Datadog / Grafana Tempo / CloudWatch) | 已有成熟 APM 投资、需要与上下游服务共享同一条 Trace、对数据主权具有极高审计诉求 | 缺乏开箱即用的交互式 Eval、标注工作台与 Prompt 版本演进视图，需自行拼接 |
| **Langfuse** | 追求 Trace、Eval 与 Prompt 版本管理一体化，且具备**完全自托管能力** | 协议兼容 OTel 但专属插件生态略窄于纯开源社区 |
| **LangSmith** | 深度依托 LangChain / LangGraph 技术栈，追求极速接入 | 与专有框架绑定极深，企业级私有化成本门槛极高 |
| **Arize / Phoenix** | 算法与 ML 实验主导团队，关注 Embedding 空间漂移与实验对比 | 偏向模型分析，针对后端分布式工程调用链排障偏弱 |
| **云原生 Bedrock / Vertex 托管套件** | 全栈部署在对应云端、需要与 IAM/VPC 边界深度集成、追求极简合规交付 | 严重受限于云厂商围墙内，跨多云视界缺失，复杂 Agent 评测能力偏弱 |

**推荐的企业级双层设计**：

> 底层仪表化必须完全基于中立的 OpenTelemetry 标准构建，确保业务代码绝不绑定任何专有监控供应商的 SDK。通过 OTLP 协议将遥测流推送至网关 Collector，随后分流派发：一条流推向企业级现有 APM 保证全局排障一致性；另一条流清洗后投递至 AI 原生治理平台（如自托管的 Langfuse）进行微调分析与版本管理。

---

## 七、让 trace 变成闭环(满分收尾)

监控看板绝不是可观测性的终点，其最高价值在于**将线上失败请求自动化反哺为评测测试集**：

```python
def on_span_end(span):
    if (span.attr("app.human_override")
        or span.attr("app.confidence", 1.0) < 0.7
        or span.attr("app.constraint_violation")):
        enqueue_eval_candidate(
            trace_id=span.trace_id,
            reason=classify(span),
            fixtures=record_tool_responses(span),
        )
```

> “我判断一套可观测体系是不是真的在工作,只看一件事:**线上的失败有没有自动变成 eval case。** 没有这条回流,看板只是让人心安,eval 集三个月后就脱离现实了。”

---

## 八、挑战问答

**Q: 全量采样成本受得了吗?**

> 答：推行分层。**span 元数据全量**（便宜，仅包含指标与字符串）；**交互明文内容默认不采**；**出错、低置信度、人工推翻的 100% 保留**，正常成功流量按 1%–5% 低频抽样。核心依赖**尾部采样（Tail-based Sampling）**：在 Trace 结束时根据结局状态决定留存策略，否则无法捕捉劣质样本。

**Q: 多 agent 的 trace 怎么关联?**

> 答：这正是放弃单机日志转投 OTel 的核心刚需——跨网络进程的上下文传播（Context Propagation）。业务侧依托 `gen_ai.conversation.id` 维持长程会话追踪，技术侧依托 W3C 协议的 `trace_id` 维持因果拓扑。针对 MCP 工具层，官方语义约定已同步迁移，可无缝天然承接。

**Q: 你在 ConvFinQA 里明确说不要 OTel,现在又说要?**

> 答：“那个决定在那个架构里是对的:单进程同步调用,因果链已经完整落盘在内容寻址缓存和 append-only JSONL 里。我当时写了明确的触发条件——**因果一旦跨出进程**就该上。Aegis 要建的就是那种系统,所以我会从第一天埋。我拒绝的是在不需要的地方加运维面,不是拒绝可观测性。”

**Q: spec 不稳定,现在埋了以后不是白埋?**

> 答：“所以要 adapter 层。而且即使属性名变了,**span 的结构和维度设计不会变**——哪些操作值得一个 span、成本归到哪些维度、内容记不记,这些才是真正的设计决策,属性名只是绑定。”

**Q: 怎么证明可观测性是值得的投入?**

> 答：用 **MTTD**（静默退化的平均发现时间）当目标指标，再做一次演习验证它：故意在预发环境中降级检索相似度或换用低配模型，观察监控看板与评估系统多久能自主抓获异常。**能被演习验证的可观测性，才是真正的企业级护城河。**

---

## 升维法则：系统的可观测性是业务健康度的镜子

从最初史蒂夫·鲍尔默对业务报表数字的严厉审视，到如今企业级 AI 架构中对每个 Token 与 Span 的精准归因，这背后贯穿着同一条跨越时代的软件工程法则：

> **第一原则：隐式成本显性化（Make Implicit Costs Explicit at the Interface）**
> 
> **机制机理**：任何在系统调用接口上未被清晰度量与归因的外部资源消耗（无论是算力、网络带宽还是模型 Token），都会不可避免地在组织协作的盲区中发生公地悲剧式滥用。开发者倾向于无节制地堆砌 Prompt 长度与重试跳数，直到财务账单或延迟熔断引发崩溃。只有将每一次调用的具体成本、成败归属以强约束的元数据显式暴露在每一次请求的返回与追踪中，工程优化才会自发产生。
> 
> **边界条件**：该原则仅适用于资源消耗与计算链路解耦的非确定性系统。在传统的确定性纯内存算法中，过度追踪微秒级损耗本身所带来的 CPU 开销，反而会侵蚀核心业务吞吐。
> 
> > 举一反三：审视你的系统，每一次下游外部依赖调用（第三方接口、数据库连接池、大模型算力），其真实消耗是否都能在五分钟内追溯到具体的业务功能与发起主体？如果不能，治理必须从为它打上归属标签开始。

在你的真实系统里，今天是否有一次失败的线上请求，正静悄悄地等待着成为你明天测试集里的全新用例？
