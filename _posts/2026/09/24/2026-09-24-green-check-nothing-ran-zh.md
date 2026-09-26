---
title: 你的发布检查，验证的是事实还是空结果？
header:
    image: /assets/images/bg_raw/BingWallpaper (16).jpg
date: 2026-09-24
tags:
 - git
 - release-engineering
 - dependency-management
 - airflow
 - ci
permalink: /blogs/tech/zh/green-check-nothing-ran
layout: single
category: tech
---
> "空谈无用，给我看代码。" — Linus Torvalds

# 你的发布检查，验证的是事实还是空结果？

*两条看似只读的命令，足以暴露依赖、分支和自动化之间最危险的盲区。*

你的发布检查里，有多少个“通过”，其实只是“什么都没查到”？

本文给你一套可在一分钟内执行的检查顺序：先确认依赖的运行时事实，再确认分支拓扑，最后识别那些退出码为零、结论却完全不成立的假绿灯。

先跑这一组。把 `main` 替换成你的发布分支；如果团队确实采用 `master`/`develop`，再使用对应名称。

```bash
git fetch --all --prune
git rev-list --left-right --count origin/main...origin/develop
git log --oneline --no-merges origin/develop..origin/main
git diff --stat origin/develop origin/main
```

这不是发布批准按钮。它只是在回答：远端快照是否新鲜、两条线各自欠了什么提交、以及它们最终内容到底差了什么。

> **空结果不是通过；空结果首先意味着你要验证检查是否真的覆盖了目标。**

| 看到的信号 | 它实际证明什么 | 它没有证明什么 | 下一步 |
|---|---|---|---|
| `git grep` 无输出 | 当前匹配模式没有命中 | 项目没有该依赖 | 扩大搜索范围或解析配置文件 |
| `rev-list --count` 为 `0` | 某一侧没有对方独有的提交 | 两个分支的文件内容相同 | 再看 `git diff` |
| pre-commit 全部 `Skipped` | 没有文件匹配钩子作用域 | 代码质量没有问题 | 确认暂存区，或显式跑全量检查 |
| CI 绿 | 当前被执行的检查通过 | 检查验证了你关心的目标 | 看检查范围、环境和排除规则 |

这张表是本文最重要的结论：发布工程里最危险的失败，往往不是报错，而是系统安静地回答了一个比你问题更小的问题。

## 两条命令，问的是两种不同的真相

```bash
git grep "apache-airflow = " pyproject.toml
git rev-list --count origin/main..origin/develop && \
git rev-list --count origin/develop..origin/main
```

第一条想问的是：项目**声明**了怎样的 Airflow 版本约束？第二条想问的是：发布线和集成线分别有多少对方尚未拥有的提交？

它们表面无关，实际都属于发布工程：一个检查依赖治理，一个检查交付历史。在使用 Poetry、`pyproject.toml` 和长期集成分支的仓库里，这通常就是发布前巡检的一部分。

但先把边界说死。

`pyproject.toml` 是声明层，不是运行时真相。它表达“我允许解析到什么版本范围”；锁文件记录某次解析得到的精确依赖树；而真正运行的环境还可能来自镜像、托管平台配置或其他安装流程。想确认当前环境装了什么，应在那个环境里查询，例如：

```bash
poetry show apache-airflow
# 或在目标 Python 环境中
python -c "import airflow; print(airflow.__version__)"
```

同样，`rev-list --count` 是体温计，不是 CT。它数提交，不解释提交内容、冲突风险、补丁是否等价，更不会告诉你远端引用是不是过期。

## 为什么“查不到”比“查到一行”更值得紧张

`git grep "apache-airflow = " pyproject.toml` 的问题不在 Git，而在这个模式太具体。它假设依赖恰好以带空格的单行 TOML 键值对出现。

以下任意一种写法，都可能让它无声漏报：依赖写成表格式；等号两侧风格不同；声明位于分组依赖；仓库是多模块结构；真正约束在 requirements、镜像构建文件或 Airflow 的 constraints 文件中。

