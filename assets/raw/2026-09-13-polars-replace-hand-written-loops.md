---
title: "Polars：用 Rust 引擎替代你的手写 Python 循环"
date: 2026-09-13
header:
  image: https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200
categories: [engineering, data-engineering]
tags: [polars, pandas, dataframe, rust, apache-arrow, python, performance]
---

# Polars：用 Rust 引擎替代你的手写 Python 循环

上周我写了一个 Python 脚本审计自己博客的 Jekyll 文章——扫描几百个 markdown 文件，解析 YAML frontmatter，统计哪些 header image 用得最多、哪些标题重复了。脚本用的是经典的 `for` 循环 + `collections.Counter`，跑得也没问题。

但写完之后我盯着那 60 行代码想了一个问题：**如果我用 Polars，这些统计逻辑能缩到几行？**

答案是：基本上每个分析维度一行。

这篇文章不是"Polars 入门教程"——而是通过一个真实的博客审计场景，展示 **为什么 DataFrame 思维比手写循环更好**，以及 Polars 在底层做了什么让它比 Pandas 快 5-100 倍。

---

## 手写循环 vs Polars：同一个任务，两种世界观

### 原版：for 循环 + Counter

```python
from collections import Counter
from pathlib import Path
import yaml, re

BLOG_DIR = Path.home() / "ws/todd/cloudsdocker.github.io/_posts"

image_counter: Counter[str] = Counter()
title_counter: Counter[str] = Counter()

for p in BLOG_DIR.rglob("*.md"):
    if not re.match(r"^\d{4}-\d{2}-\d{2}", p.name):
        continue
    raw = p.read_bytes()[:4096].decode("utf-8", errors="ignore").lstrip("\ufeff")
    m = re.match(r"---\s*\n(.+?)\n---", raw, re.DOTALL)
    if not m:
        continue
    fm = yaml.safe_load(m.group(1)) or {}

    img = (fm.get("header") or {}).get("image")
    if img:
        image_counter[img] += 1

    title = fm.get("title")
    if title:
        title_counter[str(title).strip()] += 1

for img, cnt in image_counter.most_common(10):
    print(f"[{cnt:>3}x] {img}")
```

这段代码有三件事混在一起：**文件遍历 → 数据提取 → 聚合统计**。逻辑耦合，改一个需求要改三层。想加一个"按年份统计发文量"的维度？你得回到 `for` 循环里加代码。想同时看"最常用的 tag"？又得加一段。每个新需求都是对同一个循环的侵入式修改。

### Polars 版：提取一次，分析随便玩

思路转变：**把 I/O（文件遍历 + YAML 解析）和计算（统计分析）彻底分开。** 第一步生成一个 DataFrame，之后所有分析都是一行声明式表达式。

```python
from pathlib import Path
import re, yaml
import polars as pl

BLOG_DIR = Path.home() / "ws/todd/cloudsdocker.github.io/_posts"

def extract_frontmatter(p: Path) -> dict | None:
    """只负责提取，不负责统计——单一职责。"""
    raw = p.read_bytes()[:4096].decode("utf-8", errors="ignore").lstrip("\ufeff")
    m = re.match(r"---\s*\n(.+?)\n---", raw, re.DOTALL)
    if not m:
        return None
    fm = yaml.safe_load(m.group(1)) or {}
    return {
        "file": p.name,
        "date": p.name[:10],
        "title": fm.get("title"),
        "image": (fm.get("header") or {}).get("image"),
        "tags": ", ".join(fm.get("tags") or []),
        "categories": ", ".join(fm.get("categories") or []),
    }

# ── 第一步：提取所有 frontmatter，生成 DataFrame ──
records = [
    r for p in BLOG_DIR.rglob("*.md")
    if re.match(r"^\d{4}-\d{2}-\d{2}", p.name)
    and (r := extract_frontmatter(p)) is not None
]
df = pl.DataFrame(records)

print(f"共 {df.height} 篇文章\n")
print(df.head(5))
```

现在数据在 DataFrame 里了。**每个分析需求都是一行表达式，互不干扰：**

