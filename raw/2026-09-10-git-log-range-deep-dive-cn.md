title
git-log-range-deep-dive.zh-CN.md
content
---
title: "从一条 git log 命令讲透 Git 的范围语法"
subtitle: "master..origin/branch 到底在问什么?"
date: 2026-09-10
tags: [git, 版本控制, 工程实践, code-review]
lang: zh-CN
---

# 从一条 `git log` 命令讲透 Git 的范围语法

某天你在 review 一个 Airflow 升级分支，看到同事敲下这条命令：

```bash
git log master..origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade --oneline
```

看得懂，但说不清。本文就从这一条命令出发，把 Git 的**范围语法(revision range)** 彻底讲明白——包括 `..` 与 `...`、`^` 与 `--not`、以及那个让无数人翻车的坑：**`...` 在 `git log` 和 `git diff` 里语义完全不同**。

---

## 一句话结论

这条命令在问：

> **「`origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade` 这个远程分支上，有哪些提交是我本地 `master` 还没有的?」**

每个提交用一行显示。

---

## 一、逐段拆解

| 片段 | 含义 |
|---|---|
| `git log` | 按「可达性(reachability)」遍历提交图并输出提交列表 |
| `master` | 本地分支 `master` 所指向的提交(一个 commit-ish) |
| `..` | 双点范围操作符 |
| `origin/...upgrade` | 远程跟踪分支(remote-tracking branch)，即上次 `git fetch` 时抓下来的远端状态**快照** |
| `--oneline` | 等价于 `--pretty=oneline --abbrev-commit`，即「短 SHA + 提交标题」一行一条 |

分支名 `DATAPLATCORE-1265-airflow-2.11.2-upgrade` 本身没有语法含义，只是团队命名约定：**Jira ticket 号 + 任务描述**(把 Airflow 升到 2.11.2)。好的分支名让 `git log --oneline` 的输出自带上下文，这也是一种工程素养。

---

## 二、`..` 的精确语义

```
A..B ≡ B ^A ≡ B --not A
```

集合表达：**「从 B 可达的提交」减去「从 A 可达的提交」**。

图示：

```
D---E---F origin/DATAPLAT...-upgrade
/
A---B---C master
```

- `master..origin/...` → 输出 `F E D`(升级分支上的新工作)
- `origin/.....master` → 输出 `C`(master 上有、分支还没合并进来的东西)

**顺序反了结果完全不同**，这是最常见的误用。

三个关键点：

1. **这不是「diff」，而是「提交集合的差」。** 想看文件内容差异要用 `git diff`(而且要用三点，见第四节)。
2. **默认逆时序输出**(最新在最上面)，不是拓扑顺序。需要拓扑顺序加 `--topo-order`。
3. **若两者已完全合并，输出为空** —— 空结果本身就是有用信号。

---

## 三、深入一层：`^` 与 `--not`，才是真正的底层

`..` 只是语法糖。`git log` 的本质是「**从若干起点出发做图遍历**」：

- 不带前缀的 ref = **正向起点**(include)
- 带 `^` 前缀的 ref = **排除点**(exclude)，「从它可达的所有提交都别给我」

所以 `B ^A` 读作：从 B 开始往下走，凡是 A 也能走到的，全部剪掉。

验证：

```bash
git log --oneline master..origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade
git log --oneline origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade ^master
# 两者输出完全一致
```

**为什么要知道底层写法?** 因为 `^` 可以任意组合，`..` 不行：

```bash
# 「在 feature 上，但既不在 master 也不在 develop 上」的提交
git log --oneline feature ^master ^develop

# 「在 B 或 C 上，但不在 A 上」
git log --oneline B C ^A
```

`..` 只能表达「一减一」，`^` 能表达「多减多」。这是从「会用」到「懂」的分界线。

> **Shell 提示**：在某些 shell(尤其 zsh 的部分配置、Windows CMD)里 `^` 需要转义或加引号。写 `'^master'` 最稳妥，或者干脆用 `--not master`。

