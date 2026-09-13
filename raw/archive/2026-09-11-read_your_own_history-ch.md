title
读懂自己的提交历史：git log、git diff 与版本范围详解（中文）
content

# 读懂自己的提交历史：`git log`、`git diff` 与版本范围实战详解

> *"Your branch is ahead of 'origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade' by 18 commits."*

每个工程师都见过这行输出。18 个提交躺在本地，即将推送给别人 review。推送之前，你需要先回答一个问题：**这里面到底有什么？**

本文从这一行 `git status` 出发，一路深入底层机制——版本范围（revision range）、各种 diff 输出格式，以及那几个能把"18 个提交"变成一段能写进 PR 描述的清晰叙述的命令。

---

## 一、"ahead by 18 commits" 到底是什么意思

`git status` **并没有联网**。它比较的是两个本地引用：

```
refs/heads/DATAPLATCORE-1265-airflow-2.11.2-upgrade ← 你的分支
refs/remotes/origin/DATAPLATCORE-1265-... ← 你本地缓存的远端快照
```

第二个叫**远程跟踪分支（remote-tracking branch）**：它只是一个本地文件，记录了你上次与远端通信时远端所在的位置。然后 Git 遍历提交图，统计"从一边可达、从另一边不可达"的提交数量。

> ⚠️ **坑点：** "ahead by 18，工作区干净"**并不代表远端没有变化**。如果同事一小时前推送了代码而你没有 fetch，Git 完全不知情。先执行 `git fetch`——它只更新远程跟踪引用，不动你的工作区。之后这个 ahead/behind 数字才可信。

```bash
git fetch # 刷新本地缓存的远端引用
git status -sb # 简短分支行：## branch...origin/branch [ahead 18]
```

> 🎉 **趣闻：** `git fetch` 是极少数"几乎永远安全"的网络命令。它只写 `refs/remotes/*` 和对象库，不碰工作区、暂存区和本地分支。真正危险的是 `git pull`，因为它是 `fetch` + `merge`（或 `rebase`）粘在一起。

---

## 二、`@{u}`：别再手打那个长分支名了

`DATAPLATCORE-1265-airflow-2.11.2-upgrade` 打起来很累。Git 提供了简写：

| 简写 | 含义 |
|---|---|
| `@{u}` / `@{upstream}` | 当前分支跟踪的上游分支 |
| `@{push}` | `git push` 会推到的位置（三角工作流下与上游不同）|
| `@` | `HEAD` 的裸简写 |
| `HEAD~3` | 沿第一父提交回退三个 |
| `HEAD^2` | 合并提交的**第二个父提交** |
| `HEAD@{2}` | `HEAD` 两次移动之前指向的位置（reflog，不是提交图！）|

`@{u}` 是通过配置解析出来的：

```bash
git config --get branch.DATAPLATCORE-1265-airflow-2.11.2-upgrade.remote # origin
git config --get branch.DATAPLATCORE-1265-airflow-2.11.2-upgrade.merge # refs/heads/...
```

若缺失，`@{u}` 会报 *"no upstream configured"*，此时必须写全引用名。

> 🎉 **趣闻：** `~` 和 `^` 很容易混。`^` 是"选哪个父提交"（`HEAD^2` = 第二父）；`~` 是"往回走，永远走第一父"（`HEAD~2` = 祖父）。所以 `HEAD~2 == HEAD^^`，但 `HEAD^2 ≠ HEAD~2`。在 Windows `cmd.exe` 里 `^` 是转义字符，这就是 `HEAD^^^` 在那里莫名失效的原因。

> 🎉 **趣闻：** `@{...}` 这套 reflog 语法支持日期形式：`git log master@{yesterday}`、`HEAD@{2.days.ago}`，问的是"这个引用当时指向哪里"。周二那次搞坏的 rebase，就是靠它救回来的。

---

## 三、版本范围是集合运算，不是区间

这是理解 Git 最有价值的心智模型。`A..B` **不是**线性意义上的"A 到 B 之间的提交"，它是这个式子的简写：

```
^A B → { B 可达的提交 } 减去 { A 可达的提交 }
```

`^` 前缀表示"排除从这里可达的一切"。所以下面三条完全等价：

```bash
git log @{u}..HEAD
git log HEAD ^@{u}
git log ^@{u} HEAD
```

既然是集合运算，就可以自由组合——多个排除项、多个端点：

```bash
git log HEAD ^main ^release/2.10 # 在我分支上，但不在 main、也不在 release 上
git log v2.11.2 v2.11.1 ^v2.10.0 # 两个 tag 的并集减去一个更老的 tag
```

