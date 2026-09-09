---
title: 薄执行层，厚安全能力：我们如何为 AI 工作流构建 AST 沙箱
header:
    image: /assets/images/hd_aws_certificat.png
date: 2026-09-08
tags:
 - ai-agents
 - python
 - ast
 - security
 - reliability
permalink: /blogs/tech/zh/ast-sandbox-ai-workflows
layout: single
category: tech
---
> “我们知道我们是什么，但不知道我们可能成为什么。” — 威廉·莎士比亚

# 薄执行层，厚安全能力：我们如何为 AI 工作流构建 AST 沙箱

*当模型负责推理、工具负责确定性计算时，真正需要隔离的不是“算术”，而是执行权。*

## 🎯 周二下午的一道账

周二 14:17，林岚在排查一个金融分析工作流的结果。模型刚刚读完一段财务文本，接着需要计算一个看起来毫不起眼的表达式：带括号、带百分比，还夹着报表里常见的“（损失）”式负数标记。

14:18，周闻提出了一个合理建议：给模型接一个 Python REPL。模型不会算，就让 Python 算。毕竟，加减乘除是程序最擅长的事。

14:19，顾言摇头。不是因为 Python 算得不对，而是因为这个方案把两件性质完全不同的事绑在了一起：**让模型表达计算意图**，和**让模型获得通用代码执行权**。

后者的风险远大于前者。

这类冲突很容易变成一场无意义的争论：一边嫌模型连算术都做不好，一边嫌安全限制妨碍交付。更糟的是，结果不稳定会让人怀疑模型“开始胡编乱造”，排查半天才发现，问题根本不在推理，而在工具接口。

**没有人做错。周闻是在追求确定性，顾言是在守住执行边界。真正缺失的是一个共同的心智模型：计算不等于代码执行。**

在前一篇关于受约束推理输出的讨论之后，这里是另一个常见的 Agent 生产问题：即使模型可以按结构输出步骤，遇到多层括号、百分比、货币符号或财务文本中的负数表示，纯靠模型完成算术仍然不可靠。此时需要的不是更长的提示词，而是一个小而严格的计算工具。

> 📌 **本节要点**：模型的算术不稳定，不能靠“允许它执行任何代码”来补。冲突的根源不是谁更谨慎，而是把有限计算和通用执行混为了一谈。

## 🧠 30 秒版本：别给计算器装上一台挖掘机

模型需要的是“算这道式子”的能力，不是“运行一段 Python 程序”的能力。

| 方案 | 模型拿到的能力 | 能处理金融格式 | 安全边界 | 相对成本 |
|---|---|---:|---|---|
| 让模型心算 | 生成自然语言中的计算结果 | 勉强 | 无额外执行风险，但结果不确定 | 低实现成本，高校验成本 |
| Python REPL / `eval()` | 通用 Python 执行 | 需自行清洗 | 极宽，可能触及文件、进程、网络等能力 | 初期低，长期风险高 |
| AST 算术沙箱 | 仅允许定义好的数学表达式 | 可在入口规范化 | 窄，只接受白名单语法 | 中等实现成本，低运行风险 |

最反直觉的地方在这里：**AST 沙箱并不是“更安全的 `eval()`”；它的目标是根本不调用 `eval()`。**

它先把表达式解析为抽象语法树（AST），再只解释自己明确允许的节点。模型即使写出了函数调用、属性访问、列表、索引或导入语句，也没有机会进入执行阶段。

> 📌 **本节要点**：当需求只是四则运算时，通用执行环境是一种能力过剩。能力越多，验证边界越大，生产成本也越高。

## 🏗️ 心智模型：把模型当成填单员，不是持钥匙的维修工

可以把整个流程想成银行柜台。

林岚需要的是把一张计算单送进窗口：`(100 - 20) * 15%`。柜员要做的事情是识别金额、百分比和运算符，然后把结果交回来。

如果把 Python REPL 暴露给模型，相当于柜员不仅能处理这张单，还拿到了金库钥匙、工具间钥匙，以及一张写着“需要什么自己找”的通行证。大多数时候什么都不会发生；问题在于，一次格式异常、一次意外生成，或者一次提示注入，就可能让“算一道题”越过本不该跨越的边界。

