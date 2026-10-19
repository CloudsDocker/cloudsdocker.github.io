---
layout: post
title: "The Multi-Agent Trap: Designing Reliable, Observable, and Deterministic AI-Native Systems"
tags: ["AI", "Architecture", "Agents", "Reliability", "LangGraph"]
---

*When the system itself begins to reason, our old definitions of reliability crumble. We must forge new laws of predictability in a universe governed by probability.*

> **【案例背景与代称说明 / Enterprise Context Note】**
> 本文探讨的生产级架构与工程实践中，**Aegis**（源自古典神话中的庇护之盾，寓意稳健承保与严密风控）为作者在深度技术特稿中使用的虚构企业代称，指代某世界顶级跨国金融与保险巨擘（Global Tier-1 Carrier / Fortune Global 100）。此举旨在恪守商业隐私与合规边界，同时为读者完整呈现高并发、严监管生产环境下的顶级 AI Native 系统工程实战。

---


# MAS multiple Agent
在日常架构讨论中面对此类需求，优秀的工程切入点是**先审视前提假设**：

> "默认答案是不该用。多 agent 是一笔要付的成本,得有具体理由才值。"

然后给出值得付这笔钱的四个理由。

## 真正成立的理由

**1. 上下文隔离(最主要的一个)**
主 agent 的 context 是稀缺资源。一个要翻 40 份文档才能得出一句结论的子任务,应该在它自己的窗口里烧完 token,只把那句结论交回来。这不是为了"分工",是为了**防止主线被噪音污染**。

**2. 并行化换延迟**
只在**读多写少**的任务上成立——同时查五个来源,然后汇总。一旦涉及协调写入,并行就从优势变成灾难。

**3. 权限边界**
这条在保险场景里最硬:能读客户 PII 的那个 agent,不应该同时有外部调用权限。把权限切开,每个 agent 遵守最小权限,这是架构级的防御,不是 prompt 层的约束。

**4. 独立演进与独立评估**
每个 agent 有自己的 prompt 版本、自己的黄金集、自己的回归套件。团队可以分别 own。这是**组织扩展**的理由,不是技术理由——但它常常才是真实原因,值得诚实说出来。

## 要付的代价(能主动讲出来才显得做过)

- **错误复合**:单步 95% 的可靠性,五步串起来就是 77%
- **交接有损**:子 agent 不知道主 agent 知道的事,交接全靠一段摘要,信息必然丢失
- **token 成本**:普遍是单 agent 的十几倍
- **可观测性复杂度**:trace 从一条线变成一棵树,排障难一个量级
- **评估难度**:非确定性叠加非确定性,归因变得很难——哪个环节该背锅?

## 我用的判定标准

> **子任务能不能用一段话描述清楚,结果能不能用一段话交回来?** 不能,就说明交接会丢太多东西,留在单 agent 里。

```flowchart
再加一条:**读多写少 → 适合拆;需要协调写入 → 不要拆。**
```

## 什么时候明确不该拆

- 任务其实是固定流程——那是 workflow,不是 agent,更不是多 agent
- 子任务之间要频繁来回对齐——通信成本会吃掉全部收益
- 延迟预算紧的同步场景
- 还没把单 agent 的 eval 做好——**没有评估体系就上多 agent,等于在看不见的地方制造复杂度**

最后这句很值钱,因为它把多 agent 的问题拉回到了他们真正关心的 eval 上。

# intro
这是上一题的正确追问,你的老板或Team Lead在确认这不仅仅是理论方案，而是经得起生产检验的工程实践。

**正面回答:绝大多数情况下就该用确定性编排。** Agent 只在一种情况下才挣得到位置——**控制流本身无法在设计时枚举**。

## 确定性失效的四个信号

1. **分支不可枚举**。输入空间开放,长尾无限。你写到第 40 个 `if` 还在加,说明你在用代码模拟判断。
2. **步数依赖中间结果**。要检索几轮、要不要换个查询词重来,取决于上一轮读到了什么。DAG 画不出来,因为边的存在与否是运行时才知道的。
3. **失败后需要换策略而不是重试**。确定性重试是"再做一次同样的事";这里需要的是"这条路不通,换个方法"。
4. **维护成本翻转**。每新增一类 case 就要改编排代码并重新发布,规则库增长快过业务增长。

这四条一条都不满足,就老老实实用 Step Functions。

## 确定性赢在哪(这些是真实的、不是保守)

