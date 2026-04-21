---
title: "Cognitive Scaffolding: The Unseen Clockwork of AI Memory and Skills | 认知脚手架：揭秘大模型“记忆”与“技能”的幕后黑盒"
header:
    image: /assets/images/hd_state_machine.png
date: 2026-04-20
tags:
- AI
- Architecture
- Large Language Models
- System Thinking
layout: single
category: tech
---

> "Simple can be harder than complex: you have to work hard to get your thinking clean to make it simple." — Steve Jobs

## (Chinese Version)

### 引言：齐天大圣与如来神掌

9月3日的阅兵方阵整齐划一，那种极致的“秩序感”总能让人联想到工程领域里的极致追求。作为一名在顶级科技公司深耕了20年的基础设施工程师，我看到的不仅是队形，更是背后严丝合缝的调度系统。

最近，很多同行在讨论 AI 的“进化”时，总会提到一个令人着迷的幻觉：AI 似乎开始“认识”我们了。如果你觉得 Claude 能记住你的偏好、熟练使用某种特定技能是因为它“长脑子”了，**那么这篇文章可能就是为你准备的**。

从**第一性原理**出发， AI 的本质是一个“冻结的函数”。它法力无边，像极了那个能翻十万八千里跟斗的孙悟空。但它有一个致命的特质：**瞬时失忆**。每次对话窗口的关闭，都意味着这个函数的入参清零，悟空再次回到了五指山下。

那么，它是如何表现出“长效记忆”和“专业技能”的？答案不在模型权重里，而在于两套精密设计的外部脚手架：**Memory（记忆系统）** 与 **Skills（技能系统）**。

---

### 第一章：无状态的禅意——为什么 AI 必须“失忆”？

**普通人的看法**：AI 不记得我是因为它还不够聪明，或者厂商为了省钱。

**资深工程师的洞察**：无状态（Stateless）是系统架构的“最优解”。
1.  **安全隔离**：如果模型是有状态的，恶意用户可以通过渐进式对话“磨损”模型的价值观基线。无状态确保了每次交互都从完全相同的安全基线出发。
2.  **物理隐私**：有状态系统依赖逻辑隔离（容易出 Bug）；无状态架构实现了物理隔离——根本没有共享状态，也就没有泄露路径。
3.  **横向扩展**：遵循 RESTful 的设计哲学，任何请求可以路由到任何实例，实现了互联网级的极致伸缩。

---

### 第二章：记忆系统（Memory）——外部化的陈述性知识

所谓“记忆”，本质上是大模型的一张动态“便利贴”。

#### 1. 它是如何工作的？
当你要求 Claude“记住我是工程师”时，它并不是在修改神经突触，而是在调用一个名为 `memory_user_edits` 的工具。
*   **写入路径**：
    *   **显式写入**：通过 `add` 或 `replace` 命令，将信息持久化到外部数据库。
    *   **隐式摘要**：后台系统异步分析历史对话，自动提炼标签。
*   **约束之美（奥卡姆剃刀）**：
    *   **30 条上限**：这不是随意定的，而是基于 **Token 经济学**。每条记忆都会在对话开始时被注入 System Prompt。如果记忆无限增长，会迅速吃掉上下文窗口（Context Window），并引入歧义。
    *   **100k 字符限制**：确保了信息的“最小描述长度”。

#### 2. 陷阱：近因偏差（Recency Bias）
记忆系统像一块会随时间褪色的黑板。系统 Prompt 明确指出：记忆存在**近因偏差**。越新的对话权重越高，三年前的偏好可能在大量新信息的冲刷下逐渐模糊。这是一种“自由能原理”的工程实现——系统必须优先响应当下的不确定性。

---

### 第三章：技能系统（Skills）——程序性的肌肉记忆

如果说 Memory 决定了 Claude “面对的是谁”，那么 Skills 决定了它 “如何做事”。

#### 1. 知识蒸馏：从 Trial-and-Error 到 SKILL.md
在 `/mnt/skills/` 目录下，存储着名为 `SKILL.md` 的文件。这不仅是说明书，更是**冷冻脱水的实战智慧**。
*   **案例分析**：比如处理 Word 文档的 `docx` 技能。它是工程师们经历了成千上万次“生成-报错-调整-再测试”的循环后，蒸馏出来的最佳实践路径。
*   **三层加载协议**：
    *   **Metadata**：永远在线，让模型知道“我有这个锤子”。
    *   **SKILL.md**：当描述（Description）命中任务时，按需加载。
    *   **References**：极其细节的参考，仅在执行阶段读取。

#### 2. 独特的视角：外部化的 Few-shot Learning
传统 Prompt 优化需要手动给例子（Few-shot）。Skills 将其资产化。这意味着你可以为自己公司特定的报告格式创建一个 `SKILL.md`。从此，Claude 不再需要你每次重复教它“怎么做”，它通过读取这个文件，瞬间获得了职业级的“肌肉记忆”。

---

### 第四章：架构层面的博弈——System Prompt 的排序艺术

在读取顺序上，系统有着严格的层级：
1.  **核心规范**：模型必须遵守的底线（先读）。
2.  **Memory 注入**：你是谁（次读）。
3.  **对话历史**：现在聊什么（后读）。

这种排序确保了**当前对话上下文拥有最高优先级**。如果记忆说你用 Python，但你现在问 Java，当前对话会瞬间覆盖记忆里的旧习惯。这是**二分法**在信息管理中的应用：区分“长期偏好”与“瞬时需求”。

---

### 总结：差距体现在思维维度