AST 沙箱则像一台专用计算器：

- 它认识数字、括号和少量运算符；
- 它可以把 `$100` 这类展示格式还原为数值；
- 它能把 `20%` 解释为 `20/100`；
- 它不认识文件、网络、导入、对象属性和函数调用；
- 它遇到不认识的东西，会拒绝，而不是猜。

报表中的“（损失）”式负数是一个很好的边界案例。它不能被算术解释器悄悄猜成普通括号，因为普通括号本身又是分组语法。若产品需要这种格式，应在进入表达式语言前，由有明确规则的上游提取器转换为 `-123`；不能让一个看似便利的替换规则擅自改变表达式含义。

回看周二下午，周闻真正想要的是确定性；顾言真正担心的是授权范围。专用计算器同时满足了两人：结果由确定的程序给出，模型却始终拿不到通用运行时。

> 📌 **本节要点**：把工具设计成“填一张单、办一件事”，而不是“给一串代码、什么都能干”。专用能力的价值，正在于它拒绝无关能力。

## 🛠️ 机制：从脏表达式到受限求值

原始思路可以概括为三步：先处理模型容易混入的金融符号；再用 `ast.parse(..., mode='eval')` 解析表达式；最后遍历白名单节点并计算结果。

```mermaid
flowchart LR
    A[模型输出表达式] --> B[输入长度与字符检查]
    B --> C[金融格式规范化<br/>$ 删除，20% 转为 (20/100)]
    C --> D[ast.parse mode=eval]
    D --> E{节点是否在白名单?}
    E -->|是| F[递归解释并校验<br/>实数、有限值与幂域]
    E -->|否| G[返回 error + Hint]
    F --> H[返回数值结果]
    D -->|语法错误| G
```

这里有一个需要说清的技术细节。下面这个核心片段表达了原始设计的方向：

```python
def safe_eval_expression(expr: str) -> float:
    # 1. 前置清洗：把金融符号处理掉
    expr = expr.replace("$", "").replace("%", "/100")

    # 2. 解析 AST 树
    node = ast.parse(expr, mode="eval").body

    # 3. 严格受限的 AST 节点遍历与求值
    return _eval_node(node)
```

方向对，但不能直接把这段简化代码原样带进生产。朴素的 `replace("%", "/100")` 会把 `20%` 变成 `20/100`，却不会自动补上必要的分组；更复杂的表达式可能因为运算优先级而得到错误含义。它也没有处理异常、输入长度、数值类型和资源消耗。

下面是一种更完整的实现。它支持数值常量、括号、一元正负号、`+`、`-`、`*`、`/`、`**`，以及紧随数值或右括号的百分号。它明确不支持变量、函数、比较、布尔值、列表、属性访问和下标。

这里的三个上限是**示例配置占位符，不是通用的生产安全线**。`_MAX_EXPRESSION_LENGTH`、`_MAX_AST_NODES` 和 `_MAX_ABS_EXPONENT` 必须由运行方根据自己的延迟预算、内存预算、允许的数值范围和真实工作负载设定，并用压测与回归测试验证。没有一组脱离上下文的数字，可以替你完成资源治理。