可枚举、可测试、延迟可预测、成本固定、失败点定位清晰,而且**可审计**——在 local regulators 下,"我能拿出这个决定走了哪条分支"是硬要求。Agent 的 trace 也能满足,但举证成本高一个量级。

## 我实际会用的形态:确定性外骨骼 + 模型内核

作为 Lead AI Engineer，在日常工作中做架构设计最该强调这一点,因为它才是生产答案:

- **外层确定性**,拥有事务边界、重试、超时、权限、审计、幂等、状态持久化
- **模型只在节点内部做判断**:分类、抽取、这一步该调哪个工具
- Agent 的自由度被框在一个确定性的信封里——**它能决定做什么,但不能决定边界在哪**

prod-guard 那套东西本质上就是这个:放开 agent 的选择权,但不可逆动作必须穿过一道确定性的闸门。

## 两个方向都要走

```flowchart
**确定性 → agent**:先用规则跑,**埋点记录人工在哪里偏离了规则**。等数据证明分支真的爆炸了,再把那一段换成 agent。这样你是拿证据做的决定,不是拿直觉。

**Agent → 确定性**:反过来更被低估。用 agent 做**发现**,等路径跑稳定了,把高频路径固化成确定性流程,agent 只兜底长尾。成本和延迟会掉一个数量级。
```

> 一句收尾:"Agent 适合用来**找**出流程,确定性编排适合用来**跑**流程。很多团队的问题是找完了还一直用 agent 在跑。"

---

这个词组值得逐词拆,因为它藏着一个反直觉的东西:**传统软件可靠性的定义,在这里整个失效了。**

## "AI-native" 的分界线

不是"系统里有 AI",而是**模型参与了控制流的决策**。

| | AI-enabled | AI-native |
|---|---|---|
| 模型的位置 | 一个功能(摘要、分类、推荐) | 决定下一步做什么 |
| 控制流 | 设计时写死 | 运行时产生 |
| 失败方式 | 抛异常 | 看起来很合理地做错事 |
| 移除模型 | 系统还能跑,少个功能 | 系统不存在 |

判定方法:**把模型拿掉,还剩什么?** 剩一个少了功能的系统 = AI-enabled;什么都不剩 = AI-native。

JD 用这个词,是在说他们要造的不是"保险系统 + AI 功能",而是**流程本身由 agent 组织起来**的东西。

## "reliable" 在这里意味着什么

传统可靠性建立在三个假设上,这三个全都塌了:

| 传统假设 | AI-native 的现实 |
|---|---|
```flowchart
| 同样输入 → 同样输出 | 同样输入,输出每次不同 |
```
| 失败会抛错 | 失败是流畅、自信、错误的输出 |
| 测试能穷举分支 | 分支在运行时才产生 |
| 正确性是布尔值 | 正确性是分布 |
| 升级依赖是我的决定 | 模型供应商可以在我不知情时改变行为 |

最后一条在保险公司特别要命:**你的核心依赖会自己变**。模型版本退役、行为漂移、安全策略调整——这些都不是你发布的,但后果是你的。

所以这里的 reliable 不是"不出错",而是:

> **在一个本质上非确定、偶尔会自信地犯错的组件之上,构造出行为可预测、后果有界、失败可发现的系统。**

## 五个支柱(这就是企业级生产系统该有的完整架构)

**1. 后果有界**
最重要的一条。可靠性不是让模型不犯错,是**让它犯错时也不造成不可逆损失**。不可逆动作必须穿过确定性闸门、最小权限、幂等、步数与预算上限。`prod-guard` 就是这个支柱的实例。

**2. 正确性是统计量**
"它能工作吗"不是一个有意义的问题。有意义的问题是:**在这个分布上成功率是多少、方差多大、失败集中在哪类输入**。所以 eval 不是测试,是可靠性的度量工具本身。

**3. 失败必须可见**
传统系统坏了会报警;AI-native 系统坏了会继续输出漂亮的话。所以要主动造信号:置信度分流、输出的结构化校验、引用强制、路径约束断言、与基线的持续比对。**没有观测,你甚至不知道它已经坏了三个月。**

**4. 优雅降级**
模型不可用或质量不达标时,系统退到什么?——退到规则、退到人工、退到"我不知道"。**一个只有满血路径的 AI-native 系统不叫可靠。**

**5. 面对漂移的韧性**
模型版本 pin、变更时跑全量回归、prompt 作为代码版本化、留回滚路径、持续跑线上基线集检测漂移。

## 保险语境下再加一层

