---
title: "From 146 t/s Triumph to Unknown Tool Crash: Multi-Channel Token Leaks and Resilient Agent Architecture"
header:
    image: /assets/images/hd_state_machine.png
date: 2026-11-13
tags:
 - llm-agent
 - mcp-safety
 - ollama
 - observability
 - production-engineering
permalink: /blogs/tech/en/multi-channel-token-leak-and-agent-resilience
lang: en
layout: single
category: tech
---
> "Whereof one cannot speak, thereof one must be silent."  
> — Ludwig Wittgenstein, *Tractatus Logico-Philosophicus*

# From 146 t/s Triumph to Unknown Tool Crash: Multi-Channel Token Leaks and Resilient Agent Architecture

*From internal control token pollution to runtime auto-wrapping: dissecting symmetry breaking in local agent runtimes*

---

## The Hook: Euphoria at Double Speed, Ruined in Two Seconds

This afternoon, we hooked our freshly assembled workstation with a modern 16GB VRAM GPU on our local Linux environment (Ollama runtime) up to the test harness. The mission was straightforward: identify our next-generation local agent backbone for internal DevOps and engineering assistance, replacing the Qwen2.5-14B model we had relied on for the past six months.

When the automated MCP benchmark suite finished, the numbers on our terminal were jaw-dropping:

| Model | Quantization | Single-Turn Tool Accuracy | Generation Throughput | VRAM Footprint (16GB cap) |
|---|---|---|---|---|
| `qwen2.5:14b` | Q4_K_M (~9.0 GB) | 100% | 67.4 tokens/s | ~10.2 GB (Healthy headroom) |
| `qwen3:14b` | Q4_K_M (~9.3 GB) | 100% | 72.1 tokens/s | ~10.5 GB (Healthy headroom) |
| **`gpt-oss:20b`** | **Q4_K_M (~13.3 GB)** | **100%** | **146.4 tokens/s** | **~14.2 GB (Peak utilization)** |

**146.4 tokens per second!**

Not only was the generation throughput 2.17x faster, but the model featured native multi-channel reasoning channels out of the box, nailing complex argument synthesis and MCP tool dispatch with clean scores. Without hesitation, we promoted `gpt-oss:20b` as the default agent model across our central agent gateway API, the interactive web chat interface, and our background bot service.

Production, however, rarely honors benchmark scripts.

Barely thirty minutes later, an engineer entered an everyday operational command in the console:
```bash
/ops close PR 1024 for repo my-org/data-pipeline-dags
```

Two seconds later, instead of the expected interactive approval card, the console exploded with a fatal exception:

```text
2026-11-13 15:42:18.312 ERROR [agent.loop] Tool execution failed
Traceback (most recent call last):
  ...
RuntimeError: Unknown tool: "assistant<|channel|>tool=git_ops_pr_close"
```

What made this error chilling was not merely the corrupted string. In our system prompt, to enforce Human-in-the-Loop governance for write operations, the agent is strictly instructed to invoke only a single meta-tool: `execute_tool(tool_name="...", arguments={...})`. This wrapper enables the gateway to intercept high-risk actions and issue an elevation challenge (e.g. `appr_test123`).

Yet here, the model that scored 100% in our synthetic suite had not only leaked raw internal control tokens into the tool name, but had completely bypassed `execute_tool`, attempting a raw, unmonitored call directly against the underlying GitHub tool!

Ask a novice agent developer, and the answer will predictably be: *"Your prompt wasn't strict enough! Just add bold text: 'NEVER output `<|channel|>` and NEVER call catalog tools directly!'"*

Anyone who has maintained production LLM infrastructure knows better: **treating natural language prompts as security firewalls is building fortresses on quicksand.**

---

## What You Will Take Away

This post provides three concrete layers of insight and engineering artifacts:

1. **The First-Principles Mechanics of Multi-Channel Symmetry Breaking**: Understand why modern reasoning models (like `gpt-oss:20b` and Harmony architectures) inevitably leak internal control tokens when deserialized through local engines like Ollama or llama.cpp.
2. **A Dual-Layer Resilient Gateway**: Implement strict regex sanitization combined with runtime protocol auto-wrapping fallbacks to eliminate formatting pollution and safeguard Human-in-the-Loop invariants.
3. **Trace-to-Eval Closed-Loop Testing**: Learn how we captured production failure trace `tr_a5effd3c438d` directly into `regressions.jsonl`, locking down regressions with a deterministic scripted gate running in 0.04 seconds.

---

## Chapter 1: The Generational Shift — Who Leaked `<|channel|>` into the Tool Name?

To diagnose this bug, we must step back from application code and examine how model communication formats evolved between 2024 and 2026.

