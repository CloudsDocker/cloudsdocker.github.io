---
layout: post
title: "The Silent Cost of AI: Observability, Cost Control, and Production Telemetry in Enterprise Systems"
tags: ["AI", "Enterprise", "Engineering", "Observability", "OpenTelemetry"]
---

*We measure what we value, and we value what we measure. In the silent expanse of artificial intelligence, an unobserved failure is not merely a technical glitch—it is a quiet erosion of truth.*

---

先摆框架,再给手段——老板和团队真正看重的是你把成本当工程约束管,不是事后省钱。

## 第一步:成本必须可归因

没有归因谈优化都是猜。我会做的:

- 每次 tool 调用一个 span,带 input/output token、模型名、耗时
- 成本归到 **feature / 租户 / 用户**三个维度,不是只有一个总账单
- 核心指标是 **cost per successful task**,不是 cost per call。失败的调用也烧钱,只看单价会骗自己——重试三次成功的"便宜模型",往往比一次成功的贵模型更贵。
- eval 里把 cost 和 latency 当**一等公民指标**,和准确率并列。任何 prompt 改动都要看三个数,不是一个。

## 按杠杆大小排序的手段

**架构层(省 10 倍,最该先做)**
- 大部分请求根本不该进 agent。前面挂一个分类/路由,常见意图走确定性流程,agent 只接长尾。
- 砍掉多余的 agent 跳数——每一跳都是一次完整上下文重放。
- 能缓存的结果别反复推理(检索结果、文档抽取、分类标签)。

**模型层(省 3–5 倍)**
- 分层路由:小模型做分类/抽取/判路,大模型只做最终推理。
- 用 eval 证明降级是安全的,而不是拍脑袋换模型。**这一步没有 eval 就不能做**——这正好把成本话题接回他们最关心的地方。
- 结构化输出 + 明确的长度约束,压输出 token(输出比输入贵得多)。

**Token 层(省 30–60%)**
- **Prompt caching**:系统提示、工具定义、常驻文档放在前缀且保持字节稳定——很多人无意中在前缀里塞了时间戳,缓存全废。
- Tool 描述瘦身。20 个工具的 schema 每轮都在重放,裁到 7 个正交的工具,省钱还提准确率。
- 上下文压缩:长对话定期 compact,子任务用 sub-agent 隔离,只回传结论。
- 检索给得准比给得多重要——reranking 后取 top-5,胜过塞 top-50。

**运行层**
- 非实时的走 batch(通常半价)。
- 每个 feature、每个租户设硬性 token 上限和循环步数上限;超限熔断而不是任其跑。
- 流式输出改善感知延迟,不省钱但常被拿来替代"换更快的模型"。

## 防失控的护栏(保险公司会特别在意)

单次任务的 **max steps / max tokens / max tool calls** 三个上限必须有,否则一个循环就能在一夜之间烧掉预算。再加预算告警和按租户限流。这是 reliability 问题,不只是财务问题。

## 一句收尾

> "成本优化真正的前提是 eval。没有评估体系,你不敢把模型换小——因为你不知道质量掉了多少。所以我一般先建 eval,成本优化是它的副产品。"

# Use different models for cost control
你问的是生产级 LLM 系统里非常重要的一种架构：Small Model First, Large Model When Needed（小模型优先，复杂任务再升级到大模型）。

作为 Lead AI Engineer，在日常系统架构演进中，这不只是一个节省 token 的技巧，而是一个完整的 LLM Routing、Model Cascading 和 Cost Optimization 设计问题。

核心思路是：

不要让最贵的模型处理每一个请求。先用便宜、低延迟的模型或确定性规则判断任务类型、复杂度和风险，再选择最合适的处理路径；只有小模型能力不足或任务复杂时，才升级到大模型。

1. 业界常见的四种架构

模式 A：Intent Classification + Routing

常见生产模式

小模型先识别用户意图，再路由到不同处理器。

```flowchart
* FAQ → RAG + 小模型
* 复杂推理 → 大模型
* 计算 → Python / 确定性工具
* 无关请求 → 拒绝或引导
```

适合保险客服、企业知识助手、IT Helpdesk。

模式 B：Model Cascading（模型级联）

先由小模型生成答案并进行质量检查；不达标时，再交给大模型。

```flowchart
Small model
    ↓
Quality check
  ↙       ↘
Pass      Fail
 ↓          ↓
Return   Large model
```

适合摘要、文本提取、简单问答等可验证任务。

模式 C：Complexity-Based Routing

根据问题复杂度选择模型，而不是所有请求都走同一条链路。

* 简单：小模型
* 中等：中型模型
* 困难：大模型

适合多步骤分析、代码助手和企业 AI 平台。

模式 D：Semantic Cache + Routing

