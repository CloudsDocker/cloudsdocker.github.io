---
title: 缺 Rust 编译器？先别 rustup，去读 uv.lock
header:
    image: /assets/images/hd_linux_tips.jpg
date: 2026-09-01
tags:
 - python
 - uv
 - packaging
 - dependencies
 - devops
permalink: /blogs/tech/zh/uv-lock-no-wheels-is-a-verdict
layout: single
category: tech
---

> 图难于其易，为大于其细。——《老子》

---

# 缺 Rust 编译器？先别 rustup，去读 uv.lock

*从 `can't find Rust compiler` 到会读发行物标签 —— 把「装编译器」从条件反射里删掉*

今天早上，`uv sync` 在 `tiktoken==0.3.3` 上炸了。日志写得很热情：

```
error: can't find Rust compiler
running build_rust
```

下面还附赠一段 2023 年的套话：升级 pip，或者去 rustup.rs 装编译器。

我入行二十年，见过太多人在这一步立刻 `curl | sh`。那一步不是错的，它只是**答错了题**。真正的判决书不在 stderr 最后一行，在 `uv.lock` 里有没有 `wheels = [...]` 这一段。

没有 wheels，就是在宣判：你手里拿的是手稿（sdist），不是印好的书（wheel）。Rust 编译器是雕版凿子。你当然可以凿，但 staff 的第一反应应该是：**我为什么在雕版？**

**读完你会带走三条直觉：**

- `uv.lock` 是法庭笔录，`uv tree` 是族谱，`uv sync` 只是法警去执行
- sdist / wheel / crate 不是三个近义词，是三个生态系统的「发行物单位」
- `cp313` 不是版本号装饰，是 ABI 门票；门票不对，再新的 pip 也变不出历史

下面按「最先该查什么」排，不是按今早报错出现的顺序。

---

## 一、三张图：lock、tree、sync

`uv` 把一件过去分散在 pip / poetry / virtualenv 里的事拆成三个明确动作。我在 0.11.16 的 help 里对过这些开关，先把职责钉死：

| 命令 | 它改什么 | 它回答的问题 | 不该拿它干什么 |
|---|---|---|---|
| `uv lock` | 只写 `uv.lock` | 「这些约束现在解析成哪一版？」 | 不装环境。解析成功 ≠ 你能跑代码 |
| `uv tree` | 默认什么都不改 | 「谁把谁拉进来的？」 | 不修版本。它是地图，不是方向盘 |
| `uv sync` | 按锁文件改 `.venv` | 「磁盘上的环境和笔录一致吗？」 | 别在它失败时先升级 pip。失败点已经过了解析 |

今早那次：`Resolved 143 packages in 2ms` —— **解析过了**。死在 build。所以问题不在「找不到包」，在「找到的那份发行物必须现场编」。

### `uv lock`：把愿望清单变成笔录

`pyproject.toml` 写的是愿望：`genai>=2.1.0`。`uv.lock` 写的是事实：当时解析出 `genai==2.1.0`，它又要 `tiktoken`，锁到了 `0.3.3`，而且**只有 sdist**。

几个会在 CI 和 code review 里反复出现的开关：

```bash
uv lock              # 按当前 pyproject 重新解析，必要时改 lock
uv lock --check      # lock 是否还跟约束一致；不一致就非零退出（给 CI）
uv lock --dry-run    # 只看会改什么，不写盘
uv lock -P tiktoken  # 只允许这一个包升级，其余钉死
uv lock -U           # 放开升级，忽略现有 pin（Implies --refresh）
```

`uv sync` / `uv tree` 上还有一对容易混的守卫：

| 开关 | 含义 |
|---|---|
| `--frozen` | **不要重新 lock**，就读现有 `uv.lock` |
| `--locked` | 可以解析，但若结果会改 lock，就失败 |

一句话：`--frozen` 是「闭卷考试」，`--locked` 是「开卷但禁止涂改答案」。

> 约束是立法，lock 是判例。团队吵架的时候，先打开判例，别先背法条。

### `uv tree`：先问「谁拉进来的」

`uv` 自己的 hint 其实已经做了一次人工 invert：

> `tiktoken` (v0.3.3) was included because `clients` (v0.1.0) depends on `genai` (v2.1.0) which depends on `tiktoken`

