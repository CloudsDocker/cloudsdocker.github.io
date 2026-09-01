---
title: "从 openpyxl 到 calamine:一次关于 xlsx 解析、Polars 生态与工程取舍的深潜"
date: 2026-08-04
categories: [engineering, data-engineering, python]
tags: [openpyxl, calamine, polars, rust, xlsx, etl, performance]
---

一段简单的 `openpyxl` 字段扫描脚本,牵出了一整条关于 Excel 解析引擎选型的技术链路:从 XLSX 文件的底层结构,到 openpyxl 的性能瓶颈,再到 Rust 编写的 python-calamine 如何在 ETL pipeline 里取而代之,最后落到 Polars 生态的全貌与实际代码重写。这篇文章按对话推进的顺序,完整记录这条思考路径。

## Part 1: openpyxl 读取原理与面试级深挖

### 🎯 30秒版本

`openpyxl` 读的不是 Excel 的"现在",是 Excel 上次保存那一刻的"过去"。XLSX 文件本质是一个 ZIP 包,里面装着一堆 XML(`sheet1.xml`、`sharedStrings.xml`……)。`openpyxl` 把这些 XML 解析成 Python 对象树,`data_only=True` 让你拿到的是**上次保存时缓存的公式计算结果**,而不是公式本身。用 `iter_rows` 当生成器一行行扫,拿字符串做包含匹配——本质就是"结构化 grep"。

### ⚙️ 底层原理

- **XLSX = ZIP + XML**:`unzip -l xxx.xlsx` 能看到 `xl/worksheets/sheet1.xml`、`xl/sharedStrings.xml`、`xl/styles.xml`。字符串默认走"共享字符串表"(去重字典),单元格里存的是索引,不是原文——这也是 Excel 文件里几万个重复字符串却不太占体积的原因。
- **`data_only=True` 的坑**:公式单元格的值只有在**上次用 Excel(或 LibreOffice)打开并保存过**时才会被缓存进 XML。如果文件是脚本生成、从未被 Excel 打开保存过,`data_only=True` 拿到的是 `None`,不是公式字符串,也不是计算结果。
- **内存模型**:`load_workbook` 默认把整个工作簿解析进内存(DOM 式),大文件很吃内存。想省内存要用 `read_only=True`,这时 `iter_rows` 才是真正的流式生成器(底层基于 `lxml.etree.iterparse` 增量解析),不是先加载全量再切片。

### 🔬 面试官追问链

**Q1: 这份 xlsx 有 50 万行、200 列,你这段代码会怎样?**
A: 默认模式会把整棵 DOM 树建在内存里,轻松 OOM 或卡死。正确做法是 `load_workbook(path, data_only=True, read_only=True)`,`iter_rows` 才是真正惰性求值的生成器,内存占用是 O(1) 而不是 O(n_rows × n_cols)。

**Q2: `read_only=True` 之后还能用 `row[0].row` 拿行号吗?有什么限制?**
A: 可以,`Cell.row/column` 属性还在。但 `read_only` 模式下工作簿不可写,也不支持随机跳转访问(不能 `ws['A100']` 任意跳),只能顺序遍历——牺牲随机访问换取常量内存。

**Q3: 每行拼接字符串做 `in` 匹配,复杂度是多少?**
A: 每行 `str(c.value)` + join 是 O(列数),子串查找是 O(字符串长度)。但每行都 materialize 完整字符串是重复的内存分配,50 万行下 GC 压力比想象中大——更好的做法是先用生成器过滤,别每行都拼完整字符串。

**Q4: 同一个 workbook 被多线程并发读,安全吗?**
A: `openpyxl` 的 `Workbook` 对象不是线程安全的。并发场景应该是每个 worker 各自 `load_workbook` 一份只读句柄,而不是共享一个 `wb` 对象跨线程访问。

**Q5: 最大的失败模式是什么?**
A: 静默返回错误数据而不是报错。`data_only=True` 拿 `None`、sheet 名打错导致 `KeyError`、路径不存在导致 `FileNotFoundError`——都要显式 try/except 兜底,别让静默 `None` 混进匹配逻辑。

### 🏗️ 大厂怎么用

