---
title: 为什么我明明写了 .gitignore，文件还是被 Git 提交了？
header:
    image: /assets/images/bg_raw/BingWallpaper (5).jpg
date: 2026-09-14
tags:
 - git
 - gitignore
 - debugging
 - version-control
 - cli
permalink: /blogs/tech/zh/gitignore-tracked-files-debugging
layout: single
category: tech
---
> “Git 已跟踪的文件不受影响。”—— Git 官方文档 `gitignore(5)`

# 为什么我明明写了 .gitignore，文件还是被 Git 提交了？

*别急着继续改规则；先确认文件是否已经进入 Git 的索引。*

打开仓库，把下面的路径换成那个“不听话”的文件，然后运行：

```bash
git ls-files --error-unmatch scripts/report.py
```

我赌它会立刻把问题分成两类：输出路径，说明文件已经被跟踪；报错，说明 Git 的索引里没有它。

读完这篇，你会得到一套可重复执行的排障流程：确认仓库上下文，判断 tracked / untracked，定位命中的 ignore 规则，再选择不会误伤其他仓库或协作者的修复方式。

真正反直觉的地方在这里：`.gitignore` 不是“禁止提交清单”。它是 Git 在发现未跟踪文件时使用的筛选规则。文件一旦进入索引，后来补上的 ignore 规则不会把它自动赶出去。

**决定处理方式的不是 `.gitignore` 里写了什么，而是文件是否已经进入索引。**

## `.gitignore` 管的是候选文件，不是既有成员

可以把 Git 的索引理解成一份已经登记的名单。

未跟踪文件还站在门外。Git 扫描工作区时，会参考 `.gitignore`，决定哪些文件不必出现在默认的 `git status` 中，也不应被普通的 `git add` 纳入索引。

tracked 文件已经在名单里。它之后发生的修改仍会被 Git 观察到；你再把它的名字写进 `.gitignore`，相当于给门卫递了一张“以后别让这个人进来”的纸条，可这个人早就在楼里了。

因此，排查 ignore 问题时，第一个问题不该是“哪条规则没生效”，而应该是：

> 这个文件究竟是 tracked，还是 untracked？

下面这张表可以直接作为快速判断卡：

| 证据 | 看到的结果 | 可以确定什么 | 下一步 |
|---|---|---|---|
| `git ls-files --error-unmatch <path>` | 输出路径 | 文件已 tracked | 要停止跟踪，使用 `git rm --cached` |
| `git ls-files --error-unmatch <path>` | 报错 | 索引中没有该路径 | 继续检查 ignore 规则和路径是否正确 |
| `git check-ignore -v <path>` | 输出规则来源、行号和模式 | 未跟踪文件命中了 ignore 规则 | 修改对应规则，或有意识地强制添加 |
| `git check-ignore -v <path>` | 没有输出 | 可能未被忽略，也可能文件已 tracked、仓库上下文错误或路径有误 | 检查仓库根目录；必要时加 `--no-index` |
| `git status --ignored --short` | 路径前显示 `!!` | Git 在当前仓库上下文中把它视为 ignored | 再用 `check-ignore -v` 查证规则来源 |

## 空输出不是结论，它只是证据不足

普通模式可以快速查看一个路径是否已被 Git 跟踪：

```bash
git ls-files scripts/report.py
```

有输出，说明 tracked。没有输出却不能直接证明它是 untracked：路径可能写错，文件也可能根本不存在。

确定性更强的写法是：

```bash
git ls-files --error-unmatch scripts/report.py
```

如果文件已被跟踪，命令会输出路径；否则，常见的英文错误信息是：

```text
error: pathspec 'scripts/report.py' did not match any file(s) known to git
```

具体前缀和措辞可能随 Git 版本及本地化设置不同，但非零退出状态才是脚本里应当依赖的信号。

我宁愿使用会明确失败的命令，也不愿围着一段空输出猜半天。空输出很安静，但它从不承诺自己是什么意思。

## 让 Git 指出规则、来源和行号

确认文件尚未被跟踪后，运行：

```bash
git check-ignore -v scripts/report.py
```

如果路径被忽略，输出通常类似：

```text
.gitignore:12:*.py    scripts/report.py
```

从左到右分别是：

- 规则所在的 ignore 文件；
- 规则行号；
- 实际命中的模式；
- 被检查的路径。

规则来源不一定是仓库根目录的 `.gitignore`。它还可能来自：

1. 仓库或子目录中的其他 `.gitignore`；
2. 仅当前仓库生效的 `.git/info/exclude`；
3. `core.excludesfile` 指定的全局排除文件。

查看全局排除文件的位置：

```bash
git config --get core.excludesfile
```

如果命中来自全局文件，修改前要多想一步：这项变更可能影响当前用户环境中的其他仓库。能在仓库规则里解决的问题，不要顺手扩大成全局行为。

还有一个容易漏掉的细节：`git check-ignore` 默认不会报告已经被跟踪的文件。假如 `git ls-files` 已经确认文件是 tracked，但你仍想知道“如果它没有被跟踪，会命中哪条规则”，需要运行：

```bash
git check-ignore -v --no-index scripts/report.py
```

