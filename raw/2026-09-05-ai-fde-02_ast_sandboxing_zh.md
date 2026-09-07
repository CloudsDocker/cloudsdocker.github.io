# AST 沙盒执行器：为什么大模型一算账就疯？前线部署工程师（FDE）的终极解法

欢迎来到 `AI-FDE-Playbook` 系列博客的第二部分。在上一篇中，我们解决了模型“不会思考”的问题（强制 Schema CoT）。但如果你做过金融领域的 Agent，你一定遇到过另一个噩梦：**大模型（LLM）的算术能力极其不靠谱**。

加减乘除稍微多几个括号，或者遇到财报里经常出现的“（损失）”负数标识，即使是 GPT-4 级别的大模型也会开始胡编乱造（幻觉）。

### ❌ 玩具级解法：给模型一个 Python REPL
很多初级开发者会给大模型直接挂一个 Python 执行环境。但这在生产环境绝对是灾难：
1. **安全性危机**：模型可能会生成恶意的 Python 代码（`os.system("rm -rf /")`）。
2. **容错率极低**：如果模型输入了带有金融符号的字符串（比如 `"$100"` 或者 `"20%"`），Python `eval()` 会直接报错崩溃。

### ✅ 工业级解法：AST（抽象语法树）沙盒工具

在 `AI-FDE-Playbook` 中，我实现了一个专门用于金融数值计算的 AST 沙盒 `safe_eval_expression`。它的核心思路是：
1. **词法级清洗**：在执行前，用正则自动剥离掉模型经常不小心带入的 `$` 符号，并将 `%` 替换为 `/100`。
2. **AST 节点白名单**：通过 `ast.parse` 解析表达式，并限制只能使用安全的节点类型（如 `ast.Add`, `ast.Sub`, `ast.BinOp`），彻底杜绝了模型执行任意代码的可能。

```python
# src/solver/tools.py 核心逻辑片段
def safe_eval_expression(expr: str) -> float:
    # 1. 前置清洗：把金融符号处理掉
    expr = expr.replace("$", "").replace("%", "/100")
    
    # 2. 解析 AST 树
    node = ast.parse(expr, mode='eval').body
    
    # 3. 严格受限的 AST 节点遍历与求值
    return _eval_node(node)
```

**工具层兜底（Error-as-value）**
不仅如此，当计算出错时，千万不要让异常（Exception）抛给主线程导致 Agent 挂掉。在我们的架构中，所有的工具调用失败都会返回一句带有 `Hint` 的文本（比如：`error: invalid syntax. Hint: Use '*' for multiplication, not 'x'`）。把错误当成字符串重新喂给模型，让大模型在下一个 Turn 自己反思并修正语法！

这就是 Senior AI 架构师构建高健壮性 Agent 的底气所在。源码已经开源在 [AI-FDE-Playbook](https://github.com/CloudsDocker/AI-FDE-Playbook) 中，欢迎自取！