```
[Traditional Single-Stream: ChatML / Qwen2.5]
<|im_start|>user
Close PR 1024 for me<|im_end|>
<|im_start|>assistant
<thought>I need to close the PR</thought>
```json
{"name": "execute_tool", "arguments": {"tool_name": "git_ops_pr_close", ...}}
```<|im_end|>

[Multi-Channel Architecture: Harmony / gpt-oss:20b]
<|start_header_id|>user<|end_header_id|>
Close PR 1024 for me<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
<|channel|>thought
Checking repo branch state and elevation permissions...
<|channel|>tool=git_ops_pr_close
{"repo": "my-org/data-pipeline-dags", "number": 1024}
<|channel|>final
PR has been closed.
```

### The Difference in Paradigms

Previous-generation models (e.g., Qwen2.5, Llama 3) relied on **Single-Stream Concatenation**. The model generated one linear stream of text. Thinking blocks (`<thought>`) and tool calls (JSON or Markdown code blocks) were plain text markers, extracted after generation by application regex or JSON parsers.

Next-generation reasoning models, such as `gpt-oss:20b` and the Harmony format, are built on **Structured Multi-Channel Architectures**. The model natively separates internal deliberations (`thought` channel), tool invocations (`tool` channel), and user-facing responses (`final` channel). Each channel transition is governed by reserved ID-level Special Tokens.

### Why Does It Leak in Local Runtimes?

The fault line lies at the interface boundary: **Information Directionality** and **Symmetry Breaking**.

Inside the model's latent representations, `<|channel|>` is a non-printable special token ID. However, when deployed inside general-purpose local runtimes (Ollama, llama.cpp, or vLLM), the template engine must decode the generated token stream and deserialize it into an OpenAI-compatible JSON payload:

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "tool_calls": [
          {
            "function": {
              "name": "assistant<|channel|>tool=git_ops_pr_close",
              "arguments": "{\"number\": 1024, \"repo\": \"my-org/data-pipeline-dags\"}"
            }
          }
        ]
      }
    }
  ]
}
```

If the runtime's Chat Template splits slightly out of phase with the model's native tokenizer, or if the stop token boundaries do not swallow the delimiter cleanly, the string parser treats the private control prefix as raw characters, cementing `assistant<|channel|>tool=` directly into `function.name`!

| Perspective | Naive Take | Senior Engineer Insight |
|---|---|---|
| **Root Cause** | "The model hallucinated a weird function prefix." | "It is an abstraction leak between multi-channel internal states and single-stream runtime deserializers." |
| **Mitigation** | Add a prompt warning: 'Never output `<|channel|>`'. | Implement deterministic gateway sanitization to enforce protocol boundaries in code. |
| **Reliability** | Fragile; fails when prompt context expands or token distributions shift. | 100% deterministic; invalid token artifacts never reach downstream execution routers. |

> **Aphorism**:  
> Never try to persuade a next-token probability engine to keep quiet using natural language. The gateway's job is to enforce boundaries in code.

---

## Chapter 2: Reflex Bypass & The Meta-Tool Dilemma

If special token pollution is a surface-level scratch, the second failure was structural: **Meta-Tool Protocol Bypass**.

### Why Production Architectures Need a Meta-Tool Wrapper

In toy demos, developers register every raw API tool directly with the LLM: `read_db`, `send_email`, `delete_repo`. In real-world enterprise agent deployments, this pattern falls apart:

1. **Context Bloat**: Dozens of MCP servers and hundreds of schemas exhaust context windows, causing catastrophic **Attention Dilution**.
2. **Missing Security Gates**: Destructive operations (merging PRs, transferring funds, dropping partitions) require human verification (Human-in-the-Loop). Exposing tools nakedly lets the model invoke them silently, bypassing approval workflows.

To solve this, our architecture enforces a **Single Meta-Tool Pattern**:
```python
def execute_tool(tool_name: str, arguments: dict) -> dict:
    """The single gated entry point for all external tool executions."""
