---
title: 你那道"对账测试"可能从没失败过——因为它根本不会失败
header:
    image: /assets/images/bg_raw/BingWallpaper (16).jpg
date: 2026-11-19
tags:
 - data-engineering
 - data-quality
 - dbt
 - snowflake
 - testing
permalink: /blogs/tech/zh/parity-test-false-confidence
lang: zh
layout: single
category: tech
---

"第一原则是：你绝不能欺骗自己——而你恰恰是最容易被骗的那个人。"——理查德·费曼

# 你那道"对账测试"可能从没失败过——因为它根本不会失败

*从"我加了一道数据校验"到"我加了一盏永远亮绿灯的假信号"——区分资深与初级的，是你会不会去验证"这道测试真的会红吗？"*

上周我提了个 PR，给一条 Ascender 员工数据同步到 Salesforce 的管线加了一道护栏：源表 `ODS.HRIS.AH_OCCUPANCY` 每天重建，万一哪天只灌进来一半的数据，下游的 Salesforce 模型会把一堆员工当成"离职"处理。所以我写了个 dbt 测试——今天的行数如果掉到昨天的 80% 以下，就让整个 build 失败，把脏数据拦在上游。

逻辑无懈可击。测试也"通过"了。CI 一片绿。

然后仓库里的 AI reviewer（`github-dit`）留了两条评论。第一条说：你这个对账分支是死代码，永远不会触发。第二条说：你这个 time travel 查询会在每次运行时硬报错，把整条管线打挂。

两条看起来互相矛盾——一个说"永远不触发"，一个说"每次都炸"。我本来想反驳。于是我连到 Snowflake 真跑了一遍。

结果两条都对。而且它们揭示的，是同一个我做了二十年数据、依然会栽的坑：**一道对账测试，只有当它比较的两边真正独立时，才有意义。否则它就是一句穿着 `assert` 外衣的同义反复——它不会给你 0 分，它给你负分。**

如果你也写过"比较两个数应该相等"的数据校验——不管是行数对账、金额对账，还是"迁移前后记录数一致"——下面这三节就是为你准备的：

- **恒为真的测试不是中性的**：它持续发绿灯，让你撤掉本该有的警觉，比没有测试更危险。
- **"独立"是对账的唯一前提**：同一条 SQL、同一个事务快照、同一个对象血缘——这三种"假独立"会把对账变成自证。
- **Time travel 不是时光机**：在每天 `CREATE OR REPLACE` 的表上，它取不到"昨天"，因为昨天那个对象已经被删了。

下面不按我 debug 的顺序讲，按"最容易误导你的坑"排在最前面。

## 一、什么是 parity 测试（对账测试），以及它为什么这么诱人

parity 测试——我习惯叫"对账测试"——是数据工程里最朴素的一类断言：**两个本应相等的东西，断言它们相等。**

- 迁移：旧表和新表的行数应该一样。
- ETL：抽取的行数 == 落库的行数。
- 财务：借方合计 == 贷方合计。
- 我这个场景：透传视图 `input__ah_occupancy` 的行数，应该等于它的源表 `ODS.HRIS.AH_OCCUPANCY`。

它诱人，是因为它看起来既便宜又全面。你不需要枚举"哪些数据算脏"，你只要说"两边得对上"，仿佛一行 `count(A) = count(B)` 就守住了所有的数据完整性。

但对账测试有一个所有人都懂、却很少有人去验证的隐含前提：**被比较的两边，必须是两个独立的观测。** 两只独立的表，才能互相校对；如果你拿一只表的读数去校对它自己，你永远得到"一致"——那不是校对，那是重复读了一遍同一个数字。

> 对账的信息量，不在于"两个数相等"，而在于"两条独立的路径碰巧给出了同一个数"。路径不独立，相等就是必然，必然就没有信息。

## 二、陷阱一：同一条 SQL 里的对账，是同义反复

先看我最初写的那段"对账"逻辑，核心是这个分支：

```sql
with counts as (
    select
        (select count(*) from {{ ref('input__ah_occupancy') }})   as input_row_count,
        (select count(*) from {{ source('hris', 'ah_occupancy') }}) as source_row_count,
        ...
)
select ...
from counts
where ...
    or input_row_count <> source_row_count   -- ← 想抓"视图悄悄丢了行"
```

意图很清楚：`input__ah_occupancy` 是个透传视图（`select 固定列 from source`，没有 `where`、没有 join），我想断言它没有在中途莫名其妙少掉行。

**普通人的看法**：视图可能有 bug，加个对账，万无一失。

