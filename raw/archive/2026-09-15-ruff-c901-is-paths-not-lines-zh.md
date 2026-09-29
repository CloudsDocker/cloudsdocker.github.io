---
title: C901 罚的不是行数，是独立路径
header:
    image: /assets/images/hd_mvn_skip_tests.png
date: 2026-09-15
tags:
 - python
 - lint
 - ci-cd
 - ruff
 - github-actions
permalink: /blogs/tech/zh/ruff-c901-is-paths-not-lines
layout: single
category: tech
---
> “The competent programmer is fully aware of the limited size of his own skull.” — Edsger W. Dijkstra

# C901 罚的不是行数，是独立路径

*从一条 ruff 红灯，到会手算圈复杂度、会拆编排函数。*

周二上午。UAC → Salesforce 那张 PR — `ditapi-p-domestic-student-recruitment-v1` #41 — CI 红了。日志里 pytest 还没出场，先撞上 ruff：

```
error[C901]: `_build_csvs` is too complex (12 > 10)
   --> app/services/sync_uac.py:310:5
```

下面这三行是安装成功，不是故障：

```
Downloaded virtualenv
Downloaded ruff
Installed 89 packages in 68ms
```

人第一眼会往 SAS、Bulk、Salesforce 想。错了。这是 **静态分析门禁**：函数里的独立路径超了 10。

反直觉的一句：**C901 不算函数有多长。它算你能怎么走出去。** 两个新 `if` 就能把一个本来踩线的编排函数顶爆。

你要带走的不是另一份 ruff 手册，是三块能移植的知识：

- **McCabe 圈复杂度**：控制流图上的独立路径，不是 LOC
- **编排 vs 策略**：新规则进 helper，不进已经踩线的中枢
- **lint 作为合并契约**：抽函数 / `noqa` / 抬阈值 — 三选一，且要有主张

顺序是教学顺序：先读日志，再手算，最后才是怎么改。

## 1. 日志怎么读：规则码 + 数字对比 + 定义行

| 日志 | 意思 |
|---|---|
| `Downloaded virtualenv` / `Downloaded ruff` | `uv` 装了隔离环境和 ruff。**还没跑业务测试。** |
| `Built mq-canonical-models` / `ditapi-common` | 私有 git 依赖编过了，安装成功 |
| `Installed 89 packages` | 环境 OK。失败点在后面 |
| `error[C901]` | ruff 规则码：McCabe / mccabe |
| `_build_csvs` is too complex **(12 > 10)** | 实测 12，门槛 10 |
| `--> app/services/sync_uac.py:310:5` | 箭头指 **`def` 那一行**，不是某一行逻辑写错 |
| `Found 1 error` / exit 1 | 整个 job 因这一条 lint 红 |

CI 链：PR 打向 `dev` → `feature.yaml` → `ci-test.yaml` → `uv run scripts/run-test`。脚本第一句是：

```bash
ruff check app/ && pytest ...
```

`&&` 左边红了，右边 pytest 根本不跑。你在测试里找 Salesforce 映射，找错地方。

规则从哪来：`pyproject.toml` 里 `[tool.ruff.lint] select` 有 `"C90"`。**没有** `[tool.ruff.lint.mccabe] max-complexity`，所以默认就是 10。`C90` 不在 `fixable` 里：`ruff check --fix` **救不了 C901**。

> 普通人的看法：函数太长了，把注释删了就好。
> 资深工程师的洞察：先问规则码属哪一族，再问数字对不对得上。对上了再动手。

> 📌 **本节要点**：规则码决定你去数分支，还是去查业务对象。

## 2. 深挖一：McCabe，控制流图上的路

1976 年，Thomas McCabe 把程序当成有向图：语句是结点，`if` / `for` / `and` 是决策点。**圈复杂度 = 线性无关路径数**。手算公式：

```
CC = 1 + 决策点个数
```

算这些：`if` / `elif` / `for` / `while` / `except`，以及 **`and` / `or` 每个 +1**，三元、推导式里的 `if`。**不算行数。** 200 行顺序赋值可以是 1；30 行全是分支可以是 15。

嵌套 `def` 在 ruff / mccabe 里 **单独计分**。`_build_csvs` 里的 `_finalize` 不进父函数的 12。

#41 把 Study Application 的过滤塞进编排函数，多了两个决策点：

```python
if not _should_emit_study_application(...):   # +1
    if applicant.get('refnum') not in (None, ''):  # +1
```

父函数本来就在 10 附近（Account / ContactPoint / Application / Preference 四条编排腰）。10 + 2 = **12**。跟 CI 对得上。

