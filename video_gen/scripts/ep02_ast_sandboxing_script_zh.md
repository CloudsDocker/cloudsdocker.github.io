---
title: "【AI FDE 架构实战 02】千万别用 eval()！企业级 AI Agent 的 AST 安全沙箱设计"
episode: 2
series: "AI-FDE-Playbook"
language: "zh-CN"
duration: "4m 15s"
target_platform: "YouTube / Bilibili / Descript"
tags: ["AI Agent", "Python AST", "Security", "Sandbox", "Code Execution", "FDE"]
---

# 视频脚本：千万别用 eval()！企业级 AI Agent 的 AST 安全沙箱设计

## 场景 1：开场与安全爆破演示（0:00 - 0:45）
**[画面呈现 / B-Roll]**
- 警示红光背景，屏幕展示一段貌似无害的 Agent 工具调用：`tool_calculator(expr)`。
- 紧接着展示 Prompt 注入攻击 payload：`__import__('os').system('rm -rf /')` 或利用内置类遍历读取 `open('/etc/passwd')`。
- 控制台直接报警：Remote Code Execution (RCE) 漏洞利用成功。

**[录音旁白 / 逐字稿]**
“在很多开源 Agent 教程里，当模型需要计算数学算式时，作者图省事直接写了一个 `eval(expression)`。
如果你敢在企业级生产系统里这么干，我可以负责任地告诉你：你的服务器已经属于攻击者了。无论是提示词注入（Prompt Injection）还是上下文数据污染，攻击者只需要几行花式 Python 反射语法，就能绕过普通正则黑名单，直接提权执行系统命令。
今天我们来演示：为什么正则黑名单防不住注入，以及如何用 Python 内置的 AST 语法树构建零依赖、微秒级的极速安全计算沙箱。”

---

## 场景 2：为什么正则黑名单一定会失败？（0:45 - 1:30）
**[画面呈现 / B-Roll]**
- 动态白板：展示常见的正则过滤模式，比如禁止 `import`，禁止 `os`，禁止 `exec`。
- 随后演示绕过 payload：`[c for c in ().__class__.__base__.__subclasses__() if c.__name__ == 'catch_warnings'][0]()._module.__builtins__['__import__']('os')`
- 印章盖下红字：“Blacklists Always Fail”。

**[录音旁白 / 逐字稿]**
“很多开发者的第一反应是搞正则过滤：禁止出现 `import`，禁止出现双下划线 `__`。
但现代解释型语言的动态反射机制极其灵活。攻击者可以通过元类查找、字符串拼接或进制编码，完全在不出现这些关键字的情况下拿到任意系统的句柄。
在安全领域有一条铁律：永远不要使用黑名单（Denylist），必须使用白名单（Allowlist）！”

---

## 场景 3：AST 抽象语法树白名单解法（1:30 - 2:45）
**[画面呈现 / B-Roll]**
- 动态树状图：把 `(100.5 + 45) / 2` 转换为 Python AST 节点树结构。
- 树节点亮起绿色：`Expression` -> `BinOp` -> `Add` -> `Constant`。
- 树节点亮起红色：`Call`，`Attribute`，`Name` —— 任何函数调用直接拒绝。
- 展示 `src/solver/tools.py` 里的 `ast.NodeVisitor` 源码。

**[录音旁白 / 逐字稿]**
“这就是企业级 FDE 的推荐解法：使用 Python 标准库的 `ast` 模块进行语法树重构。
核心思路极其简洁：
第一，我们把模型生成的表达式通过 `ast.parse` 解析为语法树。
第二，我们严格限定允许访问的节点类型：只能是 `ast.Expression`、`ast.BinOp`、`ast.UnaryOp` 和数值字面量 `ast.Constant`。
第三，任何包含 `ast.Call`（函数调用）、`ast.Attribute`（属性访问）或者变量名查找的节点，直接抛出 `SecurityException` 拦截。
没有函数调用的语法树，在数学上就杜绝了任何执行恶意代码的可能性！”

---

## 场景 4：生产健壮性：除零、溢出与精度控制（2:45 - 3:30）
**[画面呈现 / B-Roll]**
- 演示测试用例：`1 / 0`，超大整数乘方 `9999 ** 9999`，浮点数精度 `0.1 + 0.2`。
- 终端展示沙箱安全捕获 `ZeroDivisionError` 与 `OverflowError` 并返回结构化错误。

**[录音旁白 / 逐字稿]**
“除了安全，还要考虑运行时的健壮性。
沙箱必须捕获 `ZeroDivisionError` 和指数爆炸，并将错误以结构化的友好信息反馈给推理层，触发自适应修正，而不是让主服务进程崩溃。
这种纯 AST 沙箱无需 Docker 容器冷启动，单次执行耗时小于 0.05 毫秒，且零外部依赖，是最高性价比的企业级方案。”

---

## 场景 5：结语与下期预告（3:30 - 4:15）
**[画面呈现 / B-Roll]**
- 画面切回主播与 `AI-FDE-Playbook` 仓库 `src/solver/tools.py` 页面。
- 下期预告：《从 30% 到 85% 准确率：多轮财务对话 Prompt 消融实验与校准》。

**[录音旁白 / 逐字稿]**
“把不确定的概率生成，限制在绝对确定的工程防空洞里，这就是系统级 AI 架构师的日常。
完整的 AST 沙箱实现与单元测试已经上传至 `AI-FDE-Playbook` 仓库，开箱即用。
下一期，我们将进入 Prompt 核心：如何通过严密的消融实验（Ablation Study），把多轮财务对话的准确率从 30% 一步步拉升到 85%？
记得点赞订阅，我们下期见！”