还有第二种"可靠"——**可被监管者信任**。决策可追溯(哪些证据、哪条路径)、人工在高风险点保留最终决定权、公平性可论证、客户数据边界可审计。在 local regulators CPS 230 下,这不是加分项,是上线前提。

## 一句话工程原则版本

> "AI-native 意味着控制流是模型生成的,所以可靠性不能再靠穷举分支来保证。我的做法是:**把不确定性关在一个确定性的信封里**——模型自由决定做什么,但边界、权限、不可逆动作和预算由确定性层管死;然后用 eval 把正确性变成可测量的分布,用 observability 让静默失败变得可见。可靠的 AI-native 系统不是不犯错的系统,是犯错也伤不到人的系统。"

最后这句是日常工程实践中最值得深刻铭记的一句话。

# S2

这是整个可靠性里最难的一块,因为**你要检测的是一个没有异常、没有堆栈、看起来完全正常的失败**。

## 一、先把失败分类——不同类型要用不同信号抓

| 失败类型 | 表现 | 传统监控能抓吗 |
|---|---|---|
| 硬失败 | 超时、500、JSON 解析失败 | ✅ 能 |
| **幻觉** | 编造了一条不存在的保单条款 | ❌ 完全看不见 |
| **检索退化** | 索引坏了,但模型照样基于空上下文编答案 | ❌ |
| **静默降级** | 供应商改了模型,回答变泛,成功率掉 8% | ❌ |
| **能力边界外** | 遇到没见过的 case,自信地猜 | ❌ |
| **路径漂移** | 结果还对,步数从 4 涨到 11 | ❌ |
| **拒答膨胀** | guardrail 收紧,把正常请求也挡了 | ❌ 更隐蔽 |

最后一条特别阴:**拒答率上升在所有质量指标上都不掉分**(没答错嘛),但业务价值在流失。

## 二、四层信号,按成本从低到高

### 第一层:确定性校验(每一次请求都跑,近乎零成本)

能用代码判定的,绝不用模型判定。这层能抓掉 30–40% 的问题。

```python
# 输出契约校验 —— 不只是 schema,还有业务不变量
class ClaimAssessment(BaseModel):
    policy_number: str
    covered: bool
    excess_amount: Decimal
    reasoning: str
    citations: list[Citation]          # 强制引用

    @field_validator("policy_number")
    def must_exist_in_context(cls, v, info):
        # 关键:保单号必须来自检索结果,不能是模型造的
        if v not in info.context["retrieved_policy_ids"]:
            raise HallucinationError(f"fabricated policy id: {v}")
        return v

    @model_validator(mode="after")
    def excess_within_policy_bounds(self):
        # 业务不变量:免赔额必须在该险种的合法区间内
        bounds = POLICY_BOUNDS[self.product_code]
        if not bounds.lo <= self.excess_amount <= bounds.hi:
            raise OutOfBoundsError(...)
        return self
```

**引用强制(grounding check)** 是这层里最值钱的一个:

```python
def verify_grounding(answer: str, sources: list[str]) -> GroundingReport:
    claims = extract_atomic_claims(answer)        # 拆成可验证的断言
    unsupported = []
    for c in claims:
        # 先用便宜手段:字符串/数字必须能在 source 里找到
        if c.has_numeric and not numeric_present_in(c, sources):
            unsupported.append(c)
        elif not semantic_match(c, sources, threshold=0.72):
            unsupported.append(c)
    return GroundingReport(
        grounding_rate=1 - len(unsupported)/len(claims),
        unsupported=unsupported,
    )
```

`grounding_rate` 是我会放在看板最显眼位置的单一指标。**它掉了,基本等于检索坏了或模型开始编。**

### 第二层:运行时路径断言(每次请求,低成本)

把 CI 里的 trajectory 断言搬到线上,作为**不阻断的观测**(安全类除外,那些要阻断):

```python
RUNTIME_INVARIANTS = [
    Invariant("no_write_before_approval",
              lambda t: idx(t, "require_approval") < idx(t, "issue_payment"),
              severity="BLOCK"),            # 这条直接拦
    Invariant("retrieval_before_answer",
              lambda t: "search_policy" in t.tools_called,
              severity="ALERT"),
    Invariant("step_budget",
              lambda t: t.step_count <= 8,
              severity="ALERT"),
    Invariant("no_repeated_identical_call",
              lambda t: max(t.call_counts.values()) <= 3,
              severity="ALERT"),            # 抓死循环
]
```