因此，`git grep` 适合做侦察，不适合充当配置解析器。先用它快速缩小范围，再用结构化方式确认：列出仓库中的配置文件、检查锁文件、核对部署入口。对 TOML 这类结构化文件，解析器比正则更可靠。

Airflow 场景尤其如此。Airflow 本体、Provider 包、Python 版本和官方 constraints 之间存在兼容关系。只盯住一个包的声明，容易获得一种“看起来锁住了”的安全感；真正需要管理的是完整可复现的组合。

反方观点也成立：对一个格式严格、文件位置固定的小仓库，一条精确 `git grep` 足够便宜，也足够快。问题不在于不能用文本搜索，而在于不能把“没有匹配”升级成“没有风险”。

## 双向计数不是仪式，它在区分领先和分叉

Git 的两点范围 `A..B` 表示“能从 B 到达、但不能从 A 到达的提交”。所以：

```bash
# develop 独有：待进入发布线的提交
git rev-list --count origin/main..origin/develop

# main 独有：可能未回灌的修复
git rev-list --count origin/develop..origin/main
```

只看第一条，你只能知道集成分支领先多少；看两个方向，才能区分两种完全不同的状态：

| main 独有 | develop 独有 | 拓扑含义 | 应该做什么 |
|---:|---:|---|---|
| 0 | 0 | 提交历史没有彼此独有部分 | 再用 `git diff` 确认内容层面 |
| 0 | 非 0 | develop 单向领先 | 评估发布内容 |
| 非 0 | 0 | 发布线有改动未回灌 | 先审查这些改动，常见于 hotfix |
| 非 0 | 非 0 | 两边分叉 | 不要只看数字；先看双方独有内容 |

更紧凑的写法是：

```bash
git fetch --all --prune
git rev-list --left-right --count origin/main...origin/develop
```

注意这里是**三点**。对于 `rev-list`，三点得到两侧独有提交的对称差；`--left-right` 才能把左、右两侧分别计数。两点范围本来就排除了左侧，给它加 `--left-right` 没有你想象中的双向信息。

这里藏着第一个反直觉点：同样的三点在 `git diff` 里不是“两边都看”。

```bash
# 看两个 tip 的最终净差异
git diff origin/main origin/develop

# 看 develop 从共同祖先开始引入了什么
git diff origin/main...origin/develop
```

`git diff A...B` 等价于比较 `merge-base(A, B)` 与 `B`。它适合回答“对方从分家以后带来了什么”；而两点 diff 适合回答“现在两边最终差什么”。前者用于理解来路，后者用于签字前确认结果。

**`log` 讲过程，`diff` 签字。**

## 计数说的是拓扑，不是内容

分支计数还有一个常被忽略的限制：Git 按提交对象的可达性计数，不按补丁内容计数。

一个修复如果从发布分支被 cherry-pick 到集成分支，会拥有不同的提交标识。于是它在内容上已经存在，在 `develop..main` 的拓扑计数里却仍可能出现。squash merge 和 rebase 也会制造同类现象。

需要排除这类“拓扑幽灵”时，用补丁等价性做交叉验证：

```bash
git log --oneline --no-merges --cherry-pick --right-only \
  origin/develop...origin/main

git cherry -v origin/develop origin/main
```

但也别把 `--no-merges` 当成绝对安全。合并提交中解决冲突时写下的代码，可能只存在于那个 merge commit 里；过滤所有 merge commit，就可能漏掉这部分内容。因此要补一眼：

```bash
git log --oneline --merges origin/develop..origin/main
git diff --stat origin/develop origin/main
```

这就是为什么“有多少提交没回灌”不是一个可以脱离内容直接回答的问题。数量能排序优先级，不能代替审查。

## 读操作和写操作之间，必须留一段可撤退空间

接下来是这类巡检最容易从“理解历史”滑向“改坏历史”的地方。

`git reset --hard origin/develop` 不是同步命令，它会移动当前分支、重置暂存区，并覆盖工作区中已追踪文件的未提交修改。它通常不会删除未追踪或被忽略文件，但这并不让它变得温和。已提交的内容通常还能通过 reflog 找回；从未暂存过的工作区修改，Git 未必有能力恢复。

