---
title: "LLMOps 实战 03：Prompt 是发布物，不是字符串常量"
date: 2026-11-10
categories: [engineering, ai, llmops]
tags: [prompt-versioning, immutability, content-hash, release-engineering]
---

# LLMOps 实战 03：Prompt 是发布物，不是字符串常量

> 自古入门休问荣枯事，观着容颜便得知。

线上某一轮回答出了问题，你打开代码看 prompt——可你看到的是**今天**的 prompt。出问题那一轮用的是哪一版？上周有人改过一个词吗？没人知道。

改 prompt 和改代码一样会改变系统行为，但它享受的待遇通常是：一个模块顶部的字符串常量，改了就改了，diff 里夹在一堆代码中间，没有版本号，没有发布记录，出了问题无法回滚到「上一版 prompt」而不回滚代码。

这一篇讲怎么把 prompt 升格成发布物。核心就一句话：**看一眼 trace，就该知道它是哪版 prompt 生出来的。**

---

### 1. 🎯 30 秒版本

```
prompts/manifest.yaml                    # 每个版本的 sha256 + 谁是 active
prompts/registry/agent_steering/v1.md
prompts/registry/agent_steering/v2.md    # 改行为 = 发新版本
```

- 一个版本一个文件，**发布后不可变**。
- manifest 记录每个已发布版本的内容哈希；文件被原地改动，`verify()` 立刻报错。
- 每条 trace 记下 `agent_steering@v1#2a70f54c`（名字@版本#哈希前八位）。
- 运行时可以 pin 版本：`PORTAL_PROMPT_PINS=agent_steering=v1`，不发版就回滚。

---

### 2. ⚙️ 底层原理

#### 2.1 数据结构：小到不能再小

```python
@dataclass(frozen=True)
class Prompt:
    name: str
    version: str
    sha256: str
    text: str

    @property
    def ref(self) -> str:
        return f"{self.name}@{self.version}#{self.sha256[:8]}"
```

`ref` 同时带版本号和哈希，两者回答不同的问题：版本号给人看（「v2 比 v1 新」），哈希给机器对账（「这段文本确实是当时那段」）。只有版本号，无法发现「v1 被人偷偷改过」；只有哈希，人读不懂。

#### 2.2 解析优先级

```python
@lru_cache(maxsize=64)
def get(name, version=None) -> Prompt:
    """显式指定 > 运行时 pin > manifest 的 active"""
    entry = _manifest()[name]
    version = version or _pins().get(name) or entry["active"]
    meta = entry["versions"][version]
    text = _read(meta["file"])
    sha = _sha(text)
    if sha != meta["sha256"]:
        # 能服务比崩溃重要；拦住这个改动是 CI 里 verify 的职责
        logger.error("prompt %s@%s does not match its released sha256", name, version)
    return Prompt(name, version, sha, text)
```

注意哈希不匹配时**只打日志不抛异常**。这是一个明确的分工：

- 运行时的职责是可用。线上一轮对话不该因为完整性校验失败而 500。
- CI 的职责是把关。`python -m portal_api.prompt_registry verify` 不过，改动合不进来。

同一个不变量，在不同环节用不同力度执行。**不要在运行时做本该在合并前做完的检查。**

#### 2.3 不可变性靠什么保证

```python
def verify() -> list[str]:
    problems = []
    for name, entry in _manifest().items():
        if entry.get("active") not in entry["versions"]:
            problems.append(f"{name}: active version {entry.get('active')!r} is not released")
        for version, meta in entry["versions"].items():
            if _sha(_read(meta["file"])) != meta["sha256"]:
                problems.append(f"{name}@{version}: released prompt was edited in place ...")
            if not (meta.get("notes") or "").strip():
                problems.append(f"{name}@{version}: missing release notes")
    return problems
```

三条规则：active 必须指向已发布版本；文件内容必须与发布时一致；**每个版本必须有发布说明**。最后一条看起来官僚，但六个月后你想知道 v3 为什么存在时会感谢它。

`release()` 对已存在的版本直接抛错：

```python
if version in entry["versions"]:
    raise ValueError(f"{name}@{version} is already released and is immutable")
```

#### 2.4 一个只有踩过才知道的坑：格式化工具会改哈希

仓库的 pre-commit 里有 `end-of-file-fixer`，它会给每个文件末尾补一个换行。于是：你发布 v1，算好哈希，提交，hook 给文件加了个 `\n`，哈希变了，`verify()` 说你原地改了已发布版本。

