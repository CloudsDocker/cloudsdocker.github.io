---
title: "[AI FDE Playbook 01] Why Structured Output Can Break LLM Reasoning: The Scratchpad Fix"
episode: 1
series: "AI-FDE-Playbook"
language: "en-US"
duration: "4m 30s"
target_platform: "YouTube / Descript"
tags: ["LLM", "Structured Output", "OpenAI", "Prompt Engineering", "FDE", "Pydantic"]
---

# Video Script: Why Structured Output Can Break LLM Reasoning: The Scratchpad Fix

## Scene 1: The Hook (0:00 - 0:45)
**[Visual Cue]**
- Close-up on speaker; clean dark-mode developer workstation background.
- Floating graphic on right: OpenAI Structured Outputs JSON schema next to a red evaluation error badge (ConvFinQA multi-turn accuracy plummeting to 38%).
- Subtle alert sound effect transitioning into upbeat tech background music.

**[Audio / Voiceover Narration]**
"Many engineers assume that forcing an LLM into JSON mode or Structured Outputs is the gold standard for production agents. It enforces schemas and keeps backend parsers happy.
But have you ever watched your model suddenly fail basic multi-step math the moment you turned on structured outputs without a chain-of-thought field? In financial multi-turn benchmarks, accuracy can drop from over 80% to under 40%.
Why does a standard engineering best practice actually sabotage model reasoning? Today, we are breaking down the mechanics of this 'Structured Output Blindspot' and demonstrating the production fix used by senior AI Forward-Deployed Engineers."

---

## Scene 2: The Core Problem: Autoregressive Token Mechanics (0:45 - 1:45)
**[Visual Cue]**
- 2D animation showing autoregressive token-by-token generation timeline.
- Side-by-side comparison:
  - Flawed: `{"answer": 14.5}` — Zero compute tokens between prompt and number!
  - Fixed: `{"scratchpad": "Turn 1 net income was $100M, Turn 2 revenue was $500M...", "answer": 0.20}`
- On-screen bold typography: "Tokens are computation time."

**[Audio / Voiceover Narration]**
"The failure boils down to autoregressive token mechanics. In LLMs, generated tokens are not just outputs—they are working memory and execution time.
When you force a model to emit curly-bracket, quote, answer, colon, number, the model has to produce the final numerical value in a single forward pass without intermediate computation steps. It is the equivalent of demanding a human calculate multi-variable compound interest instantaneously without scrap paper.
The solution? We must architect the thinking process directly into the JSON schema."

---

## Scene 3: The Architecture: Schema-Engineered Scratchpads (1:45 - 2:45)
**[Visual Cue]**
- Screen recording: VS Code editor showing `src/solver/cot.py` with Pydantic v2 schemas.
- Cursor highlights `scratchpad: str` field placed strictly ahead of `result` or tool calls.
- Architecture diagram: Input Context -> Scratchpad Reasoning -> Deterministic Sandbox Execution -> Output Validation.

**[Audio / Voiceover Narration]**
"Here is the battle-tested pattern. We define a Pydantic schema with an explicit `scratchpad` field:
First, field ordering is critical: the `scratchpad` field MUST appear before any numerical payload. The autoregressive decoder is forced to generate 50 to 150 reasoning tokens, clarifying references from prior conversation turns and reconciling units like millions versus thousands.
Second, the model only produces the algebraic expression, not the final arithmetic calculation, delegating exact math to an isolated execution sandbox.
By forcing reasoning tokens into the schema ahead of the result, accuracy immediately rebounds above the baseline."

---

## Scene 4: Production Guardrails & Benchmarking (2:45 - 3:45)
**[Visual Cue]**
- Terminal session: running `uv run python -m src.main --solver cot --samples 50`.
- Rich CLI tables formatting turn-by-turn evaluations, tracking strict vs scale-tolerant accuracy metrics.
- Animated chart illustrating turn-by-turn error cascade prevention.

**[Audio / Voiceover Narration]**
"In enterprise deployment, two additional guardrails are non-negotiable:
First, unit alignment—handling percentage representations such as 100x multiples versus decimals with deterministic normalization.
Second, programmatic self-healing: if an output violates strict Pydantic parsing, pass the validation error directly back to the model for a single-step self-correction rather than letting the agent crash."

---

## Scene 5: Outro & Open Source Call to Action (3:45 - 4:30)
**[Visual Cue]**
- Camera returns to host; screen displays the GitHub repo `AI-FDE-Playbook`.
- Animated overlay highlighting Star button and repo URL.
- End-screen preview card: Next episode on 'Never Use eval(): AST Sandboxing for AI Agents'.

**[Audio / Voiceover Narration]**
"This is the core mindset of a senior AI Forward-Deployed Engineer: don't treat models as black-box magic. Build deterministic architectural guardrails around probabilistic systems.
All code, full Pydantic schemas, and the benchmark testbed are open-sourced in our `AI-FDE-Playbook` repository linked below.
In episode two, we will tackle security: why you should never use `eval()`, and how to build a zero-dependency AST sandboxed calculator.
Drop a like, subscribe, and star the repo. See you in the next deep dive!"
