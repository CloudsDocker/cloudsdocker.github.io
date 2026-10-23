---
title: 'Stop Patching, Start Parsing: Why Regex Is Not Enough for Security'
header:
    image: hd_google_map_no_reviews_huawai_2.jpg
date: 2026-10-23
tags:
 - llm
 - security
 - ast
 - python
 - ai-engineering
permalink: /blogs/tech/en/secure-ast-parsing-guide
lang: en
layout: single
category: tech
---
*How to build a hardened AST sandbox that handles messy financial notations without exposing your system to arbitrary code execution.*

`"($100 - $80) / 20%"`

If you pass this string to a standard Python `eval()` function, your application doesn't just give a wrong answer—it crashes. For a developer building financial agents, this is a recurring nightmare. LLMs are remarkably expressive, but they are fundamentally unreliable at arithmetic, especially when the input involves the non-standard characters typical of accounting, like parentheses for negative losses or currency symbols.

By the end of this section, you'll understand how to move beyond brittle `eval()` calls to a hardened AST-based execution model that handles real-world financial data safely.

When building these systems, the "amateur fix" is to simply expose a raw Python REPL to the LLM. It feels like the right path until it hits production. This approach introduces two critical failure modes:

1. **Security Vulnerabilities**: A raw execution tool is a massive surface for prompt injection. If an LLM (or a malicious user providing input to the LLM) can influence the string passed to `eval()`, they can execute arbitrary code—from `os.system` calls to exfiltrating environment variables.

2. **Brittle Execution**: Financial data is "dirty." An LLM might produce `"($100 - $80) / 20%"` because it's trying to be helpful with symbols. A standard Python interpreter will throw a `SyntaxError` immediately because of the `$` and `%` characters. You end up in a cycle of the agent trying the same broken string repeatedly, wasting tokens and stalling your pipeline.

The "FDE Fix" is to implement a hardened Abstract Syntax Tree (AST) sandbox. Instead of treating the input as a raw script, we treat it as a tree of operations. This allows us to intercept the logic before it ever touches the processor.


In the `AI-FDE-Playbook`, I implemented a hardened AST sandbox tailored for financial QA based on three core design principles:

- **Pre-processing Sanitization**: We automatically strip currency symbols and normalize percentages (e.g., converting `%` to `/100`) before the expression ever reaches the parser. This aligns the LLM's "expressive" output with the "strict" requirements of the interpreter.
- **AST Node Whitelisting**: We use `ast.parse` to convert the string into a tree. We then traverse this tree and only allow a strict whitelist of safe binary operations, such as `ast.Add` and `ast.Sub`. This prevents the LLM from calling any functions, accessing attributes, or importing modules.

```python
# Snippet from src/solver/tools.py
import ast

def safe_eval_expression(expr: str) -> float:
    # 1. Clean dirty financial strings
    # We handle the 'expressive' symbols LLMs favor but Python hates.
    expr = expr.replace("$", "").replace("%", "/100")
    
    # 2. Parse into AST
    # mode='eval' ensures we are looking at an expression, not a statement.
    node = ast.parse(expr, mode='eval').body
    
    # 3. Whitelisted evaluation
    # This is where we enforce the security boundary by recursively
    # evaluating only permitted nodes.
    return _eval_node(node)

# Internal helper to recursively visit whitelisted nodes
def _eval_node(node):
    if isinstance(node, ast.Num):  # Use ast.Constant in newer Python versions
        return node.n
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Add): return left + right
        if isinstance(node.op, ast.Sub): return left - right
        if isinstance(node.op, ast.Mult): return left * right
        if isinstance(node.op, ast.Div): return left / right
    raise ValueError("Operation not permitted")
```

**Error-as-Value Resilience**

One of the most important nuances for AI engineers is treating errors as values rather than exceptions. You must never let a tool exception crash your main Agent loop. If the sandbox catches a syntax error or a forbidden operation, don't just throw an exception. Instead, return the stack trace as a soft text string with a hint: `error: invalid syntax. Hint: Use '*' for multiplication, not 'x'`. 

By feeding this string back into the LLM context, you transform a hard failure into a feedback loop. The model sees the specific reason it failed and can self-correct on the next iteration. This is how you build bulletproof, production-grade architectures.

*Honest Limit*: While AST parsing is significantly safer than `eval()`, it introduces a slight performance overhead and requires a more complex mapping of natural language to valid expressions. It is not a silver bullet for all math, but it is the standard for secure execution.\n
Dive into the open-source implementation at [AI-FDE-Playbook](https://github.com/CloudsDocker/AI-FDE-Playbook)!
