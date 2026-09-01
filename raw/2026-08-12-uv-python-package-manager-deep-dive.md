---
title: "uv 到底强在哪：从一条 scratchpad 命令说起"
date: 2026-08-12
categories: [engineering, python, tooling]
tags: [uv, pip, venv, python-packaging, shell, ci-cd]
---

某天调试一个 nonstandard-etl 项目，手边随手甩出一条 `uv venv` + `uv pip install` 的命令,
干脆借这个机会把 `uv` 从"能用"到"为什么好用"到"怎么正经用"过了一遍。这篇就是这次探索的整理版。

## Part 1：一条命令到底在干嘛

原始命令长这样（路径做了脱敏处理）：

```bash
SP=/path/to/scratchpad
uv venv --python 3.11 "$SP/venv311"
uv pip install --python "$SP/venv311/bin/python" \
  'boto3>=1.28.11,<2' 'requests>=2.31.0,<3' 'pandas>=2.1.4,<3' \
  'numpy>=1.26.3,<2' 'pyarrow>=17.0.0,<18' \
  'pytest>=7.4.2,<8' 'pytest-cov>=4.1.0,<5' 'moto>=4.2.3,<5' \
  'edr-common-python @ git+ssh://git@github.com/your-org/edr-common-python.git'
```

一句话总结：**用 `uv` 在项目的 scratchpad 目录下新建一个 Python 3.11 的干净虚拟环境，
然后往里面装了一整套"能跑 AWS + 能跑测试 + 能连公司私有仓库"的工具链。**

装的包分三类，很像给新兵发装备：

| 类别 | 包 | 干嘛用的 |
|---|---|---|
| 🛠️ 干活的家伙 | `boto3`, `requests`, `pandas`, `numpy`, `pyarrow` | 连 AWS、发 HTTP 请求、处理表格数据、读写 Parquet |
| 🧪 保命的家伙 | `pytest`, `pytest-cov`, `moto` | 跑测试、算覆盖率、**假装**在跟 AWS 打交道（moto = mock AWS，不烧真金白银） |
| 🔒 自家秘密武器 | `edr-common-python`（走 `git+ssh://` 拉私有仓库） | 公司内部封装库，装的时候要用本机配好的 SSH key 认证 |

血泪提醒：

1. `git+ssh://` 这行如果失败，99% 是 SSH key 没加载——先 `ssh -T git@github.com` 测一下，别怀疑 uv 本身。
2. `scratchpad` 目录顾名思义是"用完即扔"，这类临时环境大概率不会被复用，每次都从零建，图的就是环境洁净。

## Part 2：uv 比 pip/venv 强在哪

核心杀器：一个 Rust 写的依赖解析器 + 一个全局缓存系统，把"装包"这件事从
"每次都现磨咖啡"变成"直接从冰箱拿冰咖啡"。同样的 `requirements.txt`，
`pip` 装 30 秒，`uv` 装 1-2 秒，快一个数量级不是营销话术，是真能跑出来的数字。

类比一下：

- **`pip` 的做法**：每次有人点单，都重新去仓库翻一遍配料表、算一遍配方兼容性，
  算完了现场从供应商那里进货。慢，但简单直接。
- **`venv` 的做法**：给每个订单单独开一个全新的厨房（虚拟环境），厨房之间互不干扰，
  但每个厨房都要重新摆一遍锅碗瓢盆。
- **`uv` 的做法**：把 `pip` + `venv` + `pip-tools` 三个人的活一个人全干了，而且有个
  "中央仓库"（全局缓存 `~/.cache/uv`），同一个包版本只要下载解压一次，之后任何项目、
  任何虚拟环境要用，都是硬链接过去，不用重新下载、重新解压。这就是"瞬间"完成的秘密。

血泪提醒：

1. 依赖解析算法是真的更强。`pip` 的解析器出了名的"先装先得、装到冲突再回头"，
   遇到复杂依赖树容易卡死或装出不兼容组合；`uv` 用的是更现代的 PubGrub 算法
   （跟 Rust 的 `cargo`、Dart 的 `pub` 一个流派），冲突了也报错报得更清楚。
2. `uv venv` ≠ `python -m venv`，但生成的环境结构一样，`source venv/bin/activate`
   的老习惯完全不用变。
3. 全局缓存是把双刃剑，长期不清理 `~/.cache/uv` 会越滚越大，记得偶尔 `uv cache clean`。

## Part 3：`uv pip install` vs `uv add`（没有 `uv install` 这回事）