这层能抓到"结果看着对,过程已经坏了"——而这通常是**事故的前兆信号**,比事故本身早几天出现。

### 第三层:置信度分流(每次请求,低成本)

关键是别只用一个信号,**多个弱信号合成**:

```python
def confidence(ctx) -> Confidence:
    signals = {
        "retrieval_top_score": ctx.retrieval.scores[0],        # 检索得分
        "retrieval_margin": ctx.retrieval.scores[0] - ctx.retrieval.scores[1],
        "grounding_rate": ctx.grounding.rate,
        "self_consistency": ctx.n_sample_agreement,   # 采样 3 次的一致率(贵,只对高风险跑)
        "ood_distance": distance_to_training_dist(ctx.input_embedding),
        "step_anomaly": ctx.step_count / BASELINE_STEPS,
    }
    score = weighted(signals)
    return Confidence(score, signals)   # 信号要全部留在 trace 里,不只留合成分
```

```flowchart
**低置信度 → 路由给人工**。这把"模型可能错了"从一个质量问题变成了一个**可观测、可计数的业务事件**:低置信度分流率本身就是最好的健康指标之一。
```

### 第四层:采样审计与在线评估(抽样,高成本)

- **LLM-as-judge 抽样**:1–5% 流量,不是全量
- **人工审计**:每天固定抽 20–50 条,重点抽低置信度和高风险类别
- **生产金丝雀集**:一组固定的合成 case,每小时在真实生产环境跑一遍。这是检测供应商侧静默变更的最直接手段——**线上流量天天在变,但这组输入永远不变,它的得分掉了就是系统变了。**

## 三、线上没有 ground truth 怎么办——代理指标

这是在架构评审中你的老板或team lead最常提问的一点。答案是:**用人的行为当标注。**

| 代理指标 | 说明 | 保险场景 |
|---|---|---|
| **人工推翻率** | 复核员改了 agent 的结论 | 最强的信号,近似真实错误率 |
| **编辑距离** | 人工对草稿改了多少 | 质量的连续度量,比布尔值敏感 |
| 升级率 | 转人工的比例 | 上升 = 能力边界在收缩 |
| **客户二次联系率** | 同一 case 7 天内再来 | 第一次没解决的直接证据 |
| 放弃率 | 对话中途走掉 | |
| 返工率 | 同一 case 被重开 | |
| 拒答率 | 不作答的比例 | 抓 guardrail 过紧 |

**人工推翻率 + 编辑距离** 这一对是黄金组合,因为它们是免费的、连续的、并且天然带标注——把被推翻的 case 自动收集起来,就是你下一批 eval 用例的来源。这条闭环在日常工程落地与团队技术分享中至关重要。

## 四、告警怎么设才不会被无视

**不要对单次请求告警。** 单次低分是噪音。

```yaml
alerts:
  - name: grounding_rate_drop
    metric: p50(grounding_rate)
    window: 1h
    condition: "< baseline_7d - 0.08"       # 相对基线,不是绝对值
    min_volume: 200                          # 样本不足不告警
    severity: page

  - name: override_rate_spike
    metric: human_override_rate
    window: 24h
    condition: "> baseline_14d * 1.5"
    severity: page

  - name: canary_degradation
    metric: canary_task_success
    window: 3 consecutive runs               # 连续三次才告,防抖
    condition: "< baseline - 0.05"
    severity: page                           # 这条最可能是供应商改了模型

  - name: refusal_rate_spike                 # 容易被忘的方向
    metric: refusal_rate
    condition: "> baseline_7d * 1.4"
    severity: ticket
```

三条原则:**相对基线、要求最小样本量、按窗口聚合**。再加一条分层——page / ticket / dashboard 三级,只有真正要半夜起床的才 page。

## 五、挑战问题与回答

**Q: "线上没有标注,你凭什么说准确率掉了?"**
> 分三路。一是**代理指标**——人工推翻率和客户二次联系率,这两个不需要标注且天然带业务含义。二是**生产金丝雀集**,一组固定输入每小时跑一遍,它和线上流量的区别是输入不变,所以得分变化只能来自系统。三是**抽样审计**,每天几十条人工过。三路互相印证:如果只有线上指标掉而金丝雀没掉,那大概率是输入分布变了,不是模型变了。

**Q: "怎么区分模型变差了,还是用户问的东西变了?"**
> 这正是金丝雀集存在的理由。再加上**输入分布监控**:对输入做 embedding,监控它相对历史分布的漂移(PSI 或分布距离),同时按意图类别拆分成功率。如果成功率的下降集中在某个新出现的类别上,那是分布漂移;如果是全类别均匀下降,那是模型或检索的问题。

