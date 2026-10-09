---
layout: post
title: "AI Leadership: Enterprise Architecture, Strategic Delivery, and Engineering Rigor"
tags: ["AI", "Leadership", "Career", "Strategy", "SystemDesign"]
---

*Leadership in the age of AI is not about understanding every weight and bias; it is about steering the ship of innovation through the turbulent waters of risk, regulation, and engineering reality.*

---

Senior AI Engineer / AI Domain Architect:

```flowchart
> **不是一个“懂 GenAI 的 Senior Software Engineer”岗位，而是一个“能把 Agentic AI 平台从 0 → Production 的 Lead AI Engineer”岗位。**
```

而且有一个非常重要的新信息：a leading global company 同期的 Senior AI Engineer 招聘明确提到了 **LangGraph、the cloud provider Strands、AgentCore、MCP、Bedrock、Lambda、API Gateway、DynamoDB/RDS、SageMaker、ECS、S3、IAM、CDK/Terraform**。这比你给我的 Lead JD 更能暴露他们实际想要的技术方向。([JobLeads][1])

所以，如果我是准备拿 **最高分 / Strong Hire** 的候选人，我不会平均用力，而会按下面这个优先级准备。

---

# 一、先给你结论：必须掌握的技术

如果把这个职位拆成 100 分，我会这样分：

| 能力                                             |  权重 | 必须达到  |
| ---------------------------------------------- | --: | ----- |
| **Agentic AI / LLM Engineering**               | 25% | ⭐⭐⭐⭐⭐ |
| **RAG / Retrieval / Knowledge Architecture**   | 15% | ⭐⭐⭐⭐⭐ |
| **AI Evaluation / Observability / Guardrails** | 15% | ⭐⭐⭐⭐⭐ |
| **the cloud provider AI Architecture**                        | 15% | ⭐⭐⭐⭐⭐ |
| **Python + TypeScript**                        | 10% | ⭐⭐⭐⭐  |
| **Production / DevSecOps / AIOps**             | 10% | ⭐⭐⭐⭐⭐ |
| **System Design / Distributed Systems**        |  5% | ⭐⭐⭐⭐⭐ |
| **Data Engineering / MLOps**                   |  5% | ⭐⭐⭐⭐  |

最关键的是：

### **Agent + RAG + Evaluation + the cloud provider + Production**

这五个东西形成闭环。

---

# 二、我认为他们真正想找的人

JD 表面上写：

> AI agents
> RAG
> agentic orchestration
> evaluation
> observability
> the cloud provider
> DevSecOps

但实际上他们在找的是这样的人：

```text
                    Business Problem
                           │
                           ▼
                    AI Product Design
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
           RAG                         Agent
             │                           │
             │                    ┌──────┴──────┐
             │                    │             │
             ▼                    ▼             ▼
        Retrieval              Tools        Planning
             │                    │             │
             └───────────┬────────┴─────────────┘
                         ▼
                       LLM
                         │
                         ▼
                Guardrails / Security
                         │
                         ▼
              Evaluation / Observability
                         │
                         ▼
              the cloud provider Production Platform
                         │
                         ▼
                 Customer / Business
```

**这才是 Lead AI Engineer。**

不是：

> “我会调用 GPT API。”

---

# 三、第一优先级：Agentic AI

这是整个岗位最核心的部分。

JD 第一条 responsibility 就是：

> Lead the end-to-end development of AI agents and agentic orchestration solutions in production environments. ([a leading global company Careers][2])

而 a leading global company 同期 Senior AI Engineer 已经进一步点名：

* LangGraph
* the cloud provider Strands
* AgentCore
* MCP
* multi-agent orchestration
* tool use
* prompt engineering

([RemoteITJobs.app][3])

所以我会把这一块作为你的 **第一重点**。

---

## 你必须真正理解 Agent，而不是只会框架 API

至少要能解释：

### 1. Agent vs Workflow

这是非常容易被问的。

```text
Workflow

A → B → C → D

Agent

          ┌→ Tool A
LLM ──────┼→ Tool B
          ├→ Tool C
          └→ Human
             ↓
          Next Action
```

你必须知道：

> **如果流程可以确定性描述，就不要使用 Agent。**

例如：

```text
Receive claim
      ↓
Validate policy
      ↓
Retrieve documents
      ↓
Calculate eligibility
      ↓
Generate response
```

这是 workflow。

而：

> “根据客户的问题决定需要查什么资料、调用哪个系统、是否需要人工介入。”

才更像 agent。

---

# 四、第二个必须掌握：Agent Architecture

我会要求自己能够白板画出：

```text
                    User
                     │
                     ▼
                 API Gateway
                     │
                     ▼
              Agent Orchestrator
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       Planner     Retriever    Tools
          │          │          │
          │          ▼          ├── Policy API
          │       Vector DB     ├── Claims API
          │          │          ├── Customer API
          │          │          └── Search
          │          │
          └──────┬───┘
                 ▼
                LLM
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
     Guardrail  Eval    Memory
        │
        ▼
   Final Response
```

然后继续往下面：

```text
          ┌─────────────────────┐
          │ Observability        │
          │                     │
          │ latency             │
          │ token usage         │
          │ cost                │
          │ tool calls          │
          │ traces              │
          │ errors              │
          │ quality             │
          └─────────────────────┘
```

这会非常符合 a leading global company 的 JD。

---

# 五、第三个核心：RAG

这个你应该重点准备，因为你已经有 ConvFinQA / RAG 相关经历，这实际上可以成为你的优势。

但不要停留在：

```flowchart
> embedding → vector DB → similarity search → LLM
```

Lead Engineer 要能回答：

## 为什么 RAG 会失败？

至少要知道：

### Retrieval failure

```text
Question
   ↓
Embedding
   ↓
Retriever
   ↓
Wrong documents
   ↓
LLM
   ↓
Wrong answer
```

所以：

> **LLM quality ≠ RAG quality**

---

# 六、RAG 必须掌握到这个深度

我会要求自己能够解释：

### Retrieval

* Dense retrieval
* Sparse retrieval / BM25
* Hybrid search
* Metadata filtering
* Semantic search
* Query rewriting
* Multi-query
* Parent-child retrieval
* Hierarchical retrieval

### Ranking

* similarity score
* reranking
* cross-encoder
* top-k
* score threshold

### Chunking

必须理解：

```text
Document
    ↓
Structure-aware chunking
    ↓
semantic chunks
    ↓
embedding
```

而不是机械：

```python
text[i:i+500]
```

---

# 七、RAG Evaluation 是 Lead 的分水岭

普通 AI Engineer：

> “我们的回答准确率不错。”

Lead：

> **“How do you know?”**

这是日常架构落地与技术评审中非常关键的问题。

你应该能建立：

```text
                   Evaluation
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
 Retrieval          Generation      System
 Evaluation         Evaluation      Evaluation
        │              │              │
 Recall@K           Faithfulness     Latency
 Precision@K        Relevance        Cost
 MRR                Correctness      Reliability
 NDCG               Groundedness     Availability
```

---

# 八、AI Evaluation：我认为这是这个职位最重要的隐藏考点

JD 特别强调：

> Establish robust evaluation, monitoring, and observability frameworks

这不是普通 prompt engineering。

你要能回答：

### “How would you evaluate an AI agent in production?”

我的标准答案框架：

```text
1. Offline evaluation
2. Online evaluation
3. Component-level evaluation
4. End-to-end evaluation
5. Safety evaluation
6. Cost / latency evaluation
7. Human evaluation
```

---

# 九、Agent Evaluation 更复杂

例如一个 Claims Agent：

```text
User
 ↓
Agent
 ↓
Retrieve policy
 ↓
Call claims API
 ↓
Calculate eligibility
 ↓
Generate answer
```

最终回答错了。

你不能只说：

> LLM hallucinated.

你需要知道：

```text
Was retrieval wrong?
       ↓
Was tool selection wrong?
       ↓
Were tool arguments wrong?
       ↓
Was tool result interpreted incorrectly?
       ↓
Was reasoning wrong?
       ↓
Was final generation wrong?
```

这就是 **Agent observability + evaluation**。

---

# 十、Observability：你必须从“系统监控”升级到“LLM Observability”

你原来的 SRE 背景在这里其实非常有价值。

传统：

```text
CPU
Memory
Latency
Error Rate
Availability
```

AI system：

```text
Request
  ↓
LLM call
  ↓
Prompt
  ↓
Retrieval
  ↓
Tool call
  ↓
Tool result
  ↓
LLM call
  ↓
Final response
```

因此需要 trace：

```text
trace_id

├── prompt
├── model
├── tokens
├── latency
├── retrieval
│   ├── query
│   ├── documents
│   └── scores
├── tool_call
│   ├── tool
│   ├── arguments
│   └── result
└── response
```

然后监控：

* token usage
* cost
* latency
* model errors
* hallucination
* retrieval quality
* tool failure
* agent loop
* guardrail violations

---

# 十一、你的 SRE 背景在这里反而是优势

你过去做的：

```flowchart
> zombie GPU nodes → synthetic health check → automatic drain
```

这种故事其实非常适合迁移成：

> **AI Agent reliability engineering**

例如：

```text
Agent stuck
   ↓
Repeated tool calls
   ↓
Token explosion
   ↓
Cost explosion
```

怎么办？

```text
max_iterations
max_tokens
timeout
circuit breaker
budget limit
tool timeout
fallback model
human escalation
```

这就是 Lead AI Engineer 思维。

---

# 十二、the cloud provider：这里不能只会“用过 the cloud provider”

a leading global company 明显是 **the cloud provider-first**。

他们同时招聘的 Senior AI Engineer 已经列出了：

* Amazon Bedrock
* AgentCore
* Lambda
* API Gateway
* DynamoDB / RDS
* SageMaker
* ECS
* S3
* IAM
* CDK / Terraform

([JobLeads][1])

所以我会把 the cloud provider 分成三个层次。

---

## Level 1：必须熟

### Bedrock

必须知道：

* Foundation Models
* inference
* model selection
* embeddings
* Knowledge Bases
* Guardrails
* Agents
* model evaluation
* provisioned throughput / cost considerations

---

## Level 2：必须能设计

```text
API Gateway
     ↓
Lambda / ECS
     ↓
Agent
     ↓
Bedrock
     ↓
S3 / DynamoDB / RDS
```

必须理解：

* IAM
* VPC
* Secrets Manager
* KMS
* CloudWatch
* EventBridge
* SQS
* SNS

---

# 十三、AgentCore / Strands / LangGraph

这里我会特别提醒你。

**不要同时浅学 10 个 Agent Framework。**

最高效的方法：

### 主攻

**LangGraph**

理解：

```text
State
Node
Edge
Conditional Edge
Checkpoint
Interrupt
Human-in-the-loop
Persistence
```

然后：

### the cloud provider 原生

**the cloud provider Strands / AgentCore**

至少知道它们解决什么问题。

a leading global company 的招聘信息已经明确出现这些技术，所以在日常工作中经常需要进行针对特定框架的深度技术研讨（framework-specific discussion）。([JobLeads][1])

---

# 十四、MCP 必须知道

我会给 MCP：

**8/10 必须掌握。**

尤其是 Agentic AI。

你要理解：

```text
Agent
  │
  │ MCP
  ▼
MCP Server
  │
  ├── Tool
  ├── Resource
  └── Prompt
```

以及：

> 为什么 MCP 比每个 Agent 自己写 integration 更适合企业级生态？

还要谈：

* authentication
* authorization
* tool permissions
* data leakage
* trust boundary
* malicious tool
* prompt injection

---

# 十五、Security：Insurance 公司这里会非常重要

a leading global company 不是普通 startup。

所以你必须准备：

### LLM Security

* Prompt Injection
* Indirect Prompt Injection
* Data Exfiltration
* Sensitive Data
* PII
* Excessive Agency
* Tool Abuse
* Jailbreak
* Hallucination
* Supply-chain risk

---

## Agent Security

这是一个在日常工程架构中非常核心的研讨议题：

> **“What happens if the LLM decides to call a dangerous tool?”**

错误答案：

> Prompt 告诉模型不要调用。

正确方向：

```text
LLM
 ↓
Policy Layer
 ↓
Authorization
 ↓
Tool
```

也就是：

> **Never trust the LLM as the security boundary.**

这一句话非常值得你记住。

---

# 十六、DevSecOps

JD 明确：

> DevSecOps and AIOps

所以你必须把：

```text
Git
 ↓
CI
 ↓
Unit Tests
 ↓
Security Scan
 ↓
Build
 ↓
Deploy
 ↓
Evaluation
 ↓
Canary
 ↓
Production
 ↓
Monitoring
```

说清楚。

尤其是：

### AI CI/CD

普通软件：

```text
tests pass → deploy
```

AI：

```text
tests pass
     ↓
evaluation pass
     ↓
safety pass
     ↓
cost threshold
     ↓
latency threshold
     ↓
deploy
```

这就是很好的 Lead-level answer。

---

# 十七、Python：你必须达到这个程度

不是“会 Python”。

而是能够现场：

```python
FastAPI
Pydantic
asyncio
httpx
pytest
typing
dataclasses
```

并写：

```text
LLM service
RAG service
Agent tool
API
evaluation pipeline
```

你之前提到想保持手动 coding 能力，这个职位非常适合你这样练。

我甚至建议你：

> **不要让 AI 给你生成这些代码。**

自己写。

---

# 十八、TypeScript：不要忽略

因为 JD 明确：

> Python and TypeScript

而 a leading global company 同期 Senior AI Engineer 更进一步要求：

> TypeScript + Node.js + Python + React/Next.js

([RemoteITJobs.app][3])

你不需要成为 TypeScript 专家。

但是至少能够：

```typescript
interface AgentRequest {
   query: string;
   userId: string;
   context?: Record<string, unknown>;
}
```

并理解：

* async/await
* Promise
* interfaces
* types
* generics
* Node.js
* REST API
* streaming

---

# 十九、System Design：你本来就应该有优势

你的 Distributed Systems / SRE / Kafka / Kubernetes / the cloud provider 背景，在这个职位应该转化成：

> **AI System Design**

我会准备至少这 8 道：

### 1

**Design an enterprise AI Agent platform**

### 2

**Design a Claims Agent**

### 3

**Design a RAG platform for insurance documents**

### 4

**Design multi-agent orchestration**

### 5

**Design an LLM evaluation platform**

### 6

**Design AI observability platform**

### 7

**Design secure enterprise MCP platform**

### 8

**Design 1M requests/day AI service**

---

# 二十、其中最重要的一道：Design an Insurance Claims Agent

我认为这是你应该重点准备的。

因为目前 a leading global company 的公开招聘信息明确提到其 Agentic AI journey 与 **Claims Transformation** 有关。([LinkedIn][4])

假设：

> Customer asks:
> “Can I claim this damaged laptop?”

你的架构：

```text
                  Customer
                     │
                     ▼
                 API Gateway
                     │
                     ▼
               Claims Agent
                     │
        ┌────────────┼─────────────┐
        ▼            ▼             ▼
     Policy       Document       Claims
     Tool         Retrieval       Tool
        │            │             │
        ▼            ▼             ▼
      Core        Vector DB      Claims DB
     Systems
        │
        └────────────┬────────────┘
                     ▼
                 LLM / Agent
                     │
             ┌───────┴────────┐
             ▼                ▼
        Guardrails          Human
             │             Escalation
             ▼
           Answer
```

在日常工作中你的老板或者team lead会继续提问：

> How do you prevent hallucination?

> How do you evaluate it?

> How do you monitor it?

> What if the policy document changes?

> What if the tool is unavailable?

> What if the agent enters an infinite loop?

> How do you protect customer PII?

> How much does one request cost?

> How do you deploy a new model?

这才是真正的 Lead AI Engineer 深度架构实践。

---

# 二十一、我会给你的技术优先级

如果只有 **4 周**：

### 🔴 Tier 1 — 必须达到 9/10

**Agentic AI**