---

## 四、`...` 的两副面孔(最大的坑)

**同一个 `...` 符号，在 `git log` 和 `git diff` 里是两套语义。** 这是 Git 设计上公认的历史包袱。

### 4.1 `git log a...b` = 对称差(symmetric difference)

集合表达：`(a ∪ b) - (a ∩ b)`，即**两边各自独有的提交都列出来**。

等价底层写法：

```
a...b ≡ a b --not $(git merge-base --all a b)
```

```
D---E---F b
/
A---B---C a

git log a...b → C F E D (两边独有的全给)
git log a..b → F E D (只给 b 独有的)
```

配 `--left-right` 才真正好用：

```bash
git log --oneline --left-right --graph \
master...origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade
# < abc1234 只在 master 上
# > def5678 只在该分支上
```

### 4.2 `git diff a...b` = 「b 相对于 merge base 的内容差异」

等价于：

```bash
git diff $(git merge-base a b) b
```

即：**忽略 a 在分岔后的所有变化**，只看 b 这条线干了什么。

对比 `git diff a..b`(等同于 `git diff a b`)：那是**两个端点快照的直接对比**，会把「a 上新增的东西」显示成 b 里的「删除」——这通常不是你想要的。

### 4.3 实战结论(背下来)

```bash
# 想看「这个 PR 引入了哪些提交」—— log 用两点
git log --oneline master..origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade

# 想看「这个 PR 改了哪些代码」—— diff 用三点
git diff master...origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade

# 想看改了哪些文件 + 增删行数
git diff --stat master...origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade
```

**记忆口诀：`log` 用两点看提交，`diff` 用三点看代码。**

GitHub / GitLab 的 PR 页面展示的正是 `diff` 的三点语义——这就是为什么你在 PR 里看不到 master 上别人的改动。

---

## 五、输出为空说明什么

严格含义：**B 可达的提交集合 ⊆ A 可达的提交集合**。用 Git 术语说就是 **B 已经是 A 的祖先(ancestor)**，即 B 已被完全合并进 A。

对应的现实情况：

| 情况 | 说明 |
|---|---|
| B 已合并进 A | 最常见：PR 已 merge |
| A 与 B 指向同一提交 | 刚 fetch 完、完全同步 |
| B 比 A 旧 | 分支创建后没提交过新东西 |

**脚本里做条件判断，不要靠「log 输出空不空」**，用这两个更精确的工具：

```bash
# 退出码 0 = 是祖先(即已合并)，1 = 不是
git merge-base --is-ancestor \
origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade master
echo $?

# 或者数数量
test "$(git rev-list --count master..origin/DATAPLAT...upgrade)" -eq 0
```

> ⚠️ **重要陷阱**：空输出**不代表两边内容相同**。如果分支是通过 **squash merge** 或 **rebase** 进 master 的，SHA 全变了，`master..branch` 可能**非空**，但代码内容其实一模一样。
>
> **「提交集合」和「文件内容」是两个正交的维度。** 下一节展开。

---

## 六、为什么出现了「明明已经在 master 上」的提交

**根因**：Git 的提交身份是哈希(SHA-1/SHA-256)，而哈希覆盖了 **parent 指针、tree、作者、committer、时间戳、提交信息**。任何一项变了，SHA 就变了 —— **即使 diff 内容完全一致**。

所以「相同的改动」在 Git 眼里可能是两个毫无关系的提交对象。制造这种「双胞胎」的操作：

| 操作 | 发生了什么 |
|---|---|
| `cherry-pick` | 换了 parent → 新 SHA |
| `rebase` | 整条线重新播放 → 全部新 SHA |
| squash merge | N 个提交压成 1 个全新提交 |
| `git am` / patch 邮件流 | 从 diff 重建提交 |
| `--amend` / 改 commit message | 内容不变，SHA 变 |

### 6.1 解药：`--cherry-mark` / `--cherry-pick` / `--cherry`

