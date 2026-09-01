---
title: "从 git bundle 到 filter-repo:一次密钥泄露清理全记录"
date: 2026-08-02
categories: [engineering, git, security]
tags: [git, filter-repo, git-stash, subprocess, secret-purge, devops]
---

某天你发现仓库历史里躺着一个不该出现的密钥文件。接下来要做的不是慌,是按顺序打出一套组合拳:先备份,再取证,最后动刀重写历史,顺手把执行这套流程的脚本本身也升级一下。这篇是这套完整流程的技术拆解,四个部分,一次讲透。

## Part 1: git bundle —— 动刀前先把整个仓库"打包封存"

先说结论:这是教科书级别的"在做仓库历史重写（比如清除泄露的密钥）之前先留一条退路"的操作。

```bash
W=~/.secret-purge-20260802
git bundle create $W/original-history-backup.bundle --all
chmod 600 $W/original-history-backup.bundle
git bundle verify $W/original-history-backup.bundle
```

### 🎯 30秒版本

`git bundle` 就是把整个 Git 仓库（所有分支、tag、commit 对象）打包成**单个文件**,本质上是一个自包含的 pack file + 引用列表。它不需要网络、不需要 Git server,`.bundle` 文件本身就能被当成一个远程仓库来 `clone`/`fetch`。在做 `git filter-repo`/`BFG` 这种破坏性的历史重写之前,先 `git bundle create --all` 存一份,等于给自己留了一个"如果重写搞砸了,能瞬间时光倒流"的存档点。

### ⚙️ 底层原理

- **`--all`**:等价于 `--branches --tags`,把 `refs/heads/*` 和 `refs/tags/*` 全部引用指向的可达对象都打进 bundle,但**不包含 stash、reflog、以及未被任何引用指向的悬空 commit**。
- 文件格式本质上是:一个纯文本 header（列出打包的 ref 及其 SHA、以及 prerequisite 行）,后面紧跟一个标准的 Git **pack file**（跟 `git push` 传输的数据格式一模一样）。
- `chmod 600` 不是 Git 的事,是纵深防御:这份备份里如果原本就有泄露的密钥（大概率有,因为就是为了清它才做的备份）,这份备份本身就是敏感文件,权限必须锁到只有 owner 能读写。
- `git bundle verify` 做的事:解析 header,检查 prerequisite commit 是否存在,并做 pack file 的完整性校验（相当于轻量版的 `git fsck`）。

### 🔬 面试连环炮

**Q:`--all` 会不会漏掉什么?**
> 会漏掉 stash（`refs/stash`）和 reflog。密钥如果只存在于被 `amend`/`rebase` 覆盖前的旧 commit（现在只活在 reflog 里）,这个备份不会保存它——但这恰恰是要清理的对象,除非你想留一份"清理前的完整取证快照"。

**Q:想连 reflog 和 stash 也备份怎么办?**
> ① `git bundle create backup.bundle --all $(git rev-list -g --all)`;② 更暴力:直接 `tar czf backup.tar.gz .git`,物理复制整个 `.git` 目录,是唯一 100% 无损的方案。

**Q:verify 失败的典型场景?**
> 增量 bundle 缺 prerequisite commit,或者传输中断导致文件损坏,pack file 的 SHA 校验和对不上会直接报 `fatal: index-pack failed`。

### 🏗️ 大厂怎么用

Google 的 Android/AOSP 早期同步、跨数据中心离线迁移、金融/合规场景做"清理前状态"的审计留痕——`bundle` 是行业标准操作,不是多此一举。

### 💸 高压场景版

在金融科技这种对审计链完整性极度敏感的环境,备份文件通常要求写入 WORM 存储或加密归档,而不是只靠文件权限。更重要的是:密钥清理之后,旧密钥必须立刻在源头轮换（rotate）——这比清 Git 历史本身重要一百倍。

### 🌉 跨学科视角

这套"先备份、再动手术"的流程,跟医院手术前先给病人验血备血是一回事——`git bundle` 就是你的"备血袋"。

### 🥋 一句话总结