```python
import ast
import math
import numbers
import operator
import re

# 示例配置占位符：请按自己的延迟、内存和数值范围预算设定并测试。
_MAX_EXPRESSION_LENGTH = 1_000
_MAX_AST_NODES = 100
_MAX_ABS_EXPONENT = 100

_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}

_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_NUMBER_AT_END = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


def _normalize_financial_expression(expr: str) -> str:
    """将有限的展示格式转换为可解析的算术表达式。"""
    source = expr.strip().replace("$", "")
    output: list[str] = []

    for char in source:
        if char != "%":
            output.append(char)
            continue

        prefix = "".join(output).rstrip()
        if not prefix:
            raise ValueError("percent must follow a number or closing parenthesis")

        if prefix[-1] == ")":
            depth = 0
            start = None
            for index in range(len(prefix) - 1, -1, -1):
                if prefix[index] == ")":
                    depth += 1
                elif prefix[index] == "(":
                    depth -= 1
                    if depth == 0:
                        start = index
                        break
            if start is None:
                raise ValueError("unmatched closing parenthesis before percent")
            atom = prefix[start:]
            output = list(prefix[:start] + f"({atom}/100)")
            continue

        match = _NUMBER_AT_END.search(prefix)
        if match is None:
            raise ValueError("percent must follow a number or closing parenthesis")
        atom = match.group(0)
        output = list(prefix[:match.start()] + f"({atom}/100)")

    return "".join(output)


def _finite_float(value: object) -> float:
    """拒绝 bool、复数、NaN、无穷和无法落入 float 域的结果。"""
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise ValueError("result must be a real number")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError("result is outside the supported numeric range") from exc
    if not math.isfinite(result):
        raise ValueError("result must be finite")
    return result


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        # bool 是 int 的子类，必须显式排除。
        if type(node.value) not in (int, float):
            raise ValueError("only numeric constants are allowed")
        return _finite_float(node.value)

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _finite_float(_UNARY_OPERATORS[type(node.op)](_eval_node(node.operand)))

    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)

        if isinstance(node.op, ast.Pow):
            if abs(right) > _MAX_ABS_EXPONENT:
                raise ValueError("exponent is too large")
            # Python 对负底数和非整数指数会产生 complex；本工具只承诺 float。
            if left < 0 and not right.is_integer():
                raise ValueError("negative bases require an integer exponent")

        try:
            value = _BINARY_OPERATORS[type(node.op)](left, right)
        except OverflowError as exc:
            raise ValueError("result is outside the supported numeric range") from exc
        return _finite_float(value)

    raise ValueError(f"unsupported expression element: {type(node).__name__}")


def safe_eval_expression(expr: str) -> float:
    if not isinstance(expr, str):
        raise TypeError("expression must be a string")
    if len(expr) > _MAX_EXPRESSION_LENGTH:
        raise ValueError("expression is too long")

    normalized = _normalize_financial_expression(expr)
    tree = ast.parse(normalized, mode="eval")

    if sum(1 for _ in ast.walk(tree)) > _MAX_AST_NODES:
        raise ValueError("expression is too complex")

    return _eval_node(tree.body)
```

这里的边界有两个层次。

第一层是**语法能力边界**。`ast.parse` 只负责把字符串变成树，不负责安全。真正的安全性来自 `_eval_node()`：它只处理明确列出的节点类型，且从不把 AST 交给 Python 的 `eval()` 或 `exec()`。

第二层是**资源边界**。即使没有任意代码执行，极长表达式、极深嵌套或巨大的幂运算也可能消耗不必要的 CPU 或内存。因此，表达式长度、AST 节点数、指数范围等限制不是锦上添花，而是沙箱的一部分。更精确地说，限制的数值必须和你的资源预算绑定；示例常量只是提醒你要有这道门，不是门的标准尺寸。

还有一个经常被漏掉的边界：**“解析成功”不等于“结果可作为 `float` 返回”。**例如 `(-1) ** 0.5` 在 Python 中会得到复数；`1e308 ** 2` 可能在计算时触发溢出；某些溢出之后的继续运算还可能产生 `NaN`。所以必须对每一个中间计算结果验证：它是不是实数，能不能转换为 `float`，以及是否有限。只检查最终结果是否等于正负无穷，既漏掉 `NaN`，也漏掉了复数这个类型契约问题。

🩸 **血泪提醒**：只做“AST 节点白名单”还不够。`ast.parse()` 安全，不代表计算一定便宜，更不代表结果符合你的数值类型契约。若允许不受限的 `**`，模型不需要越权，也可能用一个看似合法的表达式拖慢工具或触发数值异常。安全边界既要限制“能做什么”，也要限制“做多少”，还要限制“产出是什么”。

> 📌 **本节要点**：AST 不是安全魔法。安全来自三件事：不调用通用求值器、只解释白名单节点、为合法但昂贵的输入设置资源上限；而 `float` 工具还必须拒绝复数、NaN、无穷和溢出结果。