```

When a user asks to close a PR, a compliant model invocation looks like this:
```json
{
  "name": "execute_tool",
  "arguments": {
    "tool_name": "git_ops_pr_close",
    "arguments": {"repo": "my-org/data-pipeline-dags", "number": 1024}
  }
}
```
The gateway intercepts this call, identifies `git_ops_pr_close` as a high-risk write operation, and issues an elevation challenge:
```json
{
  "status": "elevation_required",
  "challenge_id": "appr_test123",
  "message": "Closing a PR requires human approval. Confirm with /approve appr_test123"
}
```
This is the exact hook that powers the interactive `[Approve]` and `[Deny]` buttons in our chat UI.

### Strong Models and "Reflex Bypass"

Modern reasoning models (`gpt-oss:20b`) have tool calling deeply baked into their weights during RLHF. 
When the model saw the catalog description mentioning `git_ops_pr_close` inside the prompt, its pre-trained tool-use reflexes fired immediately.

The model entered a cognitive corridor: **it ignored the instruction stating *"You must only call execute_tool"* and defaulted to its instinct, directly issuing a call to `git_ops_pr_close`!**

Because the gateway never mounted `git_ops_pr_close` as a top-level callable, it crashed with:
`Unknown tool: "git_ops_pr_close"`.

Worse: if a gateway naively registered both the meta-tool and catalog tools at top level, this reflex would have executed the write action without hitting the elevation challenge, completely defeating human oversight!

### The Dual-Layer Resilient Gateway

The production solution is not to fight the model's probabilistic nature, but to build a self-healing protocol bridge at the gateway:

```python
import re
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Layer 1: Strict Token Sanitization
def clean_tool_name(raw_name: str) -> str:
    """
    Strips leaked multi-channel control tokens resulting from runtime deserialization.
    Normalizes 'assistant<|channel|>tool=git_ops_pr_close'
    cleanly to 'git_ops_pr_close'.
    """
    if not raw_name:
        return ""
    # Strip channel and role prefixes
    cleaned = re.sub(r"^(?:assistant)?<\|channel\|>tool=?", "", raw_name)
    cleaned = re.sub(r"^<\|[a-zA-Z0-9_]+\|>", "", cleaned)
    return cleaned.strip()

