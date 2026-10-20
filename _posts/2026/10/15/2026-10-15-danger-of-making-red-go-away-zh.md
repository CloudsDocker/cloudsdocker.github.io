---
title: "眼见为真有时候会杀掉你一天的时间"
header:
    image: /assets/images/2023-02-20-how-to-auto-test-via-headless-browser-in-python.jpg
date: 2026-10-15
tags:
 - devops
 - security
 - git
 - engineering-culture
permalink: /blogs/tech/zh/danger-of-making-red-go-away
lang: zh
layout: single
category: tech
---
> “地图不是疆域。” —— Alfred Korzybski

结合最近笔者在工作中遇到的一个git相关的错误，一开始看起来简单直接，但是前前后后花了多半天时间，才搞清楚事件的来龙去脉，平时你看到的一个错误小红点，可能只是冰山一角，需要升维思考或者换个角度才可以认识问题的全貌。
下面一起开始这个总是的算盘之旅吧。

*从“让 commit 跑起来”到“搞清楚它为什么跑不起来”——这中间隔着一个差点推上公开仓库的 OAuth 密钥。*

我在一次 `git commit` 卡在了这一行,光标不动了:

```
Check for added large files..............................................Passed
Detect hardcoded secrets.................................................
```

没有报错,没有退出,就停在 `gitleaks` 这一步。第一直觉是“钩子挂了,想办法让它过去”。

这篇文章想说的,恰恰是这个直觉错在哪里。那一行 `Detect hardcoded secrets...` 是一张**地图**;真正的疆域是:一个脱缰的进程把机器压到了 load 40,以及一个 40MB 的暂存区里藏着 14 个真实的 Google OAuth 密钥。如果我顺着“让红色消失”这个目标函数走下去,两件事都会出错——先误诊,再泄密。

如果你也在 CI 或 pre-commit 前卡过、而第一反应是“怎么把它跳过去”,下面这三节就是为你准备的:

- **“卡住(stuck)”和“失败(failed)”是两种病**,用同一种药会要命——诊断前先分清是哪种。
- **安全扫描在大 diff 上吐出一百多条,不等于它在狼来了**;报警密度高,恰恰是你最该逐条看的信号。
- **allowlist 是给噪音的,不是给密钥的**;把真 token 静音掉换 CI 变绿,等于亲手把它提交进历史。

下面按“最容易踩的坑”排序,不是按我当时踩的顺序——真实顺序里我先解决的是卡死,但对你更有用的,是先建立“别急着让红色消失”这个判断。

## 一、“卡住”不是“失败”:先分清你在看哪种红

光标停住的那一刻,有两条岔路:

- **路 A**:钩子在拒绝我(exit 非零)。那是“失败”,要去看它为什么拒绝。
- **路 B**:钩子根本还没出结果,进程在空转。那是“卡住”,问题可能根本不在钩子。

我差点直接走路 A——去改 `gitleaks` 配置,想让它“别卡了”。但一条命令拦住了我:

```bash
ps aux | grep gitleaks
# 35958 ... gitleaks git --config .gitleaks.toml --redact -v   # 跑了 91 分钟 CPU
uptime
# load averages: 22.80 39.96 33.70
```

Load 40。这台机器被一个 `gitleaks git`(**注意:没有 `--staged`**)的进程压死了——它在扫**整个 git 历史**,40MB+,而 pre-commit 真正该跑的是 `gitleaks git --pre-commit --staged`,只扫暂存区,几十毫秒的事。commit 不是被钩子拒绝,是被 CPU 饥饿饿死了。那个脱缰进程还是我自己前面手滑起的后台任务。

| | 卡住(stuck) | 失败(failed) |
|---|---|---|
| 信号 | 无输出、光标不动、风扇狂转 | 明确的 exit code、报错文本 |
| 该查的地方 | `ps` / `uptime` / `top`——系统资源 | 钩子的输出、配置、被扫的内容 |
| 典型误操作 | 去改钩子配置“让它别卡” | 去加资源“让它别慢” |
| 正解 | 找到并杀掉真正占资源的进程 | 读报错,针对报错修 |

> 红色的**形状**告诉你它是哪一种病。无输出的红和带 exit code 的红,是两套诊断路径;走错一条,你会在正确的工具上做错误的手术。

(进程表、`.git/index.lock` 这类机制我在上一篇[《git 锁与进程表的陷阱》](/blogs/tech/zh/git-locks-process-table-traps)里写过,这里不重复;本文的重点在红色之后的判断。)

## 二、129 条报警,不是一团噪音——是三种东西混在一起

杀掉脱缰进程、负载回落后,真正的 `--staged` 扫描才跑起来。结果:

```
scanned ~40.49 MB (40.49 MB) in 1m1.7s
WRN leaks found: 129
```

129 条。这里有个极强的直觉陷阱:**“这么多,肯定是误报,整体 allowlist 掉得了。”** 这台机器上但凡装过扫描器的人都动过这个念头。

但我把它们按文件分了类,画面完全变了:

| 类别 | 条数 | 命中的东西 | 判断 |
|---|---|---|---|
| 噪音 | ~100 | 抓来的第三方网页 `raw_html/*.html`、笔记、2023 年日志样本里的 UUID | 不是我的密钥,安全豁免 |
| 浏览器会话 JWT | 15 | `*_auth_state.json`、`*_session.json`(Jira / Azure DevOps / GitHub 登录态) | 真 token |
| **真实凭证** | **14** | `client_secret_*.json`、`token.json`、`credentials*.json`——**Google OAuth 的 client secret 和 token** | 真密钥 |

扫描器这次是**对的**。它在一百条网页噪音里,精确地抓到了 14 条我自己的 OAuth 密钥——而且这些文件是 `M`(已跟踪的修改),意味着它们**早就在仓库里**了,我只是在给它们续命。

这就是 129 这个数字的险恶之处:它大到让你想一键静音,而静音的代价,是把混在噪音里的真密钥一起放行。报警密度高不是“降低逐条审查价值”的理由,恰恰相反——**diff 越大、报警越密,逐条分类的收益越高**,因为那正是真密钥最容易藏身、又最容易被“反正都是误报”的心态冲掉的地方。

> 把扫描器的输出当成一个布尔(“过/不过”)来优化,你就丢掉了它真正的价值:它是一个**分类器**,不是一个闸门。

## 三、allowlist 给噪音,停跟踪给密钥

一旦承认这三类是不同的东西,处理方式就必须分叉——用一种手段处理全部,要么泄密,要么把该留的源码也误删:

```toml
# .gitleaks.toml —— 只豁免"已核实"的噪音路径
'''(^|/)raw_html/.*\.html$'''           # 抓来的第三方网页
'''(^|/)web_scrawl_scratch/.*\.html$'''
'''Meta System Design Knowledge.*\.txt$'''
'''(^|/)ai/unifyxp/support/fixlog_.*\.py$'''  # 内嵌 2023 日志样本的脚本
```

```gitignore
# .gitignore —— 真凭证:从此不再跟踪
*_auth_state.json
*_session.json
client_secret*.json
credentials*.json
token.json
token-*.json
```

```bash
# 真凭证:停止跟踪,但保留磁盘上的文件
git rm --cached <那 17 个凭证/会话文件>
```

关键是那条**绝不能走的近路**:在 `.gitleaks.toml` 里把这些 `client_secret_*.json` 的路径也一起豁免掉。那样 CI 立刻变绿,commit 立刻通过——代价是把活的 OAuth 密钥,一次又一次地提交进一个公开仓库的历史。绿色会骗你说“没事了”,而疆域里,密钥正在往外走。

| | 偷懒解 | 正解 |
|---|---|---|
| 噪音(网页/笔记) | allowlist 路径 ✅ | allowlist 路径 ✅ |
| 真凭证(OAuth/token) | allowlist 路径 ❌(提交进历史) | `git rm --cached` + `.gitignore` |
| 衡量标准 | CI 变绿了吗? | 真密钥还会不会进下一个 commit? |

重扫,`no leaks found`。这一次的绿色,是真的。

## 四、`git rm --cached` ≠ 清历史:绿色之后还有一层

必须说清楚一个容易让人松懈的点:`git rm --cached` + `.gitignore` 只解决**未来**——从下一个 commit 起不再跟踪。但那 14 个 OAuth 密钥的**旧版本,仍然躺在历史提交里**,`git log` 能翻出来,克隆过这个仓库的人也都有。

所以真正的收尾是两步,和让 commit 通过毫无关系:

1. **Rotate**——把这些 Google OAuth client secret / token 作废重发。它们一旦进过公开历史,就当已泄露。
2. **清历史**——`git filter-repo` 把这些文件从所有历史提交里抹掉(会改写所有 commit hash,需 force-push,属高风险操作,要先备份)。

这就是“代码考古学”的反面:今天图省事只让绿灯亮,三个月后没人记得历史里还埋着密钥。

> `rm --cached` 让新密钥不再进门;它不会把已经进了门的请出去。

## 彩蛋:第四道红,还是同一个毛病

commit 真正提交时,又被**另一个**钩子 `check-yaml` 拦了——和 gitleaks 毫无关系。两个原因:一批 k8s 多文档 YAML(`---` 分隔,合法,但 `check-yaml` 默认不认),外加一个真语法错:

```yaml
# swagger 文件里
  title:XYX Pricing Service   # title: 后面少了个空格,整个文档解析崩了
```

这里“让红色消失”的偷懒解是 `git commit --no-verify`——一键跳过所有钩子。它能过,但会把那个坏掉的 YAML 一起带进去。正解是两个真修复:给 `check-yaml` 加 `--allow-multiple-documents`(多文档本就合法),把 `title:XYX` 补上空格。同一个毛病,第四次出现:**绿色不是目标,它只是目标的影子。**

## 五、rebase 冲突:最像“我是不是敲错命令了”的一道红

commit 终于过了,接着 `git pull --rebase` 同步远端,它停下来吐出 `CONFLICT`,4 个文件。那一刻最自然的念头是:**“我是不是命令用错了?”**

没有。命令是对的。**rebase 冲突根本不是报错**——它是 git 在诚实地告诉你:你这个提交,和远端那几个更新的提交,改到了同一段内容,它不敢替你选,所以停下来问你。

| 普通人的看法 | 资深工程师的洞察 |
|---|---|
| “报 CONFLICT 了,我 rebase 搞砸了” | rebase 本就会在重叠改动处停下——这是设计,不是故障 |
| 慌了,`git rebase --abort` 一把退回 | 先看冲突**长什么样**,再决定 abort 还是逐个解 |

真正的根因,在更早一步:**一次 `git add -A` 把工作区 3487 个文件全塞进了一个提交**,其中很多是文件的**旧版本**,而远端那几个新提交刚好动过同一批文件。旧版撞新版,rebase 必须二选一。那 4 个冲突,**没有一个来自真正要做的安全修复**——全是被大批量顺带捎上的。

这里“让红色消失”的偷懒解有三种,每种都更糟:`git rebase --abort`(放弃同步)、`--skip`(悄悄丢掉自己的提交)、或 `push --force`(拿旧版把别人的新工作碾掉)。正解是读懂冲突的两侧——rebase 里 `ours` 是你正站上去的那个新基(远端),`theirs` 是你正在重放的提交(你的旧版)——按文件取不丢工作的那一侧,把真有用的改动留出来,再 `--continue`。

> 一把梭的 `git add -A` 不是省事,是把“我没想清楚要提交什么”这件事,延后到 rebase 冲突时连本带利还给你。

## 四道红色,四条岔路

| 红色 | 偷懒解(让它消失) | 正解(搞清为什么) | 代价差 |
|---|---|---|---|
| commit 卡死 | 改 gitleaks 配置“让它别卡” | `ps`/`uptime` 找到脱缰进程杀掉 | 在错的工具上做手术 |
| 129 条密钥报警 | 整体 allowlist | 按类分:噪音豁免、密钥停跟踪 | 把 14 个 OAuth 密钥推上公开仓库 |
| check-yaml 失败 | `--no-verify` 跳过 | 加 `--allow-multiple-documents` + 修 typo | 把坏 YAML 带进主干 |
| rebase 冲突 | `--abort` / `--skip` / `--force` | 读懂 ours/theirs,按文件取安全侧再 `--continue` | 丢掉自己或别人的工作 |

四行红色,四次同样的诱惑:把目标函数设成“让它变绿”。而每一次,变绿的最快路径,都正好是最坏的工程决策。

## 立刻可以做的事

1. 在你自己的仓库跑一次 `gitleaks git --pre-commit --staged -v`,把结果**按文件分类**,别只看总数——总数是用来吓人的,分类才是用来决策的。
2. 搜一遍有没有被跟踪的凭证产物:`git ls-files | grep -iE 'client_secret|credentials|token.*\.json|_auth_state|_session\.json'`。有就 `git rm --cached` + 加进 `.gitignore`。
3. 若上一步命中了东西,它们大概率已在历史里:把对应的密钥**全部 rotate**,再决定要不要 `git filter-repo` 清历史。
4. 给 pre-commit 的 `check-yaml` 加 `args: ['--allow-multiple-documents']`,如果你的仓库里有 k8s 清单——省得将来有人用 `--no-verify` 绕过整条安全链。
5. 把“这条红是 stuck 还是 failed”写进你 debug 的第一步,而不是凭手感改配置。
6. 戒掉 `git add -A` / `git add .` 的一把梭:按主题分批 `add`,提交前先 `git pull --rebase` 站到最新点上——大多数 rebase 冲突都是“旧版撞新版”,从源头就能避开。

---

*CI 变绿从来不是你的目标,它只是你真正目标投下的影子。盯着影子调参,你会在某个深夜,把一把本该作废的密钥,亲手推成全世界可见的历史。*
