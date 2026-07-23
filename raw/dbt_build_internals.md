# dbt build 底层原理深度解析
>
> 系列：数据工程师的硬核手册 · 第一篇  
> 适用版本：dbt-core >= 1.9  
> 源码根据：[dbt-labs/dbt-core @ GitHub](https://github.com/dbt-labs/dbt-core)

---
Raw materials to be added into blog:
**Almost — but not only `stage`.**

`dbt run` / `dbt build` **runs every model** in the project (input, stage, output, quarantine), in **dependency order** — not “stage only”.

---

## What actually happens

When you run:

```bash
dbt run
# or
dbt build   # run + test
```

dbt:

1. **Reads all `.sql` files** under `models/`
2. **Builds a graph** from `ref()` / `source()` (who depends on whom)
3. **Runs them in order** — upstream first, downstream after

For your project, roughly:

```text
source (ODS tables, not built by dbt)
    ↓
input/*.sql        → creates VIEWs (light pull from ODS)
    ↓
stage/*.sql        → creates VIEWs (joins, mapping, business rules)
    ↓
output/*.sql       → creates TABLEs (Salesforce-ready columns)
    ↓
quarantine/*.sql   → creates TABLEs (bad rows, optional branch)
```

So **transformation is spread across layers**:

| Layer | Role |
|-------|------|
| **input** | “Get data in” — select from `source()`, rename/limit columns |
| **stage** | “Do the work” — joins, filters, map to SF field names |
| **output** | “Package for delivery” — often mostly `SELECT` from stage |
| **quarantine** | “Side channel” — rows that fail validation |

**Stage is the busiest layer**, but input and output are part of the same pipeline.

---

## `run` vs `build`

| Command | Does |
|---------|------|
| **`dbt run`** | Execute models → create/replace views & tables in Snowflake |
| **`dbt build`** | **`run` + `test`** — same models, then run tests from `stage.yml` etc. |

Airflow uses **`dbt build`** in the DAG (run everything + tests).

---

## Important nuance: order is **dependencies**, not folder names

dbt doesn’t literally go “input folder → stage folder → output folder” because of folder names.

It goes:

> **`input__employee` before `stage__staff_person_account`** because stage has `ref('input__employee')`.

If model A `ref()`s model B, B runs first — always.

---

## One-line summary

> **`dbt run`/`build` kicks off the whole DAG of SQL models — input → stage → output (and quarantine) — and materializes them as views/tables in Snowflake. Stage is where most transformation lives, but it’s not the only layer that runs.**

If you only want part of that:

```bash
./run_dbt_local.sh run --select stage__staff_person_account+
```

That runs **that stage model + its downstream output**, not the entire project (unless you add `+` upstream too).

## 0. 为什么要写这篇文章

很多人用 `dbt build` 就像用微波炉——按个按钮，食物热了，不知道里面发生了什么。  
这篇文章的目标是把微波炉拆开，让你看清楚每一颗螺丝。

我们将从一行 Airflow 里的 shell 命令出发：

```bash
cd "${DBT_PROJECT_DIR}" && dbt build && dbt docs generate
```

逐层往下挖，直到找到 dbt-core 的 Python 源码，彻底弄清楚 `dbt build` 的执行序列和设计逻辑。

---

## 1. 背景：这行命令在哪里运行

在这个数据管道里，`dbt build` 并不是在你的笔记本上跑，而是在 Kubernetes 里临时创建的一个 Pod 里执行的：

```python
# sync_ascender_staff_to_salesforce_ec.py (Airflow DAG)
dbt_run = KubernetesPodOperator(
    task_id="dbt_run",
    image=dbt_image,          # Docker 镜像里才有 dbt 安装
    cmds=["bash", "-c"],
    arguments=[
        """cd "${DBT_PROJECT_DIR}" && \
               dbt build && \
               dbt docs generate """
    ],
    is_delete_operator_pod=True,   # 跑完立刻销毁 Pod
)
```

**关键认知**：

- dbt 不安装在 Airflow 服务器上，只在 Docker 镜像里
- Pod 是一次性的，跑完即毁，彻底云原生
- 所有 Snowflake 凭据通过环境变量注入 Pod

---

## 2. `dbt build` 是什么，它不是什么

### 它是什么

`dbt build` 是 dbt 的"一键全跑"命令，等价于：

```
dbt seed + dbt run + dbt test + dbt snapshot
```

但**不是简单的串行执行**，而是把所有资源节点放进同一个有向无环图（DAG）里，按依赖关系并行调度。

### 它不是什么

- 不是顺序固定的"先 seed 再 model 再 test"——顺序由依赖图决定
- 不是黑魔法——每一步都有明确的 Python 类对应
- 不是隐式定义的——源码完全开放，100% 可读

---

## 3. 源码导航：三个关键文件

```
dbt-core/core/dbt/
├── cli/main.py          # CLI 入口，注册 `dbt build` 命令
├── task/build.py        # BuildTask 类，核心调度逻辑（最重要）
├── task/run.py          # RunTask，BuildTask 的父类
└── task/runnable.py     # GraphRunnableTask，并行调度基类
```

类继承关系：

```
GraphRunnableTask  (runnable.py)
    └── RunTask    (run.py)
            └── BuildTask  (build.py)   ← dbt build 的实体
```

---

## 4. CLI 入口：`cli/main.py`

```python
# core/dbt/cli/main.py
@cli.command("build")
def build(ctx, **kwargs):
    """Run all seeds, models, snapshots, and tests in DAG order"""
    from dbt.task.build import BuildTask

    task = BuildTask(
        ctx.obj["flags"],
        ctx.obj["runtime_config"],
        ctx.obj["manifest"],
    )
    results = task.run()
    success = task.interpret_results(results)
    return results, success
```

CLI 层极其薄——就是实例化 `BuildTask` 然后调 `task.run()`。  
真正的重量级逻辑全在 `BuildTask` 里。

---

## 5. `BuildTask` 的核心设计：`RUNNER_MAP`

```python
# core/dbt/task/build.py
class BuildTask(RunTask):
    """
    The Build task processes all assets of a given process and attempts to
    'build' them in an opinionated fashion. Every resource type outlined in
    RUNNER_MAP will be processed by the mapped runners class.
    """

    RUNNER_MAP = {
        NodeType.Model:      run_model_runner,       # → ModelRunner
        NodeType.Snapshot:   snapshot_model_runner,  # → SnapshotRunner
        NodeType.Seed:       seed_runner,            # → SeedRunner
        NodeType.Test:       test_runner,            # → GenericTestRunner
        NodeType.Unit:       test_runner,            # → UnitTestRunner
        NodeType.SavedQuery: saved_query_runner,
        NodeType.Exposure:   exposure_runner,
        NodeType.Function:   function_runner,
    }
    ALL_RESOURCE_VALUES = frozenset({x for x in RUNNER_MAP.keys()})

    MARK_DEPENDENT_ERRORS_STATUSES = [
        NodeStatus.Error,
        NodeStatus.Fail,
        NodeStatus.Skipped,
        NodeStatus.PartialSuccess,
    ]
```

**设计思想**：这是一张"工种分配表"。  
`BuildTask` 本身不知道怎么跑 SQL——它只负责调度；每个节点类型交给对应的 `Runner` 去执行。这是典型的**策略模式（Strategy Pattern）**。

---

## 6. 完整执行序列

```
dbt build
   │
   ▼
BuildTask.run()          ← 继承自 GraphRunnableTask.run()
   │
   ├─ ① _runtime_initialize()
   │       ├─ 解析 manifest.json（编译时产生，含所有节点的元数据+依赖关系）
   │       ├─ 构建 GraphQueue（带拓扑排序的调度队列）
   │       └─ build_model_to_unit_test_map()
   │             └─ 找出哪些 unit test 绑定哪些 model
   │                确保 unit test 先于对应 model 执行
   │
   ├─ ② get_graph_queue()   ← BuildTask 重写了父类方法
   │       ├─ 第一次选择：full_selected_nodes（含 unit tests）
   │       ├─ 第二次选择：selected_nodes_wo_unit_tests（不含 unit tests）
   │       ├─ 差集 = selected_unit_tests（需要提前执行的单测）
   │       └─ 把 unit test 的边注入依赖图
   │
   ├─ ③ execute_nodes() 并行主循环（线程池 or 单线程）
   │       └─ while 队列未空:
   │             取一批"依赖已全部满足"的节点
   │             ┌─ 若是 Model 且有绑定的 unit test:
   │             │     handle_job_queue()
   │             │       → call_model_and_unit_tests_runner()
   │             │             先跑 unit test（全通过才继续）
   │             │             再跑 model
   │             └─ 否则:
   │                   get_runner_type(node) 查 RUNNER_MAP
   │                   实例化对应 Runner
   │                   runner.execute() → 真正的 SQL / 文件操作
   │
   └─ ④ interpret_results()  汇总 pass / error / skip 统计
```

---

## 7. 每种 Runner 内部干什么

### SeedRunner（处理 CSV 文件）

```
SeedRunner.execute(node)
   ├─ 读取 seeds/ 目录下的 .csv 文件
   ├─ 推断列类型（或使用 schema.yml 中 column_types 覆盖）
   ├─ 在数据仓库中执行：
   │     CREATE OR REPLACE TABLE <schema>.<seed_name> (<columns>)
   └─ 批量 INSERT 数据行
```

**用途**：小型静态参考数据，如国家代码、离职原因分类等。  
例子（真实项目中的种子文件）：

```csv
# seeds/data__hr_termination_reason.csv
TERM_REASON_GROUP_CD,TERM_REASON_GROUP_DESC,TERM_REASON_CD,TERM_REASON_DESC
VOLUNTARY,VOLUNTARY,ABN,Abandonment of Employment
INVOLUNTARY,INVOLUNTARY,DEC,Death
VOLUNTARY,VOLUNTARY,RS,Resignation
...
```

下游 model 通过 `{{ ref('data__hr_termination_reason') }}` 引用它，就像引用普通表一样。

### ModelRunner（处理 .sql 模型文件）

```
ModelRunner.execute(node)
   ├─ 编译 Jinja2 模板（解析 ref()、source()、env_var()、config()）
   ├─ 根据 materialized 策略选择 DDL：
   │     view        → CREATE OR REPLACE VIEW AS <sql>
   │     table       → CREATE OR REPLACE TABLE AS SELECT <sql>
   │     incremental → MERGE INTO ... / INSERT INTO ...（只处理新增行）
   │     ephemeral   → 不建表，仅作 CTE 内联到调用者 SQL 里
   ├─ 执行 pre-hook（如 CREATE SCHEMA IF NOT EXISTS ...）
   ├─ 执行主体 SQL
   └─ 执行 post-hook（如 GRANT SELECT ON TABLE ... TO ROLE ...）
```

### GenericTestRunner（处理 schema.yml 中的 tests）

```
GenericTestRunner.execute(node)
   ├─ 编译测试 SQL（如 SELECT count(*) FROM ... WHERE col IS NULL）
   ├─ 执行 SQL，检查返回行数
   └─ 行数 > 0 → FAIL（意味着有不符合预期的数据）
      行数 = 0 → PASS
```

---

## 8. 依赖图是如何构建的

`manifest.json` 是 `dbt compile` 阶段产生的文件，里面记录了每个节点的 `depends_on` 列表：

```json
{
  "nodes": {
    "model.proj.output__staff_person_account": {
      "depends_on": {
        "nodes": [
          "model.proj.stage__staff_person_account",
          "model.proj.stage__staff_eligible_employee"
        ]
      }
    }
  }
}
```

`GraphQueue` 在这个基础上做**拓扑排序**，维护一个"入度为0的节点"队列——入度为0意味着所有前置依赖都已完成，可以执行了。这是标准的 Kahn 算法思路。

---

## 9. 真实案例：`tgt_salesforce_ec_staff` 项目里 `dbt build` 实际跑了什么

项目结构：

```
tgt_salesforce_ec_staff/
├── dbt_project.yml        seed-paths: ["data"]  ← 但 data/ 目录是空的！
└── models/
    ├── input/             input__employee.sql, input__codes.sql ...   (view)
    ├── stage/             stage__staff_person_account.sql ...         (view)
    ├── output/            output__staff_person_account.sql ...        (table)
    └── quarantine/        quarantine__staff_person_employment.sql ... (table)
```

| 阶段 | 实际发生 |
|------|---------|
| Seed | 扫描 `data/` → 空目录 → **0 个节点，跳过** |
| Run  | 按依赖图：`input views` → `stage views` → `output tables` / `quarantine tables` |
| Test | schema.yml 中定义的 not_null、unique 等测试 |
| Snapshot | `snapshots/` 不存在 → **跳过** |

所以这个项目的 `dbt build` **本质等同于 `dbt run` + `dbt test`**。

---

## 10. `dbt docs generate` 是做什么的

紧跟在 `dbt build` 之后的这个命令：

```bash
dbt build && dbt docs generate
```

`dbt docs generate` 不执行任何 SQL，它只做"文档生成"：

1. 读取已存在的 `manifest.json`（由 `dbt build` 在编译阶段产生）
2. 连接数据仓库，查询 `INFORMATION_SCHEMA`，获取每张表、每个字段的实际数据类型和统计信息，写入 `catalog.json`
3. 将 `manifest.json` + `catalog.json` 合并，生成静态 HTML 文档站点
4. 文档里有完整的**血缘关系图（Lineage Graph）**——每张表从哪里来、流向哪里，一目了然

---

## 11. 关键设计思想总结

| 设计概念 | 在 dbt build 中的体现 |
|---------|---------------------|
| 策略模式 | `RUNNER_MAP` 把节点类型映射到 Runner 类 |
| 拓扑排序 | `GraphQueue` 保证依赖先于被依赖节点执行 |
| 声明式配置 | `dbt_project.yml` + `schema.yml` 定义"做什么"，dbt 决定"怎么做" |
| 失败传播 | `MARK_DEPENDENT_ERRORS_STATUSES` 确保上游失败时下游自动 Skip |
| 双重选择 | unit test 的特殊处理——先选含 unit test，再选不含，取差集 |

---

## 12. 延伸阅读：源码路径速查

| 要看什么 | 文件路径 |
|---------|---------|
| `dbt build` CLI 注册 | `core/dbt/cli/main.py` |
| `BuildTask` 全部逻辑 | `core/dbt/task/build.py` |
| `RunTask`（父类） | `core/dbt/task/run.py` |
| 并行调度基类 | `core/dbt/task/runnable.py` |
| `ModelRunner` | `core/dbt/task/run.py`（RunTask 同文件） |
| `SeedRunner` | `core/dbt/task/seed.py` |
| `GenericTestRunner` | `core/dbt/task/test.py` |
| `GraphQueue` 实现 | `core/dbt/graph/queue.py` |
| manifest 编译 | `core/dbt/compilation.py` |

---

> 作者：Todd Zhang  
> 源于真实项目 `sync_ascender_staff_to_salesforce_ec` 的源码阅读笔记  
> 本文所有结论均基于 dbt-core 源码，非凭空推测