这就是族谱。命令写成：

```bash
uv tree --frozen -d 2
uv tree --frozen --package genai
uv tree --frozen --invert --package tiktoken
uv tree --frozen --show-sizes
uv tree --frozen --python-version 3.13 --python-platform aarch64-apple-darwin
```

| 开关 | 干什么 |
|---|---|
| `--invert --package X` | 倒着长：谁依赖 X。构建失败时**第一条该跑的** |
| `--package X` | 只看以 X 为根的那一枝 |
| `--depth` | 防止 FastMCP 那种树把屏幕淹了 |
| `--show-sizes` | 压缩后的 wheel 体积。25KB 的 tar.gz 和 1MB 的 whl 不是一种东西 |
| `--outdated` | 树上每个包相对最新版差多远 |
| `--python-version` / `--python-platform` | 按目标解释器和平台过滤。同一把锁，3.11 和 3.13 看见的 wheel 可以完全不同 |
| `--no-dedupe` | 重复依赖不再用 `(*)` 折叠，排查「为什么装了两份」时用 |

今早的锁还在的时候，invert 会长成这样（根据 hint 和当时 lock 复原，不是现在机器上的输出）：

```
tiktoken v0.3.3
└── genai v2.1.0
    └── clients v0.1.0
```

我写这篇的时候，`genai` 已经从 `pyproject.toml` 拿掉了。此刻真实的顶层树是：

```
clients v0.1.0
├── beautifulsoup4 v4.15.0
├── fastmcp v3.4.7
├── google v3.0.0
├── google-genai v2.21.0
├── inquirerpy v0.3.4
├── langchain-ollama v1.1.0
├── trafilatura v2.2.0
└── typer v0.27.1
```

`uv tree --frozen` 里已经没有 `tiktoken`。这不是魔法，这是**砍掉拉它进来的那根树枝**之后，族谱自己变干净了。

📌 **takeaway：** 构建失败先 `invert`，不要先 rustup。hint 和 `--invert` 说的是同一句话。

---

## 二、sdist、wheel、crate：三个世界的「一包」

新人最容易把这三个词当成「压缩包的三种后缀」。它们根本不在同一个法庭。

| 词 | 哪个世界的单位 | 里面通常是什么 | 你的机器要不要编译 |
|---|---|---|---|
| **crate** | Rust / Cargo | `Cargo.toml` + `.rs`。tiktoken 的热路径是 Rust 写的 BPE | 编 crate 需要 `rustc` |
| **sdist** | Python / PyPI | `.tar.gz` 手稿：`pyproject.toml`、源码、构建脚本 | **要**。PEP 517 后端会在隔离环境里跑 `build_wheel` |
| **wheel** | Python / PyPI | `.whl`（就是 zip）。纯 Python 或已经编好的 `.so` / `.dylib` | **不要**。解开、放到 site-packages |

关系不是并列，是流水线：

```
Rust crate  (tiktoken 的核心实现)
    │  在「包作者的 CI」里 rustc + maturin/setuptools-rust
    ▼
Python wheel  (cp313-macosx_11_0_arm64.whl)
    │  上传到 PyPI
    ▼
你的 uv sync  —— 对上标签就拆箱，对不上就退回 sdist
    │
    ▼
sdist 现场走同一条流水线  —— 于是向你要 rustc
```

知人论世：2023 年 3 月的 `tiktoken==0.3.3` 发行时，CPython 3.13 还不存在。作者的 CI 不可能给你一张 `cp313` 门票。不是 PyPI 小气，是时间线不借债。

今早那份锁把这件事写得直白——只有 sdist，没有 wheels 段：

```toml
[[package]]
name = "tiktoken"
version = "0.3.3"
sdist = { url = ".../tiktoken-0.3.3.tar.gz", size = 25347 }
```

注意：当时这份锁**没有** `wheels = [ ... ]` 段。

对比后来带门票的版本，文件名自己就是说明书：

```
tiktoken-0.12.0-cp313-cp313-macosx_11_0_arm64.whl
```

25KB 的 tar.gz 装不下编译好的动态库。1MB 量级的 whl 才装得下。`--show-sizes` 就是把这个不对称标出来。

> 发行物是产品，编译器是工厂。缺工厂的时候，先问自己是不是进错了车间。