**资深工程师的洞察**：这两个 `count(*)` 写在**同一条 SQL 语句**里。Snowflake（以及任何符合 ACID 的数据库）对一条语句只用**一个一致性快照**——语句开始那一刻的事务时间点。这条语句里的 `input_row_count` 和 `source_row_count` 读的是**同一份数据的同一个瞬间**。而视图又是无过滤的透传，行数必然等于源表。

于是 `input_row_count <> source_row_count` 这个条件**在物理上就不可能为真**。它不是"大概率不触发"，是"永远不触发"。编译器不会报错，测试会快乐地通过，CI 会亮绿——而它校验的东西，是"1 等不等于 1"。

| | 看起来在做什么 | 实际在做什么 |
|---|---|---|
| `count(view) <> count(source)` 同句 | 检测视图丢行 | 把同一个数读两遍再比，恒等 |
| 加了 `where` 的视图，同句对账 | 检测过滤逻辑漂移 | 还是同一快照，漂移也测不出 |
| 真正的对账 | 两条独立路径的读数 | 需要一个**独立时点**的计数做对照 |

这里的关键，不是"视图有没有 bug"，而是**你用什么去校对它**。要真的抓住"视图相对源表丢了行"，你得拿它跟一个**跨时间、跨对象、独立产生**的计数去比——而不是在同一个括号里把源表再数一遍。

> 自己校对自己，永远及格。镜子里的人，不会告诉你脸脏了。

这个测试该怎么办？删掉。因为它想表达的那个有效断言——"今天的行数别比昨天少太多"——已经由另一个测试负责了。而那另一个测试，踩进了第二个坑。

## 三、陷阱二：在每日重建的表上，time travel 取不到"昨天"

另一个测试的思路更对：拿今天的行数，去比**昨天**的行数。Snowflake 提供了 time travel 语法，看起来天造地设：

```sql
select count(*)
from {{ model }}
at (offset => -86400)   -- 86400 秒 = 24 小时前
```

`AT(OFFSET => -86400)` 意思是"查这张表 24 小时前那一刻的样子"。拿它当"昨天的快照"，和今天比，掉太多就报警。配置里写着 `offset_seconds: 86400`。

看着很美。我连到 dev06 真跑了一下：

```
000707 (02000): Time travel data is not available for table AH_OCCUPANCY.
The requested time is either beyond the allowed time travel period
or before the object creation time.
```

**硬报错**，不是返回空。在 `dbt build` 里，这个错误会让源测试失败，进而**阻塞所有下游的 staff-EC 模型**——不管今天的数据到底全不全。我本来是加一道护栏防数据不全，结果这道护栏自己每天把管线打挂。本末倒置。

为什么？我顺手查了这张表的元数据：

```sql
show tables like 'AH_OCCUPANCY' in schema ODS.HRIS;
-- rows: 572000   retention_time: 1

select max(CREATED), max(LAST_ALTERED) from ODS.INFORMATION_SCHEMA.TABLES ...;
-- CREATED:      2026-11-19 02:30:49
-- LAST_ALTERED: 2026-11-19 02:32:38
```

两件事砸实了这个坑：

1. **retention_time = 1 天**。Snowflake 默认 time travel 只保留 1 天，`-86400` 正好卡在边界上。查询编译时有一点点时钟漂移，请求的时点就滑出了保留窗口。
2. 更致命的——`CREATED` 和 `LAST_ALTERED` **都是今天凌晨**，而且 `CREATED` 每天都在变。这是 `CREATE OR REPLACE TABLE` 的典型签名：**每天的重建不是往表里灌数据，而是把整张表对象删掉重建。**

第二点才是真正的杀招。`AT(OFFSET => -86400)` 查的是**当前这个对象**在 24 小时前的历史。但当前这个对象今天凌晨 2:30 才被创建出来——它根本没有"昨天"。昨天那张表是**另一个已经被 drop 掉的对象**，它的 time travel 历史挂在那个旧对象名下，用新对象的名字 `AT(OFFSET)` 永远够不着。

我试了更小的 offset 验证边界：

| offset | 含义 | 结果 |
|---|---|---|
| `-7200` | 2 小时前 | ✅ 572000（在今天这个对象的生命周期内） |
| `-86400` | 24 小时前 | ❌ 硬报错（早于对象创建时间） |

结论很硬：**在每天 `CREATE OR REPLACE` + 1 天 retention 的表上，没有任何一个 offset 能既不报错、又真的指向"上一次加载"。** reviewer 建议的两条缓解——"换个安全的 offset"和"让缺失快照优雅跳过"——在这张表上都救不了：安全的 offset 只能指到"今天早些时候"（测不出不完整的重建），而优雅跳过会让这道护栏变成永远不触发的空操作，绕回了陷阱一。

