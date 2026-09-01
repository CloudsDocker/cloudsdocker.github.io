「名不正则言不顺，言不顺则事不成。」——《论语·子路》

# `git rebase origin master` vs `git rebase origin/master`

*一个空格，一个斜杠。看起来像同一句话。*

今天在 ICAP 课上，我把这两条当成同一条命令的两种拼写。接着又踩了三脚：

1. 说 `origin` 是 remote git **branch** 的 alias
2. 说 `git rebase origin master` **会报错**
3. 说 PR 已经开了、`origin/master` 又走了 20 个提交时，rebase 的代价在那 **20 个提交的作者** 头上

三句都错。错得很贴近真实团队里会出现的那种贴近。

这篇不按发现顺序讲。先给口诀，再讲为什么你会在对的地方把代价记错人。

读完你会带走：

- 斜杠是**一个本地引用**；空格是**两个参数**
- `git rebase origin/master` **不上网**；命令成功 ≠ 跟上了远端
- rebase 的病人永远是**被改写的那根 feature**，不是手术台上那 20 针

---

### 1. 🎬 开场冲突

周二上午，群里三个人在聊同一条 PR。

林海说：先 `git rebase origin/master`，历史美观。
陈冬说：别 rebase，我昨天的 commit 还在上面留了评论。
赵雪试了 `git rebase origin master`（中间没斜杠），以为会报错——结果命令绿了，人从 `feature/foo` 上消失，本地 `master` 换了身份证。

他们谁都没做错操作。错的是同一个心智模型：把空格和斜杠当成同一种「跟上 master」的写法，又把 rebase 的代价记在远端 master 那一串人头上。

界面上两条命令像兄弟；Git 里它们是两套语法。代价不写在空格里，就会记错账。

---

### 2. 🎯 30秒版本

`origin` 是远程**仓库**在本地的别名（地址簿上的人名），不是分支。  
`origin/master` 是 `.git` 里的**本地远程跟踪引用**（这人家里那扇门的复印件）。  
`git rebase origin/master`：**一个参数**，手术台 = `origin/master`，病人 = **当前分支**。  
`git rebase origin master`：**两个参数**，先 checkout `master`，再把它接到 `origin`（通常剥成 `origin/HEAD`）尖上。

| 写法 | Git 看见几个词 | 病人 | 手术台 | 代价 |
|---|---|---|---|---|
| `git rebase origin/master` | 1（一个引用） | 当前分支，例如 `feature/foo` | 本地的 `origin/master` | 不 fetch 就接到**过期复印件**；成功 ≠ 跟上远端 |
| `git rebase origin master` | 2（远程名 + 分支名） | 本地 `master` | `origin` 解析出的 commit | 往往**不报错**；人被切走，`master` 换 SHA |
| `git merge origin/master` | 1 | 当前分支（不改写旧 SHA） | 同上 | 多一个 merge commit；代价是历史分叉，不是身份证换发 |

口诀：斜杠 = 路径；空格 = 两个词（跟谁说话 + 哪根分支）。

> 📌 **本节要点**：`origin` 禁止当 branch 讲。`rebase` 的第一参数是手术台，第二参数才是病人。

---

### 3. 🧠 心智模型：手术台与病人

Git 不是「把我的分支更新一下」。它是：

- 把病人身上**相对分叉点多出来的提交**当补丁
- 一张张贴到手术台尖上
- 贴完发**新身份证**（新 SHA）

两个动词，两件事：

- `fetch` 负责把复印件换成更新的
- `rebase` 负责把病人接到**磁盘上已经在的**那根针

回到开场：

- 林海的 `git rebase origin/master`：人在 `feature/foo` 上时，病人是 `feature/foo`，手术台是本地 `origin/master`。那 20 个已经在 master 上的提交 **SHA 一个都不动**。代价在：拉过旧 `feature/foo` 的陈冬、PR 评论的锚点、CI 已经跑过的那批 SHA。
- 赵雪的空格版：并不是写错了就报错。语法合法。危险在**成功**——HEAD 停在 `master`，`feature/foo` 的 SHA **不变**，本地 `master` 反而换了身份证。

映射到 Docker 会失效：`origin/master` 像本地的 `image:latest` 缓存，`fetch` 像 `docker pull`。**失效点**：`docker pull` 之后名字还叫 `latest`；rebase 之后 C、D 变成 C'、D'，身份证全换。缓存失效 ≠ 历史改写。

> 📌 **本节要点**：把「谁被改写」和「接到谁上面」分开。搞反了就会把代价记到 20 个无辜的人头上。

---

### 4. ⚙️ 底层原理

`git rebase` 的位置参数是：

```text
git rebase [<upstream> [<branch>]]
```

|一个参数时：upstream = 那一个词，branch = **当前 HEAD 那根**，不先切走你。  
两个参数时：先 `switch` 到第二个，再把它 rebase 到第一个解析出的 commit 上。

`git rev-parse origin` 能打出 SHA，不是因为 origin 是一颗提交。远程别名本身不是 commit。Git 在这里**默默剥皮**：`origin` → 通常是 `origin/HEAD` → 远程默认分支的本地针。它**不一定**等于 `origin/master`（默认若是 `main`，就不是）。

fetch 之前若图是：

```text
远程实际:     A ← B
你 fetch 前:
  origin/master → A
  feature/foo   → A ← C ← D

不 fetch 就 rebase origin/master:
  病人接到 A（过期手术台），B 没吃到

fetch 后:
  origin/master → B

再 rebase:
  feature/foo → A ← B ← C' ← D'
  旧的 C、D 变幽灵，reflog 里还能捞
```