> 🎉 **趣闻：** 因为是 DAG 上的集合运算，`A..B` 完全可能返回**时间上比 A 更早**的提交。可达性和时间戳毫无关系。这就是"两个版本之间有哪些提交"这个问题远比看起来微妙的原因。

### `...` 三点陷阱

三个点在 `git log` 和 `git diff` 里含义**完全不同**，老手也常踩：

| 命令 | 含义 |
|---|---|
| `git log A...B` | **对称差集**——在任一边、但不在两边都有的提交 |
| `git diff A...B` | 从 A 与 B 的**合并基点（merge base）**到 B 的差异 |
| `git diff A..B` | 两个端点的直接比较（等同于 `git diff A B`）|

所以在 `log` 里 `...` 比 `..` **更宽**；在 `diff` 里 `...` 比 `..` **更窄**——它会忽略分叉之后 A 上发生的一切。做代码审查时，你几乎总是想要 `git diff main...HEAD`：问的是"**我**改了什么"，而不是"两个分支头有什么不同"。

Git 2.30 起有了明确写法，推荐优先使用，因为不会被误读：

```bash
git diff --merge-base main HEAD
```

> 🎉 **趣闻：** GitHub 上 PR 的 "Files changed" 页面用的就是三点（基于 merge base）的 diff。这就是为什么目标分支已经跑得很远，PR 看起来却依然干净——也是为什么"GitHub 上是绿的"并不保证能干净合并。

---

## 四、五个缩放级别

同一个范围，逐级放大。用能回答你问题的最小那一级就够。

### 第 1 级——只看清单

```bash
git log --oneline @{u}..HEAD
git log --oneline --graph @{u}..HEAD # 有合并提交时加上拓扑图
git rev-list --count @{u}..HEAD # → 18
```

> 🎉 **趣闻：** `--graph` 会**隐式打开** `--topo-order`，保证父提交不会排在子提交之前。不加它时，`git log` 按**提交者日期**排序，在 rebase 过的分支上看起来会很乱。

### 第 2 级——每个提交动了哪些文件

```bash
git log --stat @{u}..HEAD # 每个提交的直方图
git log --name-status --oneline @{u}..HEAD # 状态字母，紧凑
git log --numstat --oneline @{u}..HEAD # 机器可解析：新增 删除 路径
```

状态字母：`A` 新增、`M` 修改、`D` 删除、`R` 重命名、`C` 复制、`T` 类型变化（如普通文件变符号链接）。

> 🎉 **趣闻：** `--stat` 里的 `+++---` 长条是**按终端宽度缩放**的，不是真实数字。显示 `5 +++--` 的文件可能是 3 增 2 删，也可能是 300 增 200 删。永远不要解析 `--stat`，要用 `--numstat`——那是原始数字、Tab 分隔。

### 第 3 级——完整补丁

```bash
git log -p @{u}..HEAD
git log -p --reverse @{u}..HEAD # 从旧到新——读起来像一段叙事
git log -p @{u}..HEAD -- requirements.txt # 限定单个路径
```

`--reverse` 被严重低估。按编写顺序读 18 个提交，比倒着读轻松得多。

### 第 4 级——聚合视图（18 个提交当作一次改动）

这才是 reviewer 实际看到的东西：

```bash
git diff --stat @{u}..HEAD # 摘要
git diff --name-status @{u}..HEAD # 去重后的文件清单
git diff --shortstat @{u}..HEAD # 一行：N files changed, X insertions(+), Y deletions(-)
git diff @{u}..HEAD # 全量
```

区别很重要：如果你在第 3 个提交里新建了一个文件、又在第 14 个提交里删掉了它，`git log --stat` 会显示两次事件，而 `git diff` 什么都不显示。前者是**过程churn**，后者是**净效果**。

### 第 5 级——单个提交的细节

```bash
git show <sha> # 提交信息 + 完整 diff
git show --stat <sha> # 提交信息 + 文件清单
git show <sha> -- path/to/file # 只看某个文件的改动
git show <sha>:path/to/file # 该提交下这个文件的**内容**（不是 diff）
```

> ⚠️ **合并提交的坑：** `git show <merge-sha>` 经常只打印一个头部、**完全没有 diff**。因为默认显示的是**组合 diff（`--cc`）**，它只展示与**所有**父提交都不同的 hunk——也就是只展示冲突解决部分。一个干净的合并本来就没什么可显示。想看内容请用 `git show -m <sha>`（每个父提交一份 diff），或 `git show --first-parent <sha>`（"这次合并给我分支带来了什么"）。

