# Stop Guessing, Start Measuring: A Scientific Approach to Prompt Ablation using McNemar's Test

If you build LLM applications, you know the frustration: you add a line to the prompt to fix one edge case, and suddenly 10 other cases break. "Whac-A-Mole" prompt engineering is unsustainable.

At top AI labs, FDEs do not rely on "vibes." We rely on **statistical ablation studies**.

### Why Raw Accuracy Deltas Are Misleading

Suppose Prompt A gets 75% accuracy and Prompt B (with "take a deep breath" added) hits 77%. Is Prompt B better?
**In most cases, this is just sampling noise masquerading as a signal.**

In the `AI-FDE-Playbook`, I implemented rigorous evaluation pipelines typically seen in clinical trials:
1. **Wilson Confidence Intervals**: Every accuracy number must carry a 95% CI. A 2% boost on 50 samples is mathematically meaningless.
2. **McNemar's Exact Test**: When comparing Prompt A and Prompt B, we only look at the *discordant pairs* (the specific turns where they disagreed) and calculate a p-value. If `p > 0.05`, we reject the prompt change, regardless of what the raw accuracy delta says.

### Treat Prompts as Immutable Artifacts

Stop hardcoding raw strings in your main solvers. In this architecture (`src/prompts.py`), every prompt is an immutable `PromptVersion`.
What was the hypothesis for `v2`? What changed in `v3`?
Running our benchmark suite spits out an automated Markdown table showing exactly which hypotheses passed the statistical significance tests.

This is the only way to ensure your AI Agent is monotonically improving, rather than endlessly oscillating. See the exact statistical implementation in the [AI-FDE-Playbook Repo](https://github.com/CloudsDocker/AI-FDE-Playbook).