📌 **takeaway：** crate 是 Rust 的包，sdist 是 Python 的手稿，wheel 才是给你拆的箱子。三者不是后缀变体。

---

## 三、`cp313` 不是彩蛋，是 ABI 门票

Wheel 文件名按 PEP 425 / 427 拆五段：

```
{distribution}-{version}-{python tag}-{abi tag}-{platform tag}.whl
     tiktoken      0.12.0      cp313         cp313     macosx_11_0_arm64
```

| 标签 | 人话 | 对不上会怎样 |
|---|---|---|
| `cp313` | 给 CPython 3.13 编的 | 3.12 的解释器看它，等于看隔壁桌的饭 |
| 第二个 `cp313` | ABI：用了 3.13 的 C API | `cp313t` 是 free-threaded 变体，也不是同一张票 |
| `macosx_11_0_arm64` | macOS 11+，ARM64 | Intel Mac、Linux CI、Windows 各自要自己的票 |
| `manylinux_2_28_x86_64` | 在足够新的 glibc 上编的 Linux | 老发行版可能接不住 |
| `py3-none-any` | 纯 Python，无原生扩展 | 这才是「一份 whl 走天下」 |
| `abi3` | 稳定 ABI，一张票跨多个 CPython | 少数扩展才提供 |

`.python-version` 里写 `3.13`，`requires-python = ">=3.13"`，等于你主动走进了 3.13 窗口。窗口里没有 2023 年 3 月的原生票，uv 只能退回 sdist，然后 `running build_rust`。

日志里那句「upgrade pip, a prebuilt wheel may be available」是 **sdist 里印给 pip 用户的说明书**，不是 uv 的诊断。uv 已经在用隔离构建后端。升级 pip **变不出一张从未上传过的 cp313 wheel**。

五个为什么，钉在机制上：

1. 为什么要 rustc？—— 因为在编 Rust 扩展。
2. 为什么要编？—— 因为没有匹配的 wheel。
3. 为什么没有？—— 0.3.3 发布时没有 3.13。
4. 为什么是 0.3.3？—— `clients` 依赖了 2023 年的 PyPI 包 `genai`，它拉来 tiktoken。
5. 为什么依赖 `genai`？—— 名字像 Google SDK。真正的代码却是 `import google.generativeai`，旁边还声明了另一个包 `google-genai`。

最后一个「为什么」已经不是打包问题，是**命名把人带进了错误的法庭**。

🩸 **硬教训：** 装 rustc 能让症状消失，也能让错误依赖在团队里合法化。下一台没有凿子的 CI 机器，会把同一张罚单再开一次。

📌 **takeaway：** `cp313` 是 ABI 门票。升级 pip 变不出一张从未上传的票。

---

## 四、把「装编译器」从默认动作里删掉

普通人的看法：缺编译器 → 装编译器。

资深的看法：缺编译器 → 我在装一份不该以源码形态出现的东西。

| 动作 | 它优化的是什么 | 它掩盖的是什么 |
|---|---|---|
| `rustup` 然后重试 `uv sync` | 当前这台笔记本的通过率 | 依赖图撒谎、CI 镜像膨胀、下一个同事再炸 |
| `uv add tiktoken>=0.12` 但仍留着错误的 `genai` | 让化石包碰巧够到带票的 tokenizer | 你仍然养着 2023 年的错误名字 |
| 从 `pyproject.toml` 删除 `genai`，再 `uv lock` | 依赖与 import 对齐 | 下一步可能暴露：代码还在 `import google.generativeai`，那个包名你没声明。这是**更干净的失败** |
| `uv sync --no-build` | 政策：禁止现场雕版 | 没有 wheel 就硬失败，适合 CI 当门禁 |

面试拿分点：`--no-build` 不是刻薄，是把「我们不在开发者机器上编原生扩展」写成可执行的工程产物。部落知识（「别装 rustc」）变成开关。

政策门禁——只许拆箱，不许开工厂：

```bash
uv sync --frozen --no-build
```

若你**真的**有意从源码编内部 crate，那是另一条流水线：内部 wheelhouse、固定的 rustc、缓存。那是工厂设计，不是报错后的条件反射。