> 🎉 **趣闻：** 注意那两种冒号语法。`git show A -- file` 是"提交 A 中 *file* 的差异"；`git show A:file` 是"提交 A 中 file 路径上的那个 *blob*"。一个字符之差，输出完全不同。后者是不 checkout 就查看历史版本内容的标准做法。

---

## 五、值得掌握的进阶工具

### 镐头（pickaxe）：这行代码什么时候出现的？

```bash
git log -S 'apache-airflow==' --oneline # 该字符串出现次数发生变化的提交
git log -S 'OLLAMA_HOST' --oneline -- . # 这个环境变量何时引入/移除？
git log -G 'ollama_(url|host)' --oneline # 在 diff 文本中做正则匹配
```

`-S` 统计出现次数，只报告数量发生变化的提交；`-G` 用正则匹配 diff 文本。找"新增或删除"用 `-S` 更精准，找"移动或重排版"用 `-G`。

> 🎉 **趣闻：** 这名字是字面意思——Git 文档就把 `-S` 叫做 "the pickaxe"（镐头），因为你是在历史的岩层里挖矿脉。它从 Git 极早期就存在，至今仍是回答"这是谁引入的"最快的手段——尤其当 `git blame` 只显示"最后一个改了缩进的人"时。

### 追踪单个函数的演变

```bash
git log -L :parse_dag:dags/loader.py # 按函数名追踪
git log -L 250,270:blogs_client.py # 按行号区间追踪
```

Git 会自己识别函数边界（用的是和 diff hunk 头部相同的启发式规则），把每一次触碰它的补丁都列出来。

### 我这次 rebase 改了东西吗？`range-diff`

在需要反复 rebase 到 `main` 的长期升级分支上，这个命令不可或缺：

```bash
git range-diff @{u}...HEAD # 比较同一系列的两个版本
git range-diff main old-tip new-tip # 显式写法
```

它是**"diff 的 diff"**：把两个版本的提交系列两两配对，展示每个补丁本身发生了什么变化。如果这次 rebase 本应是纯机械操作，`range-diff` 能证明这一点。

> 🎉 **趣闻：** `range-diff`（Git 2.19，2018）源自 Git 邮件列表的工作流——维护者要通过邮件审查补丁系列 v1 → v2 → v3。它用的配对引擎和 `git cherry` 相同，即 **patch-id**：把 diff 归一化掉空白和行号之后的哈希。这就是为什么一个 cherry-pick 过来的提交虽然 SHA 完全不同，却仍能被识别出来。

```bash
git log --cherry-mark --oneline @{u}...HEAD # = 上游已有，+ 仅本地有
git cherry -v @{u} # - 等价补丁已存在，+ 不存在
```

### 重命名检测其实是"猜"的（但很好用）

Git 存的是**快照**，不是操作。任何地方都没有记录"重命名"。你看到的 `R096 old/path.py → new/path.py`，是 Git 在**显示时**通过内容相似度算出来的，默认阈值 50%。

```bash
git log --stat -M @{u}..HEAD # 重命名检测（现代 Git 默认开启）
git log --stat -M20% @{u}..HEAD # 更激进
git log --stat -C @{u}..HEAD # 同时检测复制
git log --follow -- path/to/file.py # 跨重命名追踪单个文件
```

`R100` 表示纯重命名、内容完全一致。`--follow` 只支持恰好一个路径——它是后来打的补丁，不是一等公民特性。

> 🎉 **趣闻：** 正是这个设计，让 Git 在处理"我把一个函数从一个文件挪到另一个文件"时，比那些显式记录重命名的版本控制系统优雅得多。同时也正因为没有元数据可依，当你在同一个提交里既重命名又大改内容时，`git log --follow` 就会跟丢。

### 格式化，以及那两个日期

```bash
git log --pretty=format:'%h %ad %an %s' --date=short @{u}..HEAD
git log --pretty=fuller @{u}..HEAD # 同时显示 AuthorDate 和 CommitDate
git shortlog -sn @{u}..HEAD # 按作者分组统计提交数
```

常用占位符：`%H` 完整哈希、`%h` 缩写、`%an`/`%ae` 作者名/邮箱、`%ad` 作者日期、`%cd` 提交者日期、`%s` 标题、`%b` 正文、`%d` 引用装饰、`%C(auto)` 自动着色。

> 🎉 **趣闻：** 每个提交都带**两个身份**和**两个时间戳**：author 和 committer。`git rebase` 和 `git cherry-pick` 会保留作者日期、重置提交者日期。这就是为什么刚 rebase 完的分支里显示着"三周前"的提交，而它们技术上是五分钟前才产生的；也是为什么 `git log`（按提交者日期排序）和 `git log --date-order` 有时给出的顺序不一致。

