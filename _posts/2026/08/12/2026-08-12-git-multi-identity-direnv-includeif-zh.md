---
title: "你的 Git 身份和你的推送凭证，从来不是同一套系统"
header:
    image: /assets/images/hd_git.png
date: 2026-08-12
tags:
 - git
 - shell-scripting
 - devops
 - security
 - dotfiles
permalink: /blogs/tech/zh/git-multi-identity-direnv-includeif
layout: single
category: tech
---

> 名不正，则言不顺；言不顺，则事不成。——《论语·子路》

---

# 你的 Git 身份和你的推送凭证，从来不是同一套系统

*从"我的 gitconfig 明明是对的"到"我知道该查哪三个地方"*

Kai 发消息过来的时候，语气是那种已经自己折腾了一个小时、开始怀疑人生的语气：

> "我在公司仓库里提交，GitHub 上显示的是我的个人邮箱。但我 `git config user.email` 查了，返回的就是公司邮箱。它到底在骗谁？"

我让他把 `git config user.email` 的输出发过来。是公司邮箱，没错。

然后我让他加一个参数重跑：

```bash
git config --show-origin --get user.email
```

```
file:/Users/kai/.gitconfig	kai@personal.example.com
```

一行输出，故事就全变了。他之前查的那次，是在另一个终端窗口里跑的——那个窗口的当前目录，根本不在他以为的那个仓库下面。而真正提交的时候，`includeif` 压根没匹配上。

但这还不是最有意思的部分。最有意思的是：**就算 `includeif` 匹配上了、commit 里的邮箱是对的，他的 push 依然可能是用另一把 SSH key 完成的**——而 git 一个字都不会提醒他。

这篇想讲清楚的就是这件事。

**读完你会拿到三个东西：**

- 一条能在 10 秒内定位多身份环境问题的诊断命令，以及它为什么恰好查这三处
- `includeif` 和 `direnv` 的一句话分界线——一个换身份证，一个换钱包
- 一个大多数人从没意识到的对称性破缺：**commit 里写谁的名字，和 push 时用谁的钥匙，是两套互不通气的系统**

下面的顺序不是我当时的排查顺序，是按"最先该查什么"重排过的。真实排查往往是从最下游的症状倒着摸上来的，但教学要反过来。

---

## 一、那条诊断命令，为什么恰好查这三处

排查多身份环境，我固定跑这一段（只读，不改任何东西）：

```bash
echo "--- local  ---"; git -C ~/ws/work/etl-pipeline config --local --get-regexp 'ssh|url|core\.' 2>/dev/null
echo "--- global ---"; git config --global --get-regexp 'ssh|url|includeif|core\.ssh' 2>/dev/null
echo "--- direnv ---"; ls ~/.local/share/direnv/allow 2>/dev/null | head; direnv status 2>&1 | head -8
```

拆开看，每一段都在回答一个独立的问题。

### 第一段 — 这个仓库自己有没有偷偷覆盖什么

```bash
git -C ~/ws/work/etl-pipeline config --local --get-regexp 'ssh|url|core\.'
```

- `-C <path>`：不用 `cd` 过去，直接指定在哪个仓库执行。这一点很关键——**多身份问题最常见的误诊，就是在错误的当前目录下查配置**，Kai 踩的就是这个坑。
- `--local`：只读这个仓库的 `.git/config`，不看全局。优先级最高的一层先看。
- `--get-regexp 'ssh|url|core\.'`：按 key 名做正则匹配，一次捞出 `core.sshCommand`、`url."git@github.com:".insteadOf` 这类 SSH 代理和 URL 重写规则。

`url.*.insteadOf` 是很多人漏查的一项：它会在你毫无察觉的情况下把 `https://` 的远端改写成 `git@`，走完全不同的一套认证。

### 第二段 — 全局这一层，规则是怎么写的

```bash
git config --global --get-regexp 'ssh|url|includeif|core\.ssh'
```

同样的思路，对象换成 `~/.gitconfig`，多加了 `includeif`——也就是"条件性引入另一个配置文件"的规则本身。

注意这里查的是**规则**，不是**结果**。`--get-regexp 'includeif'` 告诉你"你打算按什么条件切身份"，而 `--show-origin --get user.email` 才告诉你"此时此刻实际生效的是哪一个"。这两者对不上的时候，问题就在规则的匹配条件上。

### 第三段 — direnv 到底被授权了没有

```bash
ls ~/.local/share/direnv/allow 2>/dev/null | head
direnv status 2>&1 | head -8
```

这一段查的是一个 git 完全看不见的东西：这个目录的 `.envrc` 有没有被你签字放行过。没放行，环境变量就一个都不会加载——而 git 不会报错，AWS CLI 也不会说"你忘了 allow"，它只会用默认 profile 干出你不想要的事。