先检查是否已有可信的相似请求结果，再决定是否调用模型。

```flowchart
Request
    ↓
Cache lookup
 ↙       ↘
Hit      Miss
 ↓         ↓
Return    Router
```

适合高重复率的 FAQ、政策查询和内部知识问答。

注意：这里的“业界常见”指常用的生产架构模式，并不意味着每家企业都采用完全相同的实现。具体模型、阈值和成本收益必须通过实际流量评估。

2. 真实业界例子：the cloud provider Bedrock Intelligent Prompt Routing

对 a leading global company 这种 the cloud provider 企业环境，最值得了解的是 Amazon Bedrock 的 Intelligent Prompt Routing。

the cloud provider 提供托管式路由器，可以在受支持的同系列模型之间，根据请求预测的响应质量进行动态路由，以平衡质量和成本。官方文档列出了支持的模型和区域；实际部署前应确认目标区域及模型组合。

架构大致是：

```flowchart
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

什么时候用托管路由？

* 希望少维护一套自建的模型选择逻辑。
* 模型组合符合 Bedrock 的支持范围。
* 希望统一管理模型调用、追踪和成本。

什么时候自建路由？

* 路由规则需要考虑保险产品、用户权限、业务风险。
* 某些请求必须走特定模型或确定性业务规则。
* 需要结合 RAG 质量、工具调用成功率、历史评估结果决定是否升级。

在保险场景中，我会采用混合方案：业务规则控制安全边界，模型路由优化成本，评估系统验证质量。

3. 先看一份具体路由配置

假设你在开发 a leading global company 保险助手。路由策略可以先写成配置，而不是把模型名称和阈值散落在代码里。

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

这份 YAML 是一个自定义应用层配置示例，不是 the cloud provider Bedrock 的原生配置格式。模型名通过环境变量注入，方便在开发、测试和生产环境分别配置。

这里有三个设计原则：

* 规则优先：例如确定性的计算不必先调用 LLM 分类。
* 复杂任务升级：小模型不确定、输出格式错误或发生异常时，进入明确的 fallback 路径。
* 高风险请求单独治理：不能因为小模型给出高置信度，就绕过保险理赔权限或人工审批。

4. 可运行思路的 Python 示例：小模型分类，大模型处理复杂任务

下面用 Python + OpenAI SDK 展示自建路由的核心实现。代码通过环境变量指定模型，因此你可以替换为当前账号有权限访问的模型。

先安装依赖：

pip install openai

设置环境变量：

export OPENAI_API_KEY="your-api-key"
export CLASSIFIER_MODEL="your-small-classifier-model"
export SMALL_MODEL="your-small-generation-model"
export LARGE_MODEL="your-large-generation-model"

下面是一个简化但具备实际工程结构的实现：

import json
import os
import time
from typing import Literal
from openai import OpenAI
from pydantic import BaseModel, Field
client = OpenAI()
CLASSIFIER_MODEL = os.environ["CLASSIFIER_MODEL"]
SMALL_MODEL = os.environ["SMALL_MODEL"]
LARGE_MODEL = os.environ["LARGE_MODEL"]
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
    raw = response.choices[0].message.content
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
            # Placeholder: replace with a validated deterministic tool.
            answer = "A validated calculation tool is required."
        elif route == "small":
            answer = answer_with_model(SMALL_MODEL, question)
        else:
            answer = answer_with_model(LARGE_MODEL, question)
    return {
        "answer": answer,
        "route": route,
        "reason": reason,
        "latency_ms": round(
            (time.perf_counter() - started) * 1000, 1
        ),
    }
if __name__ == "__main__":
    question = (
        "My laptop was stolen overseas. "
        "Can I claim under my travel policy?"
    )
    print(json.dumps(handle_request(question), indent=2))

这段代码在做什么？

阶段	目的
规则快速通道	简单、确定的请求不必额外调用分类模型
小模型分类	识别意图、复杂度和分类置信度
路由决策	根据意图、复杂度和置信度选择路径
模型执行	简单请求走小模型，复杂请求走大模型
延迟记录	为后续的成本和性能分析提供基础

需要注意两个生产问题：

* 示例中的 confidence 是分类模型自己报告的数值，并不天然等于真实正确概率。需要用标注数据做校准，确定阈值。
* 示例只是展示路由机制；真正的保险 RAG 助手还必须将正确的保单版本、检索证据和用户权限传入回答流程，并对关键事实、拒答和工具执行做独立验证。

另外，分类器调用本身也有成本和延迟。若每个请求都先调用小模型，再调用大模型，成本可能反而增加。

5. 如何计算是否真的省钱？

假设有 100,000 次请求，下面的价格仅用于演示计算，不代表任何模型的实际报价。

参数	假设值
小模型处理一次请求	$0.001
大模型处理一次请求	$0.020
分类器处理一次请求	$0.0002
被路由到大模型的比例	20%

全部使用大模型

100{,}000 \times \$0.020 = \$2{,}000

使用小模型分类 + 动态路由

假设 80% 的请求走小模型，20% 走大模型：

\begin{aligned}
C &= 100{,}000 \times 0.0002\\
&+80{,}000 \times 0.001\\
&+20{,}000 \times 0.020\\
&=\$580
\end{aligned}

全部使用大模型

$2,000

分类 + 路由

$580

示例成本降幅

71%

这是基于假设单价和路由比例的数学示例。真实成本还取决于输入/输出 token、重试、缓存命中、工具调用和分类错误后的升级处理。

这里最重要的不是 71% 这个数字，而是：路由系统本身必须进入成本模型。 不能只比较小模型与大模型的单次调用价格。

6. 另一种架构：先回答，再判断是否升级

上面的方案是 Classification-based Routing：先分类，再决定使用哪个模型。

另一种方案是 Model Cascading：先让小模型回答，然后判断这个答案是否足够好。

```flowchart
用户问题
    │
    ▼
