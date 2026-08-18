---
title: "第二次 Ctrl-C 之后，几百刀的实验结果变成了一个坏掉的 JSON"
header:
    image: /assets/images/hd_FileNotFoundException.png
date: 2026-08-18
tags:
 - python
 - filesystem
 - posix
 - systems
 - reliability
permalink: /blogs/tech/zh/atomic-file-write-deep-dive
layout: single
category: tech
---

> "错误永远不应该悄无声息地过去，除非它被明确地消音。" —— Tim Peters，《Python 之禅》

---

# 第二次 Ctrl-C 之后，几百刀的实验结果变成了一个坏掉的 JSON

*一行谁都写过、谁 review 都会放过的代码，和它背后三个坑*

周六上午十点，同事阿哲在群里 @ 我：

> "你昨天那个 eval 是不是挂了？我这边 `json.load` 直接 `JSONDecodeError`。我准备重跑一次。"

我愣了一下。**没挂啊。** 我昨晚亲眼看着它跑完的，进度条走到 100%，日志最后一行是 `run finished`，文件我也 `ls` 过了，`cot_gpt-5-mini_dev_natural_limitall_seed42.metrics.json`，名字一个字符都不差，就躺在输出目录里。

我们俩为这个来回确认了二十分钟。他坚持"这个文件是坏的，所以这次 run 失败了"；我坚持"这次 run 明明成功了"。**两个人看着同一个文件，得出了完全相反的结论，而且各自都有充分的证据。**

真相是：那个 run 确实跑完了。但在最后写 metrics 的那几毫秒里，我按了第二次 Ctrl-C —— 因为第一次按下去没反应，我以为没生效。进程死在了写文件的中间。

磁盘上留下的**不是"没有文件"，而是一个文件名完全正确、内容截断的 JSON**。

**我们俩谁都没判断错。** 阿哲看到的是一个坏文件，他的推论完全合理；我看到的是一次成功的 run，我的推论也完全合理。错的是那个文件——它在**撒谎**。而让它有能力撒谎的，是我三天前写下的、阿哲 review 过、两个人都觉得没问题的一行代码。

那次实验跑了六个小时，烧掉几百刀的 API 额度。而它的全部产出，就是那一个文件。

这篇文章把这行代码的复盘完整写下来：先逐行解剖，再把其中两行展开成两个独立的话题，最后讲讲这件事真正教给我的东西——它和文件系统关系不大。

---

## 🎯 30 秒吃透：`open(w)` 从来就不是一个操作

我当时写的是这一行：

```python
metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
```

**这几乎是所有开发者的默认写法**，而且它看起来还挺讲究：`json.dumps` 先完整序列化再写（比 `json.dump(fh)` 强），`encoding="utf-8"` 显式写了（比裸 `write_text` 强）。Code review 里没人会拦它——阿哲就没拦。

问题在于，`write_text` 展开之后是三个操作：

```
open(path, "w")  →  truncate（文件瞬间变 0 字节）
fh.write(...)    →  逐步填回去
fh.close()
```

在 truncate 之后、write 完成之前，磁盘上躺着一个**文件名完全正确、内容残缺**的文件。

它至少有四个问题，而且**全部是静默的**：

| # | 问题 | 触发条件 | 你会看到什么 |
|---|---|---|---|
| 1 | **不是原子的** | Ctrl-C / OOM kill / 容器 evict | 名字正确、内容截断的 JSON |
| 2 | **读者会读到半截** | 有人在那几毫秒里 open | 不完整的内容，且无法分辨 |
| 3 | **断电后内容可能是空的** | 数据只到 page cache | 0 字节的文件 |
| 4 | **权限跟着 umask 走** | 换个环境部署 | 跨环境权限不一致 |

原子写的思路只有一句话：**永远不要就地修改，只做名字的瞬间切换。**

> 📌 **本节要点**：崩溃留下的最糟糕的东西不是"没有文件"，而是"一个骗人的文件"。前者会报错，后者会让两个同事吵二十分钟。

---

## 🧠 心智模型：合同的签署

一份并购协议可以起草 30 版，律师逐条改，双方来回谈。**在签字之前，所有草稿的法律效力精确等于零。** 你不能说"这份合同已经生效了 60%"。

签字那一瞬间，效力从 0 跳到 100，中间没有任何可观察的过渡态。**这就是 `os.replace`。**

而**公证与备案**是另一回事：签完字，文件还只在你抽屉里；送去公证处存档，才经得起火灾。**这就是 `fsync`。**

两条独立的保障，回答两个不同的问题：

- "有没有可能有人看到一份半生效的合同？" → 靠签字的瞬时性（**原子性**）
- "办公室烧了这份合同还在吗？" → 靠异地存档（**持久性**）

回到那个周六上午：阿哲拿到的，正是一份"签了一半的合同"。而 `write_text` 的根本问题在于，**它让"签了一半"成为一个可观察的状态**。

所以我把它换成了这个：

```python
def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    """同目录建临时文件 → fsync → os.replace（同 fs 内 rename 是原子的）。"""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)          # 原子
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
```

八行，看着挺唬人，写完还挺满意。

**然后我复盘的时候发现，这八行里有两个真 bug 和一个重大遗漏。**

> 📌 **本节要点**：原子性和持久性是两个不同的问题，由两个不同的机制解决。`os.replace` 管"没人看到半截"，`fsync` 管"断电后还在"。搞混这两件事，是这个话题里所有困惑的源头。

---

## ⚙️ 逐行拆解

### `tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")`

三个参数，每个都在解决一个具体问题。

**`dir=path.parent` —— 这是整个函数最关键的一个参数。**

`rename(2)` 的原子性**只在同一个文件系统内成立**。跨文件系统 rename 直接返回 `EXDEV`（Invalid cross-device link），因为 rename 本质是"改一个目录项的 inode 指向"，而 inode 编号在另一个文件系统里没有意义。

