---
title: "diff / patch / Neovim 配置比对的骚操作合集"
date: 2026-09-24
categories: [engineering, shell, neovim]
tags: [diff, patch, neovim, yq, git, config]
---

天天搞跨环境、跨版本的配置比对（比如 Airflow 从 2.4.3 升到 2.10.3），
`diff` 这条老命令其实藏了一堆"知道的人不多但一用回不去"的姿势。
这篇把从基础到骚操作一路串起来：怎么看 diff、并排对比、生成可应用的 patch、
在 Neovim 里三秒看差异，最后是几个真·冷门的封神技巧。

---

## Part 1: diff -u 到底在干嘛，怎么看输出

一句话直给：`diff -u 文件A 文件B` 就是让系统帮你把两个文件"叠在一起找不同"，
`-u` 是 **unified 格式**（统一格式），最后打印出一份人类和 Git 都爱看的"差异报告"。

```
diff -u aws/qlsit/edr/airflow-2.4.3/config.yml \
        aws/qldev/edr/airflow-2.10.3/config.yml
```

翻译成人话：**"把 SIT 环境 Airflow 2.4.3 的配置，和 DEV 环境 Airflow 2.10.3 的配置
摆一起，告诉我哪些行不一样。"**

**怎么看输出（3 秒学会）：**

- `---` 那行是第一个文件（旧），`+++` 那行是第二个文件（新）
- `@@ -12,7 +12,8 @@` 这种叫 **hunk header**，意思"从第 12 行起，左边 7 行、右边 8 行"
- 行首 `-` = 只在 A 里有（被删/改前），`+` = 只在 B 里有（新增/改后），
  空格开头 = 两边都一样的上下文行

一句心法：**看 `-` 想"旧的长这样"，看 `+` 想"新的变这样"。**

---

## Part 2: 并排看更爽 — diff 的隐藏姿势

`-u` 是上下堆叠，看长文件容易眼花。想左右对照？

```
diff -y aws/qlsit/edr/airflow-2.4.3/config.yml \
        aws/qldev/edr/airflow-2.10.3/config.yml
```

`-y`（等于 `--side-by-side`）**左右两栏并排**，中间用符号提示：

- `|` = 这行两边都有但内容不一样
- `<` = 只在左边（旧文件）有
- `>` = 只在右边（新文件）有

老鸟私藏组合技：

- `diff -y --suppress-common-lines A B` → **只显示不同的行**，相同的全砍掉，屏幕瞬间清爽
- 觉得两栏太窄？加 `-W 200` 把宽度拉到 200 列
- 想要"带颜色 + 并排 + 只看不同"的顶配体验，直接上 `delta` 或 `icdiff`
  （专门做这个的第三方工具，config 比对神器）

一句心法：**`-u` 给机器看（Git/patch），`-y` 给人眼看。**

---

## Part 3: 让 diff 直接生成可应用的 patch

这才是 `-u` 真正的杀手锏——它的输出**本身就是一份补丁**，
能被 `patch` 或 `git apply` 直接吃掉。

第一步，把差异存成文件：

```
diff -u aws/qlsit/edr/airflow-2.4.3/config.yml \
        aws/qldev/edr/airflow-2.10.3/config.yml > upgrade.patch
```

之后这份 `upgrade.patch` 就能"搬运"这些改动：

```
patch aws/qlsit/edr/airflow-2.4.3/config.yml < upgrade.patch
```

或者用 Git 的方式（更安全，能预演）：

```
git apply --check upgrade.patch   # 先体检，看能不能干净打上
git apply upgrade.patch           # 确认没问题再真打
```

对跨环境场景简直量身定做：**SIT 上验证好的配置变更，打包成 patch，一键搬到别的环境**，
不用手抖复制粘贴。

⚠️ 一个坑先提上：patch 认的是**行号 + 上下文**。如果目标文件已经被人改过，
行号对不上就会 fail 或者进 `.rej` 文件。所以 `git apply --check` 是保命符，
先体检再动手。

---

## Part 4: Neovim 里三秒看 diff