Git 用 **patch-id**(对 diff 内容做规范化哈希，忽略行号偏移与上下文)来识别「等价提交」。

```bash
# 标记等价提交：= 表示两边都有(等价)，+ 表示真正独有
git log --oneline --left-right --cherry-mark master...origin/DATAPLAT...upgrade

# 直接过滤掉等价提交，只剩真正独有的
git log --oneline --left-right --cherry-pick master...origin/DATAPLAT...upgrade

# --cherry 是常用组合的简写 ≈ --right-only --cherry-mark --no-merges
git log --oneline --cherry master...origin/DATAPLAT...upgrade
```

注意：这些选项**只在三点对称差 `...` 下有意义**(需要两边都遍历才能配对)，跟两点 `..` 一起用没有效果。

### 6.2 patch-id 的局限(边界意识)

- **merge 提交没有 patch-id** → 要配 `--no-merges`
- cherry-pick 时**解决过冲突**导致内容不同 → patch-id 不匹配，仍算独有
- 空提交(无 diff)无法配对

### 6.3 另一条排查路径

```bash
# 按提交信息关键字全库搜
git log --oneline --all --grep='DATAPLATCORE-1265'

# 查某个提交存在于哪些分支上
git branch -a --contains <sha>

# 追溯 cherry-pick 来源(前提：当初用了 git cherry-pick -x)
git log --oneline --grep='cherry picked from'
```

**工程建议**：团队约定 `cherry-pick` 一律加 `-x`，它会在 commit message 里留下 `(cherry picked from commit <sha>)`，日后排查成本直接降一个数量级。

---

## 七、三个必须记住的坑

### 1. `origin/xxx` 是缓存，不是实时远端

远程跟踪分支只在 `git fetch` / `git pull` 时更新。不先 fetch，你看的是几天前的世界：

```bash
git fetch -p origin # -p / --prune 顺手清理已删除的远端分支
```

`-p` 很重要：远端分支被删了，本地 `origin/xxx` 不会自动消失，你可能在拿一个已经不存在的分支做比较。

### 2. `master` 用的是**本地** master

本地 master 若很旧，会多列出一堆「其实已经在远端 master 上」的提交。想跟远端比就明确写出来：

```bash
git log --oneline origin/master..origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade
```

**经验法则：做「分支进度」判断时，两端都用 `origin/` 前缀，把本地状态排除在外。**

### 3. 名字歧义与 `--` 分隔符

分支名里有 `.`(如 `2.11.2`)通常没问题，但如果同时存在同名的 tag 和 branch，Git 的解析优先级会让你困惑。消歧办法：

```bash
# 用全称 ref
git log --oneline refs/heads/master..refs/remotes/origin/DATAPLAT...upgrade

# 用 -- 明确「后面是路径，不是 ref」
git log --oneline master..origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade --
```

---

## 八、进阶变体：升级你的武器库

```bash
# 只数数量
git rev-list --count master..origin/DATAPLATCORE-1265-airflow-2.11.2-upgrade

# 一次拿到「领先/落后」两个数字(左边=落后，右边=领先)
git rev-list --left-right --count master...origin/DATAPLAT...upgrade

# 带图、带 ref 装饰
git log master..origin/...upgrade --oneline --graph --decorate

# 自定义格式：短SHA + 日期 + 作者 + 标题
git log master..origin/...upgrade --pretty='%h %ad %an %s' --date=short

# 顺带看每个提交改了哪些文件
git log master..origin/...upgrade --oneline --name-status

# 只看动了 Airflow 依赖的提交(路径过滤)
git log master..origin/...upgrade --oneline -- requirements.txt Dockerfile constraints.txt

# 忽略 merge 提交，看「真实」工作
git log master..origin/...upgrade --oneline --no-merges

# 与当前分支的上游做比较(通用写法，@{u} = @{upstream})
git log @{u}..HEAD --oneline # 我领先上游多少(待 push)
git log HEAD..@{u} --oneline # 我落后上游多少(待 pull)
```