> Time travel 不是时光机，是对象的病历本。对象一死，病历本跟着陪葬。你以为在穿越昨天，其实在翻一个今天才出生的人的往年体检报告。

## 四、正解：自己持久化快照，拿独立时点对照

两个坑的根因是同一个：**我一直想从"当前这张表"里变出"昨天的计数"——但一张每天被整体替换的表，身上根本不携带自己的历史。** 那就别指望它了。想要一个独立的对照点，就自己把它存下来。

做法很 dbt 原生：一个 append-only 的审计模型，每次运行往里追加一行"今天数了多少"：

```sql
-- models/audit/audit__ah_occupancy_row_count.sql
{{ config(materialized='incremental') }}

select
    current_timestamp()                                        as snapshot_ts,
    current_date()                                             as snapshot_date,
    (select count(*) from {{ source('hris', 'ah_occupancy') }}) as row_count
```

然后对账测试拿今天的源表计数，去比**审计表里最近一条、日期严格早于今天**的记录：

```sql
-- tests/assert_ah_occupancy_row_count_guard.sql
with current_count as (
    select count(*) as row_count from {{ source('hris', 'ah_occupancy') }}
),
prior_snapshot as (
    select row_count
    from {{ ref('audit__ah_occupancy_row_count') }}
    where snapshot_date < current_date()      -- 关键：严格早于今天
    order by snapshot_ts desc
    limit 1
)
select current_count.row_count, prior_snapshot.row_count
from current_count cross join prior_snapshot
where prior_snapshot.row_count > 0
    and current_count.row_count < prior_snapshot.row_count * 0.8
```

`dbt build` 会先跑模型（把今天的计数追加进审计表），再跑测试。测试用 `snapshot_date < current_date()` 把今天刚写进去的那行排除掉，只跟昨天比。冷启动时审计表里没有历史，`cross join` 出空集，测试通过——不会在第一天误杀。

对照一下三个版本到底在比什么：

| 版本 | 对照来自 | 两边独立吗 | 结果 |
|---|---|---|---|
| 同句 `count(view)<>count(source)` | 同一条语句、同一快照 | ❌ 同一个数 | 恒绿，零信息 |
| `AT(OFFSET => -86400)` | 同一个对象的 time travel | ❌ 对象每天重建，历史丢失 | 硬报错，阻塞管线 |
| append-only 审计表 | **昨天那次运行**留下的独立记录 | ✅ 跨运行、跨时间、独立落盘 | 真能抓住不完整重建 |

只有第三行，那两个被比较的数，是**两条真正独立的路径**产生的：一个是此刻数的，一个是昨天的我数完存下的。它们碰巧相等才有意义，不相等才是真信号。

> 想校对今天，你得在昨天留下一个不会被今天覆盖的锚点。没有锚点的对照，都是自言自语。

这也和我上一篇《[为什么你的增量同步在悄悄丢数据](/blogs/tech/zh/incremental-sync-silent-data-loss)》是一对：那篇讲的是"任务成功但数据悄悄少了"，这篇讲的是"你为防止它而写的那道测试，本身在骗你"。静默的数据丢失很可怕，但一盏永远亮绿的假护栏，会让你以为自己已经防住了——那是更深一层的静默。

## 立刻可以做的事

1. **翻出你仓库里所有"比较两个数应该相等"的测试**，逐个问一句：这两个数是从**两条独立路径**来的吗？如果它们来自同一条 SQL、同一个事务、同一个对象——删掉或重写，它只会给你假的安全感。
2. **给每一道你觉得重要的护栏，手动制造一次失败**。改个阈值、灌一批坏数据、断一次源，看它到底会不会变红。一道从没红过的测试，和没有测试，在证据意义上是等价的。
3. **凡是依赖 time travel / `AT(OFFSET)` 的逻辑，先查两件事**：这张表的 `retention_time` 是几天？它是 `CREATE OR REPLACE` 还是 `MERGE`/`TRUNCATE+INSERT` 加载的？前者让你够不到那么远，后者会在每次重建时把历史清零。`show tables like '...'` 和 `INFORMATION_SCHEMA.TABLES.CREATED` 一眼就能看出来。
4. **要跨天对照，就自己持久化。** 别指望一张每天重建的表替你记住昨天——它连自己的昨天都不记得。

---

*一道断言的价值，等于它失败时携带的信息量。如果它永远不会失败，它的价值就是零——而如果它让你误以为自己被保护着，它的价值是负的。写完测试，别急着看它变绿；想办法让它变红一次，你才知道它活着。*