- **数据接入层**:业务方永远在用 Excel 传数据,ETL pipeline 里标配一层"xlsx → parquet/csv 标准化"适配器,大文件场景通常跳过纯 Python 的 openpyxl,改用 Rust 后端的 calamine 或 Polars 的 `read_excel`。
- **Schema Mapping / 字段血缘扫描**:很多公司"字段血缘"工具第一步就是扫描 mapping 文档找字段名,再对接 dbt/Airflow 的 schema registry。

### 💸 高风险版本(金融场景)

正确性优先于性能:
- 用 pydantic/jsonschema 定义期望字段集合做集合差集比对,漏字段直接 fail CI。
- 记录文件 SHA256、读取时间戳、读取人,做审计留痕。
- 公式陷阱是真事故源——加"文件最后编辑时间 vs 缓存时间"一致性检查,防止"看起来对但其实是旧值"的静默 bug。

### 🌉 跨学科透镜

这就像考古学里的**地层学**:你挖出的不是"活的"数据,是一份"上次被保存时凝固的沉积层"。`data_only=True` 缓存的公式结果,像琥珀里封存的昆虫——精确记录某一历史瞬间,但如果地层之后被搅动过(公式重算却没保存),挖出来的可能是已不存在的"幽灵版本"。

---

## Part 2: python-calamine 取代 openpyxl 的工程逻辑

### 🎯 30秒版本

openpyxl 是纯 Python 写的 XML 解析器,读大 xlsx 本质是在 Python 层反复 build DOM 树,慢且吃内存。calamine 是 Rust 写的 xlsx/xls/ods 解析库,通过 PyO3 绑定暴露给 Python,把最耗时的 XML parsing 和字符串处理下沉到编译型语言里跑。ETL 只读不写,没理由为了用不到的"写公式和样式"功能,承担纯 Python 解析的性能税。

### ⚙️ 底层原理

- **openpyxl 的瓶颈**:每个 `<c>` 标签都要走一次 Python 对象构造(`Cell` 实例)、类型推断、共享字符串表查找,全是 Python 解释器里的循环,函数调用和对象分配开销在百万级 cell 时被放大。
- **calamine 做了什么**:整个解析在 Rust 里完成,一次性解析成紧凑内存结构,再通过 PyO3 一次性搬到 Python 侧,关键在于**跨语言边界穿越的次数从 O(cell 数) 降到 O(1) 或 O(sheet 数)**。
- **和 parquet 的关系**:parquet 是列式存储 + 字典编码。xlsx 的共享字符串表本质上已是字典编码的雏形,所以"xlsx → parquet"是"行式+字典编码 转成 列式+字典编码"——这也是为什么 calamine 拿到数据后直接喂给 Polars(内部是 Arrow 列式格式)比喂给 pandas(numpy,行列语义模糊)更顺滑。

### 🔬 面试官追问链

**Q1: calamine 快一个数量级,快在 I/O 还是 CPU?**
A: CPU-bound 的解析开销,不是 I/O。xlsx 文件本身不大(ZIP 压缩过)。瓶颈是"XML 文本变结构化数据"这一步的对象分配和类型判断,Rust 零成本抽象 + 无 GC 在这一步碾压 CPython。

**Q2: xlsx 里有公式,calamine 怎么处理?**
A: 只读缓存值(类似 `data_only=True`),不做公式求值,也不暴露公式字符串。需要看公式、改公式、存公式,openpyxl 仍是唯一选择。

**Q3: Polars 用 calamine 引擎,遇到合并单元格、多级表头会怎样?**
A: 合并单元格底层只有左上角 cell 有值,其余是 None,需业务层自己 forward-fill。类型推断上 calamine/Polars 更"严格死板"——一列混了字符串和数字,倾向推断统一 dtype 把不匹配的转成 null 或报错,这在"脏 Excel"迁移时最容易踩坑。

**Q4: 生产 pipeline 的标准化适配器该怎么设计容错?**
A: 三层防御:①格式探测层(magic bytes 判断真实文件类型);②schema 校验层(pydantic/pandera 校验列名列数类型,不匹配 fail 而非产出脏 parquet);③降级策略(calamine 失败时 fallback 到 openpyxl 重试)。

**Q5: 内存占用上 calamine 和 openpyxl(read_only=True)谁更省?**
A: calamine 通常仍是全量加载(没有 openpyxl read_only 那种流式游标),但底层数据结构更紧凑,同数据量下内存显著低于 openpyxl 全量 DOM 模式,但不一定低于 openpyxl 流式模式——超大文件+内存受限场景要具体权衡。

