---
title: "从一条 ssh 命令,牵出 Git/SSH/gh 的九个深水区"
date: 2026-09-03
tags: [Git, SSH, GitHub, gh, DevOps, 效率工具]
categories: [工具英雄]
description: "从一条最普通的 ssh 连接测试命令讲起,一路挖到 GIT_SSH_COMMAND、gh CLI 骚操作、一机多账号、企业版 GHE 多 host、HTTPS + SAML SSO。全是踩过的坑,拿走即用。"
---

> 起因很简单:同事甩过来一条 `ssh -i ~/.ssh/id_ed_qan -Tv git@github.com`,问我"这啥意思"。
> 结果一路聊下去,把 Git 连接这条链路上最容易翻车的坑几乎全踩了一遍。
> 干脆整理成这篇 deep dive——**每一节都是"先给你能直接用的结论,再讲为什么"**。

---

## 0. 一句话地图

这篇讲的其实是同一个问题的九个切面:**你敲下 `git clone` 的那一刻,身份是怎么被验证的?**

从底层往上:SSH 握手 → 用哪把 key → 用哪条协议(SSH vs HTTPS)→ 一机多身份怎么不打架 → 企业内网 GHE 怎么叠加 → SSO 场景怎么认证。看完你对"为什么它连不上"会有肌肉记忆。

---

## 1. 体检命令:`ssh -Tv git@github.com`

**结论:这条命令是在测试你的 SSH key 能不能敲开 GitHub 的门,不 clone 任何东西,纯体检。**

```bash
ssh -i ~/.ssh/id_ed_qan -Tv git@github.com
```

拆开:

| 部件 | 含义 |
|---|---|
| `ssh` | 敲门的人 |
| `-i ~/.ssh/id_ed_qan` | 用这把**特定**私钥(不走默认那把) |
| `-T` | 我不要交互式终端(GitHub 根本不给 shell) |
| `-v` | 啰嗦点,把握手过程打出来,方便排查 |
| `git@github.com` | 以 `git` 用户身份连 github.com |

跑成功,GitHub 会回你一句很欠揍的话:

```
Hi <你的用户名>! You've successfully authenticated, but GitHub does not provide shell access.
```

**划重点:这句"不给 shell access" 不是报错,是成功的标志。** 很多人第一次看到吓一跳。只要看到你的用户名,就是钥匙对了、大功告成。

---

## 2. `-T` 和 `-v` 的冷知识

### 大写 `-T`:关掉伪终端

平时 `ssh` 登服务器,SSH 会帮你申请一个终端好让你敲命令。但 GitHub 这扇门后面**没有房间**——它不给 shell,你申请终端等于对空气要椅子。所以连 GitHub 老手一律加 `-T`。

它有个反义词 `-t`(小写)= 强制要终端,对 GitHub 用它会看到 `Pseudo-terminal will not be allocated...`,又是一句听着像报错其实没事的废话。

> 口诀:**连 GitHub,认大 T。**

### `-v`:啰嗦三兄弟

- `-v`:讲人话级别,告诉你读了哪个配置、试了哪把 key、对方接不接受。**99% 排查够用。**
- `-vv`:加密算法协商等细节。
- `-vvv`:每个数据包都念给你听,像旁边坐了个碎碎念的解说员。

**怎么一眼看出哪把 key 生效?** 盯这两行:

```
debug1: Offering public key: .../id_ed_qan     # 我把这把递过去试试
debug1: Server accepts key: .../id_ed_qan      # 就是它,对方收下了 ✅
```

`Server accepts key` 后面跟的文件名,就是最终生效的那把。有多把 key 时,你会看到它一把一把 `Offering`,像掏钥匙串挨个试锁。

> 顺带:SSH 默认一次最多试 6 把,试太多会被 GitHub 拍出来(`Too many authentication failures`)。这就是"明明有对的 key 却连不上"的经典陷阱——用 `-i` 精准指定正好绕开它。

---

