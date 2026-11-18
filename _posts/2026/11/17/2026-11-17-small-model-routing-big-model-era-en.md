---
title: 'Industry Expert''s Perspective: Small Model Routing Success in the LLM Era'
header:
    image: /assets/images/jpa_spring_data.png
date: 2026-11-17
tags:
 - llmoops
 - small-models
 - agent
 - prompt-engineering
 - rag
permalink: /blogs/tech/en/small-model-routing-big-model-era
lang: en
layout: single
category: tech
---

> Turn your wounds into wisdom

# Industry Expert's Perspective: Small Model Routing Success in the LLM Era

*In the Era of Large Language Models, how can small model routing make your system both secure and maintainable?*

"If you throw all problems at the LLM, who decides who is ultimately responsible? I ran an agent backend with MCP on a GPU and found that the LLM was only responsible for generating the final output, while the rest was handled by small models or pure code. Why do this? This article provides a complete breakdown, allowing you to treat the LLM as an assistant for 'writing the final output' and avoid cramming all decision-making into a single model."

My home 5080 is quite powerful, but the project this series will discuss (an agent backend with MCP tools) ultimately adopted this division of labor: **the LLM is only responsible for generating the final output; all other decisions are delegated to small models or pure code.**

This article is the first in the series, laying the foundation: small model routing.

Series Catalog:

1. Small Model Routing and Degradable Backends (This article)
2. Guardrails: Four Checkpoints in the Agent Loop
3. Prompts as Deployable Artifacts, Not String Constants
4. Real-time Cross-Process Call Stacks
5. Hybrid Retrieval RAG: BM25 + Vector + RRF + Rerank
6. Evaluation, Quality Gates, and Closed-Loop Feedback
7. Engineering Intuition: Fixes Not Documented in Design Specs

### 1. 🎯 30-Second Version

- Abstract every "decision" in the system into a **slot**: embedding, reranking, classification, entity extraction, language identification.
- Each slot has two backends: a **real small model** (if installed) and a **deterministic fallback implementation** (pure Python, always available).
- Callers only recognize the interface, unaware of the underlying implementation. CI, cold-booted laptops, and offline machines can all run it.
- `profile()` reports which backend each slot actually resolved to, writing it into traces and evaluation reports—otherwise, you'll never be able to explain "who produced this score."

| Slot      | Small Model                      | Fallback Implementation    | Used by                                  |
| ---------- | ---------------------------------- | -------------------------- | ---------------------------------------- |
| embedder | bge-small (ONNX, CPU)            | Character n-gram feature hashing | RAG retrieval, injection classifier      |
| reranker  | jina reranker                    | Query term coverage        | RAG reranking                            |
| classifier| few-shot k-NN                    | Off (rules only)           | Rewriting injection                      |
| entities  | GLiNER                            | Off (regex only)           | PII without fixed shapes                 |
| language  | —                                | Unicode script heuristics  | Language routing                         |

#### Refining Slot Responsibilities

| Slot      | Typical Business Scenarios                                   | Required Input/Output      |
| ---------- | ------------------------------------------------------------ | -------------------------- |
| embedder | Document retrieval, semantic similarity calculation, vectorized feature extraction | Text → Semantic Vector     |
| reranker | Secondary sorting of candidate answers or retrieval results  | List of Texts → Sorted List |
| classifier| Business classification, sentiment analysis, named entity tag prediction | Text → Category Label      |
| entities | PII, address, date, and other entity extraction, supporting multilingual scenarios | Text → Position/Entity     |
| language | Language identification, for subsequent multilingual processing pipelines | Text → Language Code       |

#### Small Models vs. Fallback Implementations

- **Small Models**:
  - Depend on GPU/CPU, scalable, multilingual support, continuously updatable.
  - Require pre-downloaded weights, deployment on accessible model servers or local containers.
  - Have some dependency on network and hardware resources; may fail in cold-start or offline environments.
