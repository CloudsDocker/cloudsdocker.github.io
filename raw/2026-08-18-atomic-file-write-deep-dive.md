---
title: "一行 write_text 引发的血案：原子写文件里的 POSIX、崩溃一致性和文件系统边界"
date: 2026-08-18
categories: [engineering, python, systems]
tags: [atomic-write, fsync, posix, rename, filesystem, crash-consistency, python]
---

## 一切从这一行开始

我在一个 LLM 评测框架的 CLI 里，要把一次 run 的 metrics 落盘。当时写的是这一行：

```python
metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
```

**这一行几乎是所有开发者的默认写法**，而且它看起来还挺讲究的 —— `json.dumps`
先序列化再写（比 `json.dump(fh)` 强），`encoding="utf-8"` 显式写了（比裸
`write_text` 强）。Code review 里没人会拦它。

但它至少有四个问题，而且全都是**静默的**：

1. **`write_text` 不是原子的。** 它是 `open(w)` → truncate → write → close。
   进程在中间死掉（Ctrl-C、OOM kill、容器 evict），磁盘上留下的不是"没有文件"，
   而是**一个文件名完全正确、内容截断的 JSON**。下游 `json.load` 抛
   `JSONDecodeError`，读起来像"这次 run 失败了"，而不是"这次 run 的记账坏了"。
2. **有读者的话，会读到半截文件。** 监控面板、CI 的另一个 step、`tail` —— 任何
   人在那几毫秒里 open 这个路径，拿到的是不完整的内容。而且它们无法分辨。
3. **断电之后内容可能是空的。** 数据只到内核 page cache，没有任何一步保证它落盘。
4. **文件权限跟着 umask 走**，跨环境不一致。

我在的这个场景更要命：这个 metrics 文件是**整个 eval 的唯一交付物**，一次 run
花掉的钱全在里面。第二次 Ctrl-C 打在这一行中间，几百刀的实验结果就变成一个
坏 JSON。

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

**然后复盘的时候我发现，这八行里有两个真 bug 和一个重大遗漏。**

它们踩在三个不同的坑上 —— POSIX 语义、文件系统实现边界、崩溃一致性 —— 而这三个
坑里的东西（`fsync` **目录**、`EXDEV` 的真正边界、`mkstemp` 的 prefix 陷阱），
是不少资深工程师也没系统想过的。

这篇把整个复盘过程完整记下来：先逐行解剖这八行，再把其中两行单独展开成两个
独立的话题。

---

# Part 1：逐行解剖

## 🎯 30 秒版本

这个函数在解决一件事：**`open(w)` 不是一个操作，是三个操作。**

```
open(path, "w")  →  truncate（文件瞬间变 0 字节）
fh.write(...)    →  逐步填回去
fh.close()
```

在 truncate 之后、write 完成之前，磁盘上躺着一个**文件名完全正确、内容残缺**的文件。进程这时候死掉（Ctrl-C、OOM kill、容器 evict、断电），你得到的不是"没有文件"，而是"一个骗人的文件"。

原子写的思路：**永远不要就地修改，只做名字的瞬间切换。**

类比：**合同的签署。** 草稿可以改十版，每一版都没有任何法律效力；签字那一瞬间，效力从 0 跳到 100。**不存在"合同生效了一半"这个状态。** `os.replace` 就是那一笔签字。

---

## ⚙️ 逐行拆解

### `fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")`

三个参数，每个都在解决一个具体问题。

**`dir=path.parent` —— 这是整个函数最关键的一个参数。**

`rename(2)` 的原子性**只在同一个文件系统内成立**。跨文件系统 rename 直接返回 `EXDEV`（Invalid cross-device link），因为 rename 本质是「改一个 inode 的目录项指向」，inode 编号在另一个文件系统里没有意义。

如果这里写默认的 `/tmp`，在容器里几乎必然踩坑：`/tmp` 常是 tmpfs，输出目录是 overlayfs 或挂载卷 —— 两个文件系统。`os.replace` 抛 `OSError: [Errno 18]`。而更阴险的是**本地开发不报错**（都在同一个 ext4 上），CI 一上容器就炸。