### 🏗️ 大厂怎么用

- Airbnb / Uber 级别的数据平台通常搭一层轻量 microservice(或 Airflow Operator),统一把业务方上传的 xlsx 转成 parquet 落地到 data lake,下游只读 parquet,把"Excel 解析的坑"限制在一个地方。
- Polars 官方基准显示,`read_excel(engine="calamine")` 在中大型 xlsx(10 万行级)上比 pandas + openpyxl 组合快 5-10 倍。
- DuckDB 的 Excel 扩展提供了另一条路线:直接用 SQL 读 xlsx,跳过 Python 对象层。

### 💸 高风险版本(金融场景)

- **确定性要求**:calamine 和 openpyxl 对"脏" Excel 的类型推断可能不一致,金融合规场景必须锁定引擎版本 + golden file 回归测试。
- **审计链**:保留"原始 xlsx hash → parquet hash"映射记录,便于倒查。
- **公式陷阱升级版**:字段名本身是公式生成的场景下,calamine 只读缓存值,文件"公式没重新保存就传上来"会导致标准化后字段名是过期值——典型的沉默数据错误,需加字段名集合对比历史版本的 diff 检查。

### 🚀 2026年前沿

- calamine 已是 Polars 生态默认读 Excel 引擎,pandas 社区在推动可插拔引擎支持。
- DuckDB 原生 Excel 扩展日趋成熟,"SQL 直接查 xlsx"越来越流行。
- 越来越多工具直接输出 Arrow RecordBatch 而非 pandas DataFrame,减少内存格式转换次数。
- openpyxl 的定位收缩为"写"专用工具——纯读取场景下已是过时选择。

### 🌉 跨学科透镜

这就像翻译学里的**直译 vs 编译型翻译**。openpyxl 像人类同声传译,逐词逐句现场理解再转述——准确但慢。calamine 更像提前训练好的专业机器翻译引擎,把"理解语言结构"这件事在更底层、更高效的系统里预先编译好,你只要最终译文,不需要每一步都由那个慢速通用翻译官出面。

---

## Part 3: Polars 生态全貌

Polars 不只是"pandas 换个皮",而是一整套从单机内存计算到分布式云端计算的生态系统,核心卖点是 Rust 实现 + Arrow 内存格式 + 惰性执行(lazy evaluation)。pandas 是"手动挡自行车",Polars 是"带涡轮增压 + 自动驾驶"的车,同一条路,跑法完全不同。

生态构成:

| 组件 | 干什么用 | 例子 |
|---|---|---|
| polars-core | 核心 DataFrame 引擎,Rust 写,Arrow 列式内存 | `df.group_by("region").agg(pl.col("revenue").sum())` |
| Lazy API | 惰性求值,先建查询计划再优化执行,类似 Spark 的 DAG | `pl.scan_parquet("*.parquet").filter(...).collect()` |
| Streaming Engine | 数据比内存大也能跑,分批处理不 OOM | `.collect(streaming=True)` |
| IO 层 | 读写 parquet/csv/json/xlsx(calamine)/Delta Lake/Iceberg | `pl.read_excel("f.xlsx", engine="calamine")` |
| polars-cloud | 本地 Lazy 查询无缝提交到云端分布式集群 | 本地代码加 `.remote()` 即可跑在集群上 |
| connectorx 集成 | 从数据库直接拉数据到 Polars,比 pandas.read_sql 快数倍 | `pl.read_database_uri(query, uri)` |
| Arrow 互操作 | 和 DuckDB、PyArrow、Ray 之间零拷贝传数据 | `pl.from_arrow(duckdb_result.arrow())` |

更多实战例子:

```python
import polars as pl

# 例1:惰性查询 + 谓词下推(predicate pushdown)
# 只有真正 collect() 时才会执行,Polars 会自动把 filter 尽量下推到读取阶段
result = (
    pl.scan_parquet("s3://bucket/events/*.parquet")
    .filter(pl.col("event_date") >= "2026-01-01")
    .group_by("user_id")
    .agg(pl.col("amount").sum().alias("total_spend"))
    .sort("total_spend", descending=True)
    .limit(100)
    .collect()
)

# 例2:窗口函数(和 SQL 的 OVER PARTITION BY 等价)
df = df.with_columns(
    pl.col("revenue").rank(descending=True).over("region").alias("rank_in_region")
)

# 例3:和 DuckDB 零拷贝互操作,各取所长
import duckdb
arrow_tbl = df.to_arrow()
duckdb.sql("SELECT region, SUM(revenue) FROM arrow_tbl GROUP BY region")
```