### 值得写进 `~/.gitconfig` 的别名

```ini
[alias]
# 待 push / 待 pull
ahead = log --oneline @{u}..HEAD
behind = log --oneline HEAD..@{u}
# 领先/落后计数
ab = !git rev-list --left-right --count @{u}...HEAD
# 分支相对 master 引入了哪些提交
new = "!f() { git log --oneline --no-merges ${2:-origin/master}..$1; }; f"
# 这个分支改了哪些代码(PR 视图)
pr = "!f() { git diff --stat ${2:-origin/master}...$1; }; f"
# 过滤 cherry-pick 重复
real = "!f() { git log --oneline --left-right --cherry-pick --no-merges ${2:-origin/master}...$1; }; f"
```

---

## 九、典型使用场景

1. **Code review 前**：确认这个升级分支到底引入了哪几个提交，先看骨架再看代码。
2. **写 PR 描述 / release note**：`git log --oneline --no-merges base..head` 的输出稍加整理就能用。
3. **判断是否需要 rebase**：跑反向 `origin/...upgrade..origin/master`，非空说明分支落后于主线。
4. **CI 排错**：确认某个修复提交是否真的在分支上(配 `--cherry-pick` 避免被 rebase 骗)。
5. **发版前双检**：`git rev-list --left-right --count origin/master...origin/release` 一眼看清双向差距。

---

## 十、自测清单：能答出来就算出师

| # | 问题 | 答案 |
|---|---|---|
| 1 | `A..B` 的等价底层写法? | `B ^A` / `B --not A`；`^` 可多重组合，`..` 不能 |
| 2 | 输出为空说明什么? | B 可达的提交全被 A 包含，即 B 已是 A 的祖先。但**不代表内容相同**(squash/rebase 场景) |
| 3 | `git log a...b` 与 `git diff a...b` 语义相同吗? | **不同**。log 是对称差；diff 是「b 相对 merge base」。log 两点、diff 三点 |
| 4 | 为什么出现了明明已在 master 的提交? | cherry-pick / rebase / squash 产生了新 SHA。用 `--cherry-pick`(基于 patch-id)过滤 |
| 5 | `--oneline` 的短 SHA 会重复吗? | 理论上可能；Git 按仓库对象规模自动加长以保证唯一，也可用 `core.abbrev` 固定 |

---

## 小结

- `..` = 差集，`...`(在 log 里) = 对称差，底层都是 `^` / `--not` 的图遍历
- **log 两点，diff 三点** —— 一句话避开最大的坑
- 提交身份 = 哈希，**内容相同 ≠ 提交相同**；`--cherry-pick` 是 patch-id 层面的解药
- 动手前永远先 `git fetch -p origin`，否则结论再漂亮也是基于过期缓存

把 Git 当成一张有向无环图，把这些命令当成图查询语言，很多困惑会瞬间消解。

---

## 附录：顺手记一笔 —— 编辑器里删到文件末尾

排查完 Git，回到编辑器继续干活。在 LazyVim(以及任何 Vim / Neovim)里，把光标放在起始行，Normal 模式按：

```
dG
```

`d` 是删除操作符，`G` 跳到最后一行，组合起来就是**从当前行删到文件末尾**(按行删除)。

几个变体：

| 命令 | 作用 |
|---|---|
| `dG` | 当前行 → 文件末尾 |
| `:.,$d` | Ex 命令写法，同上 |
| `VG` 然后 `d` | 想先看到高亮选区再删 |
| `dgg` | 当前行 → 文件开头 |
| `d}` | 删到当前段落/块结尾 |
| `D` 或 `d$` | 只删到**行尾**，保留该行 |
| `"_dG` | 删除但不污染无名寄存器(黑洞寄存器) |

删错了 `u` 撤销。顺带一提，`d` + 动作 的组合思路和 Git 的范围语法有点异曲同工：**都是「操作符 + 范围」的正交设计**，学会一个维度就能自由组合。