**A. 直接开双窗对比（内置 diff mode）**

命令行启动：

```
nvim -d fileA fileB
```

`-d` = diff mode，左右开双窗，不同的行自动高亮上色。窗口内导航快捷键：

- `]c` → 跳到下一处差异
- `[c` → 跳到上一处差异
- `do` → **diff obtain**，把对面那行的改动"拉过来"（应用到当前窗口）
- `dp` → **diff put**，把当前行"推过去"（应用到另一窗口）

心法：**`do` = 我要你的（obtain），`dp` = 给你我的（put）。**
一边跳 `]c` 一边 `do`/`dp`，手动合并配置爽到飞起。

已经开着一个文件了？`:vsplit 另一个文件` 然后两个窗口都敲 `:diffthis`，同样进入对比。

**B. 看 Git 改动（日常更常用的）**

LazyVim 自带 **gitsigns**，改过的行左边栏会有标记。悬停当前 hunk：

- `<leader>ghp` → preview hunk，弹窗看这块改了啥
- `]h` / `[h` → 在改动块之间跳

想要"完整并排 Git diff"体验，LazyVim 生态里常配 **diffview.nvim**，
`:DiffviewOpen` 一开，整个 commit 的改动像 IDE 一样铺在眼前。

---

## Part 5: 真·冷门封神技巧

### 🥇 王炸：diff "两条命令的输出"

大多数人只会 `diff 文件 文件`，但 diff 其实能比对**任何命令跑出来的结果**，
靠的是 `<()` 这个叫 **进程替换（process substitution）** 的骚操作：

```
diff <(命令1) <(命令2)
```

`<(...)` 会把命令输出**伪装成一个临时文件**喂给 diff：

```
# 比对两个环境实际生效的环境变量，先排序再比，避免顺序噪音
diff <(sort sit.env) <(sort dev.env)

# 甚至比对两台机器/两个 pod 的实时输出
diff <(ssh sit "airflow config list") <(ssh dev "airflow config list")
```

一句心法：**diff 眼里没有"文件"和"命令"之分，只有两股文字流。**

### 🥈 借 Git 的漂亮 diff 引擎，比对任意两个文件

即使文件**根本不在 Git 仓库里**，也能白嫖 Git 那套彩色、单词级高亮的 diff：

```
git diff --no-index A B
```

再加 `--word-diff`，它会**精确到"哪个词变了"**而不是整行标红——
改了一个端口号、一个版本号，一眼就锁定：

```
git diff --no-index --word-diff \
  aws/qlsit/edr/airflow-2.4.3/config.yml \
  aws/qldev/edr/airflow-2.10.3/config.yml
```

心法：**`--no-index` = "Git，别管仓库了，就帮我比这两个文件"。**

### 🥉 YAML 语义比对：忽略"顺序 + 缩进 + 注释"的假差异

普通 diff 会把"key 换了个位置"也当成差异，YAML 里这纯属噪音。
用 `yq` 先**归一化**（排序 key + 统一格式）再比，只剩**真正的语义差异**：

```
diff <(yq -P 'sort_keys(..)' A.yml) \
     <(yq -P 'sort_keys(..)' B.yml)
```

把进程替换 + yq 合体，就是配置比对的"究极形态"。想要更专业的，
还有 `dyff`——专门为 K8s / Airflow 这类 YAML 做的语义 diff 工具。

### 🎁 隐藏彩蛋三连

**① 只要"改动摘要"，不看细节**

```
diff -u A B | diffstat
```

直接告诉你"3 个文件、+12 行、-5 行"，写升级说明/PR 描述时贴上去超专业。

**② `comm` — 集合运算三件套（处理已排序文件）**

```
comm -3 <(sort listA) <(sort listB)
```

三栏输出："只在 A"、"只在 B"、"两边都有"。想看"两个环境都装了哪些包"
vs "只有一边装的"，它比 diff 更直觉。

**③ Neovim diff 里的一键刷新**

在 diff mode 卡住、高亮乱了？敲 `zx` **强制重算 diff + 展开所有折叠**，
比关窗重开优雅一万倍。