| 命令段 | 回答的问题 | 漏查会怎样 |
|---|---|---|
| `--local` | 这个仓库有没有覆盖全局规则？ | 明明改了 `~/.gitconfig`，行为一点没变 |
| `--global` + `includeif` | 我的身份切换规则长什么样？ | 规则写了，但条件永远匹配不上 |
| `direnv allow` 列表 | 环境变量到底加载了没？ | git 一切正常，AWS / kubectl 权限却是错的 |

> 一条好的诊断命令，价值不在于它输出了什么，而在于它**同时排除了什么**。

---

## 二、includeif：静态的身份证

写在 `~/.gitconfig` 里：

```ini
[includeif "gitdir:~/ws/work/"]
    path = ~/.gitconfig-work

[includeif "gitdir:~/ws/personal/"]
    path = ~/.gitconfig-personal
```

被引入的文件长这样：

```ini
# ~/.gitconfig-work
[user]
    name = Kai Chen
    email = kai.chen@work.example.com
[core]
    sshCommand = ssh -i ~/.ssh/work_ed25519
```

三个要点：

- 触发条件是**目录路径匹配**（`gitdir:`），也可以按分支名匹配（`onbranch:`，git 2.36+）
- 一旦匹配，就把目标文件里的 `[user]`、`[core]` 等整体合并进来
- **纯静态、纯 git 内部机制**，不依赖任何外部进程，`git config --show-origin --get` 能直接看到"最终生效的值来自哪个文件"

🩸 **血泪提醒**：`gitdir:` 匹配的是**仓库目录本身**（`.git` 所在的位置），不是你 shell 的当前目录。如果你是通过 symlink 进去的、或者用的是 git worktree，路径匹配可能悄无声息地失效。macOS 上还有一个额外的坑：文件系统大小写不敏感，但 `gitdir:` 默认大小写敏感——`~/ws/Work/` 和 `~/ws/work/` 在 Finder 里是同一个目录，在 `includeif` 眼里不是。这种情况用 `gitdir/i:`。

排查它只需要一条命令，别再靠猜：

```bash
git -C <repo> config --show-origin --get user.email
```

输出里的文件路径，就是判决书。

> `includeif` 是一条规则，不是一个保证。它只在路径真的匹配上时才存在。

---

## 三、direnv：动态的钱包，而且需要你签字

`.envrc` 文件加上一次 `direnv allow`：

```bash
# ~/ws/work/etl-pipeline/.envrc
export AWS_PROFILE=work-dev
export GIT_SSH_COMMAND="ssh -i ~/.ssh/work_ed25519"
export KUBECONFIG=~/.kube/work-dev.yaml
```

- 触发条件是 **shell 每次 `cd` 进这个目录**，direnv 的 hook 会自动 source 它，离开目录时自动卸载
- 管的是**任意环境变量**，完全不局限于 git——AWS profile、K8s context、API key 全能塞
- **需要显式 `direnv allow` 授权一次**（这正是诊断命令第三段在查的东西）；而且**改了 `.envrc` 的内容，授权立即失效**，必须重新 allow

最后这条是设计上的刻意为之，也是最容易让人以为"我的改动没生效"的地方。

🩸 **血泪提醒**：`.envrc` 里的东西是**真实执行的 shell 脚本**，不是声明式配置。如果你 clone 下来一个陌生仓库，它自带 `.envrc`，千万别顺手 `direnv allow`——那等于允许别人写的脚本在你机器上跑任意命令，而且是在你每次 `cd` 进去的时候自动跑。direnv 要求重新授权，不是在给你添麻烦，它是在把"信任"这件事变成一个你必须亲手做的动作。

| | includeif | direnv |
|---|---|---|
| 归谁管 | git 内部 | shell（外部进程 + hook）|
| 触发时机 | 每次执行 git 命令 | 每次 `cd` 进/出目录 |
| 管辖范围 | 只有 git 配置项 | 任意环境变量 |
| 需要授权 | 不需要 | 需要，且改动后失效 |
| 安全模型 | 静态数据，不执行 | **执行任意代码** |
| 怎么验证 | `git config --show-origin --get` | `direnv status` |

---

## 四、对称性破缺：commit 写谁的名字，和 push 用谁的钥匙

这是这篇真正想让你记住的一节。如果你只看一节，看这节。

大多数人心里的模型是这样的：**"我把 git 身份切成公司的，那我就是在以公司身份操作。"**

这个模型是错的。它把两件毫不相干的事当成了一件：

| | 决定它的是 | 有没有人验证 |
|---|---|---|
| commit 里写着谁 | `user.name` / `user.email`，纯文本字段 | **没有**。你可以写任何人的邮箱，git 照收不误 |
| push 能不能成功 | SSH 客户端拿出了哪把私钥 | **有**。服务端拿公钥核对，错了就 `Permission denied` |

`user.email` 是**你自己填的一段元数据**，git 从不校验它——你现在就可以用 `git -c user.email=linus@kernel.org commit` 提交一个署名 Linus 的 commit。而 push 能不能成，取决于 SSH 握手时用了哪把私钥，跟 `user.email` 一个字节的关系都没有。

