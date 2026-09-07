# 科学的 Prompt 调优：告别“玄学调参”，用 McNemar 统计学检验量化你的 AI 系统

如果你在开发 LLM 应用，你一定经历过这种崩溃的时刻：为了修复一个 Case 加了一句 Prompt，结果之前的 10 个 Case 全挂了。这种“打地鼠式”的 Prompt 工程是毫无意义的。

在顶级 AI Labs，前线部署工程师（FDE）从不依靠“感觉（Vibes）”来调优，我们用**统计学和消融实验（Ablation Studies）**。

### 为什么生硬的“准确率差值（Accuracy Delta）”是骗人的？

假设 Prompt A 的准确率是 75%，Prompt B 加上了“深呼吸”后变成了 77%。这就意味着 Prompt B 更好吗？
**绝大多数情况下，这不是因为能力变强了，而只是数据采样时的噪音（Noise）。**

在 `AI-FDE-Playbook` 的架构设计中，我引入了医疗和统计界极高标准的评估法：
1. **Wilson 置信区间（Confidence Intervals）**：每个准确率数字背后都必须带上 `[95% CI]`。这让我们可以清楚地看到样本量是否足以支撑这个结论。
2. **McNemar 确切检验（McNemar Exact Test）**：当我们要对比两个不同版本的 Prompt 时，我们要看的是**“两者存在分歧的样本（Discordant Count）”**，并计算 p-value。如果 p > 0.05，即便准确率提升了 3%，我们也会在结论里写上“没有显著性提升，该改进无效”。

### 把 Prompt 视为不可变的工件（Versioned Artifacts）

不要在你的主函数里到处写字符串。在我们的架构里，每一个 Prompt 都是被封存的 `PromptVersion` 实例（存在 `src/prompts.py` 中）。
`v2` 相比 `v1` 加了什么 Hypothesis（假设）？`v3` 相比 `v2` 又加了什么？
每次改动后运行 `./scripts/benchmark.sh`，系统会生成一份严谨的对比表格。

只有这样，你才能确信你的 Agent 是随着迭代不断进化，而不是在原地无规律地震荡。查看具体的统计学实现，请移步 [AI-FDE-Playbook Repo](https://github.com/CloudsDocker/AI-FDE-Playbook)。
