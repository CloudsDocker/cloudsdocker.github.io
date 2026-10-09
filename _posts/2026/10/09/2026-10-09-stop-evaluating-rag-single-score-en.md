---
title: Stop Evaluating Your RAG Pipeline as a Single Black Box
header:
    image: /assets/images/Python-expert-write-code-like-this.jpg
date: 2026-10-09
tags:
 - rag
 - evaluation
 - architecture
 - testing
 - llm
permalink: /blogs/tech/en/stop-evaluating-rag-single-score
lang: en
layout: single
category: tech
---
> "Perfection is finally attained not when there is no longer anything to add but when there is no longer anything to take away." — Antoine de Saint-Exupéry

# Stop Evaluating Your RAG Pipeline as a Single Black Box

*A high retrieval recall score means nothing if you cannot trace exactly which layer of your pipeline actually failed.*

I keep a note from a team building AI factories: *don't treat AI as a wishing well; treat it as a workbench.* If the output is wrong, you don't yell at the model to fix a single result. You adjust the production pipeline, the rules, and the flow.

Yet, when a Retrieval-Augmented Generation (RAG) system gives a wrong answer, the industry's reflex is to shrug and declare that the LLM hallucinated. This is treating the model like a wishing well. By the end of this post, you will be able to stop guessing why your agent failed and start pinpointing exactly which layer—retrieval, tool selection, or generation—is responsible.

## 🧭 The Anatomy of a Wrong Answer

Consider a standard RAG pipeline querying a policy document. The user asks about laptop theft overseas. The final output says it is covered, but the source document explicitly excludes unattended electronics.

If you blindly blame the generation model for this error, you learn nothing. The failure could exist anywhere in the chain. Did the retriever pull the general coverage clause but miss the specific exclusion? Did the agent select the wrong customer ID when calling the policy API? Did the LLM read the exclusion but creatively interpret "unattended" to mean something else?

To answer this, we have to stop looking at AI evaluation as a single quality score.

```text
                       AI Evaluation
                             │
      ┌──────────────────────┼──────────────────────┐
      ▼                      ▼                      ▼
 RETRIEVAL                 AGENT               GENERATION
      │                      │                      │
Recall@K               Tool Selection          Correctness
Precision@K            Tool Arguments          Relevance
MRR                    Task Completion         Groundedness
NDCG                   Loop Detection          Faithfulness
      │                      │                      │
      └──────────────────────┼──────────────────────┘
                             ▼
                      SYSTEM LEVEL
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
         Latency            Cost             Safety
```

## 🏗️ Why Perfect Retrieval Still Fails

The most common failure mode in RAG is assuming that retrieval is a solved problem. It begins with chunking. Chunk size is not a magic number; it should follow the document structure and the retrieval task. If you blindly split a legal document every 500 tokens, you will sever the semantic link between a coverage clause and its subsequent exclusion. A structure-aware approach preserves sections, subsections, and clauses as the natural semantic boundaries.

Then comes the search mechanism itself. Semantic embeddings are brilliant for matching the word "stolen" in a query to "theft" in a document, but they fail completely on exact identifiers like policy number `ZX-49382-AU`. This is why enterprise architectures demand hybrid retrieval: dense embeddings for semantic meaning, combined with sparse BM25 for exact lexical matching.

But returning a massive list of chunks to the LLM destroys your context limits and your budget. The solution is a two-stage architecture. I use the first-stage retriever for recall and the second-stage reranker for precision.

To measure this, we use metrics like Mean Reciprocal Rank (MRR) to check how early the first relevant document appears, and Normalized Discounted Cumulative Gain (NDCG) to weight highly relevant exact clauses higher than generally related policy information.

🩸 **血泪提醒**：The most pervasive misunderstanding in RAG evaluation is the definition of K. Top-K does not mean K *relevant* documents; it means K *candidate* documents. If your ground truth has 4 relevant documents, and your Top-5 returns 2 of them alongside 3 useless chunks, your Recall@5 is 50% (you found half of what exists) and your Precision@5 is 40% (most of what you returned is garbage).