- **Fallback Implementations**:
  - Pure Python logic, zero external dependencies, always available.
  - Lower performance and accuracy, but ensures system availability and safety.
  - Quickly return results via simple heuristics or rules, suitable for no-network or hardware-constrained scenarios.

#### Typical Fallback Implementations

- **Character n-gram feature hashing**: Divides text into 3-4 character n-grams, then uses hashing to map them to fixed-dimension vectors. Fast, low memory footprint, suitable for embedding fallback.
- **Query term coverage**: Directly counts the overlap ratio of query terms with terms in candidate answers. Crude but quickly filters out irrelevant items.
- **Rules + Nearest Neighbor**: When small models are unavailable, first apply rule-based filtering, then use nearest neighbor (e.g., K-NN) to find the closest items in a pre-built vector library.
- **Regex**: For fixed-pattern PII (e.g., phone numbers, ID cards), regular expressions are sufficient for identification, avoiding the overhead of complex models.
- **Unicode heuristics**: Detects character ranges via Unicode writing systems to quickly determine the language of the text.

#### How `profile()` Works

```python
# 伪代码示例
for slot_name, slot in pipeline.slots.items():
    start = time.time()
    result = slot.run(input_text)
    duration = time.time() - start
    backend = slot._backend_name  # 'small_model' or 'fallback'
    trace.append({
        'slot': slot_name,
        'backend': backend,
        'duration_ms': round(duration * 1000, 2),
    })
```

### 2. ⚙️ Underpinnings

#### 2.1 Interface First: Protocol, Not Base Class

```python
class Embedder(Protocol):
    id: str
    semantic: bool  # False => only lexical similarity; semantic classifier must remain off

    def embed(self, texts: list[str]) -> list[Vector]: ...
```

Two details worth noting:

**`id` is an identifier.** Every document in the index records "which embedder vectorized me." If the model changes, the `id` changes, and incremental synchronization automatically determines all entries are stale and re-vectorizes them. Without this field, you'd end up with an index mixing two vector spaces, leading to strange retrieval results without errors—the hardest kind of bug to track down.

**`semantic` is an honesty flag.** A fallback hash embedder can also calculate cosine similarity, and the numbers might look equally legitimate, but it only understands "lexical resemblance." If you use it to drive a decision like "is this sentence an injection attack," you're making security decisions based on noise. Therefore, the interface forces each backend to declare its capabilities, allowing consumers to guard with a single line of code:

```python
if not getattr(embedder, "semantic", False):
    return  # Lexical fallback backend: similarity here is meaningless
```

> Lesson: **The most dangerous aspect of fallback implementations is not "poor performance," but "appearing the same."** Explicitly declaring capability differences in the type system and interface semantics prevents consumers from mistakenly treating fallback noise as a secure decision.

## 3. 🧭 Why Choose This, Not Others

When building a system combining large and small models, the intuition to "use LLMs for everything" often prevails. Below, we compare **latency, determinism, testability, attack surface**, and **cost** across five dimensions to explain why, in this project, decision-making is delegated to small models + rules rather than having the LLM perform it directly.

| Dimension | LLM Decision-making | Small Model / Rules |
|---|---|---|
| Latency | Seconds, occupies GPU | Milliseconds, CPU |
| Determinism | Same input may yield different output | Deterministic |
| Testability | Requires live evaluation | Standard unit tests |
| Attack Surface | Decision itself can be injected | Regex doesn't "listen" to human input |
| Cost | One extra call per round | Approximately zero |

**The last row is the most critical**: **Using an LLM to determine "if this statement is trying to trick the LLM" is akin to letting the defendant be the judge.** This seemingly exaggerated statement accurately reflects the risk of entrusting decision-making to LLMs: the model's own output could be used to mislead itself.