## 3. 握手到底发生了什么

`id_ed_qan` 看名字就是 **ed25519**(椭圆曲线,又短又快又安全,现在的默认首选,比老 RSA 香)。它和 GitHub 对暗号,四步:

**① 认脸(验证服务器)。** GitHub 先亮出它自己的公钥指纹:"我是 github.com,这是我的脸。" 你的电脑翻 `~/.ssh/known_hosts` 这本通讯录对一下:

- 没这人 → 弹 `Are you sure you want to continue connecting (yes/no)?`,你敲 yes 就存进去。**这一步是防"假 GitHub"钓鱼的**,不是走过场。
- 有且对得上 → 秒过。
- 有但对不上 → 红色警报 `REMOTE HOST IDENTIFICATION HAS CHANGED!`,直接拒连。多数是 GitHub 官方轮换了 key(会公告),但这个机制本身是保命的。

**② 亮钥匙(验证你)。** 你把 `id_ed_qan` 对应的**公钥**递过去。

**③ 出题—答题(精髓)。** 关键:你的**私钥从头到尾没离开过你的电脑**。GitHub 用你的公钥出一道只有对应私钥才能解的随机题,你在本地用私钥算出答案发回,GitHub 用公钥一验:"能答对,说明私钥在你手上。" 全程私钥不上网——这就是非对称加密的魔法。

**④ 开门。** 验过了,GitHub 说 `Hi <用户名>!`,认出的是**用户名**(你上传公钥时它就记了"这把公钥 = 这个账号")。然后送客。真正的 `clone`/`push` 数据从这条加密隧道里跑。

> 一句话:**先我确认你是真 GitHub(known_hosts),再你确认我是真的我(私钥答题),互信建立,开工。**

---

## 4. 经典乌龙:`GIT_SSH_COMMAND` 撞上 HTTPS URL

来看一条**看起来很聪明、其实会静默失效**的命令:

```bash
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed_qan" \
  git clone https://github.com/qantasloyalty/edr-airflow-dag-cli.git /tmp/test-edr-cli
```

意图很清楚:用指定 key 克隆一个仓库。**但它不会按你想的工作。** 两处打架:

- 前面 `GIT_SSH_COMMAND=...` 是说"走 SSH 时用这把 key"。
- 后面 URL 却是 **`https://`** —— HTTPS **根本不走 SSH**!

所以那个环境变量被**完全无视**。就像你攥着门禁卡,走到的却是要输密码的门,卡再对也刷不响。HTTPS 拉私有库,GitHub 要的是**用户名 + Token**,不认 SSH 私钥。

**想让 key 生效,URL 要换成 SSH 格式:**

```
https://github.com/qantasloyalty/edr-airflow-dag-cli.git
        ↓
git@github.com:qantasloyalty/edr-airflow-dag-cli.git
```

注意两个特征:`https://` → `git@github.com`,以及域名后那个 **`/` 变成 `:`**(SSH URL 的招牌)。

> 附:`git clone` 最后的 `/tmp/test-edr-cli` 是目标目录;放 `/tmp` 说明是临时验证 key,重启即焚,很合适。

---

## 5. `GIT_SSH_COMMAND` 的正确打开方式

它就是**临时塞给 git 的一张小纸条:"这次连 SSH 你用这条命令。"** 只在这一条 git 命令里生效,不污染全局。

### ① 临时指定 key —— 有个巨坑 ⚠️

```bash
# ❌ 光写 -i 有时不管用
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed_qan" git pull

# ✅ 加一把"闭嘴锁"
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed_qan -o IdentitiesOnly=yes" git pull
```

如果开了 ssh-agent 并加载了别的 key,ssh 会**先把 agent 里的 key 挨个试一遍**,你指定的那把反而排后面,还可能触发 `Too many authentication failures`。`IdentitiesOnly=yes` 的意思是"就用我 `-i` 指的这把,别的别递"。加上它才是真·精准指定。