这就是这套体系里的**对称性破缺**：两条链路看起来都叫"身份"，一条完全不设防，另一条严格校验，而它们之间没有任何一致性检查。于是你会同时拿到"push 成功了"和"署名是错的"这两个信号，还觉得它们互相印证。

更隐蔽的一层在这里：

```ini
# includeif 引入的文件里
[core]
    sshCommand = ssh -i ~/.ssh/work_ed25519
```

```bash
# .envrc 里
export GIT_SSH_COMMAND="ssh -i ~/.ssh/personal_ed25519"
```

**环境变量 `GIT_SSH_COMMAND` 的优先级高于配置项 `core.sshCommand`。** 也就是说，你在 `includeif` 里精心配好的公司 key，会被一个残留在 shell 里的环境变量默默顶掉——`git config --get core.sshCommand` 查出来还是公司的那把，因为它查的是配置，不是最终生效的行为。

想看真相，得绕过 git 自己的说法：

```bash
# 谁在真正决定 SSH 行为
echo "$GIT_SSH_COMMAND"
git config --show-origin --get core.sshCommand

# 服务端认为你是谁（GitHub 会直接告诉你账号名）
ssh -T git@github.com
```

最后那条是整套排查里最实在的一条：它不问你的配置，它问服务端。

> 配置文件告诉你"你打算是谁"，`ssh -T` 告诉你"对面认为你是谁"。这两句话不一致的次数，比你想象的多。

---

## 五、把两套系统串起来看

完整的链路是这样的，两个系统各管一段：

```
cd 进 ~/ws/work/etl-pipeline/
   ↓ direnv 加载 .envrc（前提：allow 过）
AWS_PROFILE=work-dev + GIT_SSH_COMMAND 指向公司 key
   ↓ git 命令执行，includeif 匹配 gitdir
user.email 切成公司邮箱，写进 commit
   ↓ push，SSH 握手
服务端用公钥认人 —— 认的是 key，不是 email
```

链路上任何一段断了，症状都不一样，而且都不会明确告诉你断在哪：

| 症状 | 断在哪一段 | 先查什么 |
|---|---|---|
| commit 署名是个人邮箱，但 push 成功了 | `includeif` 没匹配上；key 是对的 | `git config --show-origin --get user.email` |
| `Permission denied (publickey)` | 身份对了，key 没到位 | `echo $GIT_SSH_COMMAND`；`ssh -T git@github.com` |
| git 一切正常，AWS / kubectl 权限却是错的 | direnv 没 allow | `direnv status` |
| 改了 `.envrc` 但值还是旧的 | 改动让授权失效了 | `direnv allow` |
| 配置里明明是公司 key，用的却是个人 key | 环境变量顶掉了配置项 | `echo $GIT_SSH_COMMAND` |

注意最后两行：它们都是"你以为你改对了"的情况。这类问题最贵，因为它不触发任何报错，只是安静地做错事。

---

## 立刻可以做的事

1. **现在就在你手边的工作仓库里跑一次** `git -C . config --show-origin --get user.email`。不是 `--get`，是 `--show-origin --get`。看清楚这个值来自哪个文件——如果来自 `~/.gitconfig` 而不是你以为的那个 work 配置，你的 `includeif` 从来就没生效过。
2. **跑一次 `ssh -T git@github.com`**，看服务端叫你什么名字。这是唯一一个不依赖你本地配置说法的答案。
3. **`echo "$GIT_SSH_COMMAND"`**。如果它非空，而你并不记得是谁设的，那它正在覆盖你所有的 `core.sshCommand` 配置。
4. **把 `gitdir:` 的路径写成绝对路径来验证一次**。确认不是 symlink 或者 worktree 让匹配悄悄失效了。
5. **把这三条命令写进你 dotfiles 里的一个 `git-whoami` 函数**。这是这篇里最值钱的一条——上面那些排查步骤，现在还是"只存在于你脑子里的部落知识"，三个月后你会重新推理一遍。把它变成一个能执行的工程产物，你就再也不用推理了：

   ```bash
   git-whoami() {
     echo "email : $(git config --show-origin --get user.email 2>/dev/null || echo '(none)')"
     echo "ssh   : ${GIT_SSH_COMMAND:-$(git config --get core.sshCommand || echo '(default)')}"
     echo "aws   : ${AWS_PROFILE:-'(default)'}"
     direnv status 2>/dev/null | grep -i 'loaded rc\|allowed' || echo "direnv: n/a"
   }
   ```

6. **克隆任何陌生仓库后，`direnv allow` 之前先 `cat .envrc`**。这条不是洁癖，是安全边界。

---

*配置文件写的是你的意图，运行时环境写的是你的行为。多身份环境里出的每一个事故，都发生在这两者悄悄分岔、而没有任何人报错的那段距离里。*