如果这里写默认的 `/tmp`，在容器里几乎必然踩坑：`/tmp` 常是 tmpfs，输出目录是 overlayfs 或挂载卷——两个文件系统。`os.replace` 抛 `OSError: [Errno 18]`。

🩸 **血泪提醒**：这个坑**本地开发永远不报错**（都在同一个 ext4 或 APFS 上），CI 一上容器就炸。它不是逻辑错误，是**环境假设错误**——这类 bug 最贵，因为你在本地怎么复现都复现不出来，只能在 CI 日志里对着一个 Errno 18 发呆。（这条单独展开在 Part 2。）

**`mkstemp` 而不是 `NamedTemporaryFile` 或手拼名字。**

`mkstemp` 底层是 `open(path, O_CREAT | O_EXCL | O_RDWR, 0600)`。三个性质：

- `O_EXCL` + 随机名 = **无 TOCTOU**。不存在"检查文件不存在 → 别人抢先创建 → 你覆盖了它"的窗口。这是符号链接攻击的标准防线。
- 返回**裸 fd**，不是路径。中间没有"拿到名字再去 open"的间隙。
- 权限 **0600**，只有属主可读写——临时文件里可能有半成品敏感数据。

不用 `NamedTemporaryFile` 是因为它默认 `delete=True`，close 的时候会删掉自己，而我们恰恰要它活到 rename。

**`prefix=path.name` —— 这里是 Bug 1。**

产出的临时文件长这样：

```
cot_gpt-5-mini_dev_natural_limitall_seed42.metrics.jsonab3x9f.tmp
```

它的前 N 个字符**和真正的产物一字不差**。任何一个 `glob("*.metrics.json*")`、`ls *metrics*`、或者靠文件名区分产物的 CI 脚本，都会把这个临时文件扫进去。

修法：加个点前缀让它对 glob 隐身。

```python
prefix=f".{path.name}."   # → .cot_..._seed42.metrics.json.ab3x9f.tmp
```

（这条单独展开在 Part 3。）

---

### `with os.fdopen(fd, "w", encoding="utf-8") as fh:`

`mkstemp` 给的是**裸 fd（整数）**，不能直接 `write` 字符串。`os.fdopen` 把它包成 `TextIOWrapper`，**并把 fd 的所有权转移给这个对象**——`with` 退出时 `close()` 会关掉底层 fd。

所有权转移有个后果：**`os.fdopen` 本身如果抛异常（比如 encoding 名字打错），fd 就泄漏了**——既没被 fdopen 接管，也没被你手动 `os.close`。而下面的 `except` 只 unlink 了路径，没关 fd。长跑进程里这是文件描述符泄漏。

严格写法是把 fdopen 也纳入保护，或者用 `os.close(fd)` 兜底。实践中 encoding 是硬编码的，这个分支永远不会走——**但值得知道它存在，因为面试官会问"fd 的所有权在哪一刻转移"**。

`encoding="utf-8"` 是必须显式写的：Python 3.15 之前，不写就跟随 locale，Windows 上默认是 cp1252 / GBK。你的 metrics 里只要有一个中文或 emoji，Linux 上写得好好的，Windows 上 `UnicodeEncodeError`。

---

### `json.dump(payload, fh, indent=2)` —— 这里是 Bug 2

`json.dump` 是**流式**的：它一边遍历对象一边往 `fh` 写。

如果 `payload` 里混进一个不可序列化的对象（`datetime`、`Path`、`Decimal`、numpy 标量都是常客），`TypeError` 会在**已经写出一部分之后**抛出。

在这个函数里后果不严重（临时文件会被 unlink），但它揭示了一个更好的结构：**先完整序列化成字符串，成功了再碰 I/O。**

```python
text = json.dumps(payload, indent=2)   # 会失败就在这里失败，此时磁盘上什么都没发生
```

这是"把失败往前推到无副作用的阶段"。序列化错误是纯计算错误，不该和 I/O 错误纠缠在同一个清理路径上。而且 `json.dumps` 一次性构造字符串，`fh.write(text)` 一次系统调用写完，比流式的多次小 write 更快。

（代价是大对象的内存峰值翻倍。metrics 文件几十 KB，无所谓；GB 级导出就该流式。）

---

### `fh.flush()` —— 大部分人搞错它和 fsync 的关系

数据从你的变量到磁盘，要穿三层：

```
Python str
   ↓  fh.write()
① Python 用户态缓冲区（TextIOWrapper + BufferedWriter，默认 8KB）
   ↓  fh.flush()  →  触发 write(2) 系统调用
② 内核 page cache（此时 read() 已经能读到，但断电就没）
   ↓  os.fsync()  →  触发设备刷写
③ 物理介质
```

**`flush()` 只做 ①→②，`fsync()` 只做 ②→③。**

🩸 **血泪提醒**：顺序不能反、不能省。如果不 flush 直接 fsync，数据还躺在用户态缓冲区里，内核里根本没有这些字节——**fsync 会成功返回，并且什么都没同步**。这是本文最阴险的一个静默失败：你的代码里有一行 `os.fsync`，你的 code review 通过了，你的持久性保证是零。

（`with` 块退出时会自动 flush，但那发生在 fsync **之后**。所以必须手动提前。）

---

### `os.fsync(fh.fileno())`

强制把 page cache 刷到物理介质，防的是**断电 / 内核 panic / 虚拟机被硬拔**，不是防进程崩溃。

进程崩溃不需要 fsync：数据一旦进了 page cache（②），内核就负责了，进程死掉不影响，别的进程 read 得到，最终也会被回写。

**那为什么还要 fsync？** 因为存在一个具体的灾难序列：

```
write 完成，数据在 page cache（未落盘）
rename 完成，元数据落盘了
断电
重启 → 目录项指向新文件，但文件内容是 0 字节或垃圾
```