### ② 跳过 host 检查(临时救急)

```bash
GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" git clone ...
```

前者"别问 yes/no,自动接受新主机",后者"验证结果写 /dev/null,不记账"。常见于 CI、临时跳板机。

> 🚨 严肃提醒:这等于**关掉了防中间人钓鱼那道锁**(第 3 节"认脸"那步)。只在"完全清楚对面是谁、环境用完即焚"时用,别在自己长期机器上这么干。

### ③ 顺手 debug

```bash
GIT_SSH_COMMAND="ssh -v" git fetch
```

### 它和 `~/.ssh/config` 谁听谁的?

**不是二选一,是叠加,冲突时命令行赢。** 因为 `GIT_SSH_COMMAND` 本质就是在拼一条 `ssh ...`,而 ssh 永远会读 `~/.ssh/config`。真实优先级是 SSH 通用规则:

> **命令行参数(`-i`/`-o`)> `~/.ssh/config` > `/etc/ssh/ssh_config`**

翻译:你在 `GIT_SSH_COMMAND` 里 `-i` 指定的 key 会盖过 config 里同 host 的 `IdentityFile`;但 config 里你**没覆盖**的设置(`Port`、`ProxyJump`、`HostName` 映射)照样生效。举例:config 给 `github.com` 配了跳板机,你临时换 key —— 结果是**照走跳板机 + 用你的临时 key**,各干各的。

### 它自己家的三兄弟排序

> **`GIT_SSH_COMMAND`(环境变量,临时)> `git config core.sshCommand`(持久)> 老古董 `GIT_SSH`**

想"这个仓库永远用某把 key",别每次敲环境变量,钉死在仓库里:

```bash
git config core.sshCommand "ssh -i ~/.ssh/id_ed_qan -o IdentitiesOnly=yes"
```

---

## 6. gh CLI 的懒人哲学

**发现:`gh auth switch` 不带参数会自动切——只登了两个账号时,它一声不吭切到另一个;三个以上弹菜单让你选。** 这背后是 gh 一以贯之的哲学:**能猜到你要啥,就不烦你。** 同款骚操作:

- **`gh pr checkout 1234`** —— 把别人的 PR 一键拉到本地跑起来,不用手动 `git fetch` 那串 refs。Review 神器。
- **`gh pr create --fill`** —— 建 PR 时自动拿 commit 信息填标题和正文。加 `--web` 建完直接开浏览器。
- **`gh browse`** —— 秒开当前仓库的 GitHub 页面;`gh browse path/to/file.py:42` 直接跳到某文件某行,发链接绝了。
- **`gh repo clone owner/repo`** —— clone 不用写全 URL,而且自动用 `gh auth` 的凭证,不用操心走 SSH 还是 HTTPS。
- **`gh run watch`** —— 提交后实时盯 CI/Actions,跑完弹通知,不用刷网页。
- **`gh api /repos/{owner}/{repo}/issues`** —— 核武器。任何 API 端点都帮你带着登录态去敲,脚本化通吃。
- **`gh alias set co "pr checkout"`** —— 把长命令存成短命令,以后 `gh co 1234` 收工。

---

## 7. 一台机器多个 GitHub 账号

**先认清:你要解决的是两个独立身份,别混为一谈——**

1. **SSH 身份**:push/pull 时 GitHub 认哪把钥匙(有没有权限)。
2. **Commit 身份**:提交上署的 `name/email`(记录里显示是谁)。

这俩互相独立!很多人 SSH 配对了,结果公司仓库里全是个人 gmail 的提交,尴尬到脚趾抠地。两块都要配。

### 7.1 SSH 身份:Host 别名大法

问题根源:两把 key,连的都是同一个 `github.com`,SSH 猜不出用哪把。解法是在 `~/.ssh/config` 里造**假域名**,各绑一把 key:

```ssh-config
# 公司号(Qantas)
Host github-qantas
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed_qan
    IdentitiesOnly yes

# 个人号
Host github-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed_personal
    IdentitiesOnly yes
```