这就是「架构上消除问题类」而不是「加个 try 兜住 EXDEV 再退化成 copy」：**临时文件生在目标旁边，跨设备这件事根本不可能发生。**

（这条单独展开在 Part 2。）

**`mkstemp` 而不是 `NamedTemporaryFile` 或手拼名字。**

`mkstemp` 底层是 `open(path, O_CREAT | O_EXCL | O_RDWR, 0600)`。三个性质：

- `O_EXCL` + 随机名 = **无 TOCTOU**。不存在「检查文件不存在 → 别人抢先创建 → 你覆盖了它」的窗口。这是符号链接攻击的标准防线。
- 返回**裸 fd**，不是路径。中间没有「拿到名字再去 open」的间隙。
- 权限 **0600**，只有属主可读写 —— 临时文件里可能有半成品敏感数据。

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

`mkstemp` 给的是**裸 fd（整数）**，不能直接 `write` 字符串。`os.fdopen` 把它包成 Python 的 `TextIOWrapper`，**并把 fd 的所有权转移给这个对象** —— `with` 退出时 `close()` 会关掉底层 fd。

所有权转移这件事有个后果：**`os.fdopen` 本身如果抛异常（比如 encoding 名字打错），fd 就泄漏了** —— 既没被 fdopen 接管，也没被你手动 `os.close`。而下面的 `except` 只 unlink 了路径，没关 fd。长跑进程里这是文件描述符泄漏。

严格写法是把 fdopen 也纳入保护，或者用 `os.close(fd)` 兜底。实践中 encoding 是硬编码的，这个分支永远不会走 —— **但值得知道它存在，因为会问「fd 的所有权在哪一刻转移」**。

`encoding="utf-8"` 是必须显式写的：Python 3.15 之前，不写就跟随 locale，Windows 上默认是 cp1252 / GBK。你的 metrics 里只要有一个中文或 emoji，Linux 上写得好好的，Windows 上 `UnicodeEncodeError`。

---

### `json.dump(payload, fh, indent=2)` —— 这里是 Bug 2

`json.dump` 是**流式**的：它一边遍历对象一边往 `fh` 写。

如果 `payload` 里混进一个不可序列化的对象（`datetime`、`Path`、`Decimal`、numpy 标量都是常客），`TypeError` 会在**已经写出一部分之后**抛出。

在这个函数里后果不严重（临时文件会被 unlink），但它揭示了一个更好的结构：**先完整序列化成字符串，成功了再碰 I/O。**

```python
text = json.dumps(payload, indent=2)   # 会失败就在这里失败，此时磁盘上什么都没发生
```

这是「把失败往前推到无副作用的阶段」。序列化错误是纯计算错误，不该和 I/O 错误纠缠在同一个清理路径上。而且 `json.dumps` 一次性构造字符串，`fh.write(text)` 一次系统调用写完，比流式的多次小 write 更快。

（代价是大对象的内存峰值翻倍。metrics 文件几十 KB，无所谓；如果是 GB 级导出，那就该流式。）

---

### `fh.flush()`

**这一行不是可选的，而且大部分人搞错它和 fsync 的关系。**

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

所以顺序不能反、不能省：如果不 flush 直接 fsync，数据还躺在用户态缓冲区里，内核里根本没有这些字节，**fsync 会成功返回，并且什么都没同步**。这是一个静默失败 —— 你以为你持久化了。

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

也就是**元数据先于数据落盘**，你得到一个「名字正确、内容为空」的文件 —— 恰恰是原子写要防的那个东西，从后门溜回来了。

ext4 在 2009 年之后加了个 hack（Ted Ts'o 在 delayed allocation 引发大规模文件清零投诉后打的补丁）：`rename` 覆盖已有文件时会自动触发数据回写。**但这是 ext4 的特殊照顾，不是 POSIX 保证**，XFS、btrfs、以及各种网络文件系统上不一定成立。所以显式 fsync。