## 💡 修复：让错误回到模型手里，而不是炸掉工作流

林岚和顾言最后没有把计算异常抛回主线程。原因很朴素：模型生成的工具参数本来就带有不确定性。一次工具输入不合规，不应该等同于整个 Agent 失败。

因此，工具层采用 **Error-as-value**：成功时返回结果；失败时返回带有可操作提示的文本。比如模型把乘法写成了自然语言中常见的 `x`，工具可以返回：

```text
error: invalid syntax. Hint: Use '*' for multiplication, not 'x'
```

然后把这段文本作为工具结果回传给模型，让它在下一轮修正表达式。

这个策略不是“吞掉异常”。恰恰相反，它是把异常从控制流问题变成模型可见的数据。主流程仍然记录结构化失败信息，方便监控与排查；只是不会因为一条可恢复的格式错误，把整条工作流直接打断。

一个简化的包装方式如下。注意 `OverflowError` 也必须被纳入稳定的错误协议：即使当前求值器已把多数数值溢出转成 `ValueError`，包装层仍应防御性捕获它，避免未来改动或库行为差异让一次可恢复失败中断工作流。

```python
def calculate_tool(expression: str) -> str:
    try:
        value = safe_eval_expression(expression)
        return f"result: {value}"
    except SyntaxError:
        return "error: invalid syntax. Hint: Use '*' for multiplication, not 'x'."
    except ZeroDivisionError:
        return "error: division by zero. Hint: Check the denominator."
    except OverflowError:
        return "error: result is outside the supported numeric range. Hint: Use smaller values or exponents."
    except (TypeError, ValueError) as exc:
        return f"error: {exc}. Hint: Use finite real numbers, parentheses, and + - * / ** only."
```

这里也要克制：不要把底层堆栈、运行环境信息或实现细节直接塞给模型。提示应当告诉它下一步怎么修，而不是泄露不该成为工具协议一部分的内部信息。

对林岚而言，变化很具体：模型第一次写错表达式时，任务没有中断；它收到了“乘法用 `*`”的提示，下一轮给出可解析表达式，结果由受限计算器确定地产生。周闻也得到了想要的确定性，只不过确定性不再建立在一个开放 REPL 上。那道字段在那之后的处理周期里，只由这个计算工具修改一次。

> 📌 **本节要点**：对 Agent 而言，很多工具错误是可恢复的交互信号。把错误包装成有提示的返回值，可以保住工作流，同时让模型有机会自我修正。

## 🧭 诚实的边界：这不是通用 Python，也不该是

AST 算术沙箱的代价很明确：你需要维护一个小语言。

每多支持一种写法，都要回答几个问题：它的语义是什么？它是否会引入资源风险？错误信息如何设计？测试样例在哪里？例如，是否支持千位分隔符、货币缩写、财务报表中的括号负数、科学计数法、舍入规则、日期差、汇率单位？这些不是“顺手加一下”的格式问题，而是在扩展语言边界。

它也并非适用于所有任务：

- 如果任务确实需要数据分析、文件处理或复杂领域函数，专用算术解释器会变得笨重；应考虑权限更清晰的专用服务，而不是不断给表达式语言加洞。
- 如果计算具有审计、合规或精确小数要求，`float` 往往不够。金额通常应根据业务规则使用 `decimal.Decimal`，并明确舍入方式。
- 如果输入来自不可信文本，除了执行安全，还要考虑输入规范化是否改变了原始含义。`$` 和 `%` 的处理必须是产品协议的一部分，而不是悄悄发生的猜测。
- 如果模型经常生成超出白名单的表达式，问题可能不在沙箱，而在工具说明、示例或上游提取步骤没有把输入约束讲清楚。
- 如果你尚未定义延迟、内存和可接受数值范围的预算，就不应把示例中的长度、节点数和指数阈值当成生产配置。先测量工作负载，再决定门槛；否则阈值只是看起来很严肃的一串数字。

**“薄执行层，厚安全能力”不等于把所有逻辑塞进一个函数。**薄的是可执行语义：只做必要的运算。厚的是围绕它的边界：输入规范、白名单、资源限制、数值契约、错误协议、日志与测试。