**在对 Git 历史动刀之前不做 bundle 备份,就跟外科医生不验血型直接开刀一样——不是艺高人胆大,是缺乏最基本的失败预案。**

---

## Part 2: git stash —— 把"藏起来的第三个爹"挖出来

`bundle` 备份的是已提交的历史,但 `git stash` 里可能还藏着**从未提交过**的敏感文件。这一段就是在挖那部分漏网之鱼。

```bash
git stash show -p stash@{0} > tracked.patch
git show --name-only --pretty= stash@{0}^3   # 未跟踪文件
git show stash@{0}^3:$f                       # 取出具体内容
```

### 🎯 30秒版本

一次 `git stash -u`（保存未跟踪文件）在底层其实创建了**最多三个 commit**:一个记录已跟踪文件的改动（parent 2）,一个记录未跟踪文件（parent 3）,外加 index 状态（parent 1）,最后拼成一个合并 commit。普通 `pop` 会自动拼回工作区,但要"只取证不恢复"就得手动 `git show` 这几个隐藏父节点。

### ⚙️ 底层原理

```
stash@{0}          <- 一个特殊的 merge commit,指向 refs/stash
  ├── ^1  = HEAD 快照
  ├── ^2  = index（已 staged）的改动快照
  └── ^3  = untracked/-u 保存的文件快照（仅当用了 -u 或 -a）
```

`^3` 是关键,它不是 diff,而是一个独立的完整 commit。`git show stash@{0}^3:$f` 用 `commit:path` 语法直接从对象库 cat 出原始字节,不落地工作区、不碰 index。

### 🔬 面试连环炮

**Q:不加 `-u` 时 `^3` 存在吗?**
> 不存在。只在显式加 `-u`（untracked）或 `-a`（all）时才会创建。

**Q:`stash -u` 有什么隐藏代价?**
> 会额外生成一整棵未跟踪文件的 tree + blob 对象,这些对象**不会被普通 `git gc` 自动清理**,因为 `refs/stash` 本身是可达引用——这也是很多人"没提交什么但 `.git` 却越来越大"的隐藏原因。

**Q:`stash drop` 真的能删干净吗?**
> 不能。真正抹掉必须在 `stash drop` 之后再执行 `git reflog expire --expire=now --all && git gc --prune=now --aggressive`,这一步才是真正的粉碎,而不是扔进回收站。

### 🏗️ 大厂怎么用

不少公开的密钥泄露事故复盘里都出现过同一个模式:工程师 `stash -u` 联调用的临时密钥,后来 `stash clear` 以为清干净了,结果安全扫描工具从悬空对象里依然挖出了密钥——因为没做 `gc --prune=now`。

### 💸 高压场景版

在受监管的金融代码库里,`git stash` 往往是被制度性劝退甚至工具层面禁用的对象,因为它是一个游离于 commit 历史之外、不触发任何 hook 的审计盲区。很多合规团队直接在 `pre-push` hook 里检查 `git stash list` 是否为空。

### 🌉 跨学科视角

`stash` 的三 parent 结构,很像病历系统里的"隐藏病史"——正式病历（commit history）之外,还有那些"做过但没写进正式病历"的记录（stash 里的未跟踪文件）。审计如果只看 `git log`,会漏掉 `refs/stash` 里那些真实发生过的敏感数据。

### 🥋 一句话总结

**git stash 不是"没发生过",它只是把证据从病历首页移到了病历附录第三页——真正的密钥清理,必须连附录一起烧。**

---

## Part 3: git filter-repo —— 真正的历史手术刀落地时刻

前两步是备血和取证,这一步才是真正开刀——`--invert-paths` 把含密钥/敏感备份的文件从整个提交历史里物理抹除,`--replace-text` 顺手把散落在其他文件里的密钥字符串批量脱敏。

```bash
nohup setsid git filter-repo --force \
  --replace-text $W/replacements.txt \
  --path ufiz/tfn/auto_aws/token_output.txt \
  --path src/main/code/env/mac/.zshrc.bak.20260731-082026 \
  --path src/main/code/env/mac/.zshrc.bak.20260731-082111 \
  --invert-paths \
  > $W/filterrepo.log 2>&1 < /dev/null & disown
```