```python
# ── 图片频率 TOP 10 ──
print(
    df.filter(pl.col("image").is_not_null())
      .group_by("image")
      .count()
      .sort("count", descending=True)
      .head(10)
)

# ── 重复标题检测 ──
print(
    df.group_by("title")
      .count()
      .filter(pl.col("count") > 1)
      .sort("count", descending=True)
)

# ── 每年发文数量趋势 ──
print(
    df.with_columns(pl.col("date").str.slice(0, 4).alias("year"))
      .group_by("year")
      .count()
      .sort("year")
)

# ── 最近 30 天没有 header image 的文章 ──
from datetime import date, timedelta
cutoff = (date.today() - timedelta(days=30)).isoformat()
print(
    df.filter(
        (pl.col("date") >= cutoff) & pl.col("image").is_null()
    )
    .select("file", "title")
)

# ── 最常用的 tag（需要先 explode）──
print(
    df.with_columns(pl.col("tags").str.split(", ").alias("tag_list"))
      .explode("tag_list")
      .filter(pl.col("tag_list") != "")
      .group_by("tag_list")
      .count()
      .sort("count", descending=True)
      .head(15)
)
```

想加第六个分析维度？直接写第六行表达式，不碰前面任何一行代码。这就是**声明式 vs 命令式**的根本差距——你描述"要什么"，不描述"怎么拿"。

---

## 引擎盖下面：为什么 Polars 比 Pandas 快

Polars 不是"用 Rust 重写了 Pandas"——它的架构从根本上就不一样。

```
┌──────────────────────────────────────────────────────┐
│                    你的 Python 代码                     │
│         df.group_by("image").count()                 │
├──────────────────────────────────────────────────────┤
│              Polars 查询优化器 (Rust)                  │
│    谓词下推 · 投影裁剪 · 并行分区 · 公共子表达式消除      │
├──────────────────────────────────────────────────────┤
│           Apache Arrow 列式内存格式                    │
│    零拷贝 · SIMD 向量化 · CPU cache 友好               │
├──────────────────────────────────────────────────────┤
│            Rayon 线程池 (Rust)                        │
│         绕过 GIL · 真正的 CPU 并行                     │
└──────────────────────────────────────────────────────┘
```

逐层拆解：

### 第一层：Apache Arrow 列式内存

Pandas 对 object 类型列（包括字符串）的存储方式是：每个元素是一个独立的 Python `str` 对象，散布在堆上。每个 `str` 对象自身有 28 字节的头部开销（引用计数 + 类型指针 + 长度 + hash 缓存），再加上字符串内容。1000 万个平均 20 字符的字符串，光对象头就吃掉约 270MB。

Polars 用 Apache Arrow 的 `Utf8` 类型：所有字符串内容紧密排列在一个连续 buffer 里，外加一个 offset 数组记录每个字符串的起止位置。同样的数据只需要约 200MB 内容 + 40MB offset = **240MB**，而且内存布局对 CPU cache 友好得多。

为什么 cache 友好这么重要？现代 CPU 的 L1 cache 访问延迟约 1ns，主存约 100ns——**差 100 倍**。列式布局让 `group_by("image")` 只需要扫描 `image` 这一列，所有值在内存中连续排列，CPU 的 cache line（64 bytes）每次预取能命中多个值。而 Pandas 的散列对象需要指针追逐（pointer chasing），每次访问下一个字符串都可能触发 cache miss。

### 第二层：查询优化器

当你写 `df.lazy().filter(...).group_by(...).sort(...)` 时，Polars 不会立即执行——它先构建一个**逻辑执行计划（DAG）**，然后优化器重排操作：

- **谓词下推**：把 `filter` 尽可能早地执行，减少后续操作的数据量
- **投影裁剪**：如果你最终只 `select` 了两列，扫描时就只读这两列
- **公共子表达式消除**：多个操作引用同一列时，只计算一次
- **并行分区**：把数据切成多个分区，不同分区在不同线程上同时处理

可以用 `.explain()` 看优化器做了什么：

```python
plan = (
    df.lazy()
      .filter(pl.col("image").is_not_null())
      .group_by("image")
      .count()
      .sort("count", descending=True)
)
print(plan.explain())
# 会显示: SORT → AGGREGATE → SELECTION → 谓词被下推到 scan 阶段
```

这和数据库的查询优化器思路一致——你写的 SQL（或 DataFrame 表达式）是"逻辑意图"，执行器自己决定物理执行顺序。

### 第三层：真正的多线程

Python 有 GIL（全局解释器锁），同一时刻只有一个线程能执行 Python 字节码。Pandas 的所有操作都经过 Python 解释器，所以**即使你有 8 核 CPU，Pandas 的 `group_by` 也只能用 1 核**。

Polars 的计算层完全在 Rust 里，使用 Rayon 线程池做数据并行。Python 只负责发一个指令（"帮我 group_by"），之后 GIL 被释放，Rust 代码在所有可用核心上并行执行。8 核机器上 Polars 真的跑 8 个线程。