**注意 fsync 的代价**：它是同步阻塞的，等物理确认。机械盘上几到几十毫秒，SSD 上零点几到几毫秒，网络存储上可能上百毫秒。在写几千个小文件的循环里，fsync 会是压倒性的瓶颈 —— 那种场景要么批量写后一次 fsync 目录，要么接受弱保证。

---

### `os.replace(tmp, path)` —— 签字的那一刻

**原子性的完整定义**：任何时刻、任何观察者去 `open(path)`，看到的要么是完整的旧文件，要么是完整的新文件，**不存在第三种状态，也不存在文件短暂消失的窗口**。

底层就是 `rename(2)`，POSIX 明确要求：新名字若已存在则被移除并完成改名，且该操作相对于其他线程是原子的。

**关键点：已经打开旧文件的读者不受影响。** rename 只改目录项，旧的 inode 引用计数还有 +1 来自那个打开的 fd。读者会安安静静把旧内容读完 —— 这就是 Unix 的 inode/dentry 分离带来的白送好处，也是为什么 `logrotate` 能在服务运行时安全轮转日志。

**`os.replace` 而不是 `os.rename`：** 在 POSIX 上两者一样，但 **Windows 上 `os.rename` 目标存在时直接抛 `FileExistsError`**。`os.replace` 保证跨平台的覆盖语义（Windows 下走 `MoveFileEx` + `MOVEFILE_REPLACE_EXISTING`）。

**Windows 的注意事项**（如果你的 CI 有 Windows runner）：`MoveFileEx` 在目标文件**被另一个进程打开**时会失败（sharing violation，`PermissionError`）。Unix 上完全没这问题。杀毒软件扫描你刚写的文件时尤其容易撞上 —— 这是 Windows 上写文件工具普遍要加重试的原因。

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

要真正保证「rename 已持久化」，必须 fsync **父目录的 fd**：

```python
dir_fd = os.open(path.parent, os.O_RDONLY)
try:
    os.fsync(dir_fd)
finally:
    os.close(dir_fd)
```

这是 SQLite、etcd、PostgreSQL 的 WAL 实现里都有的一步，也是**教科书原子写实现和网上随手抄的版本之间最常见的差距**。

（Windows 上不能 fsync 目录，`os.open` 目录直接报错，所以要包一层平台判断。）

---

### `except BaseException:` / `unlink(missing_ok=True)` / `raise`

**用 `BaseException` 而不是 `Exception` 是正确的，而且是有意的。**

`KeyboardInterrupt` 和 `SystemExit` 继承自 `BaseException` 而**不**继承 `Exception`。这个函数的整个存在理由就是「Ctrl-C 也不能留下烂摊子」—— 只 catch `Exception` 的话，Ctrl-C 打进来时临时文件会留在磁盘上，堆积成垃圾。

`missing_ok=True` 覆盖两种情况：mkstemp 之后立刻被信号打断（文件存在，删）、以及 `os.replace` 已经成功之后才出异常（tmp 已经不在了，不该报错）。

`raise` 裸抛保留原始 traceback。**这个函数只做清理，不做决策** —— 是重试还是放弃，是调用方的事。清理和策略分离。

---

## 🔬 追问链

**Q1: 这个函数保证的是原子性还是持久性？**

两者是**不同的属性，由不同的机制提供**：

| 属性 | 防的是 | 靠哪一步 |
|---|---|---|
| 原子性 | 读者看到半截文件 | `os.replace` |
| 持久性 | 断电后内容丢失 | `flush` + `fsync`（数据）+ fsync 目录（元数据） |

只要原子性，`os.replace` 一行就够；要持久性，三次 fsync 一次都不能少。**在容器/云环境里，很多团队有意只要原子性不要持久性** —— 因为节点挂了整个实例都重建，fsync 的开销白付。这是一个应该显式做出的取舍，而不是「抄了个函数不知道它保证了什么」。

**Q2: 权限有什么问题？**

有，而且很常见：`mkstemp` 建的文件是 **0600**。如果目标文件原本是 0644（其他用户可读，比如给 nginx 或另一个服务账号读），原子写之后**权限被静默收紧到 0600**，那个服务突然读不到了 —— 而且没有任何报错，只有下游的 `PermissionError`。