* Agent architecture
* Tool calling
* Planning
* State
* Memory
* Multi-agent
* Human-in-the-loop
* LangGraph
* Strands
* AgentCore
* MCP

**RAG**

* chunking
* embeddings
* hybrid retrieval
* reranking
* query rewriting
* metadata filtering
* retrieval evaluation

**AI Evaluation**

* correctness
* relevance
* faithfulness
* groundedness
* retrieval recall
* precision
* end-to-end evaluation
* LLM-as-judge
* human evaluation

**Production AI**

* observability
* tracing
* guardrails
* security
* cost
* latency
* reliability

---

# 二十二、Tier 2 — 8/10

### the cloud provider

```text
Bedrock
AgentCore
Lambda
ECS
API Gateway
S3
DynamoDB
RDS
IAM
CloudWatch
SQS
EventBridge
Secrets Manager
KMS
```

### IaC

```text
Terraform
the cloud provider CDK
```

### DevSecOps

```text
CI/CD
container
security scanning
testing
deployment
rollback
canary
```

---

# 二十三、Tier 3 — 7/10

* SageMaker
* MLOps
* data pipelines
* Kafka
* Spark/Flink
* Kubernetes
* React
* Next.js
* GraphQL

这些很重要，但**不要为了它们牺牲 Agent / Evaluation / the cloud provider AI**。

---

# 二十四、我特别建议你不要犯的错误

### ❌ 不要花大量时间背 Transformer

这个职位不是 ML Research Engineer。

你不需要深入：

```text
attention mathematics
backpropagation
CNN
RNN
```

达到研究级。

---

### ❌ 不要沉迷 Prompt Engineering

Prompt：

```text
You are a helpful assistant...
```

这种东西对于 Lead Engineer 权重很低。

---

### ❌ 不要把 Agent 当成 LangChain API

真正的日常工程落地考量：

> Why agent?

> Why workflow?

> Why multi-agent?

> Why not deterministic orchestration?

> How do you evaluate?

> How do you control cost?

> How do you secure tools?

---

# 二十五、你个人最大的优势和短板

结合你过去的经历，我反而认为这个职位与你的背景**匹配度相当高**。

### 你的优势

| 领域                   |                      你的基础 | 我的判断   |
| -------------------- | ------------------------: | ------ |
| Software Engineering |                 20+ years | ⭐⭐⭐⭐⭐  |
| Distributed Systems  |                        很强 | ⭐⭐⭐⭐⭐  |
| the cloud provider                  |                     有实际经验 | ⭐⭐⭐⭐   |
| SRE                  | 有实际 production experience | ⭐⭐⭐⭐⭐  |
| DevOps               |                        很强 | ⭐⭐⭐⭐⭐  |
| Kafka                |                     有生产经验 | ⭐⭐⭐⭐⭐  |
| Kubernetes           |                         有 | ⭐⭐⭐⭐   |
| ML systems           |      TikTok/GPU/Inference | ⭐⭐⭐⭐   |
| Python               |                         有 | ⭐⭐⭐⭐   |
| AI/LLM               |                     已经在转型 | ⭐⭐⭐⭐   |
| RAG                  |            有 ConvFinQA 项目 | ⭐⭐⭐⭐   |
| Agentic AI           |                  **需要强化** | ⭐⭐⭐    |
| Evaluation           |                  **需要强化** | ⭐⭐⭐    |
| MCP                  |                  **需要强化** | ⭐⭐/⭐⭐⭐ |
| TypeScript           |                  有基础/实际经验 | ⭐⭐⭐⭐   |

所以我不会建议你重新学一遍 Machine Learning。

**你的路线应该是：**

```text
已有能力
Software Engineering
       +
Distributed Systems
       +
the cloud provider
       +
SRE / DevOps
       +
ML / LLM
       ↓
━━━━━━━━━━━━━━━━━━━━
强化
Agentic AI
       +
RAG
       +
Evaluation
       +
LLM Observability
       +
AI Security
       ↓
━━━━━━━━━━━━━━━━━━━━
Lead AI Engineer
```

---

# 二十六、如果我是你，我会做一个“生产标杆级示范项目”

不要做 20 个小 demo。

只做 **一个 Production-grade Insurance AI Agent**。

例如：

## a leading global company Claims Copilot

```text
                ┌─────────────────────┐
                │   Customer Query    │
                └──────────┬──────────┘
                           ↓
                    Claims Agent
                           │
             ┌─────────────┼─────────────┐
             ↓             ↓             ↓
        Policy Agent   Document RAG   Claims Tool
             │             │             │
             ↓             ↓             ↓
          Policy DB     Vector DB     Mock API
             │             │             │
             └─────────────┼─────────────┘
                           ↓
                       LLM
                           ↓
                     Guardrails
                           ↓
                    Human Escalation
```

然后把下面全部做出来：

### AI

* RAG
* Agent
* Tool calling
* MCP
* LangGraph

### Engineering

* FastAPI
* Python
* TypeScript
* Docker
* Terraform

### the cloud provider

* Bedrock
* Lambda/ECS
* API Gateway
* S3
* DynamoDB
* IAM

### Production

* CI/CD
* tracing
* metrics
* logging
* evaluation
* cost tracking
* security

### Evaluation

做一个：

```text
100 test questions

             Baseline
                ↓
           Evaluation
                ↓
 ┌──────────────┼───────────────┐
 ↓              ↓               ↓
Retrieval     Answer          Safety
Recall        Accuracy        Score
 ↓              ↓               ↓
   └────────────┼───────────────┘
                ↓
          Regression Test
```

**这个项目比你刷 100 个 LangChain tutorial 有价值 10 倍。**

---

# 二十七、最后给你一个Lead AI Engineer 的工程主导心态

普通候选人回答：

> “I have experience with RAG and LangChain.”

Senior 候选人：

> “I built a RAG system using LangChain.”

Lead 候选人：

> **“Before choosing RAG, I first determine whether retrieval is actually required. Then I define measurable quality, latency, cost and safety objectives. I design the retrieval, agent orchestration and tool boundaries around those requirements, and establish evaluation and observability before putting the system into production.”**

这三种回答的层次完全不同。

---

## 我给这个岗位的“必考知识树”

```text
                     LEAD AI ENGINEER
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
      AI/LLM            Engineering           Cloud
        │                   │                   │
   ┌────┼────┐         ┌────┼────┐         ┌────┼────┐
   │    │    │         │    │    │         │    │    │
 Agent RAG Eval       Python DevSecOps    the cloud provider  IaC Security
   │    │    │         │    │    │         │    │    │
   │    │    │         │    │    │         │    │    │
LangGraph │ LLM Judge FastAPI CI/CD     Bedrock ECS IAM
Strands   │ Metrics   Async   Docker    AgentCore Lambda KMS
MCP       │ Tracing   Tests   K8s       API GW  S3   VPC
          │
     Hybrid Search
     Reranking
     Chunking
     Grounding
```

**如果这是我自己去拿这个职位，我接下来不会再泛泛地学 AI。**

我会直接进入 **企业级 Lead AI Engineer 架构实战与深度落地模式**：把这个 JD 拆成大约 **30 个高频核心架构议题**，然后逐个做到 **“即使老板或team lead深入追问3层也能给出扎实解法”**。

尤其是我会重点训练你这 **10 道题**：

1. **Design an enterprise Agentic AI platform**
2. **Design an insurance Claims Agent**
3. **RAG：为什么 retrieval 会失败？如何优化？**
4. **How do you evaluate an AI Agent?**
5. **How do you monitor an AI Agent in production?**
6. **LangGraph vs the cloud provider Strands vs AgentCore**
7. **How would you secure an Agent + MCP tools?**
8. **How do you control LLM cost and latency?**
9. **How do you deploy and regression-test a new LLM?**
10. **When should you NOT use an Agent?**

这 10 道题如果你能达到 **Lead/Principal level**，我认为会比单纯把 LangChain、LlamaIndex、OpenAI API 再学一遍有效得多。

另外，a leading global company 目前确实是在 Sydney 同时扩充 **Lead AI Engineer、Senior AI Engineer、AI Domain Architect**，公开招聘信息还明确把这次招聘描述为其 **agentic AI journey**，所以这不是普通的“职位 JD 堆关键词”，而是一个正在建设中的 AI engineering capability。([LinkedIn][5])

如果你准备投这个岗位，我下一步建议直接做一份 **“a leading global company Lead AI Engineer 30-Day Interview Plan”**，按你现有水平标出 **Already Strong / Need Refresh / Must Learn / Interview Critical**，再每天配具体 coding + system design + agentic AI 练习。

[1]: https://www.jobleads.com/au/job/senior-ai-engineer--north-sydney-council--ebf502f2e5703fbee421eb7600cc616f6?utm_source=chatgpt.com "Senior AI Engineer | North Sydney Council | JobLeads.com"
[2]: https://www.careers.a leading global company.com/job/North-Sydney-Lead-AI-Engineer/1370522657/?utm_source=chatgpt.com "Lead AI Engineer Job Details | a leading global company Insurance Company Ltd."
[3]: https://www.remoteitjobs.app/job/a leading global company-australia-senior-ai-engineer?utm_source=chatgpt.com "Senior AI Engineer [Remote Job] @a leading global company Australia"
[4]: https://sg.linkedin.com/in/jundali?utm_source=chatgpt.com "Kwan Tat L. - Morgan Stanley | LinkedIn"
[5]: https://fr.linkedin.com/in/danielle-leberre-30012816a?utm_source=chatgpt.com "Danielle Leberre - Poitiers et périphérie | Profil professionnel | LinkedIn"


# Confidence
可以。这个问题其实是**作为 Lead AI Engineer 在日常工作中架构设计上最值得深入推敲的一题**。

你不要把自己表达成“我知道几个 eval metric 的人”，而要表达成：

> **我把 AI Evaluation 当成 Production Quality Engineering，而不是模型测试。**

这句话一旦立住，你的层级就上来了。

---

# 1. 在日常工作中面对架构评审先给出一个 Lead-level 总框架

在日常工作中你的老板或者team lead会提问：

> **How would you design an evaluation framework for AI agents in production?**

你可以非常自信地说：

I would treat evaluation as a production engineering discipline rather than simply measuring model accuracy.

My evaluation framework would have four layers:

**First, offline evaluation.**
I would maintain a representative golden dataset covering normal cases, edge cases, adversarial cases and historical production failures. Every change to the model, prompt, retrieval strategy or agent workflow would run against this dataset before deployment.

**Second, component-level evaluation.**
For an agentic system, I don't only evaluate the final answer. I separately evaluate retrieval quality, tool selection, tool arguments, policy compliance, reasoning trajectory where appropriate, and final response quality. This allows us to identify where the failure actually occurred.

**Third, end-to-end evaluation.**
I would measure task success, correctness, groundedness, safety, latency and cost. For high-risk insurance use cases, I would also include human review for cases where automated evaluation is not sufficiently reliable.

**Fourth, continuous production evaluation.**
After deployment, I would sample production traces and continuously evaluate them. I would monitor quality metrics alongside traditional operational metrics such as latency, error rate and cost. Significant quality degradation would trigger investigation or rollback just like a traditional production regression.

The key principle is that evaluation should be part of the CI/CD lifecycle. A model or prompt change should not reach production simply because the application tests pass; it should also pass our AI quality, safety, latency and cost gates.

这段你如果能够**不背稿、自然讲出来**，已经是比较明显的 Lead-level。

---

# 2. 然后画出这个架构

架构设计与技术评审时在白板上直接绘制：

```text
                       Production AI System
                               │
                               ▼
                        ┌─────────────┐
                        │   Agent     │
                        └──────┬──────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
          Retrieval          Tools             LLM
              │                │                │
              └────────────────┼────────────────┘
                               │
                               ▼
                         Final Response
                               │
                               ▼
                    ┌────────────────────┐
                    │ Evaluation Layer   │
                    └─────────┬──────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
      Component             E2E                Safety
      Evaluation          Evaluation          Evaluation
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                    ┌──────────────────┐
                    │ Quality Gate     │
                    └────────┬─────────┘
                             ▼
                       Production
                             │
                             ▼
                       Monitoring
                             │
                             ▼
                    Production Samples
                             │
                             └──────────► Evaluation
```

然后补一句：

> **This creates a closed feedback loop between development, deployment and production.**

这个词非常重要：

## **closed-loop evaluation**

---

# 3. 但是顶级候选人和普通候选人的区别在这里

在日常工作中你的老板或者team lead很可能马上追问：

> **What exactly would you evaluate?**

不要回答：

> Accuracy and hallucination.

太浅。

你应该拆成：

```text
                    AI Evaluation
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
       ▼                 ▼                 ▼
    Retrieval         Agent              Generation
       │                 │                 │
   Recall@K          Tool selection     Correctness
   Precision@K       Tool arguments     Relevance
   MRR               Task completion    Groundedness
   NDCG              Loop detection    Faithfulness
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                         ▼
                    System Level
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           Latency      Cost       Safety
```

然后说：

> **I deliberately separate component metrics from end-to-end metrics, because a poor final answer doesn't necessarily mean the LLM is the problem.**

这是非常好的 Lead-level 表达。

---

# 4. 举一个保险公司的例子

这是你真正应该掌握的。

假设 a leading global company 有：

> **Claims Assistant**

用户问：

> “My laptop was damaged while travelling. Am I covered?”

系统：

```text
User
 ↓
Claims Agent
 ↓
Retrieve Policy
 ↓
Retrieve Travel Conditions
 ↓
Call Claims System
 ↓
LLM
 ↓
Answer
```

最后回答：

> “Yes, you're covered.”

但实际上应该：

> “No, accidental damage outside Australia isn't covered under this policy.”

普通开发者：

> **The LLM hallucinated.**

你：

> **I wouldn't immediately blame the LLM. I would trace the complete execution path.**

然后：

```text
Question
   ↓
Retrieval
   ↓
Wrong policy document
   ↓
LLM
   ↓
Incorrect answer
```

于是：

> **The failure is a retrieval failure, not necessarily a generation failure.**

这句话非常重要。

---

# 5. 然后你进一步说：Failure Attribution

这是我特别建议你掌握的概念。

## AI Eval 不应该只有一个 score

错误：

```text
Overall score = 82%
```

你根本不知道为什么。

好的 framework：

```text
Task Success                  91%
Retrieval Recall              87%
Tool Selection                96%
Tool Argument Accuracy        94%
Groundedness                  93%
Answer Correctness            91%
Safety                         99%
Latency                        95%
Cost                           92%
```

然后可以知道：

> **Retrieval is currently our biggest quality bottleneck.**

这就是 **diagnostic evaluation**。

---

# 6. 你还需要一个非常重要的概念：Golden Dataset

在日常工作中你的老板或者team lead会提问：

> Where do your evaluation datasets come from?

回答不要只是：

> We create test cases.

应该说：

```text
Golden Dataset
      │
      ├── Expert-created cases
      ├── Historical production cases
      ├── Synthetic cases
      ├── Edge cases
      ├── Adversarial cases
      └── Previous production failures
```

特别是：

> **Every production failure should have the potential to become a regression test.**

这是非常强的一句话。

意思是：

```text
Production failure
       ↓
Root cause
       ↓
Add test case
       ↓
Golden dataset
       ↓
Future deployments
       ↓
Never regress
```

这就是 Software Engineering + AI Engineering 的结合。

你的背景其实非常适合讲这个。

---

# 7. LLM-as-a-Judge 怎么说才不会显得幼稚

在日常工作中你的老板或者team lead很可能会提问：

> **Would you use an LLM to evaluate another LLM?**

不要说：

> Yes, use GPT-5 as judge.

太浅。

你应该说：

> **Yes, but I wouldn't treat an LLM judge as ground truth.**

然后：

```text
                    Evaluation
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
    Programmatic      LLM Judge         Human
       │                 │                 │
 exact match        semantic quality   expert review
 schema              groundedness      high-risk cases
 policy rules        relevance         ambiguous cases
 latency             style
```