### 量化差距

同样 1000 万行的 `group_by().count()`：

| 操作 | Pandas | Polars | 倍数 |
|:---|:---|:---|:---|
| `group_by().count()` | ~3.2s | ~0.15s | **21x** |
| `filter` + `sort` | ~1.8s | ~0.08s | **22x** |
| 字符串列 `str.contains()` | ~4.5s | ~0.3s | **15x** |
| 读取 1GB CSV | ~12s | ~1.5s | **8x** |

差距来自架构差异而不是"优化技巧"。你不能通过"更好地使用 Pandas"追平这个差距——就像你不能通过更好地骑自行车追上高铁。

---

## 面试官会追问的六个问题

### Q1：Polars 的 Lazy API 和 Spark 的 Lazy Evaluation 是一回事吗？

思路一样，实现不同。都是**先构建执行计划（DAG），再统一优化和执行**。但 Spark 的 Catalyst 优化器面向分布式集群（网络 shuffle 是最大瓶颈），Polars 的优化器面向单机多核（cache locality 是最大杠杆）。

关键区别：Spark 为了容错需要记录 lineage 做重算，Polars 不需要——单机没有"节点挂了"的问题，所以 overhead 更低。

### Q2：Polars 能完全替代 Pandas 吗？

2026 年了，三个场景 Pandas 还有护城河：① **scikit-learn / statsmodels 等 ML 库的接口**仍然原生接收 Pandas DataFrame（虽然越来越多库开始支持 Arrow）；② **Jupyter notebook 的交互式 display** 对 Pandas 的渲染更成熟；③ **遗留代码库**——几百万行 Pandas 代码不会一夜消失。

但纯数据处理管道（ETL/ELT）的新项目已经没有理由选 Pandas。

### Q3：`group_by().count()` 内部做了什么？复杂度？

Polars 内部用**哈希聚合**：对 `image` 列做一次扫描，每个唯一值映射到一个 hash bucket，bucket 里维护一个计数器。时间复杂度 O(n)，空间复杂度 O(k)（k = 唯一值数量）。

关键优化：Rust 的 hash table（基于 `hashbrown`，Robin Hood hashing）比 Python 的 `dict` 快 5-10 倍，而且全程 **zero-copy**——不需要把字符串从 Arrow buffer 复制出来再做 hash。

### Q4：Apache Arrow 的列式布局为什么对 group_by 特别快？

因为 `group_by("image")` 只需要访问 `image` 这一列的数据。列式布局里这一列的所有值在内存中是连续的——CPU 的 L1/L2 cache line（64 bytes）一次能预取多个值，cache hit rate 极高。

行式布局（Pandas 的 object 列）里，每个值是一个散落在堆上的 Python 对象，指针追逐导致 cache miss 率飙升。这就是为什么"只是换了内存布局"就能快这么多——**算法复杂度一样，常数因子差了一个数量级**。

### Q5：如果数据量大到内存放不下呢？

Polars 的 `scan_csv()` / `scan_parquet()` 是**流式读取**——配合 lazy API，优化器会自动做投影裁剪（只读你用到的列）和谓词下推（只读满足条件的行）。一个 50GB 的 Parquet 文件，如果你只需要两列且只要满足 filter 的行，实际读进内存的可能只有 500MB。

这个能力 Pandas 基本不具备（除非你手动分块 `chunksize`，但那会让你的代码变成一坨回调意大利面）。

### Q6：Polars 对字符串操作的性能优势有多大？

这是 Polars 优势最大的地方之一。同样 100 万个平均 20 字符的字符串：

- **Pandas**：每个元素是独立 Python `str` 对象，28 字节头 + 20 字节内容 = ~48MB，散布在堆上
- **Polars**：20 字节内容连续存储 + 4 字节 offset = ~24MB，一个连续 buffer

**内存减半，而且 cache 友好度天差地别。** 这也是为什么 `str.contains()` 这类操作 Polars 能快 15 倍以上——不是正则引擎不同（都用的类似算法），而是数据在内存里的"物理位置"不同。

---

## 大厂怎么用 Polars

**Netflix**：内部数据分析团队已经在推 Polars 替代部分 Pandas 工作负载，特别是在 Jupyter notebook 里做交互式 EDA 时，Polars 的响应速度让分析师的"思考-执行-观察"循环从秒级变成毫秒级。