> 📌 **本节要点**：专用沙箱用维护成本换取可控边界。需求一旦变成复杂领域语言，应重新评估工具边界，而不是把算术解释器悄悄养成半个 Python。

## 🛠️ 排障手册：先看症状，再看边界

当计算工具表现异常时，不要先责怪模型“不会思考”。按下面的路径定位，通常更快。

| 症状 | 常见原因 | 检查或执行方式 |
|---|---|---|
| `$100` 或 `20%` 报语法错误 | 入口没有做展示格式规范化，或规范化规则不完整 | 在测试中运行 `safe_eval_expression("$100 * 20%")`，确认结果与预期一致 |
| 模型写 `2 x 3` 后任务失败 | 把工具异常抛到了主流程，没有 Error-as-value | 检查工具包装层是否捕获 `SyntaxError`，并返回带 Hint 的文本 |
| `open(...)`、`obj.attr`、`items[0]` 被接受 | 误用了 `eval()`，或 AST 遍历器默认放行未知节点 | 加入拒绝测试：`safe_eval_expression("open('x')")` 必须抛出受控错误 |
| `(-1) ** 0.5` 返回了意外类型，或极大计算让工具异常退出 | 没有声明幂运算的实数域，也没有对每次计算结果校验有限实数 | 验证该表达式被拒绝；验证 `calculate_tool("1e308 ** 2")` 返回稳定的 `error` 文本 |
| 简单输入很慢 | 未限制表达式长度、树规模或幂运算，或阈值没有按预算校准 | 检查长度、AST 节点计数和指数限制是否存在；以自己的延迟、内存和数值预算压测后设置阈值 |
| 金额出现尾数误差 | 使用二进制浮点表示需要精确十进制的金额 | 明确金额规则；需要精确小数时改用 `Decimal` 并测试舍入 |
| 模型反复修不好表达式 | Hint 只说“失败了”，没有告诉它允许什么 | 在错误返回中写出下一步动作，例如“Use `*` for multiplication” |

可以先从这组最小回归测试开始：

```python
assert safe_eval_expression("1 + 2 * 3") == 7.0
assert safe_eval_expression("$100 * 20%") == 20.0
assert safe_eval_expression("-(10 - 3)") == -7.0
assert safe_eval_expression("(10 + 10)%") == 0.2

for expression in [
    "open('x')",
    "().__class__",
    "[1, 2]",
    "True",
    "(-1) ** 0.5",
    "1e308 ** 2",
]:
    try:
        safe_eval_expression(expression)
        raise AssertionError(f"should have rejected: {expression}")
    except (SyntaxError, TypeError, ValueError, OverflowError):
        pass

assert calculate_tool("1e308 ** 2").startswith("error:")
```

> 📌 **本节要点**：排障时先区分四类问题：格式没有规范化、语法没有被正确拒绝、数值域没有被正确约束、错误没有被正确回传。它们看起来都像“模型算错了”，修法完全不同。

## 🧭 从一台计算器，推到四条通用原则

### 1. 能力必须按任务切片

这是最小权限原则（principle of least privilege）的工程化表达：主体只应拥有完成当前任务所必需的最小权限。

机制很简单。权限不是抽象的“有”或“没有”，而是一组具体能力。能力越宽，意外路径越多；而验证所有意外路径的成本会迅速超过实现本身。模型只需要四则运算，就不应顺便得到文件系统、进程和网络的执行权。

医疗中，护士可以按医嘱配药，并不意味着可以修改全部病历或开具任意处方。不是不信任个人，而是职责边界本身就在保护病人、保护流程，也保护执行者。

> 举一反三：明天审视一个自动化接口时，问一句：**它拿到的是完成任务的能力，还是一整套顺手附送的万能权限？**

### 2. 代价必须写在界面上

“安全”常常被误解成禁止危险动作。但真正难处理的，是合法动作背后的隐性成本。巨大的幂运算未必越权，却可能昂贵；超长表达式未必错误，却可能拖垮服务。

这就是成本可见性：如果一个接口允许某种资源消耗，就必须把上限、配额、超时或拒绝条件写进接口契约。否则系统表面上只暴露了功能，暗地里却暴露了无限预算。