---

## Part 4: 用 calamine 重写原始扫描脚本

原始需求是扫描多个 sheet,找出包含特定字段名的行。下面给出两个版本:**原生 python-calamine**(最简单、最省内存)和 **Polars + calamine 引擎**(适合后续接过滤/聚合逻辑)。

### 版本 A:原生 python-calamine

```python
from python_calamine import CalamineWorkbook

path = '/Users/toddzhang/ws/mq/uac/docs/FTG-083-UAC_to_SFEC_Full_Mapping_v2 _mask_fields_revised.xlsx'

wb = CalamineWorkbook.from_path(path)

for sheet_name in ['PersonAccount', 'UAC-SFBuildCheck']:
    print('====', sheet_name)
    sheet = wb.get_sheet_by_name(sheet_name)
    rows = sheet.to_python()  # list[list[Any]],一次性解析成 Python 原生类型

    for row_idx, row in enumerate(rows[:80], start=1):
        vals = [str(v) for v in row if v is not None]
        joined = ' | '.join(vals)
        if 'UacApplicantId' in joined or 'external' in joined.lower():
            print(f'r{row_idx}: {joined[:400]}')
```

**关键差异**(相对 openpyxl):
- `to_python()` 一次性把整张 sheet 解析进内存的 list of list,没有 openpyxl 那种逐 cell 生成器,没有 `read_only=True` 的等价流式模式——calamine 的哲学是"反正 Rust 解析够快,直接全量吐给你"。
- `data_only` 参数不存在——calamine 从设计上只读缓存值,没有"读公式 vs 读结果"的选项。
- 没有 `.row` / `.column` 属性,拿到的是纯 Python list,行号要自己用 `enumerate` 维护。

### 版本 B:Polars + calamine 引擎(推荐)

```python
import polars as pl

path = '/Users/toddzhang/ws/mq/uac/docs/FTG-083-UAC_to_SFEC_Full_Mapping_v2 _mask_fields_revised.xlsx'

for sheet_name in ['PersonAccount', 'UAC-SFBuildCheck']:
    print('====', sheet_name)
    df = pl.read_excel(
        path,
        sheet_name=sheet_name,
        engine="calamine",
        read_options={"header_row": None},  # 原代码没假设有表头,保持一致
    )

    # 把整行拼成一个字符串列,再用 Polars 表达式做包含匹配(向量化,不是 Python for 循环)
    joined_expr = pl.concat_str(
        [pl.col(c).cast(pl.Utf8) for c in df.columns],
        separator=' | ',
        ignore_nulls=True,
    )

    matched = (
        df.with_row_index("row_num", offset=1)
        .with_columns(joined_expr.alias("joined"))
        .filter(
            pl.col("joined").str.contains("UacApplicantId")
            | pl.col("joined").str.to_lowercase().str.contains("external")
        )
        .head(80)
    )

    for row in matched.iter_rows(named=True):
        print(f"r{row['row_num']}: {row['joined'][:400]}")
```

版本 B 的价值在于:字符串匹配从 Python 层的逐行循环,变成了 Polars 表达式引擎里的**向量化字符串操作**(底层调用 Rust 的 `str.contains`,SIMD 加速)。百万行级数据下,原始 openpyxl 版本大概率是秒级到十秒级的 Python for 循环,换成 Polars 表达式基本是毫秒级。

**选择建议**:只是简单扫几个 sheet 找字段名 → 版本 A 够用,依赖最少。要接入正式的 ETL/校验 pipeline、后续还要 groupby/join/diff → 直接上版本 B,少写一层胶水代码。

---

## 总结

**一句话 mic-drop**:calamine 快的不是"Rust 比 Python 快"这种玄学,而是把"跨语言边界穿越次数从每个 cell 一次降到每张表一次"——工程优化的本质永远是减少边界穿越,不是换一种语言重写逻辑。