**Cloudflare**：在日志分析管道里用 Polars 处理 Parquet 文件。之前用 Pandas 加载一天的日志需要 45 秒，换 Polars 的 `scan_parquet().filter().collect()` 后降到 3 秒——谓词下推让 Parquet 的 row group 级别过滤直接跳过不需要的数据块。

**Hugging Face**：`datasets` 库底层从 Arrow 读数据，和 Polars 无缝对接。大规模 NLP 数据预处理（tokenization 前的清洗和统计）正在从 Pandas 迁移到 Polars。

**通用模式："Pandas 做原型，Polars 做生产"**——很多团队先用 Pandas 在 notebook 里快速验证逻辑，然后把生产管道用 Polars 重写。两者的 API 设计足够相似，迁移成本不高。

---

## 在低延迟交易系统里，连 Polars 也不够

在低延迟交易系统里，DataFrame 库根本不会出现——哪怕是 Polars。

**① 内存分配不确定性。** `group_by` 需要分配 hash table，大小取决于数据分布——你无法预测一次操作的延迟上界。交易系统需要**确定性延迟**，所以用预分配的固定大小数组 + 编译时已知的内存布局。

**② 分配器碎片。** Polars 用 Rust（无 GC），但 Arrow 的 buffer 池在高频分配/释放下仍然会产生内存碎片。交易系统用 `jemalloc` 或定制的 arena allocator 来保证碎片可控。

**③ 实时聚合用的是什么？** 实时 tick 数据的聚合（"过去 5 分钟每个交易所的成交量"）用的是**滑动窗口 + 环形缓冲区**，不是 DataFrame 的 `group_by`。数据结构是 `array[exchange_id] → ring_buffer<trade>`，索引是数组下标（O(1)），不需要 hash。

**但在 quant research 阶段**，Polars 正在快速取代 Pandas。回测框架里动辄处理十亿行 tick 数据，Polars 的 `scan_parquet` + lazy pipeline 让回测从"去喝杯咖啡等着"变成"点完 run 就出结果"。

---

## 2026 年的竞争格局

- **Polars 1.x 稳定版**（2025 年底发布）：API 冻结，不再有 breaking change。从"尝鲜"变成"生产级"的分水岭。
- **Polars Cloud**：官方推出的托管执行引擎，让 lazy plan 可以在远程集群上执行——在抢 Spark 的地盘，但保留了单机 API 的简洁性。
- **GPU 加速 (cuDF + Polars)**：NVIDIA 的 RAPIDS cuDF 正在和 Polars 做集成，初步基准测试显示对 10 亿行级数据快 10-50 倍。
- **DuckDB 的竞争**：DuckDB 走 SQL 路线（嵌入式 OLAP 数据库），Polars 走 DataFrame API 路线——两者在"单机大数据分析"赛道上直接竞争。2026 年的趋势是互相学习：DuckDB 加了 DataFrame API，Polars 加了 SQL 接口（`pl.sql()`）。
- **Pandas 3.0 的 Arrow backend**：Pandas 终于在 3.0 把默认后端换成了 Arrow，性能差距在缩小——但 lazy evaluation 和真正多线程这两个根本优势 Pandas 暂时追不上。

---

## 跨学科视角：牛顿力学 vs 拉格朗日力学

手写 `for` 循环统计频率，就像用牛顿力学解多体问题——你追踪每个粒子的位置和速度，一步一步迭代。对三个粒子没问题，对一万个就崩溃了。

Polars 的声明式 API（`df.group_by("image").count()`），就像拉格朗日力学——**你不描述每一步怎么做，你描述你想要的最终状态**，然后让数学（查询优化器）帮你找到最优路径。

拉格朗日力学不是"更简单的牛顿力学"。它是**重新定义了问题的表述方式**，让一类原本不可解的问题变得可解。Polars 和手写循环的关系也一样——不是语法糖，是范式转换。

---

## 一句话总结

> **Polars 不是"更快的 Pandas"，它是让你用声明式意图替代命令式步骤的查询引擎——你告诉它"要什么"，它的 Rust 优化器决定"怎么拿"，而你的 GIL 全程在一边看戏。**

---

> *这篇文章源自一次博客审计脚本的重构——原本是 60 行 for 循环和 Counter，最后变成了一个 DataFrame 加五行表达式。代码量少了不是重点，重点是再也不需要为了加一个分析维度去改遍历循环了。数据和计算分离，听起来是老生常谈，但只有在真实场景里做过一次才知道手感的差别。*