然后：

> I would calibrate the LLM judge against human-labelled examples and periodically measure judge-human agreement.

这句话非常重要。

---

# 8. Insurance 场景尤其要强调 Risk-based Evaluation

这是 a leading global company 和普通 SaaS 最大的区别之一。

你可以主动说：

> **For insurance, I would not treat every AI interaction equally.**

例如：

```text
Low Risk
│
├── FAQ
├── Policy explanation
└── General information

Medium Risk
│
├── Claim guidance
├── Coverage interpretation
└── Document summarisation

High Risk
│
├── Claim decision
├── Payment decision
├── Legal interpretation
└── Customer eligibility
```

风险越高：

```text
Human review ↑
Automation ↓
Evaluation strictness ↑
Auditability ↑
```

所以：

> **The evaluation threshold should be risk-based rather than one global threshold for the entire platform.**

这个非常像真正做过 enterprise AI governance 的人。

---

# 9. Production Evaluation 和 Offline Evaluation 要分开

这是日常工程实践中非常体现架构功底、容易拉开差距的地方。

### Offline

```text
Code change
   ↓
Golden dataset
   ↓
Evaluation
   ↓
PASS / FAIL
```

### Production

```text
Real traffic
     ↓
Sampling
     ↓
Trace
     ↓
Evaluation
     ↓
Quality metrics
     ↓
Drift detection
```

然后你可以说：

> Offline evaluation tells me whether the candidate version is better before deployment. Production evaluation tells me whether it remains good under real-world traffic and distribution.

非常好。

---

# 10. 最后一定要讲 Evaluation Gate

这是 **Lead Engineer** 必须讲出来的。

例如：

```text
                 Pull Request
                       │
                       ▼
                 Unit Tests
                       │
                       ▼
               Integration Tests
                       │
                       ▼
                AI Evaluation
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
   Accuracy         Safety           Cost
      ≥90%            99%            <$X
       │               │                │
       └───────────────┼────────────────┘
                       ▼
                  Deployment
                       │
                       ▼
                    Canary
                       │
                       ▼
              Production Eval
                       │
                ┌──────┴──────┐
                ▼             ▼
              Good          Bad
                │             │
                ▼             ▼
             Rollout       Rollback
```

一句话：

> **AI evaluation becomes a deployment gate, not a dashboard that nobody acts on.**

非常强。

---

# 11. 在日常工作中你的老板或者team lead会提问：What metrics?

你可以直接回答：

### Retrieval

* Recall@K
* Precision@K
* MRR / NDCG
* Context relevance

### Generation

* correctness
* relevance
* faithfulness
* groundedness
* completeness

### Agent

* task completion rate
* tool selection accuracy
* tool argument accuracy
* unnecessary tool calls
* loop rate
* escalation rate

### Production

* latency
* token consumption
* cost/request
* error rate
* availability

### Safety

* policy violation
* PII leakage
* prompt injection resistance
* unsafe tool invocation

---

# 12. 在日常工作中你的老板或者team lead会提问：How do you know your evaluation is reliable?

这是**高级追问**。

你回答：

> **Evaluation itself needs to be evaluated.**

然后：

```text
Human-labelled Dataset
          ↓
      LLM Judge
          ↓
   Compare results
          ↓
 Agreement / Correlation
          ↓
 Calibrate judge
          ↓
 Periodic re-validation
```

然后补：

> For high-risk decisions, I would retain human-in-the-loop evaluation rather than relying entirely on automated judges.

这就很稳。

---

# 13. 最后给你一段真正作为 Lead AI Engineer 在日常工作中向团队与主管阐述方案的标准版本

不要背整段，但你可以练到自然说出来：

For a production AI system, I would treat evaluation as part of the engineering lifecycle, not as a one-time model benchmark.

I would build a layered evaluation framework.

At the bottom, we have a versioned golden dataset containing representative business cases, edge cases, adversarial cases and historical production failures.

Then I evaluate the system at multiple levels. For RAG, I measure retrieval quality separately. For agents, I evaluate tool selection, tool arguments, task completion and unnecessary or looping behaviour. At the generation layer, I measure correctness, relevance, groundedness and faithfulness.

Then I have end-to-end evaluation for the actual business outcome.

I also separate automated evaluation from human evaluation. LLM-as-a-judge can be useful for semantic quality, but I would calibrate it against human-labelled examples and never treat the judge as absolute ground truth.

For an insurance environment, I would make the evaluation risk-based. A policy FAQ can have a different automation threshold from a claim or payment decision, where we need much stronger controls and potentially human approval.

Finally, I would close the loop with production observability. We sample real production traces, continuously evaluate them for quality, safety, latency and cost, and feed significant failures back into the golden dataset as regression tests.

Most importantly, the evaluation needs to become an engineering gate. A prompt, model, retrieval or agent workflow change should only reach production if it passes predefined quality, safety, latency and cost thresholds.

That gives us a continuous loop:

```flowchart
**build → evaluate → deploy → observe → learn → regression test → improve.**
```

That's how I would make AI quality measurable and continuously improve it in production.

---

## 你要真正记住的不是 20 个 metric，而是这 6 个词

在日常工作中如果需要快速抓住架构本质，只记住：

```flowchart
> **Dataset → Component → End-to-End → Risk → Production → Feedback Loop**
```

然后展开：

```text
Dataset
   ↓
Component Evaluation
   ↓
E2E Business Outcome
   ↓
Risk-based Threshold
   ↓
Production Monitoring
   ↓
Feedback → Regression Dataset
```

这就是你回答 **“How do you build a production-grade AI evaluation framework?”** 的骨架。

而且这个问题与你自己的背景非常契合：你不是从“LLM prompt engineer”起步，而是有 **SRE + distributed systems + ML inference + production engineering** 背景。你真正应该卖给 a leading global company 的差异化不是“我比别人更会 prompt”，而是：

> **“I know how to turn probabilistic AI behaviour into an observable, testable and governable production system.”**

这句话，我建议你重点练熟。


---


# 133976
# JD
Lead AI Engineer
133976
A new transformational adventure awaits you… 

 

How does 5 weeks of annual leave, a fulfilling career you'll genuinely enjoy, and working for a reputable organization that promotes wellbeing and drives digital transformation sound to you?

 

As one of Forbes 2024 ‘World’s Best Employers’ and Fortune’s ‘World’s Most Admired Companies’ for 2025, a leading global company - a leader in the insurance industry, is on a journey towards a brighter future… A brighter future for you - focused on your career, your wellbeing, and your community - as well as our customers and the planet.

 

Join us on this thrilling journey as we work towards our vision of becoming Australia's leading digital insurer. If you're eager to be part of a values-driven global organisation that's experiencing real growth and transformation, and if you share our commitment to making a tangible difference and taking continuous steps towards a sustainable future for our people, customers, communities, and our planet, then keep reading!

 

 

Let’s create a brighter future together, let’s make a difference  

 

It’s important to know, what you do matters. At a leading global company, we don’t just cover, we care.

 

As a Lead Engineer within our ZX initiative, you’ll play a key role in shaping the future of AI-led insurance at a leading global company. This is a greenfield opportunity to design and build agent-based solutions from the ground up, working on complex problems that directly impact customer outcomes and business performance. You’ll operate across the full lifecycle, from early experimentation through to production, delivering scalable and reliable AI-native systems.

 

You’ll work closely with engineering, product, and design teams to bring agentic systems to life. This is a hands-on leadership role where you’ll set technical direction, uplift engineering standards, and help define how we build, evaluate, and scale AI solutions in a modern, cloud-native environment.

 

You will also be responsible for the following:

 

Lead the end-to-end development of AI agents and agentic orchestration solutions in production environments
Drive engineering excellence through strong DevSecOps and AIOps practices, ensuring security, reliability, and resilience
Establish robust evaluation, monitoring, and observability frameworks to improve quality, accuracy, and performance
Build scalable, reusable components and contribute to shared frameworks, standards, and internal documentation
Optimise developer productivity through AI-powered engineering tools and automation across the delivery lifecycle
Collaborate with cross-functional teams to solve real customer and business problems using AI-native approaches
 

Important to your success – let’s grow together

You are a hands-on technical leader who thrives in ambiguity and brings structure to complex problems. You collaborate openly, challenge thinking constructively, and take ownership of outcomes while supporting others to do their best work.

In order to be successful, you will have the following:

Extensive experience in software engineering, machine learning, or data science within cloud-native environments
Strong programming capability across languages such as Python and TypeScript, with experience using modern AI frameworks
Proven experience building AI agents, RAG pipelines, or agentic systems using LLM-based development frameworks
Deep understanding of AI evaluation, observability, and optimisation techniques to improve model performance and reliability
Experience with the cloud provider services and infrastructure as code tools to design and manage scalable cloud solutions
Strong knowledge of DevSecOps, data engineering concepts, and working in Agile, product-led delivery environments
 

Belong. a leading global company is here to support you 

 

There are so many reasons why a leading global company is a great place to be and the right choice for you, but here are just a few.

 

Enjoy 5 weeks of annual leave for permanent staff through our Z leave initiative, along with 15 days of personal/carer’s leave as we empower our people to manage their own wellbeing. Plus, access to Family Care (parental leave).
Benefit from a hybrid working arrangement – 3 days in the office and 2 days working from home per week for full-time employees.
Access programs to stay healthy and feel healthier, receive an AUD$500 wellbeing payment per year, and a AUD$295 new starter e-voucher for your work-from-home setup (flex work - hybrid working), along with other great benefits through our Shine portal.
Grow and thrive in your career with our award-winning training programs. We support and encourage your development because our strength lies in our people, and we value your individuality.
Work with global, diverse, and inclusive teams; explore your passions, fuel innovation, drive equity, collaborate, and make a positive difference beyond your role.
Take advantage of global mobility opportunities across more than 200 countries worldwide.
Volunteer and work in our state-of-the-art Green Star rated offices (when you are in the office) and dress for your day.
We plant a tree for every new employee.
Not to mention our various employer of choice awards/memberships – WGEA; Family Inclusive Workplace; Gold AWEI Employer, Pride in Diversity… to name a few.
 

We could go on, but the main point is that a leading global company is a great place to be, where you can truly belong, be yourself, maintain work/life balance, and thrive in a supportive environment.

 

a leading global company is an equal opportunity employer.  We are committed to ensuring that our recruitment process is fair and accessible for all candidates. If you require any special accommodations to participate in our recruitment process, we encourage you to please let us know at the time of your application.  

 

So, if you want to come on an adventure that will build a brighter future together, and feel a sense of togetherness, then please apply today to start your adventure!

# AI guide to prepare

## claude
下面按"如果作为企业级 Lead AI Engineer 主导该岗位架构与落地"来拆。

## 一、这个 JD 真正在考什么（按权重排序）

JD 里出现两次以上的词才是真正的痛点。这份 JD 反复强调 **evaluation / observability / production**，而不是"会用 LangChain"。说明他们大概率已经有能跑的 demo，但卡在"怎么证明它靠谱、怎么上线、怎么规模化"。

| 权重 | 考察点 | 团队与管理层真正关注的核心价值 |
|---|---|---|
| ★★★★★ | **把 agent 送进生产的真实经验** | 流量规模、失败率、回滚方式、成本、人机交接点、线上事故与根因 |
| ★★★★★ | **Eval 体系** | 黄金测试集怎么建、trajectory eval vs 最终答案 eval、LLM-as-judge 怎么校准、怎么进 CI 做回归 |
| ★★★★☆ | **非确定性系统的可靠性工程** | 幂等、超时、重试、降级、tool 调用失败处理、guardrails、prompt injection |
| ★★★★☆ | **架构判断力** | 什么时候**不该**用 agent；单 agent vs 多 agent;context engineering;成本/延迟权衡 |
| ★★★☆☆ | **the cloud provider 具体性** | Bedrock(含 Guardrails/Knowledge Bases/AgentCore)、Step Functions、Lambda/Fargate、OpenSearch 或 Aurora pgvector、IAM 最小权限、Terraform/CDK |
| ★★★☆☆ | **Lead 的"带结构进混沌"** | 怎么在需求不清时收敛范围、怎么建标准而不是自己闷头写、怎么提 code review 和文档水位 |
| ★★★☆☆ | **保险合规直觉** | local regulators CPS 230(运营韧性)、CPS 234(信息安全)、Privacy Act、理赔/核保决策必须留痕和可解释、公平性 |
| ★★☆☆☆ | TypeScript / 开发者效能 | 前端 agent UI、内部 AI 工具链、怎么量化团队提效 |

JD 里 "greenfield"、"thrives in ambiguity"、"hands-on leadership" 三个词连在一起,翻译过来是:**我们没人能定技术方向,需要一个能自己把需求拆出来、还愿意自己写代码的人。** 在日常工作中你要主动表现"我来帮你们把问题结构化",而不是等着被问。

## 二、红线——听到这几类回答我会直接 reject

**技术红线**

1. **没有 eval,靠感觉**。"我们 prompt 调得挺好的,人工看了几个 case 觉得不错" —— 这是 demo 工程师和生产工程师的分水岭,这岗位一票否决。
2. **RAG 只会说"丢进向量库搜一下"**,说不出 chunking 策略、hybrid search、reranking、recall@k / context precision 怎么量。
3. **"agent 输出不确定所以没法测试"**。正确答案是分层测:tool 层确定性单测 + trajectory 断言 + 任务成功率的统计性回归 + 线上在线指标。说"没法测"等于说"我没上过线"。
4. **对 PII / 合规无感**:"客户数据直接调 OpenAI API 就行"、"脱敏不归我管"。保险公司,在企业级合规场景下，这种设计在生产环境中是绝对不合格的。
5. **安全盲区**:不知道 prompt injection、不区分可信/不可信输入、agent 的 tool 权限随便给(OWASP LLM Top 10 里的 excessive agency)。
6. **框架名词党**:满嘴 LangGraph / CrewAI,但问不出 token 成本怎么算、context window 怎么管、为什么选它而不是自己写 orchestration。
7. **多 agent 万能论**:什么都上多 agent,说不清"其实这个场景一个 routing workflow 就够了"。
8. **幻觉的解法是"写更好的 prompt"**,而不是系统性约束(结构化输出、引用强制、检索约束、校验层、HITL)。

**行为红线**

9. 贬低前同事或前雇主、把失败全推给"业务需求变了"。
10. "我只负责写代码,标准/文档不是我的事" —— 直接与 JD 的 lead 定位冲突。
11. 简历注水:说"我做过 X",追问实现细节就开始模糊、改口、转话题。在架构评审中一旦出现一次含混,整场的可信度全部重算。
12. 对任何技术选型都没有 trade-off,只有信仰("Claude 就是比 GPT 好")。
13. 讲不出一次真实失败和根因。Lead 岗没有事故故事 = 没上过生产。
14. "AI 生成的代码我不 review" / "我用 Cursor 一把梭"。

## 三、该准备的知识清单(按补课优先级)

**必须能白板讲清楚的**

- **Agent 模式谱系**:prompt chaining / routing / parallelization / orchestrator-workers / evaluator-optimizer,以及"什么时候退回到确定性 workflow"。这是最能体现 senior 判断力的一段。
- **Eval 工程**:离线黄金集的构造与标注成本、任务级成功率、步骤级 trajectory 评估、LLM-as-judge 与人工标注的一致性校准(别只说用 judge,要说你怎么验证 judge 本身)、CI 里的回归套件、线上 A/B 与 canary、cost/latency SLO。
- **Observability**:OpenTelemetry GenAI semantic conventions、每次 tool 调用一个 span、token 与成本归因到 feature、trace 里的 PII 脱敏、Langfuse/LangSmith/Arize/Bedrock 原生这几条路线的取舍。
- **Context engineering**:压缩、sub-agent 隔离上下文、外部记忆、tool 设计原则(少而正交,描述即接口)。你手上的 MCP 经验在这里是直接加分项。
- **the cloud provider 落地图**:Bedrock + Guardrails、Step Functions 做长流程编排、SQS 做异步、Fargate/Lambda 的选择依据、向量层选 OpenSearch Serverless 还是 Aurora pgvector、PrivateLink/KMS/IAM、Terraform 或 CDK 管 prompt 与 model 版本。
- **保险场景**:挑 1–2 个具体用例想透架构,比如理赔分流(文档抽取 + 规则 + agent,人工复核在哪一步)、核保辅助、客服 copilot。能主动说"这个场景我会把最终决策留给人,因为 CPS 230 下要可追溯",加分极大。

