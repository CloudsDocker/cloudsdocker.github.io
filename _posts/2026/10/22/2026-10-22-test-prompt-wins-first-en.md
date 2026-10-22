---
title: Run This Before You Accept a Prompt Win
header:
    image: /assets/images/bg_raw/BingWallpaper (12).jpg
date: 2026-10-22
tags:
 - llm
 - prompt-engineering
 - evaluation
 - statistics
 - testing
permalink: /blogs/tech/en/test-prompt-wins-first
lang: en
layout: single
category: tech
---
“It is a capital mistake to theorize before one has data. Insensibly one begins to twist facts to suit theories, instead of theories to suit facts.” — Arthur Conan Doyle

# Run This Before You Accept a Prompt Win

Edison reportedly listed more than 1,600 materials that might withstand heat, then tested them one by one. When asked why so many failures had not discouraged him, he reframed the result: none of those trials were wasted; each had shown which materials did not work. The point was not that brute force is always admirable. It was that a conclusion earned by repeated tests is fundamentally different from one inferred from a few encouraging anecdotes.

*For paired LLM evaluations, a higher percentage is not evidence until the changed cases survive a significance test.*

Open your evaluation results and run the comparison you already have:

```sh
./scripts/benchmark.sh
```

If that command reports Prompt A at 75% and Prompt B at 77%, do not merge B yet. A two-point gain can be a better prompt. It can also be the same prompt performance wearing a more flattering sample.

The promise here is practical: by the end, you will know how to compare two prompt versions without mistaking ordinary evaluation noise for an improvement.

I have watched prompt work turn into whack-a-mole. Add one sentence to repair one failing case; ten cases that used to pass now fail. Add another sentence; a different cluster moves. The loop feels productive because the output changes. It is meaningless if we cannot tell improvement from movement.

**A prompt win is a claim about changed decisions, not a larger percentage.**

## Why a raw accuracy delta lies by omission

Suppose Prompt A scores 75% and Prompt B adds “take a deep breath” before answering and scores 77%. Is B better?

Usually, that question cannot be answered from those two percentages alone. Accuracy is an estimate from a finite set of examples. Change the sampled cases, change a few borderline judgments, or simply encounter a different distribution of inputs, and the estimate moves. The delta does not tell us whether B solved cases A missed, whether B regressed on A’s successes, or whether the observed movement is compatible with chance.

That does not mean accuracy is useless. It means accuracy is a summary, not a verdict.

The first discipline is to attach a 95% confidence interval to every reported accuracy. A Wilson confidence interval is a good default for a binomial accuracy estimate, especially when sample sizes are not large or the accuracy is near either extreme. It makes the uncertainty visible instead of allowing a bare percentage to pretend it has infinite precision.

Wilson intervals still do not answer the paired comparison question by themselves. Comparing overlapping or non-overlapping intervals is not a substitute for a test designed for two systems evaluated on the same cases.

Here is the compact version worth keeping beside every prompt benchmark:

| What you observed | What to inspect next | What it can establish |
|---|---|---|
| A: 75%, B: 77% | 95% Wilson intervals | Uncertainty around each accuracy estimate |
| The same cases ran through both prompts | Cases where A and B disagree | Whether either version changes outcomes |
| A larger B percentage | McNemar exact-test p-value | Whether paired outcome changes are statistically distinguishable from symmetry |

The surprise is that the cases where both prompts are correct, and the cases where both are wrong, do not drive McNemar’s test. The test is about disagreement.

For each evaluated case, reduce the outcome to correct or incorrect for each version. Then make the paired table:

|  | B correct | B incorrect |
|---|---:|---:|
| A correct | both correct | A wins |
| A incorrect | B wins | both incorrect |

McNemar’s exact test uses the two off-diagonal cells: `A wins` and `B wins`. These are the discordant cases. If B’s two-point headline comes from a tiny and roughly balanced set of disagreements, there is little evidence that B is actually superior. If the exact test gives `p > 0.05`, I would write: “no statistically significant improvement under this evaluation; treat the change as ineffective.” That remains true even if a raw accuracy number happens to rise by three percentage points.

The threshold is a decision convention, not a magic boundary between truth and falsehood. A p-value above 0.05 does not prove the prompts are identical; it says this evaluation did not supply enough evidence to reject the no-difference model at that threshold. That distinction matters when a benchmark is small.

## Version the prompt, not the feeling about it

A statistical test cannot rescue an untraceable change. If prompt text is scattered as string literals through a main function, nobody can state what was tested. A result cannot be reproduced, and a regression cannot be explained.

Treat each prompt as an immutable artifact. In a repository, that can be a `PromptVersion` instance in a dedicated module such as `/path/to/repo/src/prompts.py`. The important property is not the class name. It is that an evaluation names an exact version and that version does not silently mutate after the result is recorded.

A minimal shape might look like this:

```python
@dataclass(frozen=True)
class PromptVersion:
    name: str
    hypothesis: str
    template: str
```

The hypothesis is not decoration. `v2` should say what it changed relative to `v1` and why: perhaps it adds an explicit constraint intended to reduce a known ambiguity. `v3` should state what it changed relative to `v2`. Without that record, a prompt history becomes a pile of prose revisions and lucky guesses.

After every change, run the benchmark and preserve the comparison table: version identifiers, the hypothesis, the evaluated case set, accuracy with its 95% Wilson interval, discordant counts, and the McNemar exact-test result. This is prompt ablation in its useful form: change one meaningful variable, measure it against a stable baseline, and retain both gains and failures.

I take a firm position here: do not promote a prompt because its aggregate accuracy rose. Promote it when the paired evidence supports the hypothesis, or when you explicitly accept a non-statistical reason for the tradeoff and document it.

The strongest counter-case is real. Some prompt changes are adopted for reasons an accuracy test does not capture: a safety requirement, a clearer output contract, lower latency, lower cost, or a failure category whose consequence outweighs its frequency. In those cases, accuracy and McNemar should not be used as a veto. They should be reported honestly alongside the criterion that actually decided the change.

McNemar also has limits. It needs paired outcomes from the same cases and a binary definition of success. If grading is noisy, subjective, or multi-dimensional, first improve the evaluator and decide what “correct” means. If cases are correlated—for example, many are near-duplicates—the nominal p-value can look more confident than the independent-case assumption deserves. And statistical significance does not tell you whether an effect is large enough to matter operationally.

That is why the artifact is the unit of work. A prompt version carries its exact text and hypothesis; the benchmark carries the paired outcomes and uncertainty; the decision record carries the reason for shipping or rejecting it. Together, they let an agent evolve through iteration rather than oscillate without a map.

Before accepting your next prompt win, ask one narrower question: which exact cases changed, and would you still ship the revision after looking only at those disagreements?
