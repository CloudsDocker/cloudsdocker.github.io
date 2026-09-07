---
title: "[AI FDE Playbook 02] Never Use eval(): Building AST Sandboxed Execution for AI Agents"
episode: 2
series: "AI-FDE-Playbook"
language: "en-US"
duration: "4m 15s"
target_platform: "YouTube / Descript"
tags: ["AI Agent", "Python AST", "Security", "Sandbox", "Code Execution", "FDE"]
---

# Video Script: Never Use eval(): Building AST Sandboxed Execution for AI Agents

## Scene 1: The Hook (0:00 - 0:45)
**[Visual Cue]**
- Red alert accent lighting; code snippet on screen: `def calculate(expr): return eval(expr)`.
- Rapid demonstration of a prompt injection payload: `__import__('os').system('rm -rf /')` reading sensitive environment credentials.
- Terminal flashing red: Remote Code Execution (RCE) confirmed.

**[Audio / Voiceover Narration]**
"In countless quickstart tutorials, whenever an AI Agent needs to calculate a math formula, you see a naive one-liner: `eval(expression)`.
If you deploy this in an enterprise environment, your server is essentially an open door. Between indirect prompt injection and unvetted document context, an attacker only needs basic Python reflection syntax to bypass regular expression blacklists and compromise your infrastructure.
Today, we examine why keyword filtering fails, and how to build a zero-dependency, microsecond-latency AST execution sandbox using Python's native standard library."

---

## Scene 2: The Fallacy of Regex Blacklists (0:45 - 1:30)
**[Visual Cue]**
- Whiteboard graphic showing regex blacklist patterns: filtering `import`, `os`, `exec`, `__`.
- Animated bypass payload walking Python object hierarchies: `[c for c in ().__class__.__base__.__subclasses__()...]`.
- Bold stamp: "Blacklists Always Fail".

**[Audio / Voiceover Narration]**
"A common developer instinct is to add regex sanitizers: blocking keywords like `import`, `eval`, or double-underscores.
In dynamic interpreted languages, this is security theater. Attackers can traverse base classes and subclasses or construct strings dynamically to access builtins without ever typing a forbidden keyword.
The golden rule in security engineering: never rely on a denylist. You must enforce a strict, immutable allowlist."

---

## Scene 3: The AST Whitelist Solution (1:30 - 2:45)
**[Visual Cue]**
- Visual animated AST tree for expression `(100.5 + 45) / 2`.
- Green highlighted nodes: `ast.Expression`, `ast.BinOp`, `ast.Constant`.
- Red highlighted forbidden nodes: `ast.Call`, `ast.Attribute`, `ast.Name` — completely rejected.
- Screen recording of `src/solver/tools.py` showing `SafeMathVisitor`.

**[Audio / Voiceover Narration]**
"Here is the senior FDE pattern: parse expressions using Python's native `ast` module before execution.
The architecture is straightforward:
First, we parse the raw expression into an Abstract Syntax Tree using `ast.parse(expr, mode='eval')`.
Second, we implement a custom visitor that strictly permits four safe node types: `Expression`, `BinOp`, `UnaryOp`, and `Constant` numbers.
Third, any occurrence of `Call` (function invocations) or `Attribute` (attribute access) immediately raises a `SecurityException`.
Without function calls or variable resolution, code execution is mathematically impossible."

---

## Scene 4: Production Resiliency: Zero-Div, Overflow, Precision (2:45 - 3:30)
**[Visual Cue]**
- Test cases running: `1 / 0`, exponent runaway `9999 ** 9999`, float drift.
- Terminal showing clean handled exceptions returned to the agent loop without crashing the process.

**[Audio / Voiceover Narration]**
"Beyond security, production systems demand fault tolerance.
The sandbox cleanly intercepts `ZeroDivisionError` and caps exponent size, packaging mathematical failures into structured feedback for model self-correction.
Unlike heavyweight Docker execution containers, this AST sandbox requires zero external dependencies and executes in under 50 microseconds."

---

## Scene 5: Outro & Next Episode Teaser (3:30 - 4:15)
**[Visual Cue]**
- Screen showing `AI-FDE-Playbook` GitHub repository: `src/solver/tools.py`.
- Next episode teaser: 'From 30% to 85% Accuracy: Multi-turn Prompt Ablation & Calibration'.

**[Audio / Voiceover Narration]**
"Confining probabilistic outputs within deterministic, secure guardrails is the hallmark of senior AI engineering.
The complete AST sandbox implementation and test suite are available in our `AI-FDE-Playbook` repo.
In the next episode, we dive into prompt science: how rigorous ablation studies took our multi-turn financial reasoning from 30% to 85% accuracy.
Hit like, subscribe, and star the repo. See you next time!"