航空中的行李限重并不是因为超重行李“不合法”，而是飞机的载重、油耗和配平都是真实成本。把限制写在柜台规则上，所有人才能据此行动。

> 举一反三：面对一个“只要能跑就行”的接口，追问：**它允许的最坏输入会消耗什么，谁来为这个消耗付费？**

### 3. 类型契约必须覆盖失败路径

`safe_eval_expression()` 声明返回 `float`，这不是一句装饰性的类型标注。它意味着每条可达路径都要满足同一个契约：不能悄悄返回复数，不能把 `NaN` 或无穷当成正常结果，也不能让溢出绕过工具协议。

机制同样适用于任何接口：成功路径最容易被设计，边界路径最容易泄露真实语义。只在最终出口做一次浅检查，就像只在出院窗口量一次体温；病人在中间发生了什么，流程并不知道。对每一步可能改变域的操作做校验，才能让边界成为边界。

银行的转账金额字段不只要检查“像不像数字”，还要检查币种、精度、余额和限额。一个形式正确但超出允许范围的金额，仍然不是可执行的转账请求。

> 举一反三：下次看到一个函数承诺返回某种类型时，问一句：**异常输入、溢出、缺失值和边界计算，是否仍然被这份承诺约束？**

### 4. 可恢复错误应当成为协议，而不是事故

Error-as-value 背后是一种对协作系统的理解：错误不总是终点，很多时候只是下一步决策所需的信息。

如果错误只以异常形式向上传播，调用方只能中断；如果错误包含稳定类别和可执行提示，调用方——无论是人还是模型——就能调整输入、再次尝试。关键不在于假装没有失败，而在于让失败具备可读、可处理的形状。

银行转账页面提示“收款账户格式不正确，请检查位数”，比只显示“系统错误”更有价值。前者把修复权交回用户；后者把用户推回客服队列。

> 举一反三：下次设计失败返回时，问一句：**收到这条消息的人，是否知道下一步该做什么？**

### 5. 共享的心智模型，比单点正确更重要

周闻要确定性，顾言要安全性；两者并不冲突。冲突来自团队没有先把“计算”和“执行”拆开讨论。

复杂系统里，局部优化往往都合理：有人缩短交付路径，有人收紧风险边界，有人追求模型成功率。只有共享了对象边界、成本边界和失败语义，局部的正确才会拼成整体的正确。

城市道路上，司机希望快，行人希望安全，商家希望客流。交通灯、斑马线和限速不是谁战胜谁，而是把彼此看不见的成本变成共同遵守的界面。

> 举一反三：当讨论陷入“效率对安全”的二选一时，先问：**我们是否把同一个词指向了同一种能力和同一份代价？**

> 📌 **本节要点**：AST 沙箱的价值不只在算术。它提醒我们：按任务切能力、把代价写进接口、让类型契约覆盖边界路径、把可恢复错误做成协议，并用共同模型化解看似对立的目标。

## 🎯 今天就能做的事

1. 找出一个会接收模型生成内容的执行工具，写下它真正需要的最小操作集合；把“以后可能有用”的能力先删掉。
2. 为表达式工具加入拒绝测试，至少覆盖函数调用、属性访问、下标、布尔值、负底数的非整数幂、溢出结果和超长输入。
3. 运行最小验证：`safe_eval_expression("$100 * 20%")` 与 `safe_eval_expression("(10 + 10)%")`，确认金融格式规范化与运算优先级符合你的协议。
4. 运行失败路径验证：`calculate_tool("1e308 ** 2")`。确认它返回稳定的 `error` 和可操作的 `Hint`，而不是直接终止整个 Agent。
5. 不要照抄示例阈值。为表达式长度、AST 节点数、指数范围写下延迟、内存和数值范围预算，再用代表性输入测试后设定配置。
6. 在下一次站会上问一个非技术问题：**我们系统里有哪些“为了方便”而给出的万能权限，其实没人能清楚说出边界？**

**真正可靠的系统，不是让每个组件都无所不能，而是让每个组件只做自己该做的事。**