也就是**元数据先于数据落盘**，你得到一个"名字正确、内容为空"的文件——恰恰是原子写要防的那个东西，从后门溜回来了。

ext4 在 2009 年之后加了个 hack（Ted Ts'o 在 delayed allocation 引发大规模文件清零投诉后打的补丁）：`rename` 覆盖已有文件时会自动触发数据回写。**但这是 ext4 的特殊照顾，不是 POSIX 保证**，XFS、btrfs、各种网络文件系统上不一定成立。所以要显式 fsync。

**注意 fsync 的代价**：它是同步阻塞的，等物理确认。机械盘上几到几十毫秒，SSD 上零点几到几毫秒，网络存储上可能上百毫秒。在写几千个小文件的循环里，fsync 会是压倒性的瓶颈——那种场景要么批量写后一次 fsync 目录，要么接受弱保证。

---

### `os.replace(tmp, path)` —— 签字的那一刻

**原子性的完整定义**：任何时刻、任何观察者去 `open(path)`，看到的要么是完整的旧文件，要么是完整的新文件，**不存在第三种状态，也不存在文件短暂消失的窗口**。

底层就是 `rename(2)`，POSIX 明确要求：新名字若已存在则被移除并完成改名，且该操作相对于其他线程是原子的。

**关键点：已经打开旧文件的读者不受影响。** rename 只改目录项，旧的 inode 引用计数还有 +1 来自那个打开的 fd。读者会安安静静把旧内容读完——这是 Unix 的 inode/dentry 分离白送的好处，也是为什么 `logrotate` 能在服务运行时安全轮转日志。

**`os.replace` 而不是 `os.rename`**：POSIX 上两者一样，但 **Windows 上 `os.rename` 目标存在时直接抛 `FileExistsError`**。`os.replace` 保证跨平台的覆盖语义（Windows 下走 `MoveFileEx` + `MOVEFILE_REPLACE_EXISTING`）。

**Windows 注意事项**（如果你的 CI 有 Windows runner）：`MoveFileEx` 在目标文件**被另一个进程打开**时会失败（sharing violation，`PermissionError`）。Unix 上没这问题。杀毒软件扫描你刚写的文件时尤其容易撞上——这是 Windows 上写文件工具普遍要加重试的原因。

---

### 🔴 重大遗漏：没有 fsync 目录

`os.replace` 修改的是**目录的内容**（目录项），而目录本身也是文件，它的修改同样先进 page cache。

```
os.replace 返回成功
    ↓
新的目录项在 page cache 里
    ↓
断电
    ↓
重启 → 目录项没落盘 → 文件"回滚"到旧版本，或者两个名字都不见了
```

要真正保证"rename 已持久化"，必须 fsync **父目录的 fd**：

```python
dir_fd = os.open(path.parent, os.O_RDONLY)
try:
    os.fsync(dir_fd)
finally:
    os.close(dir_fd)
```

这是 SQLite、etcd、PostgreSQL 的 WAL 实现里都有的一步，也是**教科书原子写和网上随手抄的版本之间最常见的差距**。

（Windows 上不能 fsync 目录，`os.open` 目录直接报错，所以要包一层平台判断。）

---

### `except BaseException:` / `unlink(missing_ok=True)` / `raise`

**用 `BaseException` 而不是 `Exception` 是正确的，而且是有意的。**

`KeyboardInterrupt` 和 `SystemExit` 继承自 `BaseException` 而**不**继承 `Exception`。这个函数的整个存在理由就是"Ctrl-C 也不能留下烂摊子"——只 catch `Exception` 的话，Ctrl-C 打进来时临时文件会留在磁盘上，堆积成垃圾。

回想一下开头：**我那次事故的直接触发器，就是第二次 Ctrl-C。** 如果当时这个 `except` 写的是 `Exception`，我不但会得到一个坏 JSON，还会额外收获一个永远不会被清理的临时文件。

`missing_ok=True` 覆盖两种情况：mkstemp 之后立刻被信号打断（文件存在，删）、以及 `os.replace` 已经成功之后才出异常（tmp 已经不在了，不该报错）。

`raise` 裸抛保留原始 traceback。**这个函数只做清理，不做决策**——是重试还是放弃，是调用方的事。清理和策略分离。

> 📌 **本节要点**：这八行里，`dir=`、`flush()` 的位置、`BaseException`、以及那个缺失的目录 fsync，每一个都在防一种**不会报错的失败**。原子写的难点从来不是写对，是知道自己在防什么。

---

## 🔬 面试官追问链

**Q1: 这个函数保证的是原子性还是持久性？**

两者是**不同的属性，由不同的机制提供**：

| 属性 | 防的是 | 靠哪一步 |
|---|---|---|
| 原子性 | 读者看到半截文件 | `os.replace` |
| 持久性 | 断电后内容丢失 | `flush` + `fsync`（数据）+ fsync 目录（元数据） |

只要原子性，`os.replace` 一行就够；要持久性，三次同步一次都不能少。**在容器/云环境里，很多团队有意只要原子性不要持久性**——节点挂了整个实例都重建，fsync 的开销白付。这该是一个显式的取舍，而不是"抄了个函数不知道它保证了什么"。

**Q2: 权限有什么问题？**

有，而且很常见：`mkstemp` 建的文件是 **0600**。如果目标文件原本是 0644（其他用户可读，比如给 nginx 或另一个服务账号读），原子写之后**权限被静默收紧到 0600**，那个服务突然读不到了——而且没有任何报错，只有下游的 `PermissionError`。

修法：rename 之前按 umask 或按原文件的 mode 修正。

**Q3: NFS 上还成立吗？**

部分成立，需要小心。`rename` 在 NFS **服务端**是原子的。但 NFSv3 的客户端属性缓存（`acregmin`/`acregmax`，通常 3~60 秒）意味着**另一台客户端可能在一段时间内还看到旧文件**。原子性没被破坏（不会看到半截），但**可见性有延迟**。

