---
title: "多身份 Git 环境排查：从一行诊断命令看懂 includeif 与 direnv"
date: 2026-08-12
categories: [engineering, git, shell]
tags: [git, direnv, includeif, ssh, dotfiles]
---

日常在公司仓库（Macquarie SSO）和个人仓库之间切换时，最怕的就是"用错身份 push"或者"AWS 权限对不上"。这篇记录一次真实的排查过程：从一行诊断命令拆解开始，最后理清 `includeif` 和 `direnv` 这两个经常被搞混的机制到底谁管什么。

## Part 1：拆解一段诊断命令

排查的起点是这样一段命令（只分析，不执行）：

```bash
echo "--- local ---"; git -C ~/ws/qa/edr-nonstandard-etl config --local --get-regexp 'ssh|url|core\.' 2>/dev/null
echo "--- global ---"; git config --global --get-regexp 'ssh|url|includeif|core\.ssh' 2>/dev/null
echo "--- direnv allow list ---"; ls ~/.local/share/direnv/allow 2>/dev/null | head; direnv status 2>&1 | head -8
```

### 第一段 — 查看 local repo 的 git 配置

```bash
git -C ~/ws/qa/edr-nonstandard-etl config --local --get-regexp 'ssh|url|core\.'
```

- `-C <path>`：不用 `cd` 过去，直接指定在哪个仓库执行 git 命令
- `config --local`：只读这个仓库自己的 `.git/config`，不看全局配置
- `--get-regexp 'ssh|url|core\.'`：用正则匹配 key 名，抓出所有跟 `ssh`、`url`、`core.` 相关的配置项（比如 `core.sshCommand`、`url."xxx".insteadOf` 这种 SSH 代理/重写规则）

### 第二段 — 查看 global git 配置

```bash
git config --global --get-regexp 'ssh|url|includeif|core\.ssh'
```

同理，但看的是 `~/.gitconfig`，多加了 `includeif`（条件性引入其他配置文件，常用于"公司目录用这套 SSH key，个人目录用另一套"）。

### 第三段 — 查看 direnv 授权列表

```bash
ls ~/.local/share/direnv/allow 2>/dev/null | head
direnv status 2>&1 | head -8
```

整体来看，这套命令是在验证："这个仓库到底用的是哪个 SSH 身份 / URL 重写规则，direnv 有没有 allow 这个目录" —— 典型的多身份环境排查思路。

## Part 2：includeif vs direnv，一句话区分

> **`includeif` 管的是"我是谁"（git identity），`direnv` 管的是"我在哪个环境里"（env vars / PATH / secrets）。一个改身份证，一个换钱包。**

### includeif：按目录自动切换 git 身份

写在 `~/.gitconfig` 里：

```ini
[includeif "gitdir:~/ws/mq/"]
    path = ~/.gitconfig-macquarie

[includeif "gitdir:~/ws/personal/"]
    path = ~/.gitconfig-personal
```

- 触发条件是**目录路径匹配**（`gitdir:`），也可以按分支名匹配（`onbranch:`，git 2.36+）
- 一旦匹配，就把对应文件里的 `[user] name/email`、`[core] sshCommand` 等整体引入
- **纯静态、纯 git 内部机制**，不依赖任何外部进程，`git config --get` 能直接看到合并结果

🩸 **血泪提醒**：`gitdir:` 匹配的是**仓库目录本身**（`.git` 所在位置），如果你是通过 symlink 或者 worktree 进去的，路径匹配可能对不上——这时候要用 `gitdir/i:`（大小写不敏感）或者干脆写绝对路径 debug。

### direnv：按目录自动加载 shell 环境

`.envrc` 文件 + `direnv allow`：

```bash
# ~/ws/mq/edr-nonstandard-etl/.envrc
export AWS_PROFILE=mqu-dev
export GIT_SSH_COMMAND="ssh -i ~/.ssh/mq_id_ed25519"
```

- 触发条件是 **shell 每次 `cd` 进这个目录**，direnv hook 会自动 `source` 这个文件
- 管的是**任意环境变量**，不局限于 git——AWS profile、K8s context、API key 全能塞
- **需要显式 `direnv allow` 授权一次**（这就是原命令在查的 allow list），改了 `.envrc` 内容还要重新 allow，防止恶意仓库偷偷执行代码

🩸 **血泪提醒**：`.envrc` 里的代码是**真实执行的 shell 脚本**，不是声明式配置。如果 `git pull` 下来一个陌生仓库自带 `.envrc`，千万别无脑 `direnv allow`——这等于允许别人的脚本在你机器上跑任意命令。

### 组合拳怎么打

`includeif` 只改 git 层面的身份，**不会**自动把对应的 SSH key 加到 agent 里，也不会切 AWS profile。所以完整链条是：

```
进入 ~/ws/mq/edr-nonstandard-etl/
   ↓ direnv 自动加载
GIT_SSH_COMMAND 指向 mq 的 key + AWS_PROFILE=mqu-dev
   ↓ includeif 匹配 gitdir
git identity 切换成 macquarie 邮箱
```

两个系统各管一段，**任何一段没配对，就会出现"用错身份 push"或者"AWS 权限对不上"这种坑**。

## 小结

- `includeif` = 静态、git 内部、管身份
- `direnv` = 动态、shell 层、管环境变量，且需要显式信任
- 多身份开发环境要两者配合才完整，单独排查任何一个都可能漏掉另一半的问题