小模型生成答案
    │
    ▼
质量验证
    │
    ├── 通过 ─────► 返回答案
    │
    └── 未通过 ──► 大模型重新处理
```

例如，用户问：

“What is the excess on my policy?”

小模型从检索到的保单条款中提取 excess，随后由确定性校验器检查：

* 是否找到了适用的保单条款？
* 金额是否来自该条款？
* 币种和适用条件是否一致？
* 是否存在多个适用的 excess？

如果答案不完整，可以升级给大模型重新分析。

但是，不要把小模型自己说的“我有 95% 信心”当成质量验证通过的充分条件。最好使用可验证的证据、结构化规则、独立评估器或人工审核。

对高风险理赔判断，我不会先让小模型做出决定，再用置信度决定是否升级；我会先执行权限、规则和风险检查，必要时直接走受控流程。

7. Lead Engineer 应该如何评估这套路由系统？

只看成本是不够的。至少要监控以下指标：

指标	要回答的问题
Cost per request	平均每次请求花多少钱？
Escalation rate	有多少请求升级到大模型？
Task success rate	用户的任务是否真正完成？
Quality by route	小模型路径是否比大模型路径更容易出错？
p50 / p95 latency	路由是否增加了用户等待时间？
Fallback rate	分类失败、超时或质量不合格的比例是多少？
Safety violation rate	是否发生越权、错误政策引用或不安全操作？

特别要注意 selection bias：简单请求本来就容易处理，因此不能只拿小模型路径的准确率和大模型路径直接比较。应该在同一批代表性问题上进行对照测试，验证路由策略是否在维持质量的同时降低成本。

建议采用以下上线流程：

* 用历史请求建立标注数据集。
* 比较全量大模型与路由方案的成本、质量和延迟。
* 先以 shadow mode 运行路由，不改变用户实际收到的答案。
* 通过离线评估和小流量 canary 验证后，再逐步扩大流量。
* 监控分业务类型、风险等级和模型版本的表现，质量退化时回滚。

8. 在日常工程实践中可以这样总结

I would use a combination of rule-based routing, model-based classification and quality-driven escalation.

First, I would handle deterministic cases without an LLM where possible. For other requests, a lightweight classifier would identify the intent, complexity and risk level, and route the request to the most cost-effective model that meets the required quality threshold.

For tasks where quality can be verified, I would consider a cascading approach: start with a smaller model and escalate when validation fails. For high-risk insurance decisions, however, I would enforce deterministic controls and human approval rather than relying on model confidence alone.

I would evaluate the routing policy against a representative dataset, measuring task success, cost per request, p95 latency, escalation rate and safety violations. I would deploy it gradually and continuously monitor quality by route and business risk.

The objective is not simply to maximise the percentage of requests handled by a small model. It is to minimise total cost while meeting explicit quality, latency and safety requirements.

最后，如果你要在 a leading global company 的 the cloud provider 环境中真正落地，我建议先深入两个方向：

* Amazon Bedrock Intelligent Prompt Routing：了解托管式模型路由、fallback 和配置限制。官方文档：Intelligent Prompt Routing⁠。
* 自建 Python Router：掌握分类器、路由策略、模型调用、质量门禁、可观测性与成本核算。这样你才能解释什么时候应该用托管服务，什么时候值得自建。

---

这块是你唯一真正的缺口,所以给足细节。先确立一个展现深厚架构底蕴的专业判断——**因为这个 spec 现在还不稳定,而大多数候选人不知道。**

## 一、先讲现状(这本身就是加分项)

截至 2026 年年中,官方 registry 里每一个 `gen_ai.*` 属性、span、metric、event 都还挂着 "Development" 稳定性标记(也就是以前的 experimental)。一个 GenAI span 上唯一 Stable 的属性是 `error.type`、`server.address`、`server.port`,而且这三个是从核心 conventions 继承来的,不是 GenAI 组自己写的。

更重要的结构性变化是 2026 年 6 月 12 日的 v1.42.0:所有 GenAI conventions——包括 OpenAI 专属的和 MCP 的——在主仓库里被废弃,迁到了独立的 `open-telemetry/semantic-conventions-genai`,目的就是让这块能用比核心稳定性门槛更快的节奏迭代。

**在日常工程中这样应用：**

> "我会按 OTel GenAI conventions 埋,但我清楚它整套还是 Development 状态,属性名可能无预警变。所以我**不会让业务代码直接写 `gen_ai.*` 字面量**——中间夹一层我们自己的 adapter,spec 变了只改 adapter。这是我对所有未稳定标准的默认做法。"

这段话的价值不在于知识,在于它展示**你怎么对待不成熟的依赖**。

## 二、Span 树长什么样

一次理赔问答的 trace:

```
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