修法：rename 之前按 umask 或按原文件的 mode 修正。

**Q3: NFS 上还成立吗？**

部分成立，需要小心。`rename` 在 NFS **服务端**是原子的。但 NFSv3 的客户端属性缓存（默认 `acregmin`/`acregmax` 3~60 秒）意味着**另一台客户端可能在一段时间内还看到旧文件**。原子性没被破坏（不会看到半截），但**可见性有延迟**。

另外 NFS 上 `unlink` 一个被打开的文件会触发 **silly rename**（服务端把它改名成 `.nfsXXXX`），所以清理逻辑可能留下神秘的隐藏文件。

分布式协调不要靠文件系统 —— 那是 etcd/Consul 的活。

**Q4: 并发两个进程同时对同一个 path 做原子写会怎样？**

不会损坏，但是 **last-writer-wins，且没有任何提示**。两个 tmp 文件名不同（mkstemp 随机），各写各的，两次 rename 串行执行，后到的赢。

原子写保证的是「不会写出一个坏文件」，**不保证「不会丢一次更新」**。要防丢更新需要额外的锁（`flock`）或者 CAS 语义（`O_EXCL` 创建，存在就失败）。

**Q5: 为什么不用 `os.sync()`？**

`os.sync()` 刷**整个系统**的所有脏页，是一个全局操作，在繁忙机器上可能阻塞秒级。`fsync(fd)` 只针对一个文件。永远用后者。

顺带：Linux 上还有 `os.fdatasync()`，只同步数据不同步非必要元数据（如 mtime），略快。对新建文件没意义（size 是必要元数据，必须同步），对覆盖写有意义。

---

## 🏗️ 大厂怎么用

**SQLite 的 rollback journal**：整个 ACID 的 D 就建立在这套动作上，而且 SQLite 的源码注释里详细记录了它在各种文件系统上被坑的历史 —— 包括 macOS 上 `fsync` 默认**不真正刷写磁盘缓存**（要用 `F_FULLFSYNC` fcntl 才行，因为 Apple 认为 fsync 太慢了）。这是「同一个 API，不同平台不同语义」的教科书案例。

**etcd / Kubernetes**：etcd 的 WAL 写入路径上有一个专门的 `fileutil.Fsync`，在 macOS 上就是走 `F_FULLFSYNC`。etcd 对 fsync 延迟极度敏感，官方文档明确要求 SSD，并把 `wal_fsync_duration_seconds` 列为最关键的监控指标之一 —— **fsync 慢 = etcd 心跳超时 = 整个集群 leader 选举抖动**。

**Kafka 反其道而行**：Kafka 默认**不 fsync**，靠多副本复制来保证持久性。它的赌注是「三台机器同时断电的概率，低于 fsync 带来的吞吐损失」。这是一个明确的、写在设计文档里的取舍 —— 也说明 fsync 不是永远该加。

**Git**：所有对象写入都是这个模式（写临时文件 → rename 到 `.git/objects/xx/yyyy`），并且因为对象是内容寻址的（文件名就是内容 hash），**rename 的 last-writer-wins 天然无害** —— 两个进程写同一个 hash，内容必然相同。这是用数据模型消掉并发问题的漂亮例子。

---

## 💸 高风险版本（金融 / 审计 / 关键系统）

- **`fsync` 返回成功不代表数据在盘上。** Linux 在 2018 年爆出著名的 "fsync-gate"（PostgreSQL 社区发现）：如果回写发生错误，内核会**清掉脏页标记并只把错误报告给下一次 fsync 一次**，之后的 fsync 返回成功。PostgreSQL 因此把 fsync 失败改成**直接 panic 崩溃**，而不是重试 —— 因为重试会得到虚假的成功。金融系统里同样：**fsync 失败 = 立刻停机，不要重试。**

- **企业级存储的 write cache。** RAID 卡带电池的写缓存会让 fsync 快得不真实。这在正常情况下是对的（掉电有电池保护），但电池老化后就变成静默的数据丢失。所以有定期的 BBU 健康检查。