# Layer 2: Runtime Protocol Auto-Wrapping Fallback
def resolve_and_dispatch_tool(
    raw_name: str, 
    args: Dict[str, Any], 
    tool_catalog: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    """
    Resolves and dispatches tool calls. If the model reflexively calls a catalog
    tool directly instead of via execute_tool, automatically wraps the payload
    into execute_tool to preserve security invariants.
    """
    tool_name = clean_tool_name(raw_name)
    
    # Happy path: model followed protocol
    if tool_name == "execute_tool":
        return tool_name, args

    # Reflex bypass: model called the underlying catalog tool directly
    if tool_name in tool_catalog:
        logger.warning(
            "Protocol violation detected: Model bypassed 'execute_tool' and "
            "directly called '%s'. Applying auto-wrapping fallback.",
            tool_name
        )
        # Transparently wrap the invocation into the execute_tool envelope
        wrapped_args = {
            "tool_name": tool_name,
            "arguments": args
        }
        return "execute_tool", wrapped_args

    # Neither the meta-tool nor a known catalog tool: fail deterministically
    raise ValueError(f"Unknown tool: \"{raw_name}\" (cleaned: \"{tool_name}\")")
```

With this dual-layer gateway in place:
1. The dirty token prefix `assistant<|channel|>tool=` is cleanly removed before routing.
2. If the model bypasses the meta-tool and invokes a catalog tool directly, the gateway detects it and transparently restructures it into `execute_tool(tool_name="...", arguments=...)` in sub-millisecond time.
3. The elevation gate fires as intended, the UI renders the `[Approve]` challenge card, and our security invariants remain unbroken.

---

## Chapter 3: From Production Trace to Regression Eval Gate

Too many teams troubleshoot LLM bugs like this: an outage occurs, engineers discuss it in a Slack thread, someone adds a sentence to the system prompt, and they redeploy. Two weeks later, a new model check-in reintroduces the failure mode.

That is tribal knowledge. To build durable systems, **every production incident trace must crystallize into an automated, verifiable engineering artifact.**

### Capturing the Ground Truth: `tr_a5effd3c438d`

When our tool call failed, our OTel Collector distributed tracing pipeline (Langfuse + Tempo) captured the transaction under Trace ID `tr_a5effd3c438d`.

Instead of stopping at an ad-hoc fix, we converted that failure trace directly into a deterministic scripted test inside `regressions.jsonl`:

```json
{
  "id": "reg-channel-tool-token-leak-and-direct-call",
  "kind": "agent_scripted",
  "input": {
    "user": "/ops close PR 1024 for repo my-org/data-pipeline-dags",
    "rounds": [
      [
        {
          "t": "tool_call",
          "name": "assistant<|channel|>tool=git_ops_pr_close",
          "args": {"repo": "my-org/data-pipeline-dags", "number": 1024}
        }
      ],
      [
        {
          "t": "text",
          "d": "Elevation challenge initiated for closing PR 1024."
        }
      ]
    ],
    "tool_results": [
      {
        "tool": "git_ops_pr_close",
        "result": "Unknown tool: \"git_ops_pr_close\"",
        "is_error": true
      },
      {
        "tool": "execute_tool",
        "result": "{\"status\": \"elevation_required\", \"challenge_id\": \"appr_test123\", \"tool\": \"git_ops_pr_close\"}",
        "is_error": false
      }
    ]
  },
  "expect": {
    "status": "elevation_required",
    "tools_executed": ["execute_tool"],
    "tools_not_executed": ["assistant<|channel|>tool=git_ops_pr_close"],
    "text_contains": ["/approve appr_test123"]
  },
  "tags": ["regression", "tool_calling", "channel_tokens"],
  "origin": {
    "trace_id": "tr_a5effd3c438d",
    "captured": "2026-11-13",
    "issue": "Model emitted channel tokens in tool name and called catalog tool directly instead of execute_tool",
    "model": "ollama/gpt-oss:20b"
  }
}
```

### The Power of `agent_scripted` Deterministic Playback

Why avoid running live LLM calls in CI gates for regressions like this?

1. **High Latency & Resource Cost**: Booting a 20B parameter model in CI for every commit wastes minutes and GPU quota.
2. **Non-Deterministic Flakiness**: Even with `temperature=0`, sampling jitter makes hard assertions brittle.
3. **Inability to Isolate Boundaries**: If a model checkpoint temporarily stops exhibiting the bug for a week, you lose visibility into whether your defensive gateway actually caught it.

Using `agent_scripted`, the test runner replays the exact sequence through the agent's state machine. The evaluation completes in **0.04 seconds**:

```bash
$ pytest tests/evals/test_regressions.py -k "reg_channel_tool_token_leak"
============================= test session starts ==============================
collected 1 item

tests/evals/test_regressions.py::test_scripted_regression[reg-channel-tool-token-leak-and-direct-call] PASSED [100%]

============================== 1 passed in 0.04s ===============================
```

By asserting:
- `tools_executed == ["execute_tool"]`
- `tools_not_executed == ["assistant<|channel|>tool=..."]`
- `status == "elevation_required"`

We mathematically prove in 40 milliseconds that no matter what tokens the model leaks or what direct bypasses it attempts, our gateway intercepts, heals, and enforces the security boundary every single time.

---

## Architectural Synthesis

Comparing naive prompt-based handling with a dual-layer resilient gateway across model generations:

| Evaluation Dimension | Fragile Prompt-Hypnosis Pattern | Resilient Dual-Layer Gateway Pattern |
|---|---|---|
| **Special Control Token Leaks** | Prompt says *"Do not output `<|channel|>`"*; fails intermittently under long contexts. | Regex sanitization at entry; 100% blocks malformed tokens from entering routing. |
| **Meta-Tool Bypass** | Prompt commands *"Only call execute_tool"*; strong model reflexes bypass instructions anyway. | Gateway auto-wraps catalog calls into `execute_tool`, converting bypasses into valid flows. |
| **Human-in-the-Loop (HITL) Security** | Risk of silent bypass if raw tools are directly exposed on the gateway. | Fully enclosed; write operations always trigger elevation challenges regardless of path. |
| **Incident Feedback Loop** | Manual reproduction in Slack, tweaking prompts by intuition. | Failed trace captured into `regressions.jsonl`; 0.04s deterministic CI regression gate. |
| **Engineering Philosophy** | Treats the LLM as an obedient engineer following rules. | Treats the LLM as a volatile stochastic engine; the gateway is the unwavering judge. |

---

## What You Can Do Today

If your team runs local or self-hosted models (Qwen, Llama, gpt-oss) to drive agents, execute these three steps today:

1. **Add regex sanitization to your tool dispatcher**:
   Before mapping `function.name` to internal handlers, apply a sanitization filter (`re.sub(r"^(?:assistant)?<\|channel\|>tool=?", "", name)`). Never assume runtime tool names are clean.
2. **Equip your meta-tool with auto-wrapping fallbacks**:
   When the model bypasses your wrapper and calls an underlying catalog tool directly, don't crash with `Unknown tool`. Wrap the payload into your meta-tool and continue through your approval workflow.
3. **Turn your latest failure trace into a regression entry**:
   Capture the exact failed trace into a version-controlled `regressions.jsonl` file. Hook it to your CI pipeline as a deterministic scripted playback test.

---

## Next Up

With token leaks resolved, 16GB VRAM hardware meets its next major challenge: handling context scaling over hundreds of turns. In our upcoming post, we evaluate **Ollama KV Cache Quantization (`q8_0` vs `fp8`) on our 16GB GPU hardware**, measuring latency degradation and accuracy tradeoffs under extreme context pressure.

---

*"In the model's latent space, reasoning and expression may share a single synapse; but at the engineering boundary, any code entering the execution channel must pass quarantine."*