- `Host github-qantas` 是你**自己编的别名**,不是真域名。
- `HostName github.com` 是别名背后真正连的。
- `IdentitiesOnly yes` 是多账号必加的"闭嘴锁"。

然后 **remote URL 用别名替换域名**:

```bash
# 公司仓库
git@github-qantas:qantasloyalty/edr-airflow-dag-cli.git
# 个人仓库
git@github-personal:<你的用户名>/xxx.git
```

已有仓库改一下:`git remote set-url origin git@github-qantas:...`。

> 口诀:**别名区分身份,HostName 指向真身。**

### 7.2 Commit 身份:按目录自动切换

在 `~/.gitconfig` 用 `includeIf`,把公司项目全放一个文件夹,自动署公司邮箱:

```ini
[includeIf "gitdir:~/work/"]
    path = ~/.gitconfig-qantas

[includeIf "gitdir:~/personal/"]
    path = ~/.gitconfig-personal
```

`~/.gitconfig-qantas`:

```ini
[user]
    name = Todd Zhang
    email = todd@qantas.com.au
```

**效果:仓库在 `~/work/` 底下就署公司邮箱,在 `~/personal/` 底下署个人的。** 目录即身份,手都不用动。

> ⚠️ 坑:`gitdir:` 路径**结尾的 `/` 别漏**;它匹配的是仓库所在目录。

---

## 8. 企业版 GHE + 多 host 混用

场景:公网 `github.com`(开源/个人)+ 公司自建 **GitHub Enterprise**(内网)同机共存。

**心法:GHE 和 github.com 是两个完全不同的服务器,不只是两个账号——要在"多 host"上再叠"多账号",SSH 和 gh 各配一套。** GHE 有它自己的域名,比如 `github.qantas.com.au`。

### 8.1 SSH:三个 Host 块摞起来

在第 7 节基础上加一块:

```ssh-config
Host github-qantas          # 公网公司号
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed_qan
    IdentitiesOnly yes

Host github-personal        # 公网个人号
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed_personal
    IdentitiesOnly yes

Host ghe                    # 内网 GitHub Enterprise
    HostName github.qantas.com.au   # ← 换成你司真实 GHE 域名
    User git
    IdentityFile ~/.ssh/id_ed_ghe
    IdentitiesOnly yes
```

对应 URL:`git@ghe:team/some-repo.git`。

**GHE 两个特有坑:**

1. **known_hosts 指纹不一样。** 第一次连会重新认脸(正常,它是另一台服务器)。若撞上 `REMOTE HOST IDENTIFICATION HAS CHANGED`,别急着删 known_hosts,先找平台组确认是官方轮换还是真出事。
2. **可能走非标端口或跳板机。** 在那个 Host 块加 `Port <端口>` 或 `ProxyJump <跳板机>`,`git@ghe:...` 会自动带上。

### 8.2 gh CLI:一个工具管两个 host

gh **原生支持多 host**:

```bash
gh auth login                                  # 默认 github.com
gh auth login --hostname github.qantas.com.au  # 内网 GHE
gh auth status                                 # 两个 host 一起列出来
```

关键规则:**gh 命令默认只对 github.com 生效**,操作 GHE 要指明:

```bash
gh repo list --hostname github.qantas.com.au   # 临时
export GH_HOST=github.qantas.com.au            # 整段会话切过去
```

> 两个维度别混:**host 是"哪台服务器"(`--hostname`/`GH_HOST`),`gh auth switch` 是"这台服务器上哪个人"。**

### 8.3 速查表

| 维度 | 公网 github.com | 内网 GHE |
|---|---|---|
| SSH 别名 | `github-qantas` / `github-personal` | `ghe` |
| 真实域名 | github.com | github.qantas.com.au |
| gh 登录 | `gh auth login` | `gh auth login --hostname ...` |
| gh 切换 | 同 host 用 `gh auth switch` | 换 host 用 `GH_HOST`/`--hostname` |
| 署名 | 按目录 `includeIf` | 同左,通常公司邮箱 |