> 奥卡姆在这里很狠：能解释「没有 cp313 wheel」的，不必再发明「我的 pip 太旧」。

📌 **takeaway：** 修依赖图，比给错误依赖配齐车间便宜。

---

## 三张地图合成一张

```
pyproject.toml          愿望 / 立法
        │  uv lock
        ▼
uv.lock                 判例：版本 + sdist/wheels
        │  uv tree --invert
        ▼
族谱                    谁把化石拉进来
        │  看有没有 wheels，看 tag 是否含 cp313
        ▼
uv sync                 拆箱 或 开工厂
```

| 你看见的 | 先打开哪张图 |
|---|---|
| `Resolved N packages` 然后 `build_rust` | lock 里那个包的 `sdist` / `wheels` |
| `was included because A depends on B` | `uv tree --invert --package <炸的包>` |
| 纯 Python 包却在编 | `--no-binary` 是不是被打开了 |
| 换了 Python 小版本就全炸 | wheel 的 python/abi tag |
| 本机能 sync、CI 不能 | `--python-platform` 过滤后的那棵树 |

📌 **takeaway：** 症状在 sync，证据在 lock，凶手在 tree。

---

## 🧭 把这次失败做成可带走的原则

解决 `tiktoken` 只是叶子。下面四条才是下次换一个包、换一个语言还能用的干。

### 原则 1：发行物优先于工具链

**机制：** 安装器先匹配 wheel 标签，匹配失败才退回 sdist。sdist 才会向你要 rustc / gcc / JDK。  
**跨域：** 图书馆进门先问有没有印本。没有印本才去抄经房。抄经房缺笔墨，正确动作是回柜台问「为什么没有印本」，不是先去买一套雕版。  
**举一反三 / Generalize：** 报错写着缺编译器，先搜发行物（wheel、jar、container image），最后才装车间。

### 原则 2：先画族谱，再动手术刀

**机制：** 解析器按图拉依赖。炸的那个包往往不是你写在 `pyproject.toml` 第一行的那个。  
**跨域：** 聚会上有人砸了杯子，先问是谁带来的，别先罚杯子厂家。  
**举一反三 / Generalize：** `uv tree --invert`、`maven dependency:tree -Dincludes`、`npm ls`、`go mod why` —— 同一条肌肉。

### 原则 3：把「不许开工厂」写成开关

**机制：** `--no-build`、`--frozen`、`uv lock --check` 把口头规矩变成非零退出。  
**跨域：** 「下班别忘锁门」是部落知识；门禁卡下班自动失效，才是工程产物。  
**举一反三 / Generalize：** 凡是你准备在 README 里写成「请注意」，先问能不能变成 CI 的一次失败。

### 原则 4：短名字不是身份证件

**机制：** PyPI 的发行名、Python 的 import 名、产品文档里的商品名，是三套系统。`genai` / `google-genai` / `google.generativeai` 可以同时为真且互不相认。  
**跨域：** 三个餐馆都叫「成都小炒」，你点的那盘可能来自另一条供应链。  
**举一反三 / Generalize：** 任何「我装上了但 import 不对」的事故，先画三列对照表，再谈版本号。

---

## 立刻可以做的事

1. 在你自己的项目里跑 `uv tree --frozen --invert --package <刚才失败的那个包>`。把输出贴进 PR 描述，不要只贴 stderr。
2. 打开 `uv.lock`，找到那个包。数一遍：有没有 `wheels` 段？有没有你的解释器标签（`cp313`、`macosx`、`manylinux`、`win_amd64`）？
3. 把 `uv lock --check` 加到 CI。lock 和 `pyproject.toml` 分叉时，绿勾不该还在。
4. 对原生依赖尝试一次 `uv sync --frozen --no-build`。失败了更好——失败发生在政策层，而不是同事的 PATH。
5. 扫一遍 `pyproject.toml` 里的短名字。`genai` 和 `google-genai` 不是同一个法庭。依赖名、import 名、文档里的商品名，三张图必须能对上。
6. 把「invert → 看 wheels 段 → 才考虑工具链」写成团队的三条命令，放进 README。这是这篇最值钱的交付：别让下次的人重新推理。

---

*stderr 最后一行是症状。lock 里缺席的 `wheels` 段才是判决。凿子很便宜，进错车间才贵。*