修法是让哈希算在**实际服务出去的内容**上，而不是磁盘字节上：

```python
def _read(rel_path: str) -> str:
    # strip 之后再算：格式化工具补的末尾换行不改变哈希
    return (PROMPTS_DIR / rel_path).read_text(encoding="utf-8").strip()
```

对应的测试名字就是需求本身：`test_trailing_newline_from_a_formatter_does_not_change_the_hash`。

> 经验：**内容寻址要先做规范化。** 先问「哪些差异在语义上不算差异」，把它们抹平再哈希。

#### 2.5 迁移：逐字节等价，先证明再切换

把现有的常量搬进 registry 时，最大的风险是「搬的过程中不小心改了一个字符」。我没有复制粘贴，而是让程序自己导出：

```python
(base / "agent_steering/v1.md").write_text(agent.STEERING, encoding="utf-8")
```

然后在删掉常量**之前**断言等价：

```python
assert r.get("agent_steering").text == agent.STEERING
```

看到 `byte-identical` 才动手删旧代码。这样这次重构对模型行为的影响可以被证明为零，评审时不需要任何人「相信」。

#### 2.6 trace 里怎么记

```python
steering = prompt_registry.get("agent_steering" if tools else "agent_offline_steering")
collector.use_prompt(steering.ref)
messages.insert(0, {"role": "system", "content": steering.text + ws_steer})
```

一行 `use_prompt`。之后每条 trace 的 `prompt_refs` 字段就是这一轮用过的全部 prompt 版本。从 trace 抓回归用例时这个字段会被一并带走，于是每条回归用例都知道自己是在哪版 prompt 下出的事。

---

### 3. 🧭 为什么选它，不选别的

**为什么是文件 + git，不是数据库或 prompt 管理平台？**

| | 文件 + manifest | 数据库 / 平台 |
|---|---|---|
| 评审 | 就是普通 PR | 另一套界面和权限 |
| 回滚 | `git revert` 或 pin | 平台功能 |
| 与代码原子发布 | 同一个 commit | 两个系统，会漂移 |
| 离线 / CI | 天然可用 | 需要网络和凭据 |
| 非工程师编辑 | 不方便 | 方便 |

最后一行是平台真正的价值。如果改 prompt 的是产品或运营，平台值得。我这里改 prompt 的就是写代码的人，而「prompt 和依赖它的代码在同一个 commit 里」这件事太有用了。

**为什么版本号是手写的 v1/v2，不直接用哈希当版本？**
因为版本之间有顺序，人要讨论「v2 比 v1 好在哪」。哈希没有顺序。两者都要。

**为什么需要运行时 pin？**
发布新 prompt 后发现不对劲，最快的止血不是 revert、等 CI、重新部署，而是改一个环境变量重启。它同时也是最朴素的灰度手段：一个实例 pin 在 v1，另一个跑 v2。

---

### 4. 🔬 常见追问

**Q：manifest 里的哈希是人手改的，有人连哈希一起改了怎么办？**
registry 自己确实拦不住。所以还有第二道锁：评测基线里也存了一份 artifact 指纹。manifest 和文件一起被改，版本号却没变，quality gate 会报「内容变了但版本还是 v1」。这部分在第 6 篇。**单层校验防手滑，双层校验才防绕过。**

**Q：prompt 里有动态部分（比如工作区信息）怎么版本化？**
版本化的是模板。上面代码里 `steering.text + ws_steer`，`ws_steer` 是运行时拼的。trace 里另存了完整渲染后的 system prompt，所以「模板是哪版」和「最终发给模型的是什么」两个问题都能回答。

**Q：怎么保证新版本没把关键条款删掉？**
`prompts` 评测集里的 prompt 契约用例：active 版本必须包含一组关键短语（比如审批相关的那条规则），并且不超过长度上限。新版本删了关键条款，CI 直接红。

---

### 5. 🛠 自己动手

1. 在你的项目里 grep 出所有内嵌的 prompt 字符串，数一数有几个、上次是谁在什么时候改的。
2. 实现 `Prompt` 数据类和 `get()`，先只支持 manifest 的 active。
3. 用「程序导出 + 断言等价」的方式迁移一个 prompt，不要手工复制。
4. 实现 `verify()`，然后原地改一个字，确认它报错；再只加一个末尾换行，确认它不报错。
5. 把 `ref` 写进你的日志或 trace，然后试着回答：「昨天下午三点那一轮用的是哪版 prompt？」