行前至少跑：

```bash
git remote -v
git symbolic-ref refs/remotes/origin/HEAD
git fetch origin
git log -1 --oneline origin/master
# 人在 feature 上再:
git rebase origin/master
```

🩸 **血泪提醒**：`git rebase origin/master` **不会去网上拉最新 master**。它 rebase 到的是你硬盘上可能已经过期的 `origin/master`。另一条不报错的：`git rebase origin master` 在两边都能解析时会**成功**，于是你改写的是本地 `master`。

已经 push 的 PR 分支要不要 rebase？不是绝对不该。

- 共享长期分支（`master` / `release`）→ 几乎从不 rebase
- **你自己的 PR 分支**、团队要线性历史、只有你在推 → 常常该 rebase，然后 `git push --force-with-lease`

lease = 先确认远端没人在你不知道时推过。裸 `--force` 会盖掉别人刚推上去的提交。

---

### 5. 💡 解法 + 诚实的权衡

开场三个人该怎么做：

1. 人在 `feature/foo` 上：`git fetch origin` 再 `git rebase origin/master`（斜杠、一个参数）
2. PR 已经有评论、有人基于旧 SHA 时：先问团队是否要线性历史；要就 `--force-with-lease`，并打招呼叫陈冬 `fetch` + 重置他的本地跟踪
3. 永远不要在特征分支上敲 `git rebase origin master` 当成「跟上远程」

方案的代价：rebase 之后 CI 重跑，评论变 outdated，同事本地会 diverged。  
不该用的时候：共享集成分支、有人已经在你的分支上叠了新提交、你不会用 lease。  
随时间变质：团队若口头说 rebase、手里却默认 merge，这套口诀会变成部落知识；把「先 fetch 再 rebase」写进文档或 alias，才能从部落知识变成工程产物。

---

### 6. 🛠️ 排坑自救

| 症状 | 原因 | 你动什么 |
|---|---|---|
| rebase 绿了，PR 仍然和 master 冲突 | 没 fetch，接在过期 `origin/master` 上 | `git fetch` 再 rebase |
| `Your branch and origin/foo have diverged` | 你 force push 了，同事手里还是旧 SHA | `git reflog` 看旧提交还在不在；补丁还在只是换了身份证 |
| `git log` 里昨天的 commit 没了 | 多半 SHA 换了，不是补丁蒸发 | 同事本机 `git reflog`，捞回旧 SHA；别忙 `reset --hard` 远端 |
| 人不在 `feature/foo` 上了 | 跑了两参数空格版 rebase | `git switch feature/foo`；用 reflog 看 `master` 是否被改写 |
| `cannot rebase: uncommitted changes` | index / 工作区不干净 | commit 或 stash，不是 rebase 坏了 |
| force push 被拒 | 远端有你没见过的提交 | `--force-with-lease` 就是来救这一命的；裸 `--force` 别用 |

同事说「我的 commit 没了」时先看两条：`git log --oneline` 是否还有同等补丁；`git reflog` 里旧 SHA 是否还在。区分「真丢了」和「身份证换了」。

---

### 7. 🧭 跳出这条命令：可以带走的原则

**1. 代价必须写在界面上**  
空格和斜杠在终端里长得几乎一样，代价差一个整数量级（换分支 vs 动当前分支）。界面不串代价时，人会用最像的那种读法填进去。药盒上两片颜色相近的药，一片是降压一片是降糖，出事的不是病人粗心，是标签没把代价写清楚。  
> 举一反三：你今天写的 CLI /表单，哪两个选项长得像兄弟、后果却一个可逆一个不可逆？

**2. 缓存不是源**  
`origin/master` 是本地缓存。操作缓存而不刷新，会得到一份自洽的「成功」。航空业用的陀螺仪读的是仪表，不是发动机本身；仪表卡住时，飞行员不能当它是发动机。  
> 举一反三：你依赖的那个「远程状态」，上一次刷新是什么时候？

**3. 改写身份 ≠ 更新内容**  
补丁还在、SHA 换了，在 Git 里就是另一个物件。法律上更名不改身份证号码；Git 相反，内容算身份。把同事的「commit 没了」当成数据丢失，你会乱 reset；当成身份证换发，你会先翻 reflog。  
> 举一反三：下次有人说东西丢了，先问是实体丢了，还是指针换了。

---

### 8. ✅ 立刻可以做的事

1. 任意一个真实仓库里跑：`git remote -v`、`git symbolic-ref refs/remotes/origin/HEAD`、`git rev-parse origin` 和 `git rev-parse origin/master`（或 `origin/main`），看三者 SHA 是否同一颗。
2. 在纸上写两行，不要真 rebase：`git rebase origin/master` vs `git rebase origin master` ——病人是谁，会不会切分支。
3. 非技术：下次代码评论里如果有人写「rebase 一下 master」，追问一句：斜杠还是空格？谁的 SHA 会变？

误解清单（课上原话，已纠正）：

- origin = remote branch 的 alias → origin = 远程**仓库**别名
- 空格版 rebase 会报错 → 往往成功，危险在成功
- rebase 的代价在 master 上那 20 个作者 → 代价在被改写的 feature、同事的旧指针、PR 锚点

*身份证换了，不代表人没了；命令绿了，不代表你跟上了世界。*

> 待验证 / 未想清楚：本仓库默认分支到底是 `master` 还是 `main`，写文章前应在真仓库里把 `symbolic-ref` 贴一次作为真实 artifact。还没把这篇升到 `_posts/`。