另外 NFS 上 `unlink` 一个被打开的文件会触发 **silly rename**（服务端把它改名成 `.nfsXXXX`），所以清理逻辑可能留下神秘的隐藏文件。

分布式协调不要靠文件系统——那是 etcd/Consul 的活。

**Q4: 并发两个进程同时对同一个 path 做原子写会怎样？**

不会损坏，但是 **last-writer-wins，且没有任何提示**。两个 tmp 文件名不同（mkstemp 随机），各写各的，两次 rename 串行执行，后到的赢。

原子写保证的是"不会写出一个坏文件"，**不保证"不会丢一次更新"**。要防丢更新需要额外的锁（`flock`）或 CAS 语义（`O_EXCL` 创建，存在即失败）。

**Q5: 为什么不用 `os.sync()`？**

`os.sync()` 刷**整个系统**的所有脏页，是全局操作，繁忙机器上可能阻塞秒级。`fsync(fd)` 只针对一个文件。永远用后者。

顺带：Linux 上还有 `os.fdatasync()`，只同步数据不同步非必要元数据（如 mtime），略快。对新建文件没意义（size 是必要元数据，必须同步），对覆盖写有意义。

---

## 🧩 Part 2：EXDEV —— "同一个文件系统"到底指什么

上面说 rename 的原子性只在同一个文件系统内成立。那么这个边界在哪？

三个常见猜测：

| 猜测 | 对吗 |
|---|---|
| 同一个文件夹下 | ❌ 太严了。同一个文件系统内**任意两个目录**都行 |
| 同一台电脑 | ⚠️ 必要但远不充分。一台电脑上通常有 5~10 个文件系统 |
| 同一个硬盘 | ❌ 既不必要也不充分 |

**正确的边界是：同一个「挂载点」（mount）。**

## 为什么是挂载点

inode 号只在**一个文件系统内部**唯一。`/` 上有 inode 12345，`/home` 上也有 inode 12345，它们毫无关系。

`rename(2)` 干的事是：**在目录 B 里加一条"名字 → inode 12345"的记录，然后从目录 A 删掉那条记录**。整个过程**一个字节的文件内容都没动**。

所以跨文件系统 rename 在物理上就无法定义——目标文件系统里的 inode 12345 是别人的文件。内核不会"帮你"偷偷降级成 copy+delete，因为那**不是原子的**，而且可能要搬 50GB。它直接告诉你 `EXDEV`，让你自己决定。

`mv` 命令看起来能跨盘搬，是因为 **`mv` 是个程序，不是 syscall**——它先试 `rename()`，收到 EXDEV 后自己退化成 copy + unlink。这也是为什么同盘 `mv` 一个 50GB 文件是瞬间的，跨盘要跑几分钟。**这个差异你一定见过，只是没想过原因。**

## 三个反直觉的情况

**① 同一块硬盘 ≠ 同一个文件系统**

一块 SSD 分了 3 个区 = 3 个文件系统。`/` 和 `/home` 在不同分区是极常见的安装布局，它们之间 rename 直接 EXDEV。

**② 同一个文件系统 ≠ 同一块硬盘**

LVM、RAID、ZFS pool 可以让一个文件系统横跨 8 块盘。这种情况下**跨物理硬盘的 rename 完全正常**，因为逻辑上还是一个文件系统。

**③ 同一个"盘"上也可能 EXDEV**

- **btrfs subvolume**：同一个设备、同一条 `mount` 命令挂上来的，但 `/data/@snapshots` 和 `/data/@current` 之间 rename 会 EXDEV。ZFS dataset 同理。
- **bind mount**（Linux 特有的坑）：`mount --bind /data /app/data` 之后，`/data/x` 和 `/app/data/y` 的 `st_dev` **完全相同**，但 rename 仍然返回 EXDEV——因为内核检查的是 `vfsmount`，不只是 `st_dev`。

第三点很重要：**`st_dev` 相等是必要条件，不是充分条件。** 想靠 `os.stat().st_dev` 预判"能不能 rename"，会漏掉 bind mount 这一类。

## 怎么看你机器上有几个文件系统

```bash
$ df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme0n1p2  460G  210G  227G  49% /          ← ①
tmpfs           7.8G  1.2M  7.8G   1% /tmp       ← ② 内存里！
/dev/nvme0n1p1  511M   31M  481M   6% /boot/efi  ← ③ 同一块盘的另一个分区
/dev/sdb1       1.8T  900G  850G  52% /mnt/data  ← ④
```

**每一行就是一个文件系统。行与行之间 rename 一律 EXDEV。**

判断两个路径是否同属一个文件系统，看设备号：

```python
Path("/tmp").stat().st_dev == Path("/home/you/project").stat().st_dev
```

## 为什么这个坑在容器里几乎必然踩到

一个典型的 Docker 容器：

```
/           overlayfs      ← 镜像层
/tmp        tmpfs          ← 内存（很多基础镜像这么配）
/app/data   volume/bind    ← 挂载卷
/dev/shm    tmpfs
```

**四个不同的文件系统。** 于是经典失败链出现了：

```python
# 看着人畜无害
fd, tmp = tempfile.mkstemp()          # → /tmp/xxxx（tmpfs）
...
os.replace(tmp, "/app/data/metrics.json")   # → 挂载卷
# OSError: [Errno 18] Invalid cross-device link
```

**而你本地 Mac 上跑一切正常**——因为 macOS 的 `/tmp` 和你的项目目录在同一个 APFS 卷上。代码写完、测试通过、CI 一上容器就炸。

## 所以正确写法不是"检测再处理"

很多人的第一反应是加个兜底：

```python
try:
    os.replace(tmp, path)
except OSError as e:
    if e.errno == errno.EXDEV:
        shutil.move(tmp, path)   # ❌ 灾难
```