关键:**最后一行**。把"分流给人"记成一个 span 属性,它就从一个隐形行为变成了可计数、可告警的业务事件。

## 三、属性怎么埋(代码样例)

核心属性包括 `gen_ai.request.model`、`gen_ai.usage.input_tokens`,metric 侧有 `gen_ai.client.token.usage` 和 `gen_ai.client.operation.duration`;span 属性(recommended)还有 `gen_ai.response.model`、`gen_ai.response.finish_reasons`、`gen_ai.conversation.id`。operation 分 `chat`、`execute_tool`、`invoke_agent`、`create_agent`、`embeddings` 几类。

```python
# adapter 层 —— 业务代码不直接碰 gen_ai.* 字面量
class GenAIAttrs:
    OPERATION   = "gen_ai.operation.name"
    REQ_MODEL   = "gen_ai.request.model"
    RES_MODEL   = "gen_ai.response.model"
    FINISH      = "gen_ai.response.finish_reasons"
    CONV_ID     = "gen_ai.conversation.id"
    IN_TOKENS   = "gen_ai.usage.input_tokens" #gitleaks:allow
    OUT_TOKENS  = "gen_ai.usage.output_tokens" #gitleaks:allow
    CACHE_READ  = "gen_ai.usage.cache_read.input_tokens"
    TOOL_NAME   = "gen_ai.tool.name"


@contextmanager
def llm_span(model: str, conversation_id: str, *, feature: str, tenant: str):
    # span 命名约定:"{operation} {model}"
    with tracer.start_as_current_span(f"chat {model}") as span:
        span.set_attribute(GenAIAttrs.OPERATION, "chat")
        span.set_attribute(GenAIAttrs.REQ_MODEL, model)
        span.set_attribute(GenAIAttrs.CONV_ID, conversation_id)
        # 自定义维度 —— 成本归因靠这两个
        span.set_attribute("app.feature", feature)        # claims_triage
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
    # 成本当场算,不要事后用均价估
    span.set_attribute("app.cost_usd", price(resp.model, u))
```

`app.prompt_version` 这一条别漏——**prompt 改了但代码没改**是最常见的"查不出原因"的质量波动源,没有这个维度你连关联都做不了。

缓存那个属性值得单独提:token 属性后来长出了不少亲戚,包括 `gen_ai.usage.cache_read.input_tokens` 和 `gen_ai.usage.reasoning.output_tokens`,这两个在你想认真做成本归因的时候才会用上。**reasoning token 单独计,否则推理模型的账永远对不上。**

### 工具调用的 span

```python
def traced_tool(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with tracer.start_as_current_span(f"execute_tool {fn.__name__}") as span:
            span.set_attribute(GenAIAttrs.OPERATION, "execute_tool")
            span.set_attribute(GenAIAttrs.TOOL_NAME, fn.__name__)
            span.set_attribute("app.tool.args_hash", hash_args(kwargs))  # 不是原文
            try:
                out = fn(*args, **kwargs)
            except Exception as e:
                span.set_attribute("error.type", type(e).__name__)  # 这个是 Stable 的
                span.set_status(Status(StatusCode.ERROR))
                raise
            if fn.__name__ in IRREVERSIBLE_TOOLS:
                span.set_attribute("app.irreversible", True)   # 审计必需
            return out
    return wrapper
```

## 四、PII 脱敏——在 SDK 层,不是后端

内容现在走的是 Opt-In 的 span 属性:`gen_ai.input.messages`、`gen_ai.output.messages`、`gen_ai.system_instructions`、`gen_ai.tool.definitions`。**Opt-In 意味着默认不记录原文,这个默认值对保险公司刚好是对的。**