从普通工程师到资深专家的差距，不在于掌握了多少命令，而在于**系统性思考**的能力：
*   **普通人**看到的是“功能”：AI 能记事了。
*   **资深者**看到的是“权衡”：为了平衡安全、成本与性能，系统是如何利用外部数据库和静态文件构建起这个个人化幻觉的？

理解了 Memory 与 Skills，你就理解了如何go extra mile：不仅仅是提问，而是学会为 AI 构建**认知脚手架**。

如果有问题，要讨论可以联系我在：
- 主页: [example.org](https://example.org)
- 邮箱: phray@example.org

---

## (English Version)

### Introduction: The Monkey King and the Buddha's Palm

The absolute precision of the September 3rd parade square is a testament to the "sense of order" that defines high-end engineering. As an infrastructure engineer with over 20 years at top-tier tech firms, I don't just see formations; I see the perfectly synchronized scheduling systems behind them.

Recently, colleagues discussing AI "evolution" often fall for a captivating illusion: the idea that AI is starting to "know" us. If you think Claude's ability to remember your preferences or use specific skills stems from it developing a "brain," **then this article might be for you.**

From **First Principles**, the essence of an LLM is a "frozen function." It is as powerful as the Monkey King, capable of flipping across the universe in a single leap. But it has one fatal trait: **instantaneous amnesia**. Each closed session resets the function parameters. The Monkey King returns to the bottom of the mountain.

How, then, does it exhibit "long-term memory" and "professional skills"? The answer lies not in the model weights, but in two precisely engineered external scaffolds: the **Memory System** and the **Skills System**.

---

### Chapter 1: The Zen of Statelessness — Why AI Must "Forget"

**The Common View**: AI forgets because it isn't smart enough yet, or the vendor is cutting costs.

**The Expert Insight**: Statelessness is the "Global Optimum" of system architecture.
1.  **Security Isolation**: If a model were stateful, malicious users could gradually "wear down" the model's safety baseline through incremental dialogue. Statelessness ensures every interaction starts from the exact same security baseline.
2.  **Physical Privacy**: Stateful systems rely on logical isolation (error-prone); stateless architectures achieve physical isolation—there is no shared state, hence no leakage path.
3.  **Horizontal Scalability**: Following the RESTful philosophy, any request can be routed to any instance, enabling internet-scale elasticity.

---

### Chapter 2: The Memory System — Externalized Declarative Knowledge

So-called "memory" is essentially a dynamic "Post-it note" for the LLM.

#### 1. How does it work?
When you ask Claude to "remember I'm an engineer," it isn't modifying neural synapses. It calls a tool named `memory_user_edits`.
*   **Writing Paths**:
    *   **Explicit Edits**: Uses `add` or `replace` commands to persist info into an external database.
    *   **Implicit Summarization**: Background systems asynchronously analyze history to distill labels.
*   **The Beauty of Constraints (Occam's Razor)**:
    *   **The 30-Item Limit**: This isn't arbitrary; it's rooted in **Token Economics**. Every memory is injected into the System Prompt at the start. Unlimited memory would consume the context window and introduce ambiguity.
    *   **100k Character Limit**: Ensures the "Minimum Description Length."

#### 2. The Pitfall: Recency Bias
Memory acts like a blackboard that fades over time. The system prompt explicitly states that memory suffers from **Recency Bias**. Newer conversations carry more weight. A preference from three years ago may blur under the flood of new data. This is an engineering implementation of the "Free Energy Principle"—the system must prioritize resolving current uncertainty.

---

### Chapter 3: The Skills System — Procedural Muscle Memory

If Memory determines "who Claude is facing," then Skills determine "how it performs."

#### 1. Knowledge Distillation: From Trial-and-Error to SKILL.md
Within `/mnt/skills/`, static `SKILL.md` files are stored. These aren't just manuals; they are **dehydrated combat wisdom**.
*   **Case Study**: Consider the `docx` skill for Word documents. It is the distilled "best practice path" derived from thousands of "Generate-Error-Adjust-Retest" cycles by engineers.
*   **Three-Tier Loading Protocol**:
    *   **Metadata**: Always online, letting the model know "I have this hammer."
    *   **SKILL.md**: Loaded on demand when the task description hits the trigger.
    *   **References**: Granular details read only during execution.

#### 2. A Unique Perspective: Externalized Few-shot Learning
Traditional Prompt Engineering requires manual examples (Few-shot). Skills turn this into an asset. You can create a `SKILL.md` for your company's specific report format. Claude no longer needs to be "taught" every time; it reads the file and instantly gains professional-grade "muscle memory."

---

### Chapter 4: Architectural Game Theory — The Art of System Prompt Ordering

In terms of reading order, the system follows a strict hierarchy:
1.  **Core Behavioral Rules**: The non-negotiable baseline (read first).
2.  **Memory Injection**: Who you are (read second).
3.  **Conversation History**: What we are talking about now (read last).

This ordering ensures that **the current conversation context has the highest priority**. If memory says you use Python, but you ask about Java now, the current context overrides the old habit instantly. This is the **Dichotomy of Control** applied to information management: separating "long-term preference" from "instant need."

---

### Conclusion: The Gap is in the Dimension of Thinking

The gap between a junior engineer and a senior expert lies not in how many commands they know, but in their capacity for **Systems Thinking**:
*   **Juniors** see "features": The AI can now remember things.
*   **Seniors** see "trade-offs": How does the system utilize external databases and static files to construct this personalized illusion while balancing security, cost, and performance?

By understanding Memory and Skills, you understand how to go the extra mile: don't just ask questions; learn to build the **cognitive scaffolding** for the AI.

If you have questions or wish to discuss further, contact me at:
- Home: [example.org](https://example.org)
- Email: phray@example.org

---
