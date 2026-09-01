---
title: "从 `rg | head` 到交互式搜索驾驶舱:ripgrep + fzf 的正确姿势"
date: 2026-08-03
categories: [engineering, shell, developer-tools]
tags: [ripgrep, fzf, cli, zsh, neovim, gitops]
---

大多数人搜代码都是同一套动作:敲一条 `grep` 风格的命令,管道接 `head` 免得刷屏,然后眯着眼在被截断的输出里努力还原每个命中到底在哪。这套流程能用——直到它不够用。当你要的那行恰好在第 81 行,你又得回去改命令、重跑一遍。

这篇文章会带你爬一层楼梯。起点是一条同事用来审计一批 ArgoCD app 的真实命令,我们先拆开它、讲清它为什么脆弱,最后落到一个可以直接塞进 `.zshrc` 的交互式搜索函数——把"grep 完眯眼看"变成"过滤、预览、跳转"。

## 第一部分:这条命令到底在干什么

先看起点——一条 GitOps 审计命令:

```bash
rg -n "targetRevision|kubernetes/prod|kubernetes/dev|path:" dit-gitops-mqu/apps --glob '*.yaml' | head -80
```

一句话:它在 `dit-gitops-mqu/apps` 目录下所有 `.yaml` 文件里,用 ripgrep 搜四个关键词中任意一个出现的行(`targetRevision`、`kubernetes/prod`、`kubernetes/dev`、`path:`),带行号显示,只看前 80 行结果。

意图是一个经典的审查任务:**"哪些 ArgoCD app 在追哪个分支(`targetRevision`)、指向哪个环境(prod/dev)、具体的 `path` 配的是什么——而我不想手动一个个文件点开看。"**

逐段拆:

- `rg -n "A|B|C|D"` — ripgrep 的正则 OR;命中四个关键词**任意一个**的行就打印出来。`-n` 带上行号,方便你回文件里定位。
- `dit-gitops-mqu/apps` — 把搜索限定在一个目录,而不是扫整个仓库。
- `--glob '*.yaml'` — 只在 YAML 文件里匹配,过滤掉 `.md`、`.sh` 这些噪音。
- `| head -80` — 结果太多时截断,防止刷屏。方便是方便——但它也是后面我们要解决的那个坑的源头。

## 第二部分:大多数人从没用过的 ripgrep 招式

`rg` 比 `grep` 强在三个默认行为:默认递归、默认尊重 `.gitignore`、默认多线程。同样一顿乱扫,`rg` 快你 5–10 倍,还不会把 `node_modules`、`.git` 也拖进结果里膈应你。

假设你已经会基础用法,这里是每天都能派上用场、但很多人没摸到的几招:

**1. 用 `-t` / `-T` 按文件类型过滤,别手写 glob**

```bash
rg -t yaml "targetRevision"
```

`rg --type-list` 能看所有内置类型——yaml、py、go、ts 等几十种全预设好了,基本用不着自己写 glob 模式。

**2. 用 `-A` / `-B` / `-C` 显示上下文**

```bash
rg -n -B2 -A2 "targetRevision"
```

光看命中行往往不够——你分不清这是**哪个 app** 的 `targetRevision`。`-C3` 把前后各 3 行也带出来,比自己再 `cat` 一遍文件快多了。

**3. 用 `-o` 只要匹配到的那一小段**

```bash
rg -o "kubernetes/(prod|dev)"
```

配合 `sort | uniq -c`,直接统计出 prod / dev 各出现几次——不用肉眼数。

**4. 用 `--json` 输出结构化数据**

```bash
rg --json "targetRevision" | jq '.data.lines.text'
```

对我们这种审计场景,`--json` 特别搭:因为你接下来大概率是想批处理、统计、或喂给脚本,而不是人眼一行行看。

**5. 只要文件名(`-l`)或只要计数(`-c`)**

```bash
rg -l "targetRevision" dit-gitops-mqu/apps    # 哪些文件命中
rg -c "targetRevision" dit-gitops-mqu/apps    # 每个文件命中几次
```

先用 `-l` / `-c` 摸清地形,再决定展开哪块。先广度后深度——这是任何审计类任务的标准套路,也恰好是"一上来就 `head -80` 硬看"的反面。

**6. 用 `-P`(PCRE2)上全功能正则**

```bash
rg -P "(?<=path:\s).*prod.*"
```

需要 lookahead / lookbehind 时,`-P` 切到 PCRE2 引擎(rg 默认引擎更快但功能弱一点)。不用换工具。

## 第三部分:把 `rg` 接进 `fzf` 做交互式搜索

高潮来了。把 `rg` 当**数据源**、`fzf` 当**交互层**:

```bash
rg --line-number --no-heading "pattern" \
  | fzf --delimiter : --preview 'bat --color=always {1} --highlight-line {2}'
```

这样你就不是傻等 `head -80` 截断然后瞎猜,而是实时过滤命中、边移动边预览文件内容、选中一行还能直接跳进编辑器。这套基本就是 Telescope / fzf-lua 在 Neovim 里干的事,只不过在裸终端里也能用。

讲讲每一层为什么这么配:

**`--no-heading` 是关键开关。** `rg` 默认按文件分组、文件名单独一行且不带冒号——这样 `fzf` 没法按 `:` 切列。`--no-heading` 让每条结果都变成扁平的 `文件:行号:内容`,`fzf` 才好解析。

**`--delimiter :`——以及一个关于 `--with-nth` 的警告。** 很容易想用 `fzf --with-nth` 把文件名、行号那两列砍掉只留内容。别这么干。`--with-nth` 是在**选择阶段**就把那些列切没了,于是你盯着一行代码,却不知道它出自哪个文件第几行。正确姿势:让 `--delimiter` 负责给 `--preview` 命令**怎么切列**,但**展示层不砍列**——你选的时候还是能看到完整的 `文件:行号:内容`,预览窗口再单独把上下文摊开。

**跳转编辑器的收尾:**

```bash
rg --line-number --no-heading "pattern" \
  | fzf --delimiter : --preview 'bat --color=always {1} --highlight-line {2}' \
  | awk -F: '{print $1" +"$2}' \
  | xargs -o nvim
```

最后一步故意用 `awk -F:` 而不是 `cut`:`awk` 后面还能塞逻辑(比如以后想加个条件跳过某些文件),而 `cut` 是死的字段提取,没有扩展空间。

**把它包成 `.zshrc` 里的一个 `rgf` 函数:**

```bash
rgf() {
  rg --line-number --no-heading "$1" ${2:-.} \
    | fzf --delimiter : \
          --preview 'bat --color=always {1} --highlight-line {2}' \
          --preview-window '~3' \
    | awk -F: '{print $1" +"$2}' \
    | xargs -ro nvim
}
```

用法就是 `rgf targetRevision dit-gitops-mqu/apps`。再也不用手动拼 `rg | head`、肉眼数行号再跳文件那一套。

## 收束

这里的弧线,其实是大多数 CLI 手艺的通用弧线:一条快糙猛的命令能让活儿**开个头**,但它留下的那些摩擦——截断、没上下文、不能跳转——恰恰是一点点组合就能抹掉的。`rg` 给你快、准、可脚本化的匹配;`fzf` 给你一个把它们开起来的驾驶舱。`.zshrc` 里十二行代码,"grep 完眯眼看"就变成了"过滤、预览、跳转"。