**你已有但没包装好的弹药**(这块最值钱,优先做)

- `prod-guard.py` 那个"对不可逆操作强制人工审批"的 hook —— 这正是 excessive agency 的工程解,直接对应 JD 的 DevSecOps 和保险的 HITL 要求。
- MCP server 架构 + 多 repo agent client —— 对应"可复用组件与共享框架"。
- Cursor AI skills registry 治理团队 AI 工具蔓延 —— 几乎逐字命中 JD 第 5 条 "optimise developer productivity through AI-powered engineering tools"。这条很少有候选人答得上,务必准备成一个完整故事。
- MWAA/Airflow 3 的蓝绿升级 —— 生产可靠性、迁移风险控制的硬证据。

**需要诚实补的短板**:大规模生产 agent 的线上数字、Bedrock 的一手使用经验、TypeScript。短板的正确处理不是掩盖,是"我没在 Bedrock 上做过 X,但我在 Y 上做过等价的事,迁移成本我估计在 Z",架构设计与工程治理真正需要的是可校准性。

## 四、两天的安排(工程实施规划)

**Day 1 上午(3h)— 弹药整理**
把经历压成 4 个故事,每个必须带数字和一次失败:① 生产可靠性(MWAA 蓝绿);② 自建 agent 基础设施(MCP + prod-guard);③ 团队提效与标准(skills registry);④ 跨团队在模糊需求中收敛范围。每个写成 6–8 句,练到能脱稿 2 分钟讲完。

**Day 1 下午(3h)— 补最可能被问倒的**
专攻 eval + observability,输出一页自己的《Agent 质量工程方法论》:指标分层、黄金集建设、judge 校准、CI 回归、线上监控。这一页是你日常架构评审与方案沟通的核心武器,在技术评审与白板沟通时能直接清晰绘制。

**Day 1 晚上(1.5h)— the cloud provider 对照**
把你熟悉的实现逐个映射到 Bedrock / Step Functions / OpenSearch 的对应物,准备好"为什么这样选"的 trade-off 一句话版。

**Day 2 上午(3h)— 模拟**
给自己出一道题:"为 a leading global company 设计一个理赔文档处理 agent,日均 2 万件,必须可审计"。限时 45 分钟自己讲+画,录音回放。重点检查:有没有主动问澄清问题、有没有讲 eval 和回滚、有没有讲成本。

**Day 2 下午(2h)— 收尾**
对照上面的红线逐条自查你的常用表达;准备 6–8 个反问(ZX 现在有几个 agent 在生产?eval 归谁 own?合规审批链路多长?团队多大、我带谁?hands-on 占比多少?);确认薪资与雇佣形式口径(这是 permanent 岗,和你现在的 contracting 模式不同,提前想好怎么说)。

**Day 2 晚上**:只做轻量复习,早睡。最后一天往脑子里塞新知识的边际收益是负的。

一句总结:作为 Lead AI Engineer，日常工作核心价值在于"我知道怎么让 agent 在受监管行业里稳定跑起来",而不是"我会搭 agent"。

需要的话,我可以把那一页《Agent 质量工程方法论》和 4 个 STAR 故事的框架直接给你写成文档。

## OpenAI 
我认真看了这份 a leading global company Australia Lead AI Engineer 133976 的 JD，也查了 a leading global company 目前同时招聘的 Senior AI Engineer / AI Domain Architect。我的判断很明确：

```flowchart
这不是一个“懂 GenAI 的 Senior Software Engineer”岗位，而是一个“能把 Agentic AI 平台从 0 → Production 的 Lead AI Engineer”岗位。
```

而且有一个非常重要的新信息：a leading global company 同期的 Senior AI Engineer 招聘明确提到了 LangGraph、the cloud provider Strands、AgentCore、MCP、Bedrock、Lambda、API Gateway、DynamoDB/RDS、SageMaker、ECS、S3、IAM、CDK/Terraform。这比你给我的 Lead JD 更能暴露他们实际想要的技术方向。

所以，如果我是准备拿 最高分 / Strong Hire 的候选人，我不会平均用力，而会按下面这个优先级准备。

⸻

一、先给你结论：必须掌握的技术

如果把这个职位拆成 100 分，我会这样分：

能力	权重	必须达到
Agentic AI / LLM Engineering	25%	⭐⭐⭐⭐⭐
RAG / Retrieval / Knowledge Architecture	15%	⭐⭐⭐⭐⭐
AI Evaluation / Observability / Guardrails	15%	⭐⭐⭐⭐⭐
the cloud provider AI Architecture	15%	⭐⭐⭐⭐⭐
Python + TypeScript	10%	⭐⭐⭐⭐
Production / DevSecOps / AIOps	10%	⭐⭐⭐⭐⭐
System Design / Distributed Systems	5%	⭐⭐⭐⭐⭐
Data Engineering / MLOps	5%	⭐⭐⭐⭐

最关键的是：

Agent + RAG + Evaluation + the cloud provider + Production

这五个东西形成闭环。

⸻

二、我认为他们真正想找的人

JD 表面上写：

AI agents
RAG
agentic orchestration
evaluation
observability
the cloud provider
DevSecOps

但实际上他们在找的是这样的人：

```flowchart
                    Business Problem
                           │
                           ▼
                    AI Product Design
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
           RAG                         Agent
             │                           │
             │                    ┌──────┴──────┐
             │                    │             │
             ▼                    ▼             ▼
        Retrieval              Tools        Planning
             │                    │             │
             └───────────┬────────┴─────────────┘
                         ▼
                       LLM
                         │
                         ▼
                Guardrails / Security
                         │
                         ▼
              Evaluation / Observability
                         │
                         ▼
              the cloud provider Production Platform
                         │
                         ▼
                 Customer / Business
```

这才是 Lead AI Engineer。

不是：

“我会调用 GPT API。”

⸻

三、第一优先级：Agentic AI

这是整个岗位最核心的部分。

JD 第一条 responsibility 就是：

Lead the end-to-end development of AI agents and agentic orchestration solutions in production environments. 

而 a leading global company 同期 Senior AI Engineer 已经进一步点名：

* LangGraph
* the cloud provider Strands
* AgentCore
* MCP
* multi-agent orchestration
* tool use
* prompt engineering

所以我会把这一块作为你的 第一重点。

⸻

你必须真正理解 Agent，而不是只会框架 API

至少要能解释：

1. Agent vs Workflow

这是非常容易被问的。

```flowchart
Workflow
A → B → C → D
Agent
          ┌→ Tool A
LLM ──────┼→ Tool B
          ├→ Tool C
          └→ Human
             ↓
          Next Action
```

你必须知道：

如果流程可以确定性描述，就不要使用 Agent。

例如：

```flowchart
Receive claim
      ↓
Validate policy
      ↓
Retrieve documents
      ↓
Calculate eligibility
      ↓
Generate response
```

这是 workflow。

而：

“根据客户的问题决定需要查什么资料、调用哪个系统、是否需要人工介入。”

才更像 agent。

⸻

四、第二个必须掌握：Agent Architecture

我会要求自己能够白板画出：

```flowchart
                    User
                     │
                     ▼
                 API Gateway
                     │
                     ▼
              Agent Orchestrator
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       Planner     Retriever    Tools
          │          │          │
          │          ▼          ├── Policy API
          │       Vector DB     ├── Claims API
          │          │          ├── Customer API
          │          │          └── Search
          │          │
          └──────┬───┘
                 ▼
                LLM
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
     Guardrail  Eval    Memory
        │
        ▼
   Final Response
```

然后继续往下面：

```flowchart
          ┌─────────────────────┐
          │ Observability        │
          │                     │
          │ latency             │
          │ token usage         │
          │ cost                │
          │ tool calls          │
          │ traces              │
          │ errors              │
          │ quality             │
          └─────────────────────┘
```

这会非常符合 a leading global company 的 JD。

⸻

五、第三个核心：RAG

这个你应该重点准备，因为你已经有 ConvFinQA / RAG 相关经历，这实际上可以成为你的优势。

但不要停留在：

```flowchart
embedding → vector DB → similarity search → LLM
```

Lead Engineer 要能回答：

为什么 RAG 会失败？

至少要知道：

Retrieval failure

```flowchart
Question
   ↓
Embedding
   ↓
Retriever
   ↓
Wrong documents
   ↓
LLM
   ↓
Wrong answer
```

所以：

LLM quality ≠ RAG quality

⸻

六、RAG 必须掌握到这个深度

我会要求自己能够解释：

Retrieval

* Dense retrieval
* Sparse retrieval / BM25
* Hybrid search
* Metadata filtering
* Semantic search
* Query rewriting
* Multi-query
* Parent-child retrieval
* Hierarchical retrieval

Ranking

* similarity score
* reranking
* cross-encoder
* top-k
* score threshold

Chunking

必须理解：

```flowchart
Document
    ↓
Structure-aware chunking
    ↓
semantic chunks
    ↓
embedding
```

而不是机械：

text[i:i+500]

⸻

七、RAG Evaluation 是 Lead 的分水岭

普通 AI Engineer：

“我们的回答准确率不错。”

Lead：

“How do you know?”

这是日常架构落地与技术评审中非常关键的问题。

你应该能建立：

```flowchart
                   Evaluation
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
 Retrieval          Generation      System
 Evaluation         Evaluation      Evaluation
        │              │              │
 Recall@K           Faithfulness     Latency
```
 Precision@K        Relevance        Cost
 MRR                Correctness      Reliability
 NDCG               Groundedness     Availability

⸻

八、AI Evaluation：我认为这是这个职位最重要的隐藏考点

JD 特别强调：

Establish robust evaluation, monitoring, and observability frameworks

这不是普通 prompt engineering。

你要能回答：

“How would you evaluate an AI agent in production?”

我的标准答案框架：

1. Offline evaluation
2. Online evaluation
3. Component-level evaluation
4. End-to-end evaluation
5. Safety evaluation
6. Cost / latency evaluation
7. Human evaluation

⸻

九、Agent Evaluation 更复杂

例如一个 Claims Agent：

```flowchart
User
 ↓
Agent
 ↓
Retrieve policy
 ↓
Call claims API
 ↓
Calculate eligibility
 ↓
Generate answer
```

最终回答错了。

你不能只说：

LLM hallucinated.

你需要知道：

```flowchart
Was retrieval wrong?
       ↓
Was tool selection wrong?
       ↓
Were tool arguments wrong?
       ↓
Was tool result interpreted incorrectly?
       ↓
Was reasoning wrong?
       ↓
Was final generation wrong?
```

这就是 Agent observability + evaluation。

⸻

十、Observability：你必须从“系统监控”升级到“LLM Observability”

你原来的 SRE 背景在这里其实非常有价值。

传统：

CPU
Memory
Latency
Error Rate
Availability

AI system：

```flowchart
Request
  ↓
LLM call
  ↓
Prompt
  ↓
Retrieval
  ↓
Tool call
  ↓
Tool result
  ↓
LLM call
  ↓
Final response
```

因此需要 trace：

```flowchart
trace_id
├── prompt
├── model
├── tokens
├── latency
├── retrieval
│   ├── query
│   ├── documents
│   └── scores
├── tool_call
│   ├── tool
│   ├── arguments
│   └── result
└── response
```

然后监控：

* token usage
* cost
* latency
* model errors
* hallucination
* retrieval quality
* tool failure
* agent loop
* guardrail violations

⸻

十一、你的 SRE 背景在这里反而是优势

你过去做的：

```flowchart
zombie GPU nodes → synthetic health check → automatic drain
```

这种故事其实非常适合迁移成：

AI Agent reliability engineering

例如：

```flowchart
Agent stuck
   ↓
Repeated tool calls
   ↓
Token explosion
   ↓
Cost explosion
```

怎么办？

max_iterations
max_tokens
timeout
circuit breaker
budget limit
tool timeout
fallback model
human escalation

这就是 Lead AI Engineer 思维。

⸻

十二、the cloud provider：这里不能只会“用过 the cloud provider”

a leading global company 明显是 the cloud provider-first。

他们同时招聘的 Senior AI Engineer 已经列出了：

* Amazon Bedrock
* AgentCore
* Lambda
* API Gateway
* DynamoDB / RDS
* SageMaker
* ECS
* S3
* IAM
* CDK / Terraform

所以我会把 the cloud provider 分成三个层次。

⸻

Level 1：必须熟

Bedrock

必须知道：

* Foundation Models
* inference
* model selection
* embeddings
* Knowledge Bases
* Guardrails
* Agents
* model evaluation
* provisioned throughput / cost considerations

⸻

Level 2：必须能设计

```flowchart
API Gateway
     ↓
Lambda / ECS
     ↓
Agent
     ↓
Bedrock
     ↓
S3 / DynamoDB / RDS
```

必须理解：

* IAM
* VPC
* Secrets Manager
* KMS
* CloudWatch
* EventBridge
* SQS
* SNS

⸻

十三、AgentCore / Strands / LangGraph

这里我会特别提醒你。

不要同时浅学 10 个 Agent Framework。

最高效的方法：

主攻

LangGraph

理解：

State
Node
Edge
Conditional Edge
Checkpoint
Interrupt
Human-in-the-loop
Persistence

然后：

the cloud provider 原生

the cloud provider Strands / AgentCore

至少知道它们解决什么问题。

a leading global company 的招聘信息已经明确出现这些技术，所以在日常工作中经常需要进行针对特定框架的深度技术研讨（framework-specific discussion）。

⸻

十四、MCP 必须知道

我会给 MCP：

8/10 必须掌握。

尤其是 Agentic AI。

你要理解：

```flowchart
Agent
  │
  │ MCP
  ▼
MCP Server
  │
  ├── Tool
  ├── Resource
  └── Prompt
```

以及：

为什么 MCP 比每个 Agent 自己写 integration 更适合企业级生态？

还要谈：

* authentication
* authorization
* tool permissions
* data leakage
* trust boundary
* malicious tool
* prompt injection

⸻

十五、Security：Insurance 公司这里会非常重要

a leading global company 不是普通 startup。

所以你必须准备：

LLM Security

* Prompt Injection
* Indirect Prompt Injection
* Data Exfiltration
* Sensitive Data
* PII
* Excessive Agency
* Tool Abuse
* Jailbreak
* Hallucination
* Supply-chain risk

⸻

Agent Security

这是一个在日常工程架构中非常核心的研讨议题：

“What happens if the LLM decides to call a dangerous tool?”

错误答案：

Prompt 告诉模型不要调用。

正确方向：

```flowchart
LLM
 ↓
Policy Layer
 ↓
Authorization
 ↓
Tool
```

也就是：

Never trust the LLM as the security boundary.

这一句话非常值得你记住。

⸻

十六、DevSecOps

JD 明确：

DevSecOps and AIOps

所以你必须把：

```flowchart
Git
 ↓
CI
 ↓
Unit Tests
 ↓
Security Scan
 ↓
Build
 ↓
Deploy
 ↓
Evaluation
 ↓
Canary
 ↓
Production
 ↓
Monitoring
```

说清楚。

尤其是：

AI CI/CD

普通软件：

```flowchart
tests pass → deploy
```

AI：

```flowchart
tests pass
     ↓
evaluation pass
     ↓
safety pass
     ↓
cost threshold
     ↓
latency threshold
     ↓
deploy
```

这就是很好的 Lead-level answer。

⸻