**这是最坏的写法。** `shutil.move` 跨设备时是 copy + unlink，**完全不原子**——你精心设计的原子写，在最需要它的时候静默退化成了最不安全的版本，而且没有任何日志告诉你降级了。

正确做法是让 EXDEV **在结构上不可能发生**：

```python
tempfile.mkstemp(dir=path.parent, ...)
```

临时文件生在**目标文件的隔壁**。它俩天然共享目录，共享目录就必然共享 mount，共享 mount 就必然共享文件系统。**没有检测，没有降级，没有分支——这个错误类被消除了，不是被处理了。**

## 跨机器呢

**跨机器根本轮不到 EXDEV**——你连不上另一台机器的文件系统，没有 syscall 可调。SSH/rsync/S3 全是应用层协议，不走 `rename(2)`。

唯一的例外是网络文件系统：NFS 挂上来之后，`/mnt/nfs` 就是一个正常的文件系统，内部 rename 完全合法。但 `/mnt/nfs/a` → `/home/b` 依然是 EXDEV。

顺带一个反例：**S3 没有 rename**。S3 是对象存储不是文件系统，"重命名" = COPY + DELETE 两次 API 调用，**中间那一刻两个 key 同时存在，不原子**。很多人把"写临时文件再 rename"的经验直接搬到 S3 上，然后困惑于为什么会读到不一致的状态。

> 📌 **本节要点**：`rename` 的原子性来自它只改目录项不搬数据；这也正是它跨不了文件系统的原因——inode 号出了自己的文件系统就是一串没有意义的数字。判断边界看 `df` 的行，不看硬盘也不看文件夹。

---

## 🧩 Part 3：为什么临时文件名要加一个点

回到 `prefix=f".{path.name}."` 这个改动。先看实测结果：

```python
fd1, t1 = tempfile.mkstemp(dir=d, prefix=target.name, suffix=".tmp")          # 原版
fd2, t2 = tempfile.mkstemp(dir=d, prefix=f".{target.name}.", suffix=".tmp")   # 修正版
```

输出：

```
原版临时文件: cot_gpt5_dev_seed42.metrics.jsonym6wfn0y.tmp
修正临时文件: .cot_gpt5_dev_seed42.metrics.json.lcvg6fnw.tmp

glob('*.metrics.json' )  -> ['...metrics.json']                                  ✅ 都没事
glob('*.metrics.json*')  -> ['...metrics.json', '...metrics.jsonym6wfn0y.tmp']   ⚠️ 原版被扫进来了
glob('*metrics*'      )  -> ['...metrics.json', '...metrics.jsonym6wfn0y.tmp']   ⚠️
glob('*'              )  -> ['...metrics.json', '...metrics.jsonym6wfn0y.tmp']   ⚠️

os.listdir 全部看得见: ['.cot_...tmp', 'cot_...json', 'cot_...jsonym6wfn0y.tmp']
```

**修正版那个文件在所有 4 个 glob 里都没出现，但 `os.listdir` 看得见。** 这就是全部的关键。

## `mkstemp` 的 prefix 是直接拼接，没有分隔符

```
cot_gpt5_dev_seed42.metrics.jsonym6wfn0y.tmp
                             ↑
                    随机串直接焊在 json 后面
```

公式是 `prefix + 随机 8 字符 + suffix`，中间**不插任何东西**。所以临时文件名的前 33 个字符，和真正的产物**一字不差**。

它已经不是"一个临时文件"了，它是"一个看起来像产物、名字还长了一截的东西"。

## 谁会被这个骗到

如果你的设计里**文件名承载语义**（完整的 run 叫 `.metrics.json`，不完整的叫 `.metrics.partial.json`），下游一定会有匹配文件名的代码：

```yaml
# CI 收集产物
- uses: actions/upload-artifact@v4
  with:
    path: results/*metrics*       # 把半截 JSON 也当产物上传了
```

```python
# 汇总脚本
for f in Path("results").glob("*.metrics.json*"):    # 想同时抓 .json 和 .partial.json
    data = json.loads(f.read_text())                 # 💥 JSONDecodeError
```

这里的 `*` 是为了同时匹配两种产物——**一个完全合理的写法**，但它顺手把 `.tmp` 也抓了。

## 什么时候真的会撞上

平时不会——临时文件的寿命是毫秒级。**它只在两种时刻存在，而这两种恰恰是你最需要看清目录的时刻**：

**① 崩溃残留。** 进程被 `SIGKILL`（OOM killer、`docker stop` 超时、K8s evict）打死，`except` 块**根本不会执行**，`.tmp` 永久留在盘上。输出目录里长期躺着一堆"看起来像产物"的僵尸文件，名字里还带着完整的 run 名，特别有迷惑性。

**② 并发窗口。** 一个 run 正在写文件，另一个进程（监控面板、CI 的另一个 step）同时在扫目录，正好撞上那几毫秒。复现率千分之一，排查起来极其痛苦。

## 为什么加个点就解决了

`glob` 遵循 shell 惯例：**模式里的 `*` 不匹配开头的点**。CPython 的 `glob.py` 里就一个函数：

```python
def _ishidden(path):
    return path[0] in ('.', b'.'[0])
```

模式本身以点开头时才会匹配点文件。所以 `.foo.tmp` 对 `*`、`*metrics*`、`*.metrics.json*` **全部不可见**。

**而这是平台无关的**——CPython 自己实现了这个规则，不依赖操作系统。Windows 上 `glob("*")` 同样不返回点文件。

**同时 `os.listdir` 照样看得见**，所以你自己写的清理逻辑不受影响。**该看见的看见，该屏蔽的屏蔽。**

## 这是"消除问题类"而不是"处理问题"