- **只要原子性不要持久性，是一个合法且常见的选择。** 高频写场景（每秒几千个小文件）fsync 会直接压垮 IOPS 预算。做法是：原子 rename 保证读者一致性，持久性交给上层（复制、WAL、对象存储）。**但这个决定必须写在代码注释和设计文档里**，不能是「没想到」。

- **审计要求可能禁止就地覆盖。** 很多合规场景要求 append-only 或 write-once：新版本写成 `metrics.v2.json` 而不是覆盖 `metrics.json`，保留完整历史。这时原子写的目标从「安全覆盖」变成「安全新建」，`os.replace` 换成 `os.link` + `O_EXCL`（存在即失败）。

---

## 🚀 2026 年现状

- **`os.replace` 是唯一正确的 Python 跨平台答案**，`os.rename` 在需要覆盖时基本可以视为 bug。这一点从 3.3 起就没变过。

- **`io_uring` 的普及改变了大批量场景。** Linux 5.x 之后 io_uring 支持 `IORING_OP_FSYNC` 和异步 rename，数据库和存储引擎（ScyllaDB、TigerBeetle）已经全面用上，避开了 fsync 的同步阻塞。Python 侧还没有成熟绑定，`aiofiles` 只是线程池包装，不是真异步。

- **`atomicwrites` 库已经归档。** 作者在 2022 年明确宣布 unmaintain，理由值得一读：他认为大部分用户其实不需要这个抽象，而需要的人应该理解自己在做什么。**建议：不要引这个包，就在项目里写这 15 行**，因为你需要根据自己的持久性需求调整 fsync 策略，而库替你做的决定往往不是你要的。

- **CoW 文件系统改变了假设。** btrfs / ZFS / bcachefs 本身就是写时复制，元数据更新天然事务化，很多传统的 fsync 舞蹈在上面是冗余的。但**你不能假设代码跑在哪种文件系统上**，所以还是照做。

- **正在过时的**：`os.rename` 做覆盖、只 fsync 数据不 fsync 目录、用 `NamedTemporaryFile(delete=False)` 手工管理（比 `mkstemp` 多一层抽象且更容易漏关 fd）。

---

## 🌉 跨学科透镜：合同的签署

一份并购协议可以起草 30 版，律师逐条改，双方来回谈。**在签字之前，所有草稿的法律效力精确等于零。** 你不能说「这份合同已经生效了 60%」。

签字那一瞬间，效力从 0 跳到 100，中间没有任何可观察的过渡态。这就是 `os.replace`。

而**公证与备案**是另一回事：签完字，文件还只在你抽屉里；送去公证处存档，才经得起火灾。这就是 `fsync`。

两条独立的保障，回答两个不同的问题：

- 「有没有可能有人看到一份半生效的合同？」→ 靠签字的瞬时性（原子性）
- 「办公室烧了这份合同还在吗？」→ 靠异地存档（持久性）

**而 fsync 目录，对应的是「公证处的登记簿本身有没有备份」** —— 你的文件存好了，但那本记录「这份文件归档在第 7 柜」的册子还在办公桌上没抄录。烧了照样找不到。

这也解释了为什么 Kafka 敢不 fsync：它选择了「同一份合同在三个城市各签一份」，而不是「一份合同反复公证」。

---

## 🥋 Part 1 一句话总结

> `open(w)` 是 truncate + write 两步，所以崩溃留下的不是缺失的文件而是骗人的文件；原子写用 rename 把这两步压成一个不可分割的瞬间 —— 但别忘了 rename 本身也要 fsync 它所在的那个目录。

---

# Part 2：EXDEV —— 「同一个文件系统」到底指什么

上面说 rename 的原子性只在同一个文件系统内成立。那么「同一个文件系统」的边界在哪？

三个常见猜测：

| 猜测 | 对吗 |
|---|---|
| 同一个文件夹下 | ❌ 太严了。同一个文件系统内**任意两个目录**都行 |
| 同一台电脑 | ⚠️ 必要但远不充分。一台电脑上通常有 5~10 个文件系统 |
| 同一个硬盘 | ❌ 既不必要也不充分 |

