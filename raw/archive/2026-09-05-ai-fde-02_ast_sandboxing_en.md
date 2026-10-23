# Building a Deterministic AST Sandbox: Why LLMs Suck at Math and How FDEs Fix It

Welcome to Part 2 of the `AI-FDE-Playbook` series. In Part 1, we forced the model to think using Schema-driven CoT. But if you build financial agents, you know the next nightmare: **LLMs are fundamentally unreliable at arithmetic.**

Throw in a few parentheses or financial accounting notations (like parentheses for negative losses), and even frontier models will hallucinate the math.

### ❌ The Amateur Fix: Python REPL Tools
Junior developers often just expose a raw Python execution tool to the LLM. This is a disaster in production:
1. **Security Vulnerabilities**: Prompt injections could lead the model to execute arbitrary code (e.g., `os.system`).
2. **Brittle Execution**: If the LLM passes a string like `"( $100 - $80 ) / 20%"`, a raw `eval()` crashes instantly because of the `$` and `%` characters.

### ✅ The FDE Fix: AST Sandboxed Execution

In the `AI-FDE-Playbook`, I implemented a hardened AST (Abstract Syntax Tree) sandbox tailored for financial QA. The design principles are:
1. **Pre-processing Sanitization**: Automatically strip `$` and convert `%` to `/100` before evaluation.
2. **AST Node Whitelisting**: Parse the expression with `ast.parse` and traverse only a strict whitelist of safe binary operations (`ast.Add`, `ast.Sub`). No arbitrary functions or attributes allowed.

```python
# Snippet from src/solver/tools.py
def safe_eval_expression(expr: str) -> float:
    # 1. Clean dirty financial strings
    expr = expr.replace("$", "").replace("%", "/100")
    
    # 2. Parse into AST
    node = ast.parse(expr, mode='eval').body
    
    # 3. Whitelisted evaluation
    return _eval_node(node)
```

**Error-as-Value Resilience**
Furthermore, never let tool exceptions crash your main Agent loop! When a tool fails, return the stack trace as a soft text string with a hint: `error: invalid syntax. Hint: Use '*' for multiplication, not 'x'`. Feed this string back into the LLM context so the model can self-correct on the next iteration.

This is how Senior AI Engineers build bulletproof architectures. Dive into the open-source implementation at [AI-FDE-Playbook](https://github.com/CloudsDocker/AI-FDE-Playbook)!