匹配器本身在 `_should_emit_study_application` / `_partition_mq_preferences` 里，那两个函数各自 < 10。**爆的是中枢又吞了一层业务 if。**

|看起来像|实际是|
|---|---|
|函数太长|独立路径太多|
|第 310 行写错了|计分从 `def` 开始算全身|
|应该关 C90|门禁就是为了阻止编排函数无限长|

面试拿分点：面试官问「为什么 12 不是函数太长」— 用上面这张表答。

> 路多的函数，测试也多。门禁算的是路，不是页面长度。

## 3. 深挖二：编排和策略不要住同一个脑袋

Parnas 的 information hiding：一个模块只暴露一个稳定的问题。`_build_csvs` 的问题是：**这一批要产出哪几份 CSV**。它不应该知道「为什么某个 applicant 不要 Study Application」。

|层|职责|这次谁上|
|---|---|---|
|策略|MQ 课程族 / 是否 emit / 取消仍发|`_should_emit_*`、`_partition_*`|
|序列化|把行变成带 tag 的 Bulk CSV|`_add_study_application_csv`、`_add_preference_csvs`|
|编排|按 entity 决定调谁、汇总统计|`_build_csvs`|

#41 的错误不是策略写错。策略已经抽出去了。错的是 **把策略的循环仍留在编排函数里**，父函数仍要为那两个 `if` 付费。

这个仓库上个月碰过同一道墙：`_build_csvs` 曾经 **14 > 10**，做法是抽 AMIS overlay helper，不是 `noqa`，不是改 10。同一条河。

抽出之后：

```python
if ENTITY_APPLICATION in entities:
    study_skipped_no_mq = _add_study_application_csv(
        csvs, applicants, library, category, pref_refnums, mq_refnums,
    )
```

父函数只剩一个 `if`。路从 12 回到 7 左右。Salesforce 行为不变：CSV 键、skip 计数、Cancelled 仍 emit。

本机证据：

```
uv run ruff check app/services/sync_uac.py
# All checks passed!

uv run pytest tests/test_services/test_sync_uac.py \
  tests/test_services/test_sync_uac_masking.py \
  tests/test_services/test_uac_transforms.py -q --tb=short
# 71 passed in 0.26s
```

> 策略跑出去了，编排还把循环留着— 信息隐藏只做了一半。

## 4. 深挖三：三种修法，为什么只选一个

|做法|花费|代价|何时能用|
|---|---|---|---|
| `# noqa: C901` | 一行 | 门禁对这个函数永久失效 | 生成器、一次性脚本、确认不再长 |
| `max-complexity = 12` | 改 toml | 全仓库都能堆到 12 | 基线都在 11，且你能解释为什么 |
| **抽 helper** | 一次重命名 | 多一个符号，测试仍走旧入口 | 新加的决策本身就是一块完整业务 |

这仓库的 `scripts/render.py` 用过 `noqa:C901`。那是脚本。`_build_csvs` 是 **每次 UAC 同步都要走的编排中枢**。新规则是我们这几天加的，不是历史包袱。

抬阈值的误解是：「12 跟 10 差不多」。差的不是 2，是 **「再加 AMIS / 再加一个 entity，谁来拆」**。门禁存在，是因为这个函数已经是中枢。

`ruff` 把 C90 放进 `select`、又不放进 `fixable`，是有意的：**这是设计压力，不是格式化。** 格式化可以自动改引号；路径数只能人拆。

部落知识 → 工程产物：「别把 `_build_csvs` 再堆胖」如果只留在 code review 里说一次，下一个 PR 还会堆。写进 `select = ["C90"]`，它就成为每个 PR 的契约。

> 不能 `--fix` 的 lint，才是在问你设计。

## 5. 三张图放一起

|概念|根问题|这次的答|
|---|---|---|
| McCabe | 路多，测试面就大 | 12 = 旧编排 + 2 个新 if |
| 编排 vs 策略 | 中枢不该知道为什么 skip | 循环跑进 `_add_*_csv` |
| 合并契约 | 门禁是压力还是装饰 | 抽，不 `noqa`，不抬 10 |

修完后的 commit：`438b8ad`，推进 #41。

## 立刻可以做的事

1. 下次 CI 红，先读规则码。`C901` 去数 `if`；`F401` 去删 import；业务异常才去查对象。
2. 对着爆的函数手算一遍 `1 + 决策点`。数对上了，你才知道拆哪一块。
3. 新规则进已有 helper 族：`_should_*` / `_add_*`。别把循环留在编排函数里再付一次路径费。
4. 别把 `max-complexity` 改成刚好能过的那个数。那是在拆掉门禁。

*行数是纸。路径才是账。*