**Q: "你的 guardrail 自己也是个模型,它错了怎么办?"**
> 承认这是个真问题。三条应对:第一,**guardrail 优先用确定性手段**,能用 schema、数值范围、ID 存在性校验的绝不用模型。第二,guardrail 要有自己的 eval 集,**单独测它的漏报率和误报率**——漏报让风险通过,误报让拒答率飙升,两个方向都要测。第三,**不可逆动作不依赖 guardrail 判断**,而是靠确定性的权限和审批闸门,guardrail 只是额外一层。

**Q: "LLM-as-judge 全量跑成本太高。"**
> 所以分层。确定性校验跑 100%,路径断言跑 100%(都很便宜),judge 只跑 1–5% 抽样,人工跑千分之几。抽样不是均匀的——**按风险分层抽**:高金额、低置信度、新客户、新 case 类型的抽样率调高。另外 judge 用小模型就够,它做的是打分不是推理。

**Q: "告警太多团队就不看了,你怎么防?"**
> 这是我最在意的失败模式,因为它会让前面所有工程失效。做法:只对聚合指标告警不对单次告警;阈值设在相对基线上;要求最小样本量;分三级严重度;**每个月审一次告警的真阳性率,低于某个比例的告警规则就删掉或降级**。宁可少告几条,也不能让团队学会忽略。

**Q: "trace 里全是客户 PII,怎么办?"**
> 在 SDK 层做,不是在后端做。写 span 时对 input/output 做脱敏和哈希,只保留结构化元数据(长度、token 数、引用 ID、置信度信号)和脱敏后的文本。需要原文做事故分析时,走单独的、短 TTL 的、有审批的存储。**默认不存原文**,这在 CPS 234 下基本是必须的。

**Q: "你说'坏了三个月才发现',具体怎么避免?"**
> 三个月不被发现,一定是因为**所有指标都是输出侧的**——只看延迟、错误率、吞吐,那些确实没变。要避免就必须有一个**独立于线上流量的参照系**(金丝雀集)和一个**独立于模型判断的参照系**(人工推翻率)。只要这两个里有一个在跑,三个月的静默就不可能发生。我会把"我们能多快发现一次静默退化"当成一个明确的设计目标,比如 MTTD 不超过 24 小时,然后用注入故障的演练去验证它。

最后这句是满分收尾:

> **"可靠性不是没有失败,是失败的平均发现时间足够短。我会把 MTTD 当成一个和成功率并列的一等指标,并且定期做演练去验证它——故意降级检索或换个更差的模型,看多久能被系统自己抓到。"**


---


# RAG
普通候选人回答：
“I have experience with RAG and LangChain.”
Senior 候选人：
“I built a RAG system using LangChain.”
Lead 候选人：
“Before choosing RAG, I first determine whether retrieval is actually required. Then I define measurable quality, latency, cost and safety objectives. I design the retrieval, agent orchestration and tool boundaries around those requirements, and establish evaluation and observability before putting the system into production.”
这三种回答的层次完全不同。


# faithfulness vs groundness
Faithfulness

它和 groundedness 很接近，但在日常工程实践中可以这样清晰界定：

Groundedness

Does the answer have support in the retrieved evidence?

Faithfulness

Does the generated answer faithfully represent that evidence without introducing contradictions or unsupported claims?

例如原文：

“Coverage may apply subject to the conditions listed below.”

Agent：

“Your claim is definitely covered.”

即使 Agent 引用了正确 document：

Faithfulness 仍然有问题。

因为它把：

may apply

变成：

definitely covered

# Routing of models
I would use a combination of rule-based routing, model-based classification and quality-driven escalation.

First, I would handle deterministic cases without an LLM where possible. For other requests, a lightweight classifier would identify the intent, complexity and risk level, and route the request to the most cost-effective model that meets the required quality threshold.

For tasks where quality can be verified, I would consider a cascading approach: start with a smaller model and escalate when validation fails. For high-risk insurance decisions, however, I would enforce deterministic controls and human approval rather than relying on model confidence alone.

I would evaluate the routing policy against a representative dataset, measuring task success, cost per request, p95 latency, escalation rate and safety violations. I would deploy it gradually and continuously monitor quality by route and business risk.

The objective is not simply to maximise the percentage of requests handled by a small model. It is to minimise total cost while meeting explicit quality, latency and safety requirements.