但光靠默认不够,要在导出前强制过一道:

```python
class RedactingSpanProcessor(BatchSpanProcessor):
    CONTENT_KEYS = {"gen_ai.input.messages", "gen_ai.output.messages",
                    "gen_ai.system_instructions"}

    def on_end(self, span):
        for k in self.CONTENT_KEYS:
            if k in span.attributes:
                if not CAPTURE_CONTENT_ENABLED:
                    span.attributes.pop(k)          # 默认直接丢
                else:
                    span.attributes[k] = redact(span.attributes[k])
        super().on_end(span)


def redact(text: str) -> str:
    text = PII_PATTERNS.sub(lambda m: f"<{m.lastgroup}>", text)  # 保单号/手机/邮箱/TFN
    return ner_redact(text)        # 姓名地址走 NER,正则抓不住
```

三条设计原则,在日常架构决策中必须贯彻执行：

1. **默认关,按需开**。开关做成按 feature / 按租户的配置,不是全局。
2. **原文走单独通道**:短 TTL(7–30 天)、独立 KMS key、访问要审批并留痕。日常 trace 只存元数据(长度、token 数、引用 ID、置信度、hash)。
3. **可重放不等于存原文**。你那个项目里的内容寻址缓存就是这个思路——**SHA-256 的 key 本身就是请求**,事故复现靠回放而不是靠保留明文。

## 五、成本归因:维度设计才是难点

```python
# metric 侧:用 OTel 标准 metric + 自定义维度
token_counter = meter.create_counter("gen_ai.client.token.usage")
token_counter.add(u.input_tokens, {
    "gen_ai.operation.name": "chat",
    "gen_ai.request.model": model,
    "gen_ai.token.type": "input",
    "app.feature": "claims_triage",     # ← 没有这个,账单只有一个总数
    "app.tenant": tenant_id,
    "app.outcome": "success",           # ← 关键
})
```

`app.outcome` 这一维是分水岭。有了它你才能算出真正该看的指标:

> **cost per successful task**,不是 cost per call。

失败和重试也烧钱。只看单价,一个"便宜模型重试三次"会比"贵模型一次成功"看起来更划算,而实际相反。你在 ConvFinQA 里用的 `$/turn` 就是这个思路,把 turn 换成 task 即可。

要看的三张表:**按 feature(哪个业务在烧钱)、按租户(大客户是不是在亏)、按 outcome(多少钱花在失败上)。**

## 六、工具路线取舍

| 路线 | 适合 | 代价 |
|---|---|---|
| **纯 OTel + 现有 APM**(Datadog / Grafana / CloudWatch) | 已有 APM 投资、要和非 AI 服务同一条 trace、数据主权要求高 | 没有开箱的 eval / 标注 / prompt 版本管理,要自己拼 |
| **Langfuse** | 想要 trace + eval + prompt 管理一体,且**可自托管**(保险公司常见要求) | OTel 兼容但生态比纯 OTel 窄 |
| **LangSmith** | 已在用 LangChain / LangGraph,追求最低接入成本 | 与那套生态绑定较深,自托管是企业版 |
| **Arize / Phoenix** | 偏 ML 团队,要漂移检测、embedding 可视化、评估实验管理 | 偏模型分析,工程链路侧较弱 |
| **Bedrock 原生**(+ CloudWatch / Model Invocation Logging) | 全栈在 the cloud provider、要 IAM 和 VPC 边界内闭环、合规最省事 | 跨 the cloud provider 之外的部分看不见,eval 能力有限 |

**我会给的答案是双层:**

> "底层统一打 OTel,因为我不想把 agent 的 trace 和保险核心系统的 trace 割成两套——事故排查时需要同一条 trace 串起来。上层再接一个 LLM 原生的平台做 eval、标注和 prompt 版本管理。关键是**仪表化层保持厂商中立**,这样换上层平台不需要改业务代码。在 a leading global company 这种环境,数据驻留和自托管会是选型的硬约束,所以 Langfuse 自托管或 Bedrock 原生这两条更可能胜出。"

顺带一个能显出你读过细节的点:OpenLLMetry/Traceloop 本身是基于 OTel 的,GenAI conventions 有一部分就来自它的捐赠,但它现在仍在发一些已废弃的属性(`gen_ai.prompt` / `gen_ai.completion`),迁移还在进行中。知道这种事会让人觉得你是真用过。

## 七、让 trace 变成闭环(满分收尾)

观测的终点不是看板,是**自动产出测试用例**:

```python
def on_span_end(span):
    if (span.attr("app.human_override")          # 人工推翻了
        or span.attr("app.confidence", 1.0) < 0.7  # 低置信度
        or span.attr("app.constraint_violation")): # 路径违规
        enqueue_eval_candidate(
            trace_id=span.trace_id,
            reason=classify(span),
            fixtures=record_tool_responses(span),  # 工具响应一并录下来
        )
```