```python
# 思路 A：把陷阱留着，要求每个调用方都记得绕开
for f in Path("results").glob("*.metrics.json*"):
    if f.suffix == ".tmp":     # 每个脚本都得写这一行
        continue
```

这要求**所有现在和未来的下游**都知道这个约定。CI 的 yaml 里写不了这种过滤，`rsync` 也写不了。总有一处会漏。

```python
# 思路 B：让临时文件在默认工具的视野里根本不存在
prefix=f".{path.name}."
```

改一行，所有下游白送安全——包括你还没写的那些。

> 📌 **本节要点**：跟 `dir=path.parent` 是同一个模式——**把"需要记住的约定"换成"无法违反的结构"**。前者依赖每个人的自觉，后者不依赖任何人。

---

## 🏗️ 大厂怎么用

**SQLite 的 rollback journal**：整个 ACID 的 D 就建立在这套动作上。SQLite 源码注释里详细记录了它在各种文件系统上被坑的历史——包括 macOS 上 `fsync` 默认**不真正刷写磁盘缓存**（要用 `F_FULLFSYNC` fcntl，因为 Apple 认为 fsync 太慢）。"同一个 API，不同平台不同语义"的教科书案例。

**etcd / Kubernetes**：etcd 的 WAL 写入路径上有专门的 `fileutil.Fsync`，macOS 上走 `F_FULLFSYNC`。etcd 对 fsync 延迟极度敏感，官方要求 SSD，`wal_fsync_duration_seconds` 是最关键的监控指标之一——**fsync 慢 = 心跳超时 = 整个集群 leader 选举抖动**。

**Kafka 反其道而行**：Kafka 默认**不 fsync**，靠多副本复制保证持久性。赌注是"三台机器同时断电的概率，低于 fsync 带来的吞吐损失"。这是写在设计文档里的明确取舍——也说明 fsync 不是永远该加。

**Git**：所有对象写入都是这个模式（临时文件 → rename 到 `.git/objects/xx/yyyy`），而且因为对象是内容寻址的（文件名就是内容 hash），**rename 的 last-writer-wins 天然无害**——两个进程写同一个 hash，内容必然相同。用数据模型消掉并发问题的漂亮例子。

---

## 💸 高风险场景（金融 / 审计 / 关键系统）

- **`fsync` 返回成功不代表数据在盘上。** Linux 2018 年爆出的 "fsync-gate"（PostgreSQL 社区发现）：回写发生错误时，内核会**清掉脏页标记并只把错误报告给下一次 fsync 一次**，之后的 fsync 返回成功。PostgreSQL 因此把 fsync 失败改成**直接 panic**，而不是重试——因为重试会得到虚假的成功。**fsync 失败 = 立刻停机，不要重试。**

- **企业级存储的 write cache。** RAID 卡带电池的写缓存会让 fsync 快得不真实。正常情况下这是对的（掉电有电池保护），但电池老化后就变成静默的数据丢失。所以有定期的 BBU 健康检查。

- **只要原子性不要持久性，是一个合法且常见的选择。** 高频写场景（每秒几千个小文件）fsync 会直接压垮 IOPS 预算。做法是：原子 rename 保证读者一致性，持久性交给上层（复制、WAL、对象存储）。**但这个决定必须写在代码注释和设计文档里**，不能是"没想到"。

- **审计要求可能禁止就地覆盖。** 很多合规场景要求 append-only 或 write-once：新版本写成 `metrics.v2.json` 而不是覆盖 `metrics.json`。这时目标从"安全覆盖"变成"安全新建"，`os.replace` 换成 `os.link` + `O_EXCL`（存在即失败）。

---

## 🚀 2026 年现状

- **`os.replace` 是唯一正确的 Python 跨平台答案**，`os.rename` 在需要覆盖时基本可视为 bug。这一点从 3.3 起没变过。
- **`io_uring` 改变了大批量场景。** Linux 5.x 之后支持 `IORING_OP_FSYNC` 和异步 rename，ScyllaDB、TigerBeetle 已经全面用上，避开了 fsync 的同步阻塞。Python 侧还没有成熟绑定，`aiofiles` 只是线程池包装。
- **`atomicwrites` 库已归档。** 作者 2022 年宣布 unmaintain，理由值得一读：大部分用户其实不需要这个抽象，需要的人应该理解自己在做什么。**建议：不要引这个包，就在项目里写这 15 行**——因为你需要按自己的持久性需求调 fsync 策略。
- **CoW 文件系统改变了假设。** btrfs / ZFS / bcachefs 元数据更新天然事务化，很多传统 fsync 舞蹈在上面是冗余的。但**你不能假设代码跑在哪种文件系统上**，所以还是照做。

---

## ✅ 完整修正版