十七、Python：你必须达到这个程度

不是“会 Python”。

而是能够现场：

FastAPI
Pydantic
asyncio
httpx
pytest
typing
dataclasses

并写：

LLM service
RAG service
Agent tool
API
evaluation pipeline

你之前提到想保持手动 coding 能力，这个职位非常适合你这样练。

我甚至建议你：

不要让 AI 给你生成这些代码。

自己写。

⸻

十八、TypeScript：不要忽略

因为 JD 明确：

Python and TypeScript

而 a leading global company 同期 Senior AI Engineer 更进一步要求：

TypeScript + Node.js + Python + React/Next.js

你不需要成为 TypeScript 专家。

但是至少能够：

interface AgentRequest {
   query: string;
   userId: string;
   context?: Record<string, unknown>;
}

并理解：

* async/await
* Promise
* interfaces
* types
* generics
* Node.js
* REST API
* streaming

⸻

十九、System Design：你本来就应该有优势

你的 Distributed Systems / SRE / Kafka / Kubernetes / the cloud provider 背景，在这个职位应该转化成：

AI System Design

我会准备至少这 8 道：

1

Design an enterprise AI Agent platform

2

Design a Claims Agent

3

Design a RAG platform for insurance documents

4

Design multi-agent orchestration

5

Design an LLM evaluation platform

6

Design AI observability platform

7

Design secure enterprise MCP platform

8

Design 1M requests/day AI service

⸻

二十、其中最重要的一道：Design an Insurance Claims Agent

我认为这是你应该重点准备的。

因为目前 a leading global company 的公开招聘信息明确提到其 Agentic AI journey 与 Claims Transformation 有关。

假设：

Customer asks:
“Can I claim this damaged laptop?”

你的架构：

```flowchart
                  Customer
                     │
                     ▼
                 API Gateway
                     │
                     ▼
               Claims Agent
                     │
        ┌────────────┼─────────────┐
        ▼            ▼             ▼
     Policy       Document       Claims
     Tool         Retrieval       Tool
        │            │             │
        ▼            ▼             ▼
      Core        Vector DB      Claims DB
     Systems
        │
        └────────────┬────────────┘
                     ▼
                 LLM / Agent
                     │
             ┌───────┴────────┐
             ▼                ▼
        Guardrails          Human
             │             Escalation
             ▼
           Answer
```

在日常工作中你的老板或者team lead会继续提问：

How do you prevent hallucination?

How do you evaluate it?

How do you monitor it?

What if the policy document changes?

What if the tool is unavailable?

What if the agent enters an infinite loop?

How do you protect customer PII?

How much does one request cost?

How do you deploy a new model?

这才是真正的 Lead AI Engineer 深度架构实践。

⸻

二十一、我会给你的技术优先级

如果只有 4 周：

🔴 Tier 1 — 必须达到 9/10

Agentic AI

* Agent architecture
* Tool calling
* Planning
* State
* Memory
* Multi-agent
* Human-in-the-loop
* LangGraph
* Strands
* AgentCore
* MCP

RAG

* chunking
* embeddings
* hybrid retrieval
* reranking
* query rewriting
* metadata filtering
* retrieval evaluation

AI Evaluation

* correctness
* relevance
* faithfulness
* groundedness
* retrieval recall
* precision
* end-to-end evaluation
* LLM-as-judge
* human evaluation

Production AI

* observability
* tracing
* guardrails
* security
* cost
* latency
* reliability

⸻

二十二、Tier 2 — 8/10

the cloud provider

Bedrock
AgentCore
Lambda
ECS
API Gateway
S3
DynamoDB
RDS
IAM
CloudWatch
SQS
EventBridge
Secrets Manager
KMS

IaC

Terraform
the cloud provider CDK

DevSecOps

CI/CD
container
security scanning
testing
deployment
rollback
canary

⸻

二十三、Tier 3 — 7/10

* SageMaker
* MLOps
* data pipelines
* Kafka
* Spark/Flink
* Kubernetes
* React
* Next.js
* GraphQL

这些很重要，但不要为了它们牺牲 Agent / Evaluation / the cloud provider AI。

⸻

二十四、我特别建议你不要犯的错误

❌ 不要花大量时间背 Transformer

这个职位不是 ML Research Engineer。

你不需要深入：

attention mathematics
backpropagation
CNN
RNN

达到研究级。

⸻

❌ 不要沉迷 Prompt Engineering

Prompt：

You are a helpful assistant...

这种东西对于 Lead Engineer 权重很低。

⸻

❌ 不要把 Agent 当成 LangChain API

真正的日常工程落地考量：

Why agent?

Why workflow?

Why multi-agent?

Why not deterministic orchestration?

How do you evaluate?

How do you control cost?

How do you secure tools?

⸻

二十五、你个人最大的优势和短板

结合你过去的经历，我反而认为这个职位与你的背景匹配度相当高。

你的优势

领域	你的基础	我的判断
Software Engineering	20+ years	⭐⭐⭐⭐⭐
Distributed Systems	很强	⭐⭐⭐⭐⭐
the cloud provider	有实际经验	⭐⭐⭐⭐
SRE	有实际 production experience	⭐⭐⭐⭐⭐
DevOps	很强	⭐⭐⭐⭐⭐
Kafka	有生产经验	⭐⭐⭐⭐⭐
Kubernetes	有	⭐⭐⭐⭐
ML systems	TikTok/GPU/Inference	⭐⭐⭐⭐
Python	有	⭐⭐⭐⭐
AI/LLM	已经在转型	⭐⭐⭐⭐
RAG	有 ConvFinQA 项目	⭐⭐⭐⭐
Agentic AI	需要强化	⭐⭐⭐
Evaluation	需要强化	⭐⭐⭐
MCP	需要强化	⭐⭐/⭐⭐⭐
TypeScript	有基础/实际经验	⭐⭐⭐⭐

所以我不会建议你重新学一遍 Machine Learning。

你的路线应该是：

已有能力
Software Engineering
       +
Distributed Systems
       +
the cloud provider
       +
SRE / DevOps
       +
```flowchart
ML / LLM
       ↓
━━━━━━━━━━━━━━━━━━━━
```
强化
Agentic AI
       +
RAG
       +
Evaluation
       +
LLM Observability
       +
```flowchart
AI Security
       ↓
━━━━━━━━━━━━━━━━━━━━
```
Lead AI Engineer

⸻

二十六、如果我是你，我会做一个“生产标杆级示范项目”

不要做 20 个小 demo。

只做 一个 Production-grade Insurance AI Agent。

例如：

a leading global company Claims Copilot

```flowchart
                ┌─────────────────────┐
                │   Customer Query    │
                └──────────┬──────────┘
                           ↓
                    Claims Agent
                           │
             ┌─────────────┼─────────────┐
             ↓             ↓             ↓
        Policy Agent   Document RAG   Claims Tool
             │             │             │
             ↓             ↓             ↓
          Policy DB     Vector DB     Mock API
             │             │             │
             └─────────────┼─────────────┘
                           ↓
                       LLM
                           ↓
                     Guardrails
                           ↓
                    Human Escalation
```

然后把下面全部做出来：

AI

* RAG
* Agent
* Tool calling
* MCP
* LangGraph

Engineering

* FastAPI
* Python
* TypeScript
* Docker
* Terraform

the cloud provider

* Bedrock
* Lambda/ECS
* API Gateway
* S3
* DynamoDB
* IAM

Production

* CI/CD
* tracing
* metrics
* logging
* evaluation
* cost tracking
* security

Evaluation

做一个：

100 test questions
```flowchart
             Baseline
                ↓
           Evaluation
                ↓
 ┌──────────────┼───────────────┐
 ↓              ↓               ↓
Retrieval     Answer          Safety
Recall        Accuracy        Score
 ↓              ↓               ↓
   └────────────┼───────────────┘
                ↓
          Regression Test
```

这个项目比你刷 100 个 LangChain tutorial 有价值 10 倍。

⸻

二十七、最后给你一个Lead AI Engineer 的工程主导心态

普通候选人回答：

“I have experience with RAG and LangChain.”

Senior 候选人：

“I built a RAG system using LangChain.”

Lead 候选人：

“Before choosing RAG, I first determine whether retrieval is actually required. Then I define measurable quality, latency, cost and safety objectives. I design the retrieval, agent orchestration and tool boundaries around those requirements, and establish evaluation and observability before putting the system into production.”

这三种回答的层次完全不同。

⸻

我给这个岗位的“必考知识树”

```flowchart
                     LEAD AI ENGINEER
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
      AI/LLM            Engineering           Cloud
        │                   │                   │
   ┌────┼────┐         ┌────┼────┐         ┌────┼────┐
   │    │    │         │    │    │         │    │    │
```
 Agent RAG Eval       Python DevSecOps    the cloud provider  IaC Security
```flowchart
   │    │    │         │    │    │         │    │    │
   │    │    │         │    │    │         │    │    │
LangGraph │ LLM Judge FastAPI CI/CD     Bedrock ECS IAM
Strands   │ Metrics   Async   Docker    AgentCore Lambda KMS
MCP       │ Tracing   Tests   K8s       API GW  S3   VPC
          │
     Hybrid Search
```
     Reranking
     Chunking
     Grounding

如果这是我自己去拿这个职位，我接下来不会再泛泛地学 AI。

我会直接进入 企业级 Lead AI Engineer 架构实战与深度落地模式：把这个 JD 拆成大约 30 个高频核心架构议题，然后逐个做到 “即使老板或team lead深入追问3层也能给出扎实解法”。

尤其是我会重点训练你这 10 道题：

1. Design an enterprise Agentic AI platform
2. Design an insurance Claims Agent
3. RAG：为什么 retrieval 会失败？如何优化？
4. How do you evaluate an AI Agent?
5. How do you monitor an AI Agent in production?
6. LangGraph vs the cloud provider Strands vs AgentCore
7. How would you secure an Agent + MCP tools?
8. How do you control LLM cost and latency?
9. How do you deploy and regression-test a new LLM?
10. When should you NOT use an Agent?

这 10 道题如果你能达到 Lead/Principal level，我认为会比单纯把 LangChain、LlamaIndex、OpenAI API 再学一遍有效得多。

另外，a leading global company 目前确实是在 Sydney 同时扩充 Lead AI Engineer、Senior AI Engineer、AI Domain Architect，公开招聘信息还明确把这次招聘描述为其 agentic AI journey，所以这不是普通的“职位 JD 堆关键词”，而是一个正在建设中的 AI engineering capability。

如果你准备投这个岗位，我下一步建议直接做一份 “a leading global company Lead AI Engineer 30-Day Interview Plan”，按你现有水平标出 Already Strong / Need Refresh / Must Learn / Interview Critical，再￼ 每天配具体 coding + system design + agentic AI 练习。
## evaluate 
可以。这个问题其实是作为 Lead AI Engineer 在日常工作中架构设计上最值得深入推敲的一题。

你不要把自己表达成“我知道几个 eval metric 的人”，而要表达成：

我把 AI Evaluation 当成 Production Quality Engineering，而不是模型测试。

这句话一旦立住，你的层级就上来了。

⸻

1. 在日常工作中面对架构评审先给出一个 Lead-level 总框架

在日常工作中你的老板或者team lead会提问：

How would you design an evaluation framework for AI agents in production?

你可以非常自信地说：

I would treat evaluation as a production engineering discipline rather than simply measuring model accuracy.

My evaluation framework would have four layers:

First, offline evaluation.
I would maintain a representative golden dataset covering normal cases, edge cases, adversarial cases and historical production failures. Every change to the model, prompt, retrieval strategy or agent workflow would run against this dataset before deployment.

Second, component-level evaluation.
For an agentic system, I don’t only evaluate the final answer. I separately evaluate retrieval quality, tool selection, tool arguments, policy compliance, reasoning trajectory where appropriate, and final response quality. This allows us to identify where the failure actually occurred.

Third, end-to-end evaluation.
I would measure task success, correctness, groundedness, safety, latency and cost. For high-risk insurance use cases, I would also include human review for cases where automated evaluation is not sufficiently reliable.

Fourth, continuous production evaluation.
After deployment, I would sample production traces and continuously evaluate them. I would monitor quality metrics alongside traditional operational metrics such as latency, error rate and cost. Significant quality degradation would trigger investigation or rollback just like a traditional production regression.

The key principle is that evaluation should be part of the CI/CD lifecycle. A model or prompt change should not reach production simply because the application tests pass; it should also pass our AI quality, safety, latency and cost gates.

这段你如果能够不背稿、自然讲出来，已经是比较明显的 Lead-level。

⸻

2. 然后画出这个架构

架构设计与技术评审时在白板上直接绘制：

```flowchart
                       Production AI System
                               │
                               ▼
                        ┌─────────────┐
                        │   Agent     │
                        └──────┬──────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
          Retrieval          Tools             LLM
              │                │                │
              └────────────────┼────────────────┘
                               │
                               ▼
                         Final Response
                               │
                               ▼
                    ┌────────────────────┐
                    │ Evaluation Layer   │
                    └─────────┬──────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
      Component             E2E                Safety
```
      Evaluation          Evaluation          Evaluation
```flowchart
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                    ┌──────────────────┐
                    │ Quality Gate     │
                    └────────┬─────────┘
                             ▼
                       Production
                             │
                             ▼
                       Monitoring
                             │
                             ▼
                    Production Samples
                             │
                             └──────────► Evaluation
```

然后补一句：

This creates a closed feedback loop between development, deployment and production.

这个词非常重要：

closed-loop evaluation

⸻

3. 但是顶级候选人和普通候选人的区别在这里

在日常工作中你的老板或者team lead很可能马上追问：

What exactly would you evaluate?

不要回答：

Accuracy and hallucination.

太浅。

你应该拆成：

```flowchart
                    AI Evaluation
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
       ▼                 ▼                 ▼
    Retrieval         Agent              Generation
       │                 │                 │
   Recall@K          Tool selection     Correctness
```
   Precision@K       Tool arguments     Relevance
   MRR               Task completion    Groundedness
```flowchart
   NDCG              Loop detection    Faithfulness
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
                         ▼
                    System Level
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           Latency      Cost       Safety
```

然后说：

I deliberately separate component metrics from end-to-end metrics, because a poor final answer doesn’t necessarily mean the LLM is the problem.

这是非常好的 Lead-level 表达。

⸻

4. 举一个保险公司的例子

这是你真正应该掌握的。

假设 a leading global company 有：

Claims Assistant

用户问：

“My laptop was damaged while travelling. Am I covered?”

系统：

```flowchart
User
 ↓
Claims Agent
 ↓
Retrieve Policy
 ↓
Retrieve Travel Conditions
 ↓
Call Claims System
 ↓
LLM
 ↓
Answer
```

最后回答：

“Yes, you’re covered.”

但实际上应该：

“No, accidental damage outside Australia isn’t covered under this policy.”

普通开发者：

The LLM hallucinated.

你：

I wouldn’t immediately blame the LLM. I would trace the complete execution path.

然后：

```flowchart
Question
   ↓
Retrieval
   ↓
Wrong policy document
   ↓
LLM
   ↓
Incorrect answer
```

于是：

The failure is a retrieval failure, not necessarily a generation failure.

这句话非常重要。

⸻

5. 然后你进一步说：Failure Attribution

这是我特别建议你掌握的概念。

AI Eval 不应该只有一个 score

错误：

Overall score = 82%

你根本不知道为什么。

好的 framework：

Task Success                  91%
Retrieval Recall              87%
Tool Selection                96%
Tool Argument Accuracy        94%
Groundedness                  93%
Answer Correctness            91%
Safety                         99%
Latency                        95%
Cost                           92%

然后可以知道：

Retrieval is currently our biggest quality bottleneck.

这就是 diagnostic evaluation。

⸻

6. 你还需要一个非常重要的概念：Golden Dataset

在日常工作中你的老板或者team lead会提问：

Where do your evaluation datasets come from?

回答不要只是：