> "我判断一套可观测体系是不是真的在工作,只看一件事:**线上的失败有没有自动变成 eval case。** 没有这条回流,看板只是让人心安,eval 集三个月后就脱离现实了。"

## 八、挑战问答

**Q: 全量采样成本受得了吗?**
```flowchart
→ 分层。**span 元数据全量**(便宜,就是数值和字符串);**内容默认不采**;**出错、低置信度、人工推翻的 100% 保留**,正常流量按 1–5% 抽样留内容。关键是**尾部采样**(tail-based):等 trace 结束再决定留不留,否则你永远留不到那些"结果不好"的 trace。
```

**Q: 多 agent 的 trace 怎么关联?**
```flowchart
→ 这正是 OTel 相对自建日志的唯一刚需——跨进程的 context propagation。`gen_ai.conversation.id` 作为业务侧关联键,trace/span id 作为技术侧关联键,两者都要有。**顺带提一句:MCP 的 conventions 这次也一起迁到了新仓库,如果工具层走 MCP,这部分是现成的。**
```

**Q: 你在 ConvFinQA 里明确说不要 OTel,现在又说要?**
```flowchart
→ "那个决定在那个架构里是对的:单进程同步调用,因果链已经完整落盘在内容寻址缓存和 append-only JSONL 里。我当时写了明确的触发条件——**因果一旦跨出进程**就该上。a leading global company 要建的就是那种系统,所以我会从第一天埋。我拒绝的是在不需要的地方加运维面,不是拒绝可观测性。"
```

**Q: spec 不稳定,现在埋了以后不是白埋?**
```flowchart
→ "所以要 adapter 层。而且即使属性名变了,**span 的结构和维度设计不会变**——哪些操作值得一个 span、成本归到哪些维度、内容记不记,这些才是真正的设计决策,属性名只是绑定。"
```

**Q: 怎么证明可观测性是值得的投入?**
```flowchart
→ 用 **MTTD**(静默退化的平均发现时间)当目标指标,再做一次演练验证它:故意降级检索或换个更差的模型,看多久能被系统自己抓到。**能被演练验证的可观测性,才是真的。**
```

今天花一小时把第二节(现状)、第六节(选型双层)、第八节的第三问练熟,这块缺口就补上了。

# Span
一句话:**span 是"一段有开始和结束的工作"的记录。**

不是日志那种"某一刻发生了什么",而是**一个时间区间**,带名字、带时长、带一堆属性,并且知道自己的父亲是谁。

## 最小心智模型

把一次请求的执行过程想成函数调用栈,**但是把它录下来并带上时间轴**。

```
trace                                  ← 一次完整的请求/会话
└── span: invoke_agent  claims_bot      [0ms ────────────── 4200ms]  父
    ├── span: execute_tool lookup_policy   [40ms ── 160ms]           子
    ├── span: chat  claude-sonnet          [170ms ──────── 2300ms]   子
    └── span: execute_tool calc_excess     [2310ms─2318ms]           子
```

- **Trace** = 整棵树,代表一件完整的事(一次用户提问)
- **Span** = 树上的一个节点,代表这件事里的一步
- 每个 span 有 `trace_id`(我属于哪棵树)和 `parent_span_id`(我爸是谁)——有了这两个,系统才能把散落在不同机器、不同进程里的记录重新拼成一棵树

## 一个 span 实际装着什么

```json
{
  "name": "execute_tool lookup_policy",
  "trace_id": "4bf92f3577b34da6",     // 同一次请求的所有 span 共享
  "span_id":  "00f067aa0ba902b7",
  "parent_span_id": "a3ce929d0e0e4736",
  "start_time": "2026-10-08T01:22:14.120Z",
  "end_time":   "2026-10-08T01:22:14.240Z",   // → 时长 120ms
  "status": "OK",
  "attributes": {                      // 任意键值对,这是价值所在
    "gen_ai.tool.name": "lookup_policy",
    "app.tenant": "zurich_au",
    "app.feature": "claims_triage"
  }
}
```

**属性是重点。** span 的时长只告诉你"慢",属性才告诉你"为什么慢、花了多少钱、是谁的请求"。

## 和 log / metric 的区别

| | 回答什么 | 形态 |
|---|---|---|
| **Log** | "这一刻发生了什么" | 一个时间点,一行文本 |
| **Metric** | "整体趋势如何" | 聚合数字,丢掉了个体 |
| **Span / Trace** | "**这一次**请求里,时间和钱花在哪一步了" | 时间区间 + 层级关系 |