```python
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


def _write_json_atomic(
    path: Path,
    payload: dict[str, Any],
    *,
    durable: bool = True,
    mode: int = 0o644,
) -> None:
    """原子地写一个 JSON 文件。

    保证两件不同的事，由不同机制提供：

    - **原子性**（``os.replace``）：任何读者要么看到完整的旧文件，要么看到
      完整的新文件。不存在半截状态，也不存在文件短暂消失的窗口。已经打开
      旧文件的读者不受影响，会把旧内容读完。
    - **持久性**（``durable=True``）：断电后内容仍在。需要三次同步 —— 用户
      态缓冲、数据页、以及承载新目录项的父目录。在节点故障即整体重建的
      容器环境里，这个开销常常不划算，所以它可以关掉；但那必须是一个
      显式的决定，不是遗漏。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # 先完整序列化：不可序列化的 payload 应该在碰 I/O 之前就失败，而不是
    # 写出半个文件再抛 TypeError。纯计算错误不该混进 I/O 的清理路径。
    text = json.dumps(payload, indent=2, ensure_ascii=False)

    # dir=path.parent 是本函数最关键的一个参数：rename 的原子性只在同一
    # 文件系统内成立，跨设备直接 EXDEV。默认的 /tmp 在容器里通常是 tmpfs
    # 而输出目录是挂载卷 —— 本地开发不报错，CI 上必炸。
    #
    # 前缀加点：否则临时文件会以目标文件的完整名字开头，被
    # glob("*.metrics.json*") 和依赖文件名的 CI 步骤扫进去。
    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    tmp = Path(tmp_name)

    try:
        # fdopen 接管 fd 的所有权，with 退出时关闭它。
        # encoding 必须显式：不写就跟随 locale，Windows 上是 cp1252/GBK。
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            if durable:
                # flush: 用户态缓冲 → 内核 page cache（触发 write(2)）
                # fsync: page cache → 物理介质
                # 顺序不可颠倒：不 flush 就 fsync，内核里根本没有这些字节，
                # fsync 会成功返回并且什么都没同步。
                fh.flush()
                os.fsync(fh.fileno())

        # mkstemp 建的是 0600。目标原本若是 0644，原子写会静默收紧权限，
        # 下游服务账号突然读不到且无任何报错。
        os.chmod(tmp, mode)

        # 签字的那一刻。os.rename 在 Windows 上遇到已存在的目标会抛
        # FileExistsError，所以必须是 replace。
        os.replace(tmp, path)

        if durable and sys.platform != "win32":
            # 最常被漏掉的一步：replace 修改的是父目录的内容，而目录项同样
            # 先进 page cache。不 fsync 目录，断电后文件可能"回滚"到旧版本 ——
            # 数据存住了，但记录它在哪的那一页没存住。
            dir_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)

    except BaseException:
        # BaseException 而非 Exception 是有意的：KeyboardInterrupt 和
        # SystemExit 不继承 Exception，而"Ctrl-C 也不留烂摊子"正是本函数
        # 存在的理由。
        #
        # missing_ok 覆盖两种情况：replace 已成功（tmp 已不存在），以及
        # mkstemp 之后立刻被信号打断。
        tmp.unlink(missing_ok=True)
        # 裸 raise 保留原始 traceback。本函数只负责清理，重试还是放弃是
        # 调用方的决策。
        raise
```

---

## 🧭 跳出文件系统：四条可以带走的通用原则

到这里，技术问题已经解决完了。但如果这篇只值一个函数，那它就白写了。

我和阿哲那二十分钟的争论，本质上不是一个 Python 问题。同样的事，在完全不碰代码的地方每天都在发生。下面四条，是我从那个周六上午真正带走的东西。

### 一、失败都是坏事吗？——响亮的失败是资产，沉默的成功才是负债

我们从小被教育"要减少失败"。但把这篇文章里所有的坑摆在一起看，会发现一个很反直觉的事实：**真正让我付出代价的，没有一个是"失败"。**

`os.replace` 抛出 `OSError: [Errno 18]`——**这是一次失败**，而且是这篇文章里最善良的一次。它在 CI 里当场炸掉，堆栈完整，错误码明确，五分钟就能定位。真正让我损失几百刀的，是那次**"成功"**：进程退出码 0，日志写着 `run finished`，文件名一个字符不差。

阿哲和我吵了二十分钟，不是因为问题难，是因为**那个文件给出了错误的证词**。如果磁盘上干脆什么都没有，我们十秒钟就能达成一致："写文件那步没跑成，重跑。"

所以判断一次失败好不好，不看它疼不疼，看两个量：

| | 好的失败 | 坏的失败 |
|---|---|---|
| **响度** | 立刻报错、堆栈完整、错误码明确 | 静默返回成功 |
| **延迟** | 离原因越近越好 | 在下游几小时、几天后才显形 |
| 本文例子 | `EXDEV` 当场炸、序列化在碰 I/O 前失败 | fsync 空转、权限静默收紧、`shutil.move` 无日志降级 |

**内核在这件事上做了一个道德选择。** 跨文件系统 rename 的时候，它完全有能力"帮你"退化成 copy + delete，让你的代码继续跑下去。但它拒绝了——因为那不原子，而它不愿意用一个假的成功换你的方便。**它宁可让你难受，也不骗你。** 同样，PostgreSQL 在 fsync 失败时选择直接 panic 而不是重试，因为重试会得到虚假的成功——**主动把自己搞崩，是为了不撒谎。**

航空业把这条原则做到了极致。航空安全不是靠"少出事"堆出来的，是靠**把每一次失败榨干**：黑匣子强制安装，事故报告全球公开，任何一家航司的教训所有航司都要学。更狠的是 NASA 的 ASRS——**近失事件免责上报制度**：你差点撞上另一架飞机、你差点降错跑道，只要主动报上来就免于处罚。他们花大力气去**挖掘那些没造成任何后果的失败**，因为一次没人受伤的近失，是一次免费的黑匣子。

医学上叫**假阴性**：漏诊比误诊更危险，误诊会引发复查，漏诊让病人带着"我很健康"的结论回家。消防栓生锈打不开，比消防栓根本不存在更致命，因为预案上写着"此处有消防栓"。丰田的安灯绳（Andon cord）让流水线上任何一个工人都能拉停整条产线——**把失败放大到全厂都看得见**，因为一个被藏起来的缺陷，装到车上就是召回。

所以"失败是坏事"这句话本身就问错了。失败是一次信息投递，问题只在于**这份信息有没有送到，以及送得够不够早**。

> 举一反三：别再问"怎么减少失败"，改问三个问题——**怎么让失败来得更早？怎么让它更响？怎么让它更便宜？** 顺带留意第四个：你的团队里，有没有哪种失败是"报上来会挨骂"的？那类失败不会消失，它只会转入地下，变成沉默的那一种。

### 二、消除问题类，而不是处理问题个例

面对 EXDEV，本能反应是 `try/except` 兜住再降级；面对临时文件被 glob 扫到，本能反应是让每个下游脚本加一行 `if f.suffix == ".tmp": continue`。