We create test cases.

应该说：

```flowchart
Golden Dataset
      │
      ├── Expert-created cases
      ├── Historical production cases
      ├── Synthetic cases
      ├── Edge cases
      ├── Adversarial cases
      └── Previous production failures
```

特别是：

Every production failure should have the potential to become a regression test.

这是非常强的一句话。

意思是：

```flowchart
Production failure
       ↓
Root cause
       ↓
Add test case
       ↓
Golden dataset
       ↓
Future deployments
       ↓
Never regress
```

这就是 Software Engineering + AI Engineering 的结合。

你的背景其实非常适合讲这个。

⸻

7. LLM-as-a-Judge 怎么说才不会显得幼稚

在日常工作中你的老板或者team lead很可能会提问：

Would you use an LLM to evaluate another LLM?

不要说：

Yes, use GPT-5 as judge.

太浅。

你应该说：

Yes, but I wouldn’t treat an LLM judge as ground truth.

然后：

```flowchart
                    Evaluation
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
    Programmatic      LLM Judge         Human
       │                 │                 │
 exact match        semantic quality   expert review
```
 schema              groundedness      high-risk cases
 policy rules        relevance         ambiguous cases
 latency             style

然后：

I would calibrate the LLM judge against human-labelled examples and periodically measure judge-human agreement.

这句话非常重要。

⸻

8. Insurance 场景尤其要强调 Risk-based Evaluation

这是 a leading global company 和普通 SaaS 最大的区别之一。

你可以主动说：

For insurance, I would not treat every AI interaction equally.

例如：

```flowchart
Low Risk
│
├── FAQ
├── Policy explanation
└── General information
Medium Risk
│
├── Claim guidance
├── Coverage interpretation
└── Document summarisation
High Risk
│
├── Claim decision
├── Payment decision
├── Legal interpretation
└── Customer eligibility
```

风险越高：

```flowchart
Human review ↑
Automation ↓
Evaluation strictness ↑
Auditability ↑
```

所以：

The evaluation threshold should be risk-based rather than one global threshold for the entire platform.

这个非常像真正做过 enterprise AI governance 的人。

⸻

9. Production Evaluation 和 Offline Evaluation 要分开

这是日常工程实践中非常体现架构功底、容易拉开差距的地方。

Offline

```flowchart
Code change
   ↓
Golden dataset
   ↓
Evaluation
   ↓
PASS / FAIL
```

Production

```flowchart
Real traffic
     ↓
Sampling
     ↓
Trace
     ↓
Evaluation
     ↓
Quality metrics
     ↓
Drift detection
```

然后你可以说：

Offline evaluation tells me whether the candidate version is better before deployment. Production evaluation tells me whether it remains good under real-world traffic and distribution.

非常好。

⸻

10. 最后一定要讲 Evaluation Gate

这是 Lead Engineer 必须讲出来的。

例如：

```flowchart
                 Pull Request
                       │
                       ▼
                 Unit Tests
                       │
                       ▼
               Integration Tests
                       │
                       ▼
                AI Evaluation
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
   Accuracy         Safety           Cost
      ≥90%            99%            <$X
       │               │                │
       └───────────────┼────────────────┘
                       ▼
                  Deployment
                       │
                       ▼
                    Canary
                       │
                       ▼
              Production Eval
                       │
                ┌──────┴──────┐
                ▼             ▼
              Good          Bad
                │             │
                ▼             ▼
             Rollout       Rollback
```

一句话：

AI evaluation becomes a deployment gate, not a dashboard that nobody acts on.

非常强。

⸻

11. 在日常工作中你的老板或者team lead会提问：What metrics?

你可以直接回答：

Retrieval

* Recall@K
* Precision@K
* MRR / NDCG
* Context relevance

Generation

* correctness
* relevance
* faithfulness
* groundedness
* completeness

Agent

* task completion rate
* tool selection accuracy
* tool argument accuracy
* unnecessary tool calls
* loop rate
* escalation rate

Production

* latency
* token consumption
* cost/request
* error rate
* availability

Safety

* policy violation
* PII leakage
* prompt injection resistance
* unsafe tool invocation

⸻

12. 在日常工作中你的老板或者team lead会提问：How do you know your evaluation is reliable?

这是高级追问。

你回答：

Evaluation itself needs to be evaluated.

然后：

```flowchart
Human-labelled Dataset
          ↓
      LLM Judge
          ↓
   Compare results
          ↓
 Agreement / Correlation
          ↓
 Calibrate judge
          ↓
 Periodic re-validation
```

然后补：

For high-risk decisions, I would retain human-in-the-loop evaluation rather than relying entirely on automated judges.

这就很稳。

⸻

13. 最后给你一段真正作为 Lead AI Engineer 在日常工作中向团队与主管阐述方案的标准版本

不要背整段，但你可以练到自然说出来：

For a production AI system, I would treat evaluation as part of the engineering lifecycle, not as a one-time model benchmark.

I would build a layered evaluation framework.

At the bottom, we have a versioned golden dataset containing representative business cases, edge cases, adversarial cases and historical production failures.

Then I evaluate the system at multiple levels. For RAG, I measure retrieval quality separately. For agents, I evaluate tool selection, tool arguments, task completion and unnecessary or looping behaviour. At the generation layer, I measure correctness, relevance, groundedness and faithfulness.

Then I have end-to-end evaluation for the actual business outcome.

I also separate automated evaluation from human evaluation. LLM-as-a-judge can be useful for semantic quality, but I would calibrate it against human-labelled examples and never treat the judge as absolute ground truth.

For an insurance environment, I would make the evaluation risk-based. A policy FAQ can have a different automation threshold from a claim or payment decision, where we need much stronger controls and potentially human approval.

Finally, I would close the loop with production observability. We sample real production traces, continuously evaluate them for quality, safety, latency and cost, and feed significant failures back into the golden dataset as regression tests.

Most importantly, the evaluation needs to become an engineering gate. A prompt, model, retrieval or agent workflow change should only reach production if it passes predefined quality, safety, latency and cost thresholds.

That gives us a continuous loop:

```flowchart
build → evaluate → deploy → observe → learn → regression test → improve.
```

That’s how I would make AI quality measurable and continuously improve it in production.

⸻

你要真正记住的不是 20 个 metric，而是这 6 个词

在日常工作中如果需要快速抓住架构本质，只记住：

```flowchart
Dataset → Component → End-to-End → Risk → Production → Feedback Loop
```

然后展开：

```flowchart
Dataset
   ↓
Component Evaluation
   ↓
E2E Business Outcome
   ↓
Risk-based Threshold
   ↓
Production Monitoring
   ↓
Feedback → Regression Dataset
```

这就是你回答 “How do you build a production-grade AI evaluation framework?” 的骨架。

而且这个问题与你自己的背景非常契合：你不是从“LLM prompt engineer”起步，而是有 SRE + distributed systems + ML inference + production engineering 背景。你真正应该卖给 a leading global company 的差异化不是“我比别人更会 prompt”，而是：

“I know how to turn probabilistic AI behaviour into an observable, testable and governable production system.”

这句话，我建议你重点练熟。


---

# CARDS

Spoken-English answer cards, built from the notes in this folder. Every card has the same shape:

- **SAY** — the opening sentence, say it close to verbatim; it buys you time and sets the level
- **THEN** — three speakable beats, the body of the answer
- **EXAMPLE** — one concrete insurance case
- **COST** — the trade-off or failure mode; this is what makes you sound Lead, not Senior
- **PROBE** — the follow-up they will ask, and the one-line answer

Search with `python ask.py`, two or three keywords.

---

### RAG opening — do we even need retrieval | rag intro opening framing

**SAY** — "Before choosing RAG, I first determine whether retrieval is actually required. Then I define measurable quality, latency, cost and safety objectives. I design the retrieval, agent orchestration and tool boundaries around those requirements, and I establish evaluation and observability before putting the system into production."

**THEN**
- Retrieval is the right answer when the knowledge is large, changes often, and every claim has to be attributable to a source document. Insurance policy wording is exactly that.
- It is the wrong answer when the knowledge is small and stable, or when the task is really a calculation or a lookup. Those should be deterministic tools, not retrieval.
- I would not treat RAG as "PDF, embedding, vector DB, LLM". The real pipeline is query understanding, candidate retrieval, ranking, evidence quality, grounded generation, business outcome — and every layer has its own metrics, failure modes and trade-offs.

**EXAMPLE** — "Am I covered for a stolen laptop overseas?" needs retrieval, because the answer lives in clause wording that changes by product and by version. "What is my excess?" does not; that is a deterministic calculation against the policy record.

**COST** — Retrieval adds latency, cost and a whole new class of silent failure: the index degrades and the model keeps answering confidently from an empty context. That is why I build retrieval evaluation separately from answer evaluation.

```flowchart
**PROBE** — *"How do you know retrieval is the bottleneck and not the model?"* → I evaluate retrieval independently from answer quality, so I can tell a retrieval failure from a generation failure. If the correct clause is not in the top-K at all, no amount of prompting fixes it.
```