> 🎉 **趣闻：** `--oneline` 里的缩写 SHA 并非固定 7 位。自 Git 2.11 起，`core.abbrev` 默认为 `auto`，会根据仓库对象数量决定前缀长度，以降低碰撞概率。Linux 内核现在需要 12 位。7 位这个默认值，只对小仓库合适过。

---

## 六、实战：审查一个 Airflow 升级分支

具体到 `DATAPLATCORE-1265-airflow-2.11.2-upgrade`，实用顺序如下：

```bash
# 0. 先让计数变得可信
git fetch

# 1. 净影响面——只动了版本锁定，还是渗进了 DAG？
git diff --stat @{u}..HEAD

# 2. reviewer 会打开的确切文件集合
git diff --name-status @{u}..HEAD

# 3. 按叙事顺序，用来写 PR 描述
git log --oneline --reverse @{u}..HEAD

# 4. 高风险部分，看全量
git diff @{u}..HEAD -- requirements.txt constraints.txt Dockerfile

# 5. 那个 provider 的版本锁定究竟是哪次改的？
git log -S 'apache-airflow-providers-google' -p @{u}..HEAD

# 6. 有东西偷偷溜进 dags 目录吗？
git log --oneline @{u}..HEAD -- dags/

# 7. 下次 rebase 到 main 之后，证明补丁没变
git range-diff @{u}...HEAD
```

第 1 步是单条命令里价值最高的。在升级分支上，一个只涉及 constraints 和 Dockerfile 的 `--stat`，和一个顺手重写了十二个 DAG 的 `--stat`，是完全不同性质的 review。

---

## 七、交互式浏览

不想打字、想点鼠标的时候：

```bash
gitk @{u}..HEAD # 最早的 GUI，随 Git 一起分发
tig @{u}..HEAD # 终端 UI，vim 风格按键
git log --oneline | fzf --preview 'git show --color=always {1}' # 简易版 tig
```

> 🎉 **趣闻：** `gitk` 的作者是 **Paul Mackerras**——同一个人写了 Linux 的 PPP 守护进程、维护过 PowerPC 内核移植。他在 2005 年 4 月 Git 首次发布后的几周内，用 Tcl/Tk 写出了 gitk。二十年后它仍然随官方 Git 分发，也仍然长着一副 Tcl/Tk 的样子。至于 `tig`，它就是 "git" 倒过来拼。

---

## 八、速查表

| 问题 | 命令 |
|---|---|
| 有多少未推送的提交？ | `git rev-list --count @{u}..HEAD` |
| 都是哪些提交？ | `git log --oneline @{u}..HEAD` |
| 每个提交动了哪些文件？ | `git log --name-status --oneline @{u}..HEAD` |
| 一共动了哪些文件？ | `git diff --name-status @{u}..HEAD` |
| 这次改动有多大？ | `git diff --shortstat @{u}..HEAD` |
| 完整聚合 diff（reviewer 视角）| `git diff @{u}..HEAD` |
| 按叙事顺序通读 | `git log -p --reverse @{u}..HEAD` |
| 单个提交的细节 | `git show <sha>` |
| 合并提交的真实 diff | `git show -m <sha>` |
| 历史版本的文件内容 | `git show <sha>:path` |
| 这个字符串是谁引入的？ | `git log -S 'string' --oneline` |
| 单个函数的演变史 | `git log -L :func:file` |
| rebase 有没有改动补丁？ | `git range-diff @{u}...HEAD` |
| 远端也动了，两边都看 | `git log --oneline --left-right @{u}...HEAD` |

---

## 九、最后三条冷知识

- **`git rev-list` 是引擎。** `git log` 只是同一套图遍历逻辑的 porcelain 封装，外加 diff 机制。凡是 `log` 能筛选的，`rev-list` 都能筛选——这也是脚本和 Git 自身测试套件里到处都是 `rev-list` 的原因。
- **空树有一个著名的哈希：** `4b825dc642cb6eb9a060e54bf8d69288fbee4904`。与它做 diff，就能把任意提交看成"纯新增"，这是展示无父提交的根提交"差异"的经典技巧。（或者直接 `git show --root <sha>`。）
- **SHA-1 已经不是你以为的那个 SHA-1 了。** 2017 年 SHAttered 碰撞攻击之后，Git 2.13 引入了加固版 SHA-1 实现，能检测碰撞尝试并拒绝哈希。Git 也支持完整的 SHA-256 对象格式，但出于互操作性，你日常接触的几乎每个仓库仍然是 SHA-1。

---

*写给那些接手了一个分支、一个工单号和一股隐隐不安的工程师。先 `git fetch`，然后 `git diff --stat @{u}..HEAD`。从这里开始。*