**正确的边界是：同一个「挂载点」（mount）。**

## 为什么是挂载点

inode 号只在**一个文件系统内部**唯一。`/` 上有 inode 12345，`/home` 上也有 inode 12345，它们毫无关系。

`rename(2)` 干的事是：**在目录 B 里加一条「名字 → inode 12345」的记录，然后从目录 A 删掉那条记录**。整个过程**一个字节的文件内容都没动**。

所以跨文件系统 rename 在物理上就无法定义 —— 目标文件系统里的 inode 12345 是别人的文件。内核不会「帮你」偷偷降级成 copy+delete，因为那**不是原子的**，而且可能要搬 50GB。它直接告诉你 `EXDEV`，让你自己决定怎么办。

`mv` 命令看起来能跨盘搬，是因为 **`mv` 是个程序，不是 syscall** —— 它先试 `rename()`，收到 EXDEV 后自己退化成 copy + unlink。这也是为什么同盘 `mv` 一个 50GB 文件是瞬间的，跨盘要跑几分钟。**这个差异你一定见过，只是没想过原因。**

## 三个反直觉的情况

**① 同一块硬盘 ≠ 同一个文件系统**

一块 SSD 分了 3 个区 = 3 个文件系统。`/` 和 `/home` 在不同分区是极常见的安装布局，它们之间 rename 直接 EXDEV。

**② 同一个文件系统 ≠ 同一块硬盘**

LVM、RAID、ZFS pool 可以让一个文件系统横跨 8 块盘。这种情况下**跨物理硬盘的 rename 完全正常**，因为逻辑上还是一个文件系统。

**③ 同一个「盘」上也可能 EXDEV**

- **btrfs subvolume**：同一个设备、同一个 mount 命令挂上来的，但 `/data/@snapshots` 和 `/data/@current` 之间 rename 会 EXDEV。ZFS dataset 同理。
- **bind mount**（Linux 特有的坑）：`mount --bind /data /app/data` 之后，`/data/x` 和 `/app/data/y` 的 `st_dev` **完全相同**，但 rename 仍然返回 EXDEV —— 因为内核检查的是 `vfsmount` 是否相同，不只是 `st_dev`。

这第三点很重要：**`st_dev` 相等是必要条件，不是充分条件。** 想靠 `os.stat().st_dev` 预判「能不能 rename」，会漏掉 bind mount 这一类。

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

```bash
$ stat -c '%d %n' /tmp/a /home/todd/b
1  /tmp/a
66306  /home/todd/b        # 不同 → 必然 EXDEV
```

Python 里：

```python
Path("/tmp").stat().st_dev == Path("/home/todd").stat().st_dev
```

## 为什么这个坑在容器里几乎必然踩到

看一个典型的 Docker 容器：

```
/           overlayfs      ← 镜像层
/tmp        tmpfs          ← 内存（很多基础镜像这么配）
/app/data   volume/bind    ← 挂载卷
/dev/shm    tmpfs
```

**四个不同的文件系统。**

于是这个经典的失败链就出现了：

```python
# 看着人畜无害
fd, tmp = tempfile.mkstemp()          # → /tmp/xxxx（tmpfs）
...
os.replace(tmp, "/app/data/metrics.json")   # → 挂载卷
# OSError: [Errno 18] Invalid cross-device link
```

**而你本地 Mac 上跑一切正常** —— 因为 macOS 的 `/tmp` 和你的项目目录都在同一个 APFS 卷上。代码写完、测试通过、CI 一上容器就炸。

这类 bug 特别恶心的地方在于：它不是逻辑错误，是**环境假设错误**，本地永远复现不了。

## 所以正确写法不是「检测再处理」

很多人的第一反应是加个兜底：

```python
try:
    os.replace(tmp, path)
except OSError as e:
    if e.errno == errno.EXDEV:
        shutil.move(tmp, path)   # ❌ 灾难
```