**SOURCE** — [words_must_say_during_interview.md:2](words_must_say_during_interview.md#L2) three levels of answer · [rag_interview_notes.md:2288](rag_interview_notes.md#L2288) Lead-level mental model · [rag_interview_notes.md:2189](rag_interview_notes.md#L2189) a leading global company/insurance design

---

### Chunking — structure-aware, not fixed-size | chunking chunk size split

**SAY** — "I prefer semantic and structure-aware chunking over arbitrary fixed-size splitting when the source documents have strong business structure."

**THEN**
- Chunk size is not a magic number; it should follow the document structure and the retrieval task.
- For insurance policies, clauses, sections and exclusions are much stronger semantic boundaries than a fixed token window. A fixed window will cut an exclusion in half, and half an exclusion is worse than no exclusion — it reads as coverage.
- I would benchmark different strategies against retrieval recall, precision and downstream answer quality, rather than picking a number and defending it.

**EXAMPLE** — Policy documents: split on clause and section boundaries, keep the clause identifier and the product code as metadata, and use parent-child retrieval so I match on the specific clause but pass the surrounding section to the model for context.

**COST** — Structure-aware chunking needs a real parser per document type, so it is more engineering than fixed-size splitting, and it breaks when the source format changes. Fixed-size is cheap and uniform; that is its only advantage.

```flowchart
**PROBE** — *"How would you choose chunk size?"* → I would not start with an arbitrary token size. I would first understand the document structure and the retrieval unit the business task requires, then benchmark strategies against recall, precision and downstream answer quality.
```

**SOURCE** — [rag_interview_notes.md:55](rag_interview_notes.md#L55) how to split · [rag_interview_notes.md:132](rag_interview_notes.md#L132) structure-aware · [rag_interview_notes.md:1326](rag_interview_notes.md#L1326) strategies · [rag_interview_notes.md:201](rag_interview_notes.md#L201) parent-child · [embedding_notes.md:2](embedding_notes.md#L2) chunk size answer

---

### Embeddings — what they are good and bad at | embedding embeddings semantic vector dense

**SAY** — "Dense embeddings capture semantic similarity, but they can be weaker on exact identifiers, clause numbers and domain-specific terminology."

**THEN**
- Semantic search can find a document that shares no words with the query, because the embedding encodes meaning rather than surface form. That is the whole value.
- But the same property is the weakness. "Clause 7.3", a policy number, a product code — those carry almost no semantic signal, so a dense retriever will happily return something that means roughly the same thing and is legally wrong.
- Insurance language is full of exact tokens that must match exactly. That is the single strongest argument for not running dense retrieval alone.

**EXAMPLE** — A customer asks about "exclusion 7.3". Dense retrieval returns exclusions that read similarly; lexical retrieval returns the one that is actually numbered 7.3.

**COST** — Embeddings are also a versioned dependency. If the embedding model changes, the whole index has to be rebuilt, and similarity scores are not comparable across versions — so any threshold tuned on the old index is silently invalid.

```flowchart
**PROBE** — *"Why can semantic search find documents that don't contain the same words?"* → Because retrieval happens in embedding space, not token space; similarity is measured between meanings. The flip side is that exact identifiers lose almost all their signal, which is why I add a lexical channel.
```

**SOURCE** — [rag_interview_notes.md:231](rag_interview_notes.md#L231) semantics to vectors · [rag_interview_notes.md:279](rag_interview_notes.md#L279) likely probes · [rag_interview_notes.md:314](rag_interview_notes.md#L314) the fatal problem · [rag_interview_notes.md:1445](rag_interview_notes.md#L1445) biggest weakness

---

### Hybrid retrieval and RRF | hybrid bm25 sparse dense fusion rrf

**SAY** — "I use hybrid retrieval to combine semantic recall with lexical precision."

**THEN**
- Dense retrieval gives me recall on paraphrased, conversational questions. BM25 gives me precision on exact terminology, clause identifiers and product codes.
- I run both over the same query and fuse the two ranked lists. My default is Reciprocal Rank Fusion, because it combines on rank rather than on score — so I do not have to normalise two scoring systems that are not on the same scale.
- Then metadata filtering narrows to the right product and version, and a reranker cuts the candidate set down to what actually goes into the prompt.

```flowchart
**EXAMPLE** — The full path I would draw: query → embeddings and BM25 in parallel → hybrid fusion → top 50 → metadata filter → reranker → top 5 → LLM → grounded answer.
```

**COST** — Two retrievers means two systems to operate, index and keep in sync, and fusion adds a tuning surface. RRF is robust but it throws away score magnitude, so a very confident single-channel hit gets no extra credit.

```flowchart
**PROBE** — *"Why RRF rather than weighted score fusion?"* → Because dense similarity and BM25 scores are not on a comparable scale, so weighted fusion needs per-corpus normalisation that drifts. RRF only needs the ranks, which makes it much harder to get wrong.
```

**SOURCE** — [rag_interview_notes.md:339](rag_interview_notes.md#L339) dense + sparse · [rag_interview_notes.md:383](rag_interview_notes.md#L383) insurance example · [rag_interview_notes.md:413](rag_interview_notes.md#L413) fusion · [rag_interview_notes.md:441](rag_interview_notes.md#L441) RRF · [rag_interview_notes.md:1540](rag_interview_notes.md#L1540) architecture diagram

---

### Reranking and two-stage retrieval | rerank reranker ranking two stage precision

**SAY** — "The first-stage retriever optimises recall; the reranker optimises precision over a smaller candidate set."

**THEN**
- The rule I use is: retrieve broadly, rerank selectively.
- Stage one must not miss the genuinely relevant document — that error is unrecoverable, because nothing downstream can rank a document it never saw. So stage one is tuned for recall and returns something like top 50.
- Stage two is a cross-encoder that actually reads the query together with each candidate. It is far too expensive to run over the corpus, which is exactly why it only runs over the candidates.

**EXAMPLE** — If the correct exclusion clause is retrieved but ranked 23rd, that is not a retrieval problem, it is a ranking problem — I introduce or tune a reranker rather than touching the index.

**COST** — Reranking adds real latency per request and scales with candidate count, so the top-K into the reranker is a direct latency-versus-quality dial. And a reranker cannot repair a bad first stage; it can only reorder what it is given.

```flowchart
**PROBE** — *"Ranking versus reranking?"* → Retrieval already includes an initial ranking — retrieval is retrieve plus rank. Reranking is a second, more expensive pass whose job is ordering quality among candidates, not finding them.
```

**SOURCE** — [rag_interview_notes.md:1570](rag_interview_notes.md#L1570) reranking · [rag_interview_notes.md:1596](rag_interview_notes.md#L1596) why needed · [rag_interview_notes.md:1635](rag_interview_notes.md#L1635) split of duties · [rag_interview_notes.md:1667](rag_interview_notes.md#L1667) trade-off · [rag_interview_notes.md:2792](rag_interview_notes.md#L2792) ranking vs reranking · [embedding_notes.md:57](embedding_notes.md#L57) one-liner

---

### Query rewriting | query rewriting rewrite expansion multi coreference

**SAY** — "Query rewriting can improve retrieval for conversational or ambiguous queries, but it introduces query drift, so I would evaluate the rewritten query against the original user intent."

**THEN**
- Coreference resolution is the clearest win. In a conversation, "is that covered too?" is unretrievable on its own; it has to be rewritten against the dialogue history into something self-contained.
- Query expansion helps when the customer uses everyday language and the document uses policy language — "my laptop got nicked" versus "theft of portable electronic equipment".
- Multi-query, where I issue several rewrites and fuse the results, raises recall on broad questions at the cost of extra retrieval calls.

**EXAMPLE** — Turn one: "Am I covered for theft?" Turn two: "What about overseas?" The second query only works if it is rewritten into "Am I covered for theft overseas?" before it reaches the retriever.

**COST** — Query drift is the real risk: the rewriter helpfully changes what the customer asked, retrieval succeeds against the wrong question, and the answer is confidently off-target. It also adds a model call on the critical path, so it costs latency on every request.

```flowchart
**PROBE** — *"How do you stop drift?"* → I evaluate the rewrite as its own step, with golden pairs of original and acceptable rewrites, and I keep both the original and the rewritten query in the retrieval set so a bad rewrite degrades rather than replaces.
```

**SOURCE** — [rag_interview_notes.md:451](rag_interview_notes.md#L451) query rewriting · [rag_interview_notes.md:494](rag_interview_notes.md#L494) the three uses · [rag_interview_notes.md:1751](rag_interview_notes.md#L1751) the drift risk

---

### Retrieval metrics — Recall@K, Precision@K, MRR, NDCG | recall precision mrr ndcg metrics retrieval

**SAY** — "I evaluate retrieval independently from answer quality so I can distinguish retrieval failures from generation failures."

**THEN**
- Recall@K is not "K relevant documents returned". Top-K is a candidate set; Recall@K asks how much of the ground-truth relevant set made it into that candidate set. High recall means I am not losing things.
- Precision@K asks the opposite: of what I returned, how much is actually useful. High precision means I am not feeding the model noise.
- MRR cares about where the first correct document lands, which matters when one clause answers the question. NDCG cares about the whole ordering with graded relevance, which matters when several clauses contribute.

**EXAMPLE** — Four documents are genuinely relevant. The retriever returns five and two of them are relevant: Recall@5 is 2 over 4, Precision@5 is 2 over 5. Those two numbers fail in different directions and need different fixes — low recall points at chunking, indexing or the retriever; low precision points at ranking.

**COST** — All of this needs labelled ground truth, which is expensive and goes stale as the policy wording changes. And a retriever is not an oracle — it only estimates relevance from similarity or BM25 score, so some irrelevant documents in the top-K is normal, not a bug.

```flowchart
**PROBE** — *"Where does the golden set come from?"* → Historical production data plus human labelling, and then I close the loop: every case a human reviewer overrides becomes a candidate eval case. That keeps the set from drifting away from reality.
```

**SOURCE** — [rag_interview_notes.md:1950](rag_interview_notes.md#L1950) Recall@K · [rag_interview_notes.md:1987](rag_interview_notes.md#L1987) Precision@K · [rag_interview_notes.md:2012](rag_interview_notes.md#L2012) MRR · [rag_interview_notes.md:2032](rag_interview_notes.md#L2032) NDCG · [rag_interview_notes.md:2365](rag_interview_notes.md#L2365) worked example · [rag_interview_notes.md:2976](rag_interview_notes.md#L2976) what K really is · [evaluation.md:92](evaluation.md#L92) retrieval eval layer

---

### Agent evaluation — four things RAG metrics miss | agent evaluation tool selection arguments task completion loop

**SAY** — "An agent is not question in, answer out. It plans, picks a tool, generates arguments, observes the result and decides the next action — so I evaluate each of those, not just the final text."

**THEN**
- **Tool selection accuracy**: given a golden set of questions with expected tools, how often does it pick the right one? Asking "what is my excess" and calling `get_customer` is a tool selection failure even if the final answer sounds fine.
- **Tool argument correctness**: the right tool with the wrong claim ID is worse than the wrong tool, because it returns real data about the wrong case. Right tool chosen is not the same question as right tool invoked.
- **Task completion**: did it actually finish all the required steps? An agent can complete two of five steps and produce an excellent-sounding answer. That is a fail, and answer-quality scoring will not catch it.
- **Loop rate**: the fraction of requests that enter repetitive cycles. This is the one most candidates forget, and in production it is what burns the budget.

**EXAMPLE** — "Find my policy, determine whether theft is covered, calculate the excess, and explain the result" needs five steps. If the agent runs two and says "yes, you're covered", answer quality looks good and task completion is zero.

**COST** — Trajectory evaluation needs expected paths, which are more expensive to label than question-answer pairs and more brittle when the tool set changes. So I assert on invariants — approval before payment, retrieval before answering — rather than on exact step sequences.

```flowchart
**PROBE** — *"How do you stop loops in production, not just measure them?"* → Hard limits per task: max iterations, max tool calls, timeout, token budget and cost budget. Exceeding them trips a circuit breaker rather than running on. That is a reliability control, not just a cost control.
```

**SOURCE** — [evaluation.md:302](evaluation.md#L302) agent eval layer · [evaluation.md:336](evaluation.md#L336) tool selection · [evaluation.md:397](evaluation.md#L397) tool arguments · [evaluation.md:444](evaluation.md#L444) task completion · [evaluation.md:497](evaluation.md#L497) loop detection · [evaluation.md:1294](evaluation.md#L1294) final vs trajectory eval · [evaluation.md:1318](evaluation.md#L1318) path assertions

---

### Groundedness versus faithfulness | groundedness faithfulness hallucination grounding citation

**SAY** — "Groundedness asks whether the answer has support in the retrieved evidence. Faithfulness asks whether the answer represents that evidence without introducing contradictions or unsupported claims."

**THEN**
- The distinction matters because an answer can cite exactly the right document and still be wrong about it.
- The source says "coverage may apply subject to the conditions listed below". The agent says "your claim is definitely covered". The citation is correct, so groundedness looks fine — but faithfulness is broken, because "may apply" became "definitely covered".
- In insurance that specific failure is the expensive one. It is not a hallucinated fact, it is a removed qualifier, and it reads as a coverage promise.

**EXAMPLE** — I would make grounding measurable rather than judged: decompose the answer into atomic claims, and require every number and identifier in the answer to be literally present in the retrieved sources. A fabricated policy number fails a cheap deterministic check, no model needed.

**COST** — Automated grounding checks catch fabricated identifiers and numbers well, and catch softened or strengthened qualifiers poorly — that part still needs an LLM judge on a sample, or human audit. So I treat `grounding_rate` as my headline dashboard metric and accept that it has a blind spot.

```flowchart
**PROBE** — *"What is your single most important production metric?"* → Grounding rate. If it drops, either retrieval has broken or the model has started inventing, and both of those are invisible to latency and error-rate monitoring.
```

**SOURCE** — [words_must_say_during_interview.md:12](words_must_say_during_interview.md#L12) the distinction · [evaluation.md:636](evaluation.md#L636) groundedness · [evaluation.md:672](evaluation.md#L672) faithfulness · [evaluation.md:710](evaluation.md#L710) telling the three apart · [reliable_notes.md:83](reliable_notes.md#L83) grounding check code

---

### Risk-based quality gates | gate quality gate threshold risk tier release

**SAY** — "I would avoid a single global AI quality threshold. I would define quality gates by risk tier and by failure mode."

**THEN**
- A single overall score is compensatory — it lets good average accuracy hide a catastrophic safety failure. 95% accuracy averaged with terrible safety is not a pass.
- So the gate is a conjunction, with segmentation: overall correctness at or above 95%, **and** high-risk claims at or above 99%, **and** safety violations exactly zero, **and** PII leakage exactly zero.
- And I separate hard gates from soft gates. PII leakage, unsafe tool invocation and critical policy violations are absolute blockers. Latency, cost and general response quality are legitimate trade-offs. Not all metrics are equally important.

**EXAMPLE** — Overall quality 96% with a 4% hallucination rate might be acceptable for general FAQ. For policy coverage interpretation it is not acceptable at all. Same number, different gate.

**COST** — Per-tier, per-failure-mode gates need a much bigger and better-segmented eval set — you need enough high-risk cases to measure a 99% threshold meaningfully — and they slow releases down. That is the cost I would argue is worth paying in insurance.

```flowchart
**PROBE** — *"Who sets the thresholds, and why 95% and not 90%?"* → The threshold should come from business risk and empirical baselines rather than an arbitrary number: historical production data, a human-labelled baseline, current system performance, business impact analysis, risk tolerance. Then recalibrate as production evidence accumulates. *"Who decides the risk level?"* → Not engineering alone. Risk classification is cross-functional — engineering, product, security, legal and compliance, and the business owner — scored on impact times probability, and above all on reversibility. *"What if overall passes but one critical metric fails?"* → It fails. I use non-compensatory gates for critical risk dimensions.
```

**SOURCE** — [security_gate_notes.md:117](security_gate_notes.md#L117) risk-based gate · [security_gate_notes.md:121](security_gate_notes.md#L121) a leading global company example · [security_gate_notes.md:447](security_gate_notes.md#L447) segmentation · [security_gate_notes.md:481](security_gate_notes.md#L481) failure-mode gates · [security_gate_notes.md:535](security_gate_notes.md#L535) hard vs soft · [security_gate_notes.md:617](security_gate_notes.md#L617) the four probes

---

### Agent governance | governance guardrail policy approval autonomy permission tool gateway

**SAY** — "I would approach agent governance as an architectural and runtime enforcement problem, rather than relying on prompts or model-level guardrails. The model may recommend an action, but the system must independently determine whether that action is authorised and safe to execute."

**THEN**
- First, classify agents and individual actions by business impact, reversibility and regulatory risk. A read-only policy assistant and an agent that can initiate a payment should not have the same permissions. I think in four levels: read-only, recommend-and-draft, bounded execution of reversible pre-authorised actions, and high-impact execution that requires human approval.
- Second, enforce least privilege through an identity-aware tool gateway and deterministic policy checks. Every sensitive tool call is validated before execution: caller authorisation, tool arguments, business rules, and any required approval.
- Third, intercept at runtime — before the model call, before and after tool execution, before releasing the final response — and allow, deny, warn or escalate depending on risk. Critical controls fail closed.
- Finally, the architecture I would push for is centralised policy, distributed enforcement. The important property is not how many boxes are on the diagram; it is that the agent has **no path** to perform a protected action without passing the governance layer.

**EXAMPLE** — The agent emits `approve_claim_payment` for twelve thousand dollars. The governance layer checks identity, authorisation, business policy and case state, risk policy, parameter validation, whether the approval already exists and maps to this specific action, and writes an audit record. The model thinking it should be approved is not the same as the system permitting it.

**COST** — This adds latency to every sensitive call, and a policy engine is real ongoing maintenance — rules, permission context, policy versions. Fail-closed also means a governance outage becomes a business outage, which is a trade-off I would make explicitly rather than by accident.

```flowchart
**PROBE** — *"Why isn't a system prompt enough?"* → A prompt is behavioural guidance for the model, not an enforceable security boundary. The model can misinterpret instructions, and retrieved documents can carry indirect prompt injection. Anything that matters has to be enforced by backend authorisation, the tool gateway and deterministic policy checks — never by the model constraining itself. *"How do you balance autonomy and safety?"* → Start with bounded autonomy and expand it only when evaluation evidence shows the controls work. The goal is not maximum autonomy; it is the least autonomy that achieves the business objective.
```

**SOURCE** — [goverance.md:1](goverance.md#L1) full note · [goverance.md:36](goverance.md#L36) four autonomy levels · [goverance.md:76](goverance.md#L76) the seven options · [goverance.md:98](goverance.md#L98) enterprise architecture · [goverance.md:152](goverance.md#L152) enforcement checks · [goverance.md:202](goverance.md#L202) English answer

---

### Reliable AI-native systems — the headline answer | reliable reliability ai-native nondeterministic

**SAY** — "AI-native means the control flow is generated by the model, so reliability can no longer be guaranteed by enumerating branches. My approach is to keep the non-determinism inside a deterministic envelope — the model decides what to do, but boundaries, permissions, irreversible actions and budgets are owned by a deterministic layer. Then I use evaluation to turn correctness into a measurable distribution, and observability to make silent failure visible. A reliable AI-native system is not one that never makes mistakes; it is one where mistakes cannot do damage."

**THEN**
- The distinction that matters: AI-enabled means the model is a feature. AI-native means the model decides what happens next. The test is — take the model out, and what is left? A system missing a feature, or nothing at all.
- Traditional reliability rests on assumptions that all fail here: same input gives same output, failures throw errors, tests can enumerate branches, correctness is boolean. In an AI-native system the output varies, failure is fluent and confident and wrong, branches appear at runtime, and correctness is a distribution.
- And the dependency changes underneath you. A model version is retired or its behaviour drifts, and you did not ship that change but you own the consequence.

**EXAMPLE** — Five pillars I would give as structure: bounded consequences, correctness as a statistic, failures made visible, graceful degradation, and resilience to drift. A system that only has a full-health path is not reliable — it has to degrade to rules, to a human, or to "I don't know".

**COST** — The deterministic envelope costs flexibility: every new capability has to be modelled as a permitted action, so the system is slower to extend than a free-running agent. In insurance that is the right trade.

```flowchart
**PROBE** — *"Anything beyond technical reliability?"* → Yes — reliable enough for a regulator to trust. Decisions traceable to the evidence and the path taken, humans keeping final say at high-risk points, demonstrable fairness, auditable customer data boundaries. Under local regulators CPS 230 that is a precondition for going live, not a nice-to-have.
```

**SOURCE** — [reliable_notes.md:3](reliable_notes.md#L3) AI-native line · [reliable_notes.md:18](reliable_notes.md#L18) what reliable means · [reliable_notes.md:36](reliable_notes.md#L36) five pillars · [reliable_notes.md:57](reliable_notes.md#L57) one-sentence version

---

### Detecting silent failure in production | silent failure drift detection canary override mttd monitoring

**SAY** — "The hard part is that I am trying to detect a failure with no exception, no stack trace, and output that looks completely normal. So I build signals in four layers, cheapest first."

**THEN**
- **Deterministic validation on every request, near zero cost.** Anything code can decide, code decides — never a model. Output contract plus business invariants: a policy number in the answer must exist in the retrieved results, an excess amount must fall inside the legal range for that product. This layer alone catches 30 to 40% of problems.
- **Runtime path assertions on every request.** The trajectory assertions from CI, moved into production as non-blocking observation — except safety ones, which block. No write before approval, retrieval before answering, step budget, no identical call repeated more than three times. This catches "the answer looks right but the process is already broken", which usually shows up days before the incident.
- **Confidence triage on every request.** Not one signal — several weak ones combined: top retrieval score, the margin between first and second, grounding rate, self-consistency across samples for high-risk cases only, distance from the training distribution, step-count anomaly. Low confidence routes to a human, which converts "the model might be wrong" into a countable business event.
- **Sampled audit and online evaluation.** LLM-as-judge on 1 to 5% of traffic, human audit on a few dozen cases a day weighted towards low confidence and high risk, and a production canary set — fixed synthetic cases run hourly against real production.

**EXAMPLE** — There is no ground truth online, so I use human behaviour as the label. Human override rate and edit distance are the golden pair: free, continuous, and naturally labelled. Plus repeat-contact rate within seven days, escalation rate, rework rate, and refusal rate. Refusal rate is the sneaky one — tightening a guardrail scores perfectly on every quality metric while business value quietly leaks away.

**COST** — Every layer has a false-positive cost, and the real failure mode is alert fatigue: if the team learns to ignore alerts, all of this engineering stops working. So: alert on aggregates not single requests, thresholds relative to a rolling baseline not absolute, require a minimum sample volume, three severity levels, and audit alert true-positive rates monthly and delete the rules that cry wolf.

```flowchart
**PROBE** — *"With no labels, how can you claim accuracy dropped?"* → Three independent routes that cross-check each other. Proxy metrics like override rate and repeat contact, which need no labels. A production canary set, where the input never changes so any score change must come from the system. And sampled human audit. If live metrics drop but the canary holds, the input distribution shifted, not the model. *"How do you avoid 'broken for three months'?"* → That only happens when every metric is output-side — latency, error rate, throughput, none of which moved. It requires a reference frame independent of live traffic (the canary) and one independent of model judgement (human override). I treat MTTD as a first-class metric alongside success rate, target it at under 24 hours, and verify it with drills — deliberately degrade retrieval or swap in a worse model and measure how long the system takes to notice it itself.
```

**SOURCE** — [reliable_notes.md:67](reliable_notes.md#L67) failure taxonomy · [reliable_notes.md:81](reliable_notes.md#L81) four signal layers · [reliable_notes.md:181](reliable_notes.md#L181) proxy metrics · [reliable_notes.md:197](reliable_notes.md#L197) alert design · [reliable_notes.md:230](reliable_notes.md#L230) challenge Q&A

---

### Observability and OpenTelemetry GenAI | observability otel opentelemetry span trace instrumentation

**SAY** — "I would instrument against the OpenTelemetry GenAI conventions, but I am aware the whole set is still marked Development, so attribute names can change without notice. So I would not let business code touch `gen_ai.*` literals directly — there is an adapter layer in between, and when the spec moves I only change the adapter. That is my default for any immature standard."

**THEN**
- The current state, which most candidates do not know: as of mid-2026 every `gen_ai.*` attribute, span, metric and event still carries the Development stability marker. The only Stable attributes on a GenAI span are `error.type`, `server.address` and `server.port`, and those are inherited from the core conventions. In v1.42.0, on 12 June 2026, all the GenAI conventions were deprecated in the main repo and moved to a separate `semantic-conventions-genai` repository specifically so they can iterate faster than the core stability bar allows.
- The span tree for one claims question: `invoke_agent` at the root, with child spans for each `execute_tool` call and each `chat` call, carrying retrieval top score and K, input and output tokens, cache reads, confidence and grounding rate. The most important line is the last one — recording "routed to human" as a span attribute turns an invisible behaviour into a countable, alertable business event.
- Cost attribution is where the real design difficulty is, and it is dimensional, not technical. Standard token metrics plus custom dimensions: feature, tenant, and outcome. Without `app.feature` the bill is a single number. Without `app.outcome` you cannot compute the metric that actually matters.
- Sampling is tiered: span metadata at 100% because it is just numbers and strings, content off by default, and 100% retention of content for errors, low confidence and human overrides with 1 to 5% of normal traffic. This has to be tail-based sampling — decide after the trace finishes, or you will never capture the traces that ended badly.

**EXAMPLE** — On tooling I would give a two-layer answer: OpenTelemetry underneath, because I do not want the agent traces and the insurance core system traces split across two worlds when I am debugging an incident; then an LLM-native platform on top for evaluation, annotation and prompt versioning. The key is keeping the instrumentation layer vendor-neutral so swapping the upper platform does not touch business code. At a leading global company, data residency and self-hosting will be hard constraints, so self-hosted Langfuse or Bedrock-native are the likelier winners over LangSmith.

**COST** — PII is the obvious one, and the mitigation has to be in the SDK, not the backend. Redact and hash input and output when the span is written; keep structured metadata — lengths, token counts, citation IDs, confidence signals — and redacted text. If raw text is needed for incident analysis it goes to separate, short-TTL, approval-gated storage. Default to not storing raw content; under CPS 234 that is effectively mandatory.

```flowchart
**PROBE** — *"What makes an observability setup actually good?"* → One thing only: do production failures automatically become evaluation cases? Human override, low confidence or a path violation should enqueue an eval candidate with the tool responses recorded as fixtures. Without that feedback loop a dashboard is reassurance, and the eval set is detached from reality within three months. *"The spec is unstable, isn't instrumenting now wasted?"* → That is what the adapter is for. And even when attribute names change, the span structure and the dimensional design do not — which operations deserve a span, which dimensions cost is attributed to, whether content is retained. Those are the real decisions; attribute names are just bindings.
```

**SOURCE** — [observability_notes.md:3](observability_notes.md#L3) spec status · [observability_notes.md:15](observability_notes.md#L15) span tree · [observability_notes.md:35](observability_notes.md#L35) instrumentation code · [observability_notes.md:104](observability_notes.md#L104) PII redaction · [observability_notes.md:136](observability_notes.md#L136) cost attribution · [observability_notes.md:159](observability_notes.md#L159) tooling choice · [observability_notes.md:175](observability_notes.md#L175) the feedback loop · [observability_notes.md:193](observability_notes.md#L193) challenge Q&A · [observability_notes.md:212](observability_notes.md#L212) what a span is

---

### Cost control | cost token budget cache optimisation spend

**SAY** — "I manage cost as an engineering constraint rather than something to economise on afterwards. And the real precondition for cost optimisation is evaluation — without an eval suite you cannot safely move to a smaller model, because you do not know how much quality you lost. So I usually build evaluation first, and cost optimisation falls out of it."

**THEN**
- **Attribution before optimisation.** A span per tool call with input and output tokens, model name and duration; cost attributed across three dimensions — feature, tenant, user. The headline metric is **cost per successful task, not cost per call**. Failures and retries burn money too; on unit price alone, a cheap model that retries three times looks better than an expensive model that succeeds once, and the truth is the reverse.
- **Architecture layer, roughly 10x, do this first.** Most requests should never reach an agent at all — put a classifier or router in front, send common intents down a deterministic path, and let the agent take only the long tail. Cut redundant agent hops, because every hop is a full context replay. Cache anything cacheable: retrieval results, document extraction, classification labels.
- **Model layer, 3 to 5x.** Tiered routing — small models for classification, extraction and routing; the large model only for final reasoning. Prove the downgrade is safe with evaluation instead of guessing. Structured output with explicit length constraints, because output tokens are far more expensive than input.
- **Token layer, 30 to 60%.** Prompt caching, with the system prompt, tool definitions and resident documents in a byte-stable prefix — people accidentally put a timestamp in the prefix and destroy the entire cache. Trim tool descriptions: twenty tool schemas get replayed every turn, and cutting to seven orthogonal tools saves money *and* improves accuracy. Compact long conversations, isolate sub-tasks in sub-agents that return only conclusions. And precision beats volume in retrieval — top 5 after reranking beats stuffing in top 50.

**EXAMPLE** — Runtime guardrails that an insurer will specifically care about: hard `max steps`, `max tokens` and `max tool calls` per task, plus budget alerts and per-tenant rate limiting. Without those, one loop can burn the budget overnight. That is a reliability problem, not just a finance problem.

**COST** — Batch processing halves the price but only works off the critical path. Streaming improves perceived latency without saving anything, and gets misused as a substitute for actually making the system faster.

```flowchart
**PROBE** — *"What is your target — percentage of traffic on the small model?"* → No. The objective is not to maximise the share handled by a small model. It is to minimise total cost while meeting explicit quality, latency and safety requirements.
```

**SOURCE** — [claude_cost_control.md:3](claude_cost_control.md#L3) attribution · [claude_cost_control.md:12](claude_cost_control.md#L12) levers by size · [claude_cost_control.md:35](claude_cost_control.md#L35) runaway guardrails · [claude_cost_control.md:39](claude_cost_control.md#L39) closing line

---

### Model routing and cascading | routing router cascade model selection small model

**SAY** — "I would use a combination of rule-based routing, model-based classification and quality-driven escalation."

**THEN**
- First, handle deterministic cases without an LLM wherever possible. A calculation should not need a model to classify it first.
- For the rest, a lightweight classifier identifies intent, complexity and risk level, and routes to the most cost-effective model that meets the required quality threshold.
- Where quality can be verified, I would cascade: start with the smaller model, validate, and escalate when validation fails. For high-risk insurance decisions I would not do this — there I enforce deterministic controls and human approval rather than relying on model confidence.
- I would express the policy as configuration, not scattered model names and thresholds in code: intents mapped to routes, explicit escalation triggers for low confidence, invalid output and errors, and hard token and retry limits.

**EXAMPLE** — Four patterns worth naming: intent classification plus routing; model cascading with a quality check; complexity-based routing; and semantic cache plus routing, which is the right one for high-repetition policy FAQ. On the cloud provider, Bedrock Intelligent Prompt Routing is the managed option — worth using when the model mix fits what it supports, and worth building yourself when routing has to account for insurance product, user permissions and business risk. In practice I would run a hybrid: business rules own the safety boundary, model routing optimises cost, evaluation validates quality.

**COST** — The classifier itself is latency and cost on every request, and it is a new failure mode — misroute a complex question to the small model and you get a confident bad answer rather than an error. So escalation triggers have to be explicit, and the default route should be the capable model, not the cheap one.

```flowchart
**PROBE** — *"How do you validate the routing policy?"* → Against a representative dataset, measuring task success, cost per request, p95 latency, escalation rate and safety violations. Then deploy gradually and monitor quality per route and per business risk tier, because an aggregate number will hide a route that is failing.
```

**SOURCE** — [words_must_say_during_interview.md:45](words_must_say_during_interview.md#L45) full English answer · [claude_cost_control.md:43](claude_cost_control.md#L43) four patterns, Bedrock, config

---

### Multi-agent — when not to | multi agent mas multiple agents orchestration handoff

**SAY** — "My default answer is that you shouldn't. Multi-agent is a cost you pay, and it needs a specific reason to be worth paying."

**THEN**
- **Context isolation — the main legitimate reason.** The main agent's context is a scarce resource. A sub-task that has to read forty documents to produce one conclusion should burn those tokens in its own window and hand back only the conclusion. That is not about division of labour; it is about keeping the main thread from being polluted by noise.
- **Parallelism for latency** — but only for read-heavy, write-light tasks. Query five sources at once and aggregate. The moment coordinated writes are involved, parallelism goes from advantage to disaster.
- **Permission boundaries** — the hardest reason in an insurance context. The agent that can read customer PII should not also hold external call privileges. Splitting permissions so each agent runs least-privilege is an architectural defence, not a prompt-level constraint.
- **Independent evolution and evaluation.** Each agent gets its own prompt version, golden set and regression suite, and a team can own it. That is an organisational scaling reason rather than a technical one — but it is often the real reason, and worth saying honestly.

**EXAMPLE** — My decision test: can the sub-task be described in one paragraph, and can the result be handed back in one paragraph? If not, the handoff will lose too much and it stays in a single agent. Plus: read-heavy and write-light splits well; needs coordinated writes, do not split.

**COST** — Error compounding — 95% reliability per step is 77% over five steps. Lossy handoff, because the sub-agent does not know what the main agent knows and the handoff is just a summary. Token cost, commonly ten-plus times single-agent. Observability complexity, because the trace goes from a line to a tree. And attribution difficulty — non-determinism stacked on non-determinism makes it genuinely hard to say which step is at fault.

```flowchart
**PROBE** — *"When is it clearly wrong?"* → When the task is really a fixed process — that is a workflow, not an agent, let alone multi-agent. When sub-tasks need frequent back-and-forth alignment, because communication cost eats the entire gain. In latency-tight synchronous paths. And above all, before single-agent evaluation is working — adopting multi-agent without an evaluation system is manufacturing complexity where you cannot see it.
```

**SOURCE** — [agent_note.md:2](agent_note.md#L2) full note · [agent_note.md:9](agent_note.md#L9) the four real reasons · [agent_note.md:23](agent_note.md#L23) the costs · [agent_note.md:31](agent_note.md#L31) decision test · [agent_note.md:37](agent_note.md#L37) when not to split

---

### Agent versus deterministic orchestration | deterministic orchestration workflow step functions when agent

**SAY** — "Most of the time you should use deterministic orchestration. An agent only earns its place in one situation: when the control flow genuinely cannot be enumerated at design time."

**THEN**
- Four signals that deterministic has broken down: branches are not enumerable because the input space is open-ended; the number of steps depends on intermediate results, so the DAG cannot be drawn because whether an edge exists is only known at runtime; failure requires changing strategy rather than retrying; and maintenance cost has inverted, where every new case class means editing orchestration code and shipping a release.
- If none of those four holds, use Step Functions and move on.
- What deterministic genuinely wins on — and these are real, not conservative: enumerable, testable, predictable latency, fixed cost, clear failure localisation, and auditable. Under local regulators, "I can show you which branch this decision took" is a hard requirement. An agent trace can satisfy it too, but at an order of magnitude more cost to evidence.

**EXAMPLE** — The shape I would actually build is a deterministic exoskeleton with a model core. The outer layer is deterministic and owns transaction boundaries, retries, timeouts, permissions, audit, idempotency and state persistence. The model only makes judgements inside a node — classify this, extract that, which tool next. The agent's freedom is wrapped in a deterministic envelope: it decides what to do, but it does not decide where the boundaries are.

**COST** — Both migration directions matter, and the second is underrated. Deterministic to agent: run the rules first, instrument where humans deviate from them, and only replace that segment with an agent once data proves branches really did explode — so the decision rests on evidence, not intuition. Agent to deterministic: use the agent for discovery, then freeze the high-frequency paths into deterministic flows once they stabilise and let the agent cover only the long tail. Cost and latency drop by an order of magnitude.

**PROBE** — Closing line worth saying: "Agents are good for *finding* the process; deterministic orchestration is good for *running* the process. A lot of teams have finished finding it and are still using an agent to run it."

**SOURCE** — [agent_note.md:46](agent_note.md#L46) full note · [agent_note.md:51](agent_note.md#L51) four failure signals · [agent_note.md:64](agent_note.md#L64) deterministic exoskeleton · [agent_note.md:74](agent_note.md#L74) both migration directions

---

### Level check — how to sound Lead, not Senior | level lead senior junior framing how to answer

**THEN**
- Ordinary candidate: "I have experience with RAG and LangChain." Senior: "I built a RAG system using LangChain." Lead: start from whether retrieval is needed at all, define measurable quality, latency, cost and safety objectives, design retrieval and tool boundaries around those requirements, and establish evaluation and observability before production.
- The seven sentences worth being able to say naturally — chunking is structure-aware; dense embeddings are weak on exact identifiers; hybrid retrieval combines semantic recall with lexical precision; the retriever optimises recall and the reranker optimises precision; query rewriting risks drift so evaluate it against original intent; metadata filtering enforces business boundaries but bad metadata creates false negatives; and evaluate retrieval independently from answer quality.
- The full-marks worked example, if they ask how to fix a RAG system giving wrong answers about policy exclusions: "I would first determine whether the exclusion clause is actually being retrieved. If it isn't, I would inspect document parsing and structure-aware chunking, metadata filtering, and retrieval recall. I would also add lexical retrieval, because exclusions often contain exact policy terminology and clause identifiers. If the correct clause is retrieved but ranked too low, I would introduce or tune a reranker. Finally, I would add exclusion-specific golden test cases and measure Recall@K, NDCG and downstream groundedness, so that every change can be validated rather than tuned subjectively."

**COST** — Three habits that read as junior: naming tools before naming requirements; quoting an industry-standard threshold instead of deriving one; and claiming an agent for something that is a fixed workflow. Every answer should move requirement, then design, then metric, then trade-off.

**SOURCE** — [rag_interview_notes.md:2252](rag_interview_notes.md#L2252) the seven sentences · [rag_interview_notes.md:2336](rag_interview_notes.md#L2336) full worked example · [words_must_say_during_interview.md:2](words_must_say_during_interview.md#L2) three levels · [zurich_ai_lead_20261007.md:100](zurich_ai_lead_20261007.md#L100) what the JD tests · [zurich_ai_lead_20261007.md:117](zurich_ai_lead_20261007.md#L117) instant-reject answers