根本没有 `uv install` 这个命令——`uv` 有两套完全不同的"装包"接口，
`uv pip install` 只是其中"兼容老规矩"的那一套，这是故意设计成两条腿走路。

**门派一：`uv pip *`（兼容层，模拟传统 pip workflow）**

```bash
uv pip install boto3    # 直接往当前/指定的 venv 里装
uv pip compile          # 相当于 pip-tools 的 compile
uv pip sync             # 相当于 pip-tools 的 sync
```

存在的意义：原来整套 `requirements.txt` + `pip install -r` 的老流程一个字不用改，
只把 `pip` 换成 `uv pip`，直接白嫖 10-100 倍速度。Part 1 那条命令就是这个套路。

**门派二：`uv add` / `uv sync` / `uv run`（uv 原生的"项目"工作流）**

```bash
uv add boto3            # 往 pyproject.toml 里加依赖 + 自动更新 uv.lock + 自动装
uv sync                 # 按 uv.lock 精确复现环境（团队协作/CI 用这个）
uv run script.py        # 自动确保依赖装好，再跑脚本
```

这套是 `uv` 真正想让你用的"未来"，管理的是 `pyproject.toml` + `uv.lock`，
语义上是"往项目清单里加一项"，而不是"无脑装一个包"，所以不叫 `install` 叫 `add`。

血泪提醒：

1. 两套接口互不感知彼此。`uv pip install` 装的包不会自动写进 `pyproject.toml`/`uv.lock`，
   反过来 `uv add` 也不看你手动 `uv pip install` 装了啥。混用等于左右手互搏，团队协作场景别混。
2. 一次性、用完即扔的沙盒环境适合 `uv pip install`；长期维护的项目应该上 `uv add` + `uv.lock`。
3. 还有个容易搞混的 `uv tool install`——装全局 CLI 工具用的（类似 `pipx install`），
   跟前两套都不是一回事，装的东西不进任何 venv，直接挂到 PATH。

## Part 4：`uv add` + `uv.lock` 完整工作流怎么玩

三步走：`uv init` 建项目 → `uv add xxx` 加依赖（自动写进 `pyproject.toml` 并生成/更新
`uv.lock`）→ `uv sync` 或 `uv run` 让任何一台机器精确复现同一个环境。核心思路：
`pyproject.toml` 是"我要什么"，`uv.lock` 是"精确锁死到底装的哪个版本+哪个 hash"，
两个文件都进 git，队友 clone 下来 `uv sync` 一下就跟你环境一模一样。

```bash
# 1. 建项目（会生成 pyproject.toml + 一个空的 .venv）
uv init my-etl-project
cd my-etl-project

# 2. 加依赖——同时干了三件事：装进 .venv / 写进 pyproject.toml / 更新 uv.lock
uv add boto3 pandas pyarrow

# 3. 分环境的依赖，用 group（对应老 pip 时代的 requirements-dev.txt）
uv add --dev pytest pytest-cov moto

# 4. 别人 clone 你项目后，一句话复现你的环境
uv sync

# 5. 不想手动 activate，直接跑
uv run pytest
```

跟 Part 1 那条 scratchpad 命令对比一下：

| | scratchpad 那条命令（`uv pip install`） | 项目工作流（`uv add`） |
|---|---|---|
| 目的 | 一次性、跑完就扔 | 长期维护、要给团队/CI 复用 |
| 版本记录 | 没有，全靠手打的版本号约束 | `uv.lock` 精确到 hash |
| 复现方式 | 得把命令再抄一遍 | `uv sync` 一句话 |

血泪提醒：

1. `uv add` 默认是"宽松"约束，`uv.lock` 才是"精确"约束。`pyproject.toml` 里会看到
   `boto3>=1.28.11,<2` 这种范围，但真正决定"今天装的到底是 1.28.11 还是 1.35.0"的
   是 `uv.lock`。范围给人看，锁文件给机器用——两个都要提交进 git，缺一不可。
2. `uv.lock` 冲突是团队协作的新噪音源。多人同时 `uv add` 不同包，这种自动生成的
   大文件很容易在 git merge 时炸锅，约定"谁改依赖谁 rebase 到最新再 add"能省很多事。
3. CI 里一定要用 `uv sync --frozen`，而不是 `uv sync` 或 `uv add`：`--frozen` 会拒绝
   任何"顺手升级一下锁文件"的行为，锁文件对不上直接报错退出——这是保证 CI 环境和
   本地环境**分毫不差**的关键开关，也是最容易被新手漏掉的一步。