### 🎯 30秒版本

`git filter-repo` 不是在**改**历史,是在**重建**历史——它遍历每一个 commit,重新计算 tree（删掉指定路径的文件、替换指定文本）,再重新生成一条全新的 commit 链,新旧 commit 的 SHA 全部不同。

### ⚙️ 底层原理

- **重写不是编辑,是重新构建 DAG**:commit 对象里存着 tree SHA + parent SHA,SHA 是内容的哈希。改动一个 commit,它之后所有子孙 commit 的 SHA 全部要跟着变——这就是为什么这类操作是"一次性核弹"。
- **`--path X --invert-paths`**:先构建"哪些路径要保留"的规则集,再反转成"哪些路径要删除",对每个 commit 的 tree 做一次剪枝。如果剪枝后 tree 和 parent 完全一样,这个 commit 会被整个跳过（prune empty commits）。
- **`--replace-text`** 对仓库里每一个 blob 做字节级扫描替换,比 path 过滤慢得多——这也是为什么要用 `nohup ... &` 后台跑。
- **`setsid`**:让子进程脱离当前的 controlling terminal,开一个全新的 session,从进程组根源上切断"父终端死了连带我也死"的信号链;`disown` 让 bash 的 job control 表也不再追踪这个进程。

### 🔬 面试连环炮

**Q:为什么要求在干净的 clone 上跑?**
> 因为会强制重写所有引用,旧 SHA 全部作废,一旦跑错没有 undo,除非有 bundle 备份。

**Q:删除的文件会不会残留在对象库里?**
> 会残留在旧的 `.git/objects` 里,但新历史里不可达。`filter-repo` 跑完默认自动 `reflog expire` + `gc --prune=now`,这是它比 `filter-branch` 强的地方。

**Q:多个 `--path` 是 AND 还是 OR?**
> OR。每个 `--path` 都会把匹配路径加进候选集合,多个是并集。

**Q:中途被 kill 会不会损坏仓库?**
> 不会永久损坏。`filter-repo` 先在新对象库里构建完整新历史,最后原子性地把 refs 切过去,中途夭折大概率原 refs 还指向旧历史,但需要清理残留的锁文件/备份目录才能重跑。

### 🏗️ 大厂怎么用

`git filter-branch` 因为极慢且极易写出破坏历史完整性的规则,官方文档已标注 deprecated;`filter-repo` 是 Git 官方现在唯一背书的重写工具,速度通常快一个数量级以上。超大 monorepo（Google Piper、Meta fbsource）从来不用这类全历史重写工具,应对策略几乎全部前移到"提交前拦截"。

### 💸 高压场景版

`filter-repo` 跑完只是第一步:必须强制所有协作者重新 clone 而不是 `pull`;必须清理所有下游镜像（CI 缓存、内部制品仓库、fork）;必须留一份完整的操作审计记录。真正兜底的永远是密钥轮换,跟仓库清没清干净无关。

### 🌉 跨学科视角

这是考古学里的"地层置换"——不是从某一层挖出一件文物拿走,而是说"这一整层地质剖面,只要含有这个矿物成分,我要替换掉,然后让上面所有地层的年代编号重新计算"。

### 🥋 一句话总结

**git filter-repo 不是在删文件,是在用新的因果链重新讲一遍你仓库的整个故事——所以在按下回车之前,你最好已经把旧故事的备份锁进了保险柜。**

---

## Part 4: subprocess.Popen(start_new_session=True) —— Python 版的"脱离父体独立生存"

这一轮把上一步的 `setsid git filter-repo & disown` 换成了纯 Python 的 `subprocess.Popen(..., start_new_session=True)`,同一个目标,不同的实现路径。

```python
p = subprocess.Popen([
    'git', 'filter-repo', '--force',
    '--replace-text', replacements_path,
    '--path', 'ufiz/tfn/auto_aws/token_output.txt',
    '--invert-paths',
], cwd=repo_path,
   stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
   start_new_session=True)
```

### 🎯 30秒版本