三者的典型对照:
- Metric 说:P95 延迟 8 秒,涨了
- Log 说:14:22:14 调用了 lookup_policy
- **Trace 说:这次慢的 8 秒里,6.2 秒卡在第二次 chat,因为输入 token 是平时的 4 倍,因为检索返回了 50 个 chunk 而不是 5 个**

**只有 trace 能回答"为什么"。** 这就是它存在的理由。

## 为什么 agent 特别需要它

传统 Web 请求通常就 3–4 步,看日志也能拼出来。Agent 不一样:

- 步数**运行时才确定**(可能 3 步也可能 15 步)
- 同一个工具可能被调用多次,日志里看起来一模一样,**分不清是哪一轮**
- 成本分散在多次模型调用上,不汇总就不知道总账
- 子 agent 跑在别的进程里,日志根本不在一个文件

Span 的父子关系恰好解决这些:**它天然记录了"谁调用了谁、第几次调用、各自花了多久多少钱"。**

## 代码里长什么样

就是一个上下文管理器,进入时开始计时,退出时结束:

```python
with tracer.start_as_current_span("execute_tool lookup_policy") as span:
    span.set_attribute("gen_ai.tool.name", "lookup_policy")
    result = lookup_policy(policy_id)       # 真正的工作
    span.set_attribute("app.rows_returned", len(result))
# 退出 with 块 → span 自动结束,时长算好,发送出去
```

`start_as_current_span` 里的 **current** 是关键:在这个块内部再开 span,会自动成为它的子 span。**你不用手动传父子关系**,这就是为什么它比自己写日志省事。

## 怎么决定"什么该是一个 span"

实用判据:**这一步失败或变慢时,你想不想单独看到它?**

- ✅ 每次 LLM 调用(最贵、最慢)
- ✅ 每次工具调用(最可能出错)
- ✅ 每次检索(影响质量)
- ✅ 整个 agent 运行(作为根)
- ❌ 一个纯计算的小函数(没有外部依赖,不值得)

颗粒度太细 = 噪音和开销;太粗 = 看不出问题出在哪。

## 落到你的项目上

你 ConvFinQA 里那套 append-only JSONL + 内容寻址缓存,**本质上就是手写的 span 记录**——每行一个 turn、有耗时、有 token、有可重放的输入。

差别只有两个:
1. 它没有**父子关系**(单进程不需要)
2. 它没有**跨进程传播**(一个进程内全在那儿)

这也正是你报告里那个判断的技术内核。在日常工作中与团队研讨时可以这样表述：

> "我自己手写过一版 span——每个 turn 一条记录,带时长、token、成本,输入可重放。OTel 在那之上加的是**跨进程的因果关联**和**标准化的属性名**。前者在单进程里没有需求,后者在多团队、多工具链的环境里才值钱。a leading global company 两个条件都满足,所以在那边我会直接用 OTel。"

# Span concepts
**不是 OTel 发明的。** "Span" 这个词定型于 2010 年 Google 的 Dapper 论文,OTel 只是把它标准化并推成了行业通用语。这段历史值得知道,因为它解释了为什么这个概念长成现在这样。

## 一、词源与谱系

**史前期(2002–2007):学术界先碰到了问题**
分布式系统一旦拆成几十个服务,"这次请求为什么慢"就没法靠单机日志回答了。Pinpoint(2002)、微软研究院的 Magpie(2004)、伯克利的 X-Trace(2007)各自做过尝试,但术语各不相同——有叫 request track 的,有叫 task tree 的。

**Dapper(2010):"span" 定型**
Google 发了 *Dapper, a Large-Scale Distributed Systems Tracing Infrastructure*。它把一次请求建模成一棵 **trace tree**,树上每个节点叫一个 **span**,span 之间靠父子关系连接,并通过在 RPC 调用中传递 context 来实现跨进程关联。今天你用的每一个概念——trace id、span id、parent span id、annotation(现在叫 attribute/event)、采样——全部出自这篇论文。

顺带一提,"span" 在英文里本来就是"一段跨度"的意思(时间跨度、桥的跨度),Dapper 选它是因为它精确描述了"一段有起止的工作"。**它不是生造词,是被赋予了专有含义。**

**商业 APM 的平行血脉**
同期 Dynatrace 有 PurePath、AppDynamics 有 business transaction、New Relic 也有自己的一套。它们解决同一个问题但**各叫各的名字、各用各的探针**,这正是后来标准化运动的起因。

**开源实现期(2012–2017)**
- **Zipkin**(Twitter,2012 开源)——Dapper 的直接复刻,把 span 这个词带进了开源世界
- **Jaeger**(Uber,2015 内部,2017 开源进 CNCF)
- Apache HTrace 等若干

**标准化之争(2016–2019)**
出现了两套互相竞争的规范:**OpenTracing**(CNCF,只定 API 不定实现)和 **OpenCensus**(Google 开源的内部 Census)。厂商和用户被迫二选一,很分裂。