两个都是"处理问题"。而正确解法都只改了一个参数：`dir=path.parent` 让跨设备**在物理上无法发生**；`prefix="."` 让临时文件**在默认工具的视野里不存在**。没有分支，没有约定，没有需要传达的知识。

这在制造业里有个专名：**防呆设计（poka-yoke）**，丰田生产系统的支柱之一。日本工程师新乡重夫的原则是——**不要培训工人别犯错，要让那个错误在物理上做不出来**。所以 SIM 卡有个缺角，插反了根本推不进去；所以柴油枪的口径比汽油枪粗，加错油的动作完成不了；所以微波炉门一开磁控管就断电，不是贴张"请勿开门"的标签。

同一条思路在别处：医院把外观相似的高危药品换成完全不同形状的瓶子，而不是贴"小心"贴纸；路口修环岛而不是立"请减速"的牌子——环岛让你**没法不减速**。

**约定依赖每个人记得，结构不依赖任何人。** 而团队是会换人的，你写的下游脚本也不是最后一个。

> 举一反三：下次你准备写一份"注意事项"文档、或者在群里叮嘱一句"大家记得别忘了"，先停三秒问自己：**能不能改一个默认值、一个接口、一个物理形状，让这件事根本做不出来？**

### 三、默认值是别人替你做的决定

`tempfile.mkstemp()` 不传 `dir`，默认去 `/tmp`；不传 `mode`，默认 0600；`open()` 不传 `encoding`，默认跟随 locale。

这三个默认值，每一个都曾经是某个人在某个语境下的合理选择——而那个语境不是你的。它们没有一个是错的，但它们全都**替你做了决定，而且没有通知你**。这篇文章里的两个 bug，追到底都是"我接受了一个我从没审视过的默认值"。

行为经济学对此有大量研究，最有名的是**器官捐献率**：奥地利接近 100%，德国不到 15%。两国文化、宗教、经济高度相似，差别只在表格——奥地利默认捐献，你要主动勾选退出；德国默认不捐献，你要主动勾选加入。**几乎没有人改动默认值。** 理查德·塞勒因为这一系列研究拿了诺贝尔经济学奖，`401(k)` 自动加入把美国的参与率从 40% 推到 90% 以上，用的是同一个机制。

默认值不是"没有选择"，默认值是**最强的那个选择**，因为它是唯一一个不需要任何人动手就会生效的选项。

> 举一反三：你负责的系统里，有哪些行为是"没人做过决定，但一直在生效"？把它们列出来——**那不是配置，那是你继承的、来路不明的立场。**

### 四、一个动作，只回答一个问题

原子性和持久性长得很像，都叫"保证文件写好了"，所以大量代码把它们混成一件事，然后既不知道自己保证了什么，也不知道自己付了什么代价。

拆开之后一切都清楚了：`os.replace` 只回答"会不会有人看到半截"；`fsync` 只回答"断电后还在不在"。于是你可以理直气壮地**只要一个**——Kafka 就公开选择了不要 fsync，靠三副本复制解决持久性，因为它算过那笔账。

法律世界早就把这两件事分开了：**签字**决定合同何时生效，**公证与备案**决定它能不能扛过一场火灾。没有律师会把这两个动作合并，因为它们防的是不同的灾难，成本也完全不同。而 fsync 目录对应的是最容易被忽略的第三件事：**登记簿本身有没有备份**——你的文件在第 7 柜安然无恙，但记录"它在第 7 柜"的那本册子还摊在办公桌上。火一烧，你照样找不到它。

婚姻也是一样：领证是原子的（那一刻起法律关系从 0 到 100），办婚礼是公示，两件事互相不能替代。

> 举一反三：当你发现团队反复为一个方案争论不休，先检查它是不是在**用一个动作回答两个问题**。拆开之后，往往会发现大家争的根本不是同一件事。

---

## 立刻可以做的事

先问那个决定性的问题——**"这个文件半截会不会被人当成完整的？"**

- 是**日志、缓存、可随时重新生成的中间产物** → `write_text` 完全够用，上面那 60 行是过度工程。
- 是**交付物**（别人会读、CI 会依赖、花了钱才产出的、丢了要重跑的）→ 这一行是一个等着被触发的静默故障。

如果答案是后者，逐条对照：

- [ ] 临时文件在**目标同目录**（`dir=path.parent`），不是 `/tmp` —— 否则容器里 EXDEV
- [ ] 临时文件名**以点开头** —— 否则被 glob 和 CI 扫进去
- [ ] 用 `mkstemp` 不手拼名字 —— `O_EXCL` 消除 TOCTOU
- [ ] **先序列化再 I/O** —— 序列化错误不该产生半个文件
- [ ] `flush()` **在** `fsync()` 之前 —— 顺序反了 fsync 静默无效
- [ ] `os.chmod` 修正权限 —— mkstemp 是 0600，会静默收紧
- [ ] `os.replace` 不是 `os.rename` —— Windows 上后者不能覆盖
- [ ] **fsync 父目录** —— 最常漏的一步
- [ ] `except BaseException` 不是 `Exception` —— Ctrl-C 要能清理
- [ ] 明确写下你要的是原子性还是持久性 —— 这是取舍不是遗漏

最后一条不是技术的：**去问一遍你团队里"大家记得要……"开头的那些约定。** 每一条都是一个还没被改成结构的默认值，也是一次还没发生的争论。

---

真正的教训不是"要用原子写"。而是**那一行代码看起来完全正常，所以没人会在 code review 里拦它**——它的问题不在语法、不在类型、不在测试覆盖率，而在于我们对"写文件"这个动作的默认认知从一开始就是错的：`open(w)` 从来就不是一个操作。

*所有最贵的 bug 都有同一个特征：它们不在你检查的地方，它们在你根本没想到需要检查的地方。*