**这是最坏的写法。** `shutil.move` 跨设备时是 copy + unlink，**完全不原子** —— 你精心设计的原子写，在最需要它的时候（跨设备）静默退化成了最不安全的版本。而且没有任何日志告诉你降级了。

正确做法是让 EXDEV **在结构上不可能发生**：

```python
tempfile.mkstemp(dir=path.parent, ...)
```

临时文件生在**目标文件的隔壁**。它俩天然共享目录，共享目录就必然共享 mount，共享 mount 就必然共享文件系统。**没有检测，没有降级，没有分支 —— 这个错误类被消除了，不是被处理了。**

## 跨机器呢

**跨机器根本轮不到 EXDEV** —— 你连不上另一台机器的文件系统，没有 syscall 可以调。SSH/rsync/S3 全是应用层协议，不走 `rename(2)`。

唯一的例外是**网络文件系统**：NFS 挂上来之后，`/mnt/nfs` 就是一个正常的文件系统，内部 rename 完全合法，原子性由 NFS 服务端保证。但 `/mnt/nfs/a` → `/home/b` 依然是 EXDEV，因为那是两个文件系统。

顺带一个反例：**S3 没有 rename**。S3 是对象存储不是文件系统，「重命名」= COPY + DELETE 两次 API 调用，**中间那一刻两个 key 同时存在，不原子**。所以在 S3 上做原子发布要靠别的机制（版本号、指针对象、条件写）。很多人把「写临时文件再 rename」的经验直接搬到 S3 上，然后困惑于为什么会读到不一致的状态。

## 🥋 Part 2 一句话总结

> `rename` 的原子性来自它只改目录项不搬数据；而这也正是它跨不了文件系统的原因 —— inode 号出了自己的文件系统就是一串没有意义的数字。判断边界看 `df` 的行，不看硬盘也不看文件夹。

---

# Part 3：为什么临时文件名要加一个点

回到 `prefix=f".{path.name}."` 这个改动。先看实测结果：