**合并(2019 年 5 月)**
为了有单一标准,OpenCensus 和 OpenTracing 合并成了 OpenTelemetry,提供 tracing、metrics、logs 三类规范、一套标准化 API、各语言实现,外加 Collector。

**配套标准**
W3C Trace Context 把跨进程传播的 HTTP 头(`traceparent` / `tracestate`)标准化了——这是"为什么不同厂商的系统能拼成同一条 trace"的技术基础。

## 二、所以 span 到底被谁定义

| 层 | 谁定的 | 内容 |
|---|---|---|
| **概念** | Dapper(2010) | span 是什么、父子关系、context 传播 |
| **数据模型 + API** | OpenTelemetry | span 有哪些字段、怎么创建、怎么结束 |
| **传播格式** | W3C Trace Context | `traceparent` 头的格式 |
| **传输协议** | OTLP(OTel 的) | span 怎么在网线上编码发送 |
| **属性命名** | OTel semantic conventions | `http.*`、`db.*`、`gen_ai.*` 各自该叫什么 |

**OTel 的真正贡献不是发明 span,是让所有人用同一套字段名和同一个线上协议。** 以前换 APM 厂商要把探针全拆了重装;现在仪表化一次,导出到哪儿是配置问题。

## 三、现在的行业状态(2026)

**已经不是"新兴标准"了。** OpenTelemetry 在 2026 年 5 月 21 日取得 CNCF 毕业状态,CNCF 自己的措辞是"巩固了作为事实观测标准的地位"。项目规模是 1200 家公司的约 1 万名贡献者。

**采用率(注意不同调查口径差异很大):**
- CNCF 2025 年度调查(2025 年 9 月发放,2026 年 1 月发布):**49% 的受访者已在生产中运行 OTel,另有 26% 正在评估**;而这还是在 5 月毕业公告之前采集的
- 另一份数据给的是 48.5% 已用、25% 计划用,并预期**新项目的采用率超过 90%**
- Grafana 2026 观测调查则显示 Prometheus 整体采用率 77%、OTel 42%,但指出 OTel 处于更早的采用阶段、增长曲线更陡

这几个数字口径不同(是否限定生产、是否限定云原生团队),**在立项评审与技术讨论中引用时说"大约一半的组织已在生产使用"最安全**。

**厂商侧:**几乎每一家主流观测厂商现在都原生接收 OTLP,无论是 Tempo + Prometheus 这类开源栈,还是 Datadog、Honeycomb 这类商业平台。传统 APM 厂商因此承受着越来越大的压力——**仪表化层被标准化之后,他们的护城河从"探针"变成了"分析能力"。**

**信号成熟度分层(这个区分很重要):**

| 信号 | 状态 |
|---|---|
| Traces | 成熟稳定,事实标准 |
| Metrics | 成熟 |
| Logs | 成熟度稍后于前两者 |
| **Profiles** | 2026 年 3 月 26 日进入公开 alpha,有了 OTLP Profiles 数据模型,**还不适合拿来建生产告警** |
| **GenAI 语义约定** | 全部仍是 Development 状态,**没有一个 `gen_ai.*` 属性是 Stable** |

最后两行是日常技术研讨中最该把握的核心认知:**核心 tracing 已经毕业了,但 AI 这一块还在 moving target 上。**

**一个实操注意点:**版本锁定在 OTel 上比在多数工具上更重要,因为 Collector、各语言 SDK、后端三者都要讲兼容的 OTLP 线上协议版本和语义约定版本。

## 四、日常工作中如何落地应用与向上沟通

直接背术语没意思,**用它来表达判断**:

> "Span 这个概念来自 2010 年 Google 的 Dapper,OTel 把它标准化了。到 2026 年 OTel 已经 CNCF 毕业,大约一半的组织在生产里跑,几乎所有厂商都原生收 OTLP——所以**在仪表化层面它已经没有真正的竞品了**,争论点只剩后端选谁。
>
> 但要分清成熟度:核心的 trace/metric/log 是稳的,**GenAI 的语义约定全部还是 Development 状态,一个 Stable 属性都没有**,而且今年 6 月还从主仓库拆到了独立仓库,就是为了能跑得比核心稳定性门槛更快。
>
> 所以我的做法是:**底层仪表化押 OTel,这是安全的;但 `gen_ai.*` 的属性名不直接写进业务代码,夹一层 adapter。** 稳定的部分照标准来,不稳定的部分留退路——这是我对所有未成熟依赖的默认姿势。"

这段话同时展示了三件事:你知道历史、你知道当前状态、**你知道哪部分能押哪部分不能押**。第三点才是架构决策中最具价值的核心考量。