这也解释了为什么普通 `git check-ignore -v` 的空输出不能单独证明“没有规则命中”。

## 先确认 Git 正在回答哪个仓库的问题

ignore 规则依赖仓库上下文。在错误目录里执行命令，Git 可能找不到仓库，也可能使用另一个工作树的规则。

先进入项目，再确认顶层目录：

```bash
cd ~/projects/app
git rev-parse --show-toplevel
```

输出应该是你正在排查的仓库根目录，例如：

```text
/path/to/repo
```

如果不是，后续关于 tracked 状态和 ignore 来源的判断都会错位。命令没有撒谎，只是回答了另一个仓库的问题。

## 文件可能没命中规则，但它的父目录命中了

有时 `scripts/report.py` 没有直接匹配任何文件模式，真正吞掉它的是父目录规则。把目录和文件一起检查：

```bash
git check-ignore -v \
  generated \
  generated/report.py
```

如果 `generated/` 被忽略，Git通常不会继续遍历其中的文件。这也是反向规则经常“看起来写对了，却没有效果”的原因。

下面这种写法很直觉，但不能可靠地重新包含目录里的文件：

```gitignore
generated/
!generated/report.py
```

前一条规则已经排除了整个目录，Git可能不会继续检查里面的文件。更稳妥的做法是忽略目录内容，而不是目录本身：

```gitignore
generated/*
!generated/report.py
```

如果目标位于更深层级，还需要确保通往它的每一级父目录都没有被排除。反向规则必须出现在它要覆盖的规则之后；顺序不是排版偏好，而是匹配语义的一部分。

## 修复方式由 tracked 状态决定

### 文件未被跟踪，但错误地命中了 ignore

最快的战术解法是强制添加：

```bash
git add -f generated/report.py
```

它绕过 ignore 规则，把文件加入索引。一旦文件被跟踪，后续修改也会正常出现在 Git 的变更中。

我不赞成把 `git add -f` 当作 ignore 问题的默认修复。它很适合明确、一次性的例外，例如仓库确实应该提交某个生成文件；但如果规则本身写错了，强制添加只会让下一个文件继续踩坑。

长期解法是缩小或修正 ignore 模式：

```gitignore
# 忽略目录中的其他内容
generated/*

# 保留这个文件
!generated/report.py
```

常见的命中结果也能帮助快速定位配置问题：

- 命中 `*.py`：仓库正在忽略所有匹配的 Python 文件，通常范围过大；
- 命中 `generated/`：父目录规则连带排除了其中内容；
- 来源是 `.git/info/exclude`：规则只在当前仓库的本地副本生效；
- 来源是全局 excludesfile：规则可能影响本机上的多个仓库。

### 文件已被跟踪，但你希望 Git 停止跟踪

`.gitignore` 不会替你修改索引。需要显式移除索引中的记录，同时保留当前工作区文件：

```bash
git rm --cached scripts/report.py
```

然后添加对应规则：

```gitignore
scripts/report.py
```

最后提交索引删除和 ignore 规则，仓库中的其他协作者才能获得一致的版本控制状态。

这里有一个不能省略的代价：`git rm --cached` 只保证执行命令时保留你当前工作区的文件；提交并合并这项删除后，其他工作副本在更新时可能失去原先被跟踪的文件。对于仍需存在的本地配置，通常还应提供一个可提交的模板，并提前说明迁移方式。

## 三条命令，把玄学压缩成证据链

在仓库根目录中，把路径换成目标文件：

```bash
git check-ignore -v scripts/report.py
git status --ignored --short
git ls-files --error-unmatch scripts/report.py
```

它们分别回答：

- 是否命中 ignore，以及规则来自哪里；
- 当前状态视图中，路径是 ignored、普通 untracked，还是其他状态；
- 文件是否已经进入索引。

`git status --ignored --short` 会用 `!!` 标记 ignored 路径，用 `??` 标记普通 untracked 路径；已跟踪文件的其他状态也可能出现。它适合浏览，不适合替代另外两条命令的精确判断。如果只想列出被忽略且未跟踪的路径，可以使用：

```bash
git ls-files --others --ignored --exclude-standard
```

如果第一条没有输出而第三条确认文件已 tracked，再补一次：

```bash
git check-ignore -v --no-index scripts/report.py
```

这时你得到的不是“感觉某条规则应该生效”，而是一条可核对的链：索引状态、匹配模式、规则来源和影响范围。

## 先查状态，再改规则

这件事背后有一条可迁移的原则：**规则通常不会自动改写已经持久化的状态。**

ignore 规则参与的是未跟踪文件的发现过程；索引保存的是此前已经作出的跟踪决定。两者处在不同层面，所以修改前者不会自动撤销后者。

这个原则适用于规则与状态分离的系统，但不适用于明确提供自动协调或追溯重算机制的系统。判断边界的方法很简单：先问规则是在每次读取时重新计算，还是只在状态进入系统时参与决策。

> Generalize：当配置看起来“没有生效”时，先问它控制的是未来输入，还是已经保存的状态？

现在去找一个你以为被 `.gitignore` 管住的文件，运行 `git ls-files --error-unmatch <path>`：它站在门外，还是早就在名单里？