`start_new_session=True` 在底层等价于 C 库的 `setsid()` 系统调用——让子进程成为一个全新会话的 leader,脱离父进程所在的终端控制组。跟上一步手写的 `setsid ... & disown` 做的是同一件事,区别是 shell 版本靠拼接三个命令模拟,Python 版本用一个参数直接声明,更少的移动部件。

### ⚙️ 底层原理

- `setsid()` 做三件事:子进程成为新会话的 session leader、成为新进程组的 group leader、**失去 controlling terminal**——这一步是关键,没有 controlling terminal 意味着终端发的 `SIGHUP` 根本没有对象可以送达。
- `stdin=subprocess.DEVNULL` 是显式把子进程 stdin 重定向到 `/dev/null`,防止继承一个可能被关闭的终端 fd 导致意外的 `EOF`/`SIGPIPE`。
- **最重要的细节**:`stdout`/`stderr` 都重定向到同一个文件对象,而不是 `subprocess.PIPE`。如果用 `PIPE`,内核管道缓冲区（Linux 上通常 64KB）写满后子进程会阻塞在 write 上——而这段脚本几乎立刻打印后退出,没人去读这个管道,`filter-repo` 大概率会卡死。直接写文件完全没有这个上限问题。

### 🔬 面试连环炮

**Q:Python 脚本 `sleep 10` 后退出,子进程会不会被杀?**
> 不会,这正是 `start_new_session=True` 的意义,从根本上切断了终端信号的传递路径。

**Q:这段代码有没有检查子进程是否成功启动?**
> 没有,这是明显的健壮性缺口。`Popen()` 成功只代表 fork+exec 层面没报错,不代表运行逻辑正确。生产级写法应该在 `sleep` 后加 `p.poll()` 判断。

**Q:之后怎么可靠地检查任务是否跑完?**
> 同一进程存活期用 `p.wait()`/`p.poll()` 最准;脚本已退出只能靠 `pgrep`/`ps -p` 退化判断,但 PID 会被系统回收复用,存在假阳性风险。更可靠的是检查日志里是否出现完成标志,而不是单纯看进程是否存在。

**Q:相比直接 shell 命令,Python 包一层带来了什么工程收益?**
> 可组合性和可测试性。`Popen` 返回的对象能做结构化的状态机管理,未来接入 Airflow `PythonOperator` 这类任务编排比在 `BashOperator` 里堆砌 shell 特技要好维护得多。

### 🏗️ 大厂怎么用

`nohup`/`setsid`/`disown` 这套 shell 组合拳,在生产自动化系统里基本被认为是"个人调试可以用,写进正式脚本/CI pipeline 就是技术债"。真正的生产系统要么用 systemd/launchd 注册成正式服务,要么就用编程语言的进程管理 API 显式控制每一个细节。

### 💸 高压场景版

在受监管环境里,这种"手写脚本 + Popen 后台跑 + PID 追踪"基本是审计红线——任何进程都必须有明确的生命周期归属。`sleep(10)` 这种"发射后不管"的做法,对不可逆的历史重写操作而言,风险等级跟"手术不缝合直接走人"没有本质区别。

### 🌉 跨学科视角

`start_new_session=True` 让子进程"断脐"独立生存,跟新生儿断脐带的瞬间是同一个逻辑——断脐之后必须自主呼吸、自主维持体温。而把 stdout/stderr 显式重定向到日志文件,相当于提前给这个"独立婴儿"接好了呼吸机和监护仪。

### 🥋 一句话总结

**start_new_session=True 只解决了"子进程会不会被终端信号误杀"这一个问题——它不会替你回答"这个孤儿进程到底跑没跑完、跑没跑对",那个问题永远得靠你自己写的轮询和日志校验去回答。**

---

## 收尾:这四步拼起来是什么

备份（bundle）→ 取证（stash 挖掘）→ 手术（filter-repo 重写）→ 让手术过程本身更可控（Popen 守护化）。这四步的共同底层逻辑只有一句话:**任何对 Git 历史的不可逆操作,都必须先假设它会失败,再动手。**