```python
import tempfile, os, glob
from pathlib import Path

d = Path("/tmp/globdemo")
target = d / "cot_gpt5_dev_seed42.metrics.json"
target.write_text("{}")

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

`mkstemp` 的公式是 `prefix + 随机8字符 + suffix`，中间**不插任何东西**。所以你的临时文件名的前 33 个字符，和真正的产物**一字不差**。

它已经不是"一个临时文件"了，它是"一个看起来像产物、名字还长了一截的东西"。

## 谁会被这个骗到

如果你的设计里**文件名承载语义**（比如完整的 run 叫 `.metrics.json`，不完整的叫 `.metrics.partial.json`），下游一定会有匹配文件名的代码：

**CI 收集产物**

```yaml
- uses: actions/upload-artifact@v4
  with:
    path: results/*metrics*       # 把半截 JSON 也当产物上传了
```

**汇总脚本**

```python
for f in Path("results").glob("*.metrics.json*"):    # 想同时抓 .json 和 .partial.json
    data = json.loads(f.read_text())                 # 💥 JSONDecodeError
```

这里的 `*` 是为了同时匹配 `.metrics.json` 和 `.metrics.partial.json` —— **一个完全合理的写法**，但它顺手把 `.tmp` 也抓了。

**清理 / 同步**

```bash
rsync results/*metrics* backup/       # 同步了一个正在被写的文件
find results -name '*metrics*' -mtime +30 -delete
```

## 什么时候真的会撞上

平时不会 —— 临时文件的寿命是毫秒级，写完立刻 rename 掉了。**它只在两种时刻存在，而这两种恰恰是你最需要看清目录的时刻**：

**① 崩溃残留。** 进程被 `SIGKILL`（OOM killer、`docker stop` 超时、K8s evict）打死，`except` 块**根本不会执行**，`.tmp` 永久留在盘上。于是你的输出目录里长期躺着一堆"看起来像产物"的僵尸文件 —— 而且它们的名字里带着完整的 run 名，特别有迷惑性。

**② 并发窗口。** 一个 run 正在写文件，另一个进程（监控面板、CI 的另一个 step）同时在扫目录，正好撞上那几毫秒。这种 bug 复现率千分之一，排查起来极其痛苦。

## 为什么加个点就解决了

`glob` 遵循 shell 惯例：**模式里的 `*` 不匹配开头的点**。CPython 的 `glob.py` 里就一个函数：

```python
def _ishidden(path):
    return path[0] in ('.', b'.'[0])
```

模式本身以点开头时才会匹配点文件。所以 `.foo.tmp` 对 `*`、`*metrics*`、`*.metrics.json*` **全部不可见**。

**而这是平台无关的** —— CPython 自己实现了这个规则，不依赖操作系统。Windows 上 `glob("*")` 同样不返回点文件。

**同时 `os.listdir` 照样看得见**，所以你自己写的清理逻辑（`for f in os.listdir(d): if f.endswith(".tmp")`）不受影响。**该看见的看见，该屏蔽的屏蔽** —— 这正是想要的分工。

**尾部那个点**是另一件事，纯为可读性：

```
.cot_gpt5_dev_seed42.metrics.json.lcvg6fnw.tmp
                                 ↑
                    随机串被隔开，一眼看出哪段是名字哪段是垃圾
```

## 这是「消除问题类」而不是「处理问题」

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

改一行，所有下游白送安全 —— 包括你还没写的那些。

跟 `dir=path.parent` 是同一个模式：**把「需要记住的约定」换成「无法违反的结构」。**

## 两个补充

**Windows 上点前缀不隐藏。** Windows 的"隐藏"是文件系统的一个属性位，不看名字。所以资源管理器里那个 `.tmp` 照样可见。但**Python 的 `glob` 仍然会跳过它**（上面说的 `_ishidden` 是纯字符串判断），所以你的脚本安全，只是肉眼能看到。要在 Windows 上真隐藏得调 `SetFileAttributesW`，不值得。

**`.gitignore` 顺手也简单了：**

```gitignore
results/.*.tmp
```

一行覆盖所有临时文件。

---

# 完整修正版

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
      容器环境里，这个开销常常是不划算的，所以它可以关掉；但那必须是一个
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
    # 前缀加点：临时文件否则会以目标文件的完整名字开头，被
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

# 回到开头那一行

```python
metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
```

它错了吗？**取决于这个文件是什么。**

- 是**日志、缓存、可随时重新生成的中间产物** → 这一行完全够用。上面那 60 行是
  过度工程。
- 是**交付物**（别人会读、CI 会依赖、花了钱才产出的、丢了要重跑的）→ 这一行是
  一个等着被触发的静默故障。

判断标准很简单一句话：**「这个文件半截会不会有人当成完整的？」** 会，就不能用
`write_text`。

而真正的教训不是"要用原子写"，是**这一行看起来完全正常，所以没人会在 code
review 里拦它** —— 它的问题不在语法、不在类型、不在测试覆盖率，而在于它对
「写文件」这个动作的**默认认知是错的**：`open(w)` 从来就不是一个操作。

---

# 附：Checklist

写原子写文件时逐条对照：

- [ ] 先问一句：**这个文件半截会不会被人当成完整的？** 不会 → `write_text` 就够，别过度工程

- [ ] 临时文件在**目标同目录**（`dir=path.parent`），不是 `/tmp` —— 否则容器里 EXDEV
- [ ] 临时文件名**以点开头** —— 否则被 glob 和 CI 扫进去
- [ ] 用 `mkstemp` 不用手拼名字 —— `O_EXCL` 消除 TOCTOU
- [ ] **先序列化再 I/O** —— 序列化错误不该产生半个文件
- [ ] `flush()` **在** `fsync()` 之前 —— 顺序反了 fsync 静默无效
- [ ] `os.chmod` 修正权限 —— mkstemp 是 0600，会静默收紧
- [ ] `os.replace` 不是 `os.rename` —— Windows 上后者不能覆盖
- [ ] **fsync 父目录** —— 最常漏的一步
- [ ] `except BaseException` 不是 `Exception` —— Ctrl-C 要能清理
- [ ] 明确写下你要的是原子性还是持久性 —— 这是取舍不是遗漏