### Latency
- **LLM**: A single inference often takes several seconds and must run on a GPU, leading to reduced overall system throughput.
- **Small Models**: Can be completed on a CPU, with latency typically between 1–5 ms, almost without impacting backend operations.

### Determinism
- **LLM**: The same input may yield slightly different outputs across different GPUs or different inference runs (due to random initialization, floating-point rounding, etc.).
- **Small Models**: Based on rules or deterministic models, outputs are fully reproducible, facilitating log auditing.

### Testability
- **LLM**: Requires injecting real user traffic into a production environment for evaluation, leading to high testing costs and risks.
- **Small Models**: Can be covered by regular unit tests for various Unicode combinations and regex branches, achieving test coverage of over 90%.

### Attack Surface
- **LLM**: The model's internal logic can be triggered by crafted inputs to follow unexpected inference paths; attackers can manipulate decisions through clever inputs.
- **Small Models**: Regex or rule engines strictly filter inputs, making it difficult for attackers to influence final decisions.

### Cost
- **LLM**: Each inference requires calling an external LLM API, often billed per token, leading to significant cumulative costs.
- **Small Models**: A single inference has almost no cost, primarily involving CPU computation and memory usage, which is nearly negligible.

### Choosing fastembed over sentence-transformers
fastembed uses ONNX Runtime as its inference backend, **without relying on PyTorch**. After installation, it only occupies tens of MBs of space, whereas `sentence-transformers` requires TensorFlow/PyTorch and several GBs of model weights. More importantly, fastembed achieves inference speeds of 1–2 ms on a CPU, completely avoiding competition for GPU memory with LLMs. The deployment goal is to run both LLMs and small models on the same server, and fastembed's lightweight nature makes resource allocation clearer.

### Using only Unicode Heuristics for Language Identification
The current requirement is only to determine "if this text is Chinese," with no need to distinguish between fine-grained languages like English and French. Simple Unicode range matching can accomplish this task, avoiding the introduction of additional compilation dependencies. If future business needs require more granular language detection, the interface is already reserved, and a more complete model can be substituted when the need arises.

### 4. 🔬 Common Follow-up Questions

**Q: If the fallback implementation performs poorly, is it still meaningful to run evaluations with it in CI?**
Yes, but you need to distinguish what it's testing. Behaviors unrelated to the model's quality, such as rules, processes, and wiring, are tested just as accurately by the fallback backend. For use cases related to model quality, declare dependencies with `requires: ["semantic_embedder"]`, and they will be shown as skipped in a fallback environment—**skipping must be explicitly visible, not silently counted as passed.**

**Q: Any real pitfalls encountered?**
bge-small-**en** had almost no discriminative power for Chinese. When I plotted the similarity scores for each input in the evaluation set, benign Chinese sentences had similarity scores of 0.79–0.82 to "attack examples," mixing them with actual English attacks. The reason is simple: an English model perceives all Chinese text as similar. The fix wasn't adjusting thresholds, but **routing**:

```python
if cfg.get("scripts") and small_models.detect_script(text) not in cfg["scripts"]:
    return  # Route by language: this embedder hasn't learned this script
```

This is precisely the purpose of the language identification slot—the essence of combining small models isn't about "more," but about "who should be on stage."

**Q: How do you know which backend is actually being used in production?**
`GET /ops/status` calls `profile()`. The `profile` field in evaluation reports also uses this; baselines are stored separately by profile, so scores from the two backend sets are not compared against each other.

---

### 5. 🛠 Hands-on

1. For an existing project, identify three decisions that "don't actually require an LLM" and write a Protocol for each.
2. Implement a fallback for one of them, ensuring: no third-party dependencies, same input yields same output.
3. Add a capability flag (similar to `semantic`) and find a call site where it must be checked.
4. Intentionally misspell a model name, confirm the system degrades gracefully instead of crashing, and that the log level is a warning.
5. Change an embedder and observe if your index automatically recognizes the "need for rebuilding." If not, add the `id`.