## 🛠️ Evaluating the Trajectory, Not the Output

If the retrieval is perfect, an agent can still fail. Evaluating an agent requires testing the trajectory it took to reach the answer, not just the final string it output. This is where the workbench mentality becomes critical: we are inspecting the tools and the flow, not just the final artifact.

First, we evaluate tool selection and arguments. Did the agent choose `calculate_excess()` instead of `get_customer()`? Even if it chose the right tool, did it pass the correct `claim_id`, or did it hallucinate a parameter?

Next, we measure task completion. A response might sound excellent, but if the user asked to find the policy, check the theft coverage, and calculate the excess, and the agent stopped after the second step, the task failed.

Finally, loop detection is a silent killer in production. An agent calling `search_policy` five times in a row will spike your latency, burn your token budget, and eventually time out. Loop rate must be a top-level metric.

Trajectory assertions must include negative constraints. A path can vary, but a forbidden action must remain forbidden.

| Level | Assertion | Use Case |
|---|---|---|
| Exact Sequence | Must call A -> B -> C | Almost never use; too brittle. |
| Partial Order | Must lookup policy before refund | Stable and semantically clear. |
| Negative Constraint | Do not call refund without approval | Zero tolerance. |

## 🧠 When to Fire the LLM-as-a-Judge

When retrieval and tools succeed, we evaluate generation.

Correctness asks whether the answer is right. Relevance asks whether it answers the user's specific question. You can output a perfectly correct summary of a premium schedule, but if the user asked about a stolen laptop, it is entirely irrelevant.

Groundedness and faithfulness are closely related but distinct. Groundedness asks if the generated answer has support in the retrieved evidence. Faithfulness asks whether the answer accurately represents that evidence without introducing contradictions. If the context says "Coverage may apply," and the LLM says "Your claim is definitely covered," the answer is grounded in the right document but unfaithful to the text.

📌 **Takeaway:** A 95% retrieval recall does not guarantee high answer accuracy, and LLM-as-a-judge is a brittle tool that should often be replaced by deterministic pipeline assertions.

At the system level, averages lie. Track P95 and P99 latency. Track cost *per successful task*, because a cheap agent that fails to resolve a claim is infinitely expensive. Safety is a separate evaluation dimension, not a subset of accuracy.

## The CI/CD Reality Check

How do you actually run this in continuous integration without blocking every pull request on flaky LLM variance?

First, make your tools deterministic. Record API responses as fixtures and replay them during evaluation. This narrows the variance to the model alone.

Second, test in layers. Smoke tests and safety bounds run on every PR. Full baseline comparisons run nightly.

Third, set your deployment gates on the delta, not the absolute score. A drop of 5% from the baseline is a failure.

Most importantly, production incidents must become test cases. If a user reports that the agent processed a refund without authorization, you isolate the trace ID, export a draft case, mask the PII into synthetic data, and assert a negative constraint on that exact trajectory.

## The Principle of the Traceable Defect

In probabilistic systems, failure is inevitable. Reliability is not the absence of errors, but the ability to attribute an error to a specific, localized boundary. If an error cannot be attributed, it cannot be fixed without regressing something else.

This principle stops being useful only if your system is a simple, single-prompt classifier with no external tools. In that narrow case, layered attribution is architectural overhead. But for enterprise RAG, it is mandatory.

> Generalize: What is the single aggregate score hiding in your own pipeline?

## Returning to the Workbench

This brings us back to the workbench. A workbench is characterized by its transparency. You can see the exact mechanism that snapped.

I don't want a single AI quality score. I want a decomposable evaluation system that tells me where the system failed and why.

I judge an evaluation suite by exactly two things: do production failures automatically become test cases, and does the team ignore the red lights? If you fail the second, the entire engineering effort is theatre.

The next time a user forwards a completely fabricated response, what is the first query you will run to find out why?