---

## 9. HTTPS + SAML SSO:没有 SSH 的世界

场景:公司禁掉 SSH,只准 HTTPS,还套了 SAML 单点登录。

**核心:没有 SSH key 了,你的"钥匙"变成一个 Personal Access Token(PAT);而 SSO 最大的坑是——token 建好还不够,你必须再给它"盖一个组织授权章",否则访问组织仓库会诡异地报 404。**

### 9.1 为什么走 HTTPS + Token

SSH 被禁 → 只能 HTTPS → 拉私有库要认证 → GitHub 早就不让用账号密码 → 用 **PAT**(能设权限、设过期、可单独吊销)。

- **Classic(经典版):** 一个 token 通吃所有仓库,按大类勾权限(`repo`、`read:org`、`workflow`)。
- **Fine-grained(细粒度版):** 精确到某几个仓库、只读。更安全,大厂常强制。

### 9.2 SSO 那个"盖章"坑(90% 的人栽这)⚠️

token 建好后**能访问个人仓库,一碰组织仓库就 404 或 "SAML SSO required"**。很多人以为是权限没勾对,改半天——方向全错。

真相:token 默认**没被授权给那个组织**。去 token 设置页,在这个 token 旁点 **"Configure SSO" → 对目标组织 Authorize**,盖完章才通。

> 💡 作者视角冷知识:为什么是 **404 而不是 403**?报 403("禁止")等于变相承认"这私有仓库存在,只是你没权限",会泄露仓库是否存在。GitHub 故意报 404("查无此物")防信息泄露。**所以 SSO 场景看到莫名其妙的 404,第一反应该是"token 没授权给组织",而不是"路径打错了"。**

### 9.3 最省心:让 gh 全包办

手动配 git 的 credential helper 很烦,直接用 `gh`:

```bash
gh auth login --hostname github.qantas.com.au   # 选 HTTPS,浏览器 OAuth,SSO 授权一起完成
gh auth setup-git                                # 把 token 注册成 git 的凭证助手
```

第二条是关键魔法:之后你用普通 `git clone https://...` / `git push`,git 自动找 gh 要 token,**再也不用手动输**。

### 9.4 Token 权限最小集 & 保命须知

够用就好:`repo`(读写仓库)、`read:org`(gh 很多命令要)、`workflow`(动 Actions 才勾)。

保命三条:
- **设过期时间**,别搞永不过期的 token(定时炸弹)。
- **别硬写进代码或 `.git/config`**,交给 gh / 系统凭证管家(macOS Keychain、Windows Credential Manager)。
- 怀疑泄露 → 设置页一键 **Revoke** 再重建。这就是 token 比密码强的地方。

### 9.5 一句话选型

| 场景 | 选谁 |
|---|---|
| 公司禁 SSH / 套了 SSO | HTTPS + Token |
| 自己机器、能开 SSH | SSH key(配一次不管过期) |
| CI/CD 流水线 | Token / deploy key / Actions 自带 `GITHUB_TOKEN` |

---

## 收尾:一张排错心智图

连不上 / 用错身份时,按这三层从上往下查:

1. **协议对不对?** URL 是 `git@...`(SSH)还是 `https://...`(HTTPS)?两条路认的凭证完全不同(第 4 节)。
2. **身份对不对?**
   - SSH:`ssh -Tv git@<别名>` 看 `Server accepts key` 是不是你要的那把(第 2、7 节);多账号确认 remote 用了别名。
   - HTTPS/SSO:404 先想"token 没授权给组织"(第 9 节)。
3. **署名对不对?** 随便看条自己的提交,邮箱是不是该账号的(第 7.2 节)。

把这三层变成肌肉记忆,以后 GitHub 连接问题基本都能 5 分钟内自己断案。

> 全文完。有踩到别的坑欢迎来找我补充 😎