如果你的真实意图是“把本地分支跟上目标分支”，先区分场景：

- 想保留自己的提交：使用 `git rebase` 或 `git merge --ff-only`，让无法安全前进的情况明确失败。
- 想丢弃本地状态：先保存可恢复点，再执行破坏性操作。
- 只想看看另一个分支：使用临时 worktree 或 detached checkout，不要重置正在工作的分支。

同一条原则也适用于合并。

```bash
git merge --no-commit --no-ff origin/main
```

`--no-commit` 不是 dry-run：它会修改工作区和暂存区，只是暂时不创建最终提交。再加 `--no-ff` 的原因是，快进合并不产生 merge commit，单独的 `--no-commit` 无法让快进停下来。

真正想预览时，先看这些只读信号：

```bash
git log --oneline --no-merges HEAD..origin/main
git diff --stat HEAD...origin/main
git diff HEAD...origin/main -- pyproject.toml poetry.lock
```

特别是依赖文件。升级分支与发布分支同时改动版本约束时，冲突不是纯技术问题：到底保留哪边的版本，取决于发布计划、兼容性评估和回滚策略。不要让“谁最后合并”替你做版本决策。

锁文件冲突也不应靠逐行猜测解决。先解决声明文件的语义冲突，再用项目当前依赖工具按已确认的声明重新生成锁文件，并在干净环境中验证安装结果。合并完成后，至少核对声明、锁定结果和运行时版本是否一致。

## 最会骗人的绿灯，常常来自默认作用域

`pre-commit run` 默认面向暂存区中的文件。刚执行过硬重置，或只是忘记 `git add` 时，它可能输出一片 `Skipped` 并以零退出码结束。

那不等于检查通过，只等于没有文件进入检查范围。

```bash
# 先确认默认检查到底有多少输入
git diff --cached --name-only

# 做仓库级基线检查时，显式指定范围
poetry run pre-commit run --all-files
```

对 Airflow 代码，静态格式检查还不是全部。DAG 的导入、Provider API 和运行时配置可能在 lint 全绿时仍然失败。因此更慢的 DAG 导入冒烟检查应放在 CI 或 pre-push 阶段，而不是把每次 commit 都拖到难以忍受。慢钩子逼迫开发者使用 `--no-verify`，最终会连快速检查一起失去价值。

同样的警惕适用于质量平台的排除规则。把文件排除出覆盖率统计，与把文件完全排除出静态分析，是两种不同的决定。前者改变一个指标的分母；后者可能让缺陷、漏洞和异味一起消失。若某类 DAG 文件难以按传统方式计覆盖率，可以讨论覆盖率排除，但不应因此放弃对它们的静态分析和导入验证。

我的立场是：**手工巡检可以存在，但不应成为长期控制点。**

最强的反对意见是，自动化门禁会制造误报、拖慢交付，并把团队锁进僵硬流程。这是真的。所以正确终点不是“把每条命令都变成阻塞”，而是先把关键不变量变得可观测：远端引用是否新鲜、发布分支是否存在未回灌修复、声明与运行时是否漂移、检查是否真的处理了文件。收集一段时间的信号后，再决定哪些值得升级为门禁。

## 原则：空结果必须有语义

一个检查系统只会看到它被喂进去的对象。空集合天然满足“没有失败项”这类断言，于是空结果很容易被误读成健康。

这个规律不只属于 Git：零个测试全部成功、零条告警全部处理、零个文件通过 lint，逻辑上都可能成立，工程上却未必有任何意义。

它的边界也很明确：有些检查的“无结果”确实是成功，例如查询明确不存在的资源，或确认某个目录没有待处理文件。区别不在于空不空，而在于工具是否把空结果定义成了你所关心的业务结论。

> 举一反三：当一个检查返回空、零或 `Skipped`，它是否能证明目标不存在，还是只证明你的观察窗口里没有样本？

下一次准备合并、升级或发布前，不妨挑一盏最绿的灯，追问一句：它到底检查了什么？
