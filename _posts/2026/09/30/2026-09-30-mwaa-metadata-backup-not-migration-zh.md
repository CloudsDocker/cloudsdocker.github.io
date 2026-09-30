---
title: '云厂商技术支持部门的原话：元数据库删了，我们也恢复不了'
header:
    image: /assets/images/hd_mysql_bible.jpg
date: 2026-09-30
tags:
 - aws
 - airflow
 - terraform
 - devops
 - cloud-infrastructure
permalink: /blogs/tech/zh/mwaa-metadata-backup-not-migration
lang: zh
layout: single
category: tech
---

> 「无恃其不来，恃吾有以待也。」——《孙子兵法·九变》

# AWS Support 的原话：元数据库删了，我们也恢复不了

*托管 Airflow 的全部历史，活在一个你拿不到连接串的数据库里。*

一次 MWAA 环境升级之后，整个 Airflow 元数据库归零：DAG 运行历史、任务实例记录、审计日志、Variables、Connections，全部回到出厂状态。我开了 support case 问能不能恢复，拿到的回复是这样一段：

> Unfortunately, AWS does not retain accessible snapshots or backups of deleted/replaced MWAA metadata databases. Once the old environment was destroyed via the Terraform replacement, the metadata is unrecoverable. AWS Support does not have direct access to the managed metadata database and cannot perform restores on behalf of customers.

翻译过来：AWS 不保留已删除或被替换的 MWAA 元数据库的可访问快照；旧环境一旦被 Terraform 的替换动作销毁，元数据不可恢复；AWS Support 没有这个托管数据库的直接访问权限，也无法代客户执行恢复。

这段话里没有一个词是关于「这一次」的。它描述的是一个长期成立的事实：**在这个服务模型里，你的 DAG 运行历史没有任何 AWS 侧的兜底副本。** 唯一可能存在的副本，是你自己写代码存下来的那一份。

于是问题就从"这次是谁的错"变成了一个更难的问题：**在一个连不上数据库的托管服务里，"有备份"这件事到底由谁、在哪一层、用什么代码来兜底。**

如果你读到这里心里想的是"我们有备份 DAG"——先对着它跑这一条：

```bash
grep -rn "is_paused = true" dags/ plugins/ 2>/dev/null
```

命中了的话，这个脚本每跑一次，就把整个环境的 DAG 暂停一次。它不是备份工具，是迁移工具。你把它挂上定时调度的那天，你其实给自己排了一个周期性停机。

根因两句话能说完（第一节）。真正花时间的是后面：官方给的两套导出代码为什么不能混用、四个只有读源码才知道的坑、以及生产上到底该怎么排。

看完这篇，你应该能拿走三件事：

- 托管服务托管的是**可用性**，没托管**你历史数据的持久性**。这两件事在 MWAA 上的分界线，正好落在你自己的 `dags/` 目录里。
- AWS 官方给了你两套元数据导出代码，行为完全不同：一套会暂停全部 DAG，一套不会。`grep is_paused` 一秒分辨。用错那套，你的「每日备份」就是每日停机。
- 备份文件的保质期由 Airflow 版本决定。`task_instance` 在 2.10 多了 `executor` 列，`log` 多了 `try_number` 列——跨版本恢复不是 `COPY`，是列对齐工程。

下面是按**教学顺序**排的，不是按我踩坑的顺序。真实的排查是来回折返的，你不必跟着折返一遍。

（文中环境名做了脱敏，`etl-sit-251` / `etl-sit-2112` 对应真实的旧/新环境名，版本号、时间戳、报错数量都是真实的。）

---

## 一、事故只有两行 diff，但它关掉的是一扇门

一次 MWAA 升级，Terraform PR 改了两行：

```diff
-airflow_version = "2.10.3"
+airflow_version = "2.11.2"
-name            = "etl-sit-251"
+name            = "etl-sit-2112"
```

`251` 是 2.5.1 的缩写，`2112` 是 2.11.2 的缩写——把当前 Airflow 版本焊进环境名，这个命名习惯在这个仓库里跑了好几年，看上去只是一次可读性改进。

apply 完成，控制台 `AVAILABLE`，`LastUpdate: SUCCESS`，依赖安装日志干净，调度器心跳正常。十分钟后 DAG 列表开始变红，一类是权限角色不存在，另一类查下来精确是 **195** 个：

```text
airflow.exceptions.AirflowException: The access_control mapping for DAG 'X'
includes a role named 'finance-developers', but that role does not exist
```

```text
KeyError: ''
```

角色不存在，Variable 取出来是空字符串。两个症状，一个原因：这个环境的元数据库是全新的、空的。CloudTrail 里给出了终审证据——不是一次 `UpdateEnvironment`，而是一前一后两次调用：

```text
10:58:46  DeleteEnvironment  etl-sit-251
11:26:12  CreateEnvironment  etl-sit-2112
```

根因到这里就结束了：MWAA 的 `UpdateEnvironment` 接口里，`Name` 只出现在 URL 路径 `/environments/{Name}` 上，从不出现在请求体里。改名这个动作在 API 层面不存在，所以 Terraform 只能用「删掉旧的、建一个新的」来实现你声明的状态。CloudFormation 文档里那句 `Update requires: Replacement` 说的就是这件事。

**但真正把这件事从「运维失误」变成「架构缺口」的，是 AWS Support 回复里的另一段话。**

Support 在确认根因之后，给出的就是开头那段不留余地的答复。它的信息量比根因大得多——它说的不是「你这次没了」，而是：

> 在这个服务模型里，你的 DAG 运行历史、审计日志、Variables、Connections，没有任何一个 AWS 侧的兜底副本。唯一可能存在的副本，是你自己写代码存下来的那一份。

如果你的合规、SLA 统计、审计追溯依赖这些数据——那这份副本不是「运维的 nice to have」，它是**你系统的一部分**，而且必须写在 `dags/` 里。

| 你看到的信号 | 它真正回答的问题 | 它没有回答的问题 |
|---|---|---|
| `AVAILABLE` | 环境现在是否健康 | 是不是原来那个环境 |
| `LastUpdate: SUCCESS` | 本次操作是否完成 | 这是更新还是替换 |
| 依赖安装日志干净 | 新环境构建成功 | 旧环境的状态有没有跟过来 |
| 「AWS 是托管服务」 | 谁负责跑 | 谁负责记得 |

> 托管服务托管的是「它活着」，没托管「它记得」。

---

## 二、为什么备份 Airflow 元数据是件反常的事

先把反常之处摆清楚，否则后面所有方案看起来都像过度设计。

一个普通的 Postgres 备份长这样：控制台开自动快照、`pg_dump` 拉一份、PITR 定个保留期，全程不碰应用代码。

MWAA 的元数据库上，这三条路一条都没有：没有 RDS 控制台条目，没有 endpoint，没有连接串，没有 PITR 按钮。官方文档写得很直白——**从已有的 MWAA 环境出发，没有对元数据库的直接访问**。

那唯一的入口是什么？是你自己的 DAG 进程里那个 session：

```python
from airflow import settings
from sqlalchemy import text

session = settings.Session()
result = session.execute(text("select dag_id, run_id, state from dag_run"))
```

也就是说，**能访问这个数据库的唯一身份，是"一个正在这个环境里运行的 Airflow task"**。这一条直接决定了后面所有设计的形状：备份必须是一个 DAG，恢复必须是一个 DAG，演练必须是一个 DAG，而这些 DAG 的生命周期又绑在那个随时可能被替换掉的环境上。

这就是我后来管它叫**「托管边界的静默一半」**的东西：托管服务把「跑得起来」做成了平滑的抽象——你不需要知道 Aurora 在哪、schema 怎么迁移、心跳谁在看；但它把「记得住」留在了抽象之外，而且不会在同一个界面上告诉你这条缝在哪。责任分界线从来不画在控制台上，它画在 API 参考里那一行没人读的字段列表里。

> **天花板定律**：一个托管资源的恢复能力上限，等于它交到你手上的最低层访问接口。MWAA 交给你的是 `settings.Session()`——所以你的备份能力上限，就是你愿意写多少 SQL。

---

## 三、AWS 给了你两套代码，其中一套会让你每天停机一次

这是整篇文章里最实用的一段。

搜「MWAA metadata backup」，你会撞到两份 AWS 官方出品的代码，长得很像，都在 `aws-samples` 下，都叫「导出元数据」。它们的行为**根本不同**。

### 3.1 第一套：`mwaa_export_data.py`（start-stop 用例里的那个）

这是官方迁移路径的实现。打开源码，第一个任务就说明了它的性格：

```python
# pause all active dags to have consistent and reliable copy of dag history exports
def pause_dags():
    session = settings.Session()
    session.execute(
        text(f"update dag set is_paused = true where dag_id != '{dag_id}';"))
    session.commit()
    session.close()
```

它不是「顺手暂停一下」。DAG 依赖链是：

```text
back_up_activedags >> pause_dags >> [export_data, export_active_dags,
                                     export_variable, export_connection]
                   >> clean_up >> [activate_dags_on_failure, notify_success]
```

注意 `activate_dags_on_failure` 的 `trigger_rule="one_failed"`——只有**失败时**才恢复暂停状态。成功路径上没有 unpause。因为设计意图就是这样：导完了你就该去新环境了，旧环境本来就该停着。官方文档在这件事上是坦白的：「在导出与导入过程中，所有其他 DAG 都处于暂停状态。」

还有一个更容易被忽略的动作——为了记住「哪些 DAG 本来是开着的」，它往**被备份的那个库里建表**：

```python
def back_up_activedags():
    session = settings.Session()
    session.execute(text(f"drop table if exists active_dags;"))
    session.execute(text(
        f"create table active_dags as select dag_id from dag where not is_paused and is_active;"))
```

`drop table if exists` + `create table as`。一个写生产元数据库的备份脚本。对一次性迁移来说这是合理的工程折中；对一个每天跑一遍的备份任务来说，这是在生产库里反复建删表。

### 3.2 第二套：`mwaa-dr`（PyPI 包，真正的备份工具）

同样是 AWS 出品（`aws-samples/mwaa-disaster-recovery`），`mwaa-dr` 把导出/导入包装成了一个 DAG factory。它的 backup DAG 里，`setup` 这一步是这样的：

```python
def setup_backup(self, **context):
    print("Executing the backup workflow setup ...")
    if self.storage_type == S3:
        print("No local file system setup necessary!")
        return
    # ...（只在 LOCAL_FS 模式下建目录）
```

**没有 pause。** 一行都没有。它的 DAG 结构是 `setup >> export_tables >> teardown`，纯读 + 写 S3。而且它显式支持被定时：

```python
def schedule(self) -> str:
    return Variable.get("DR_BACKUP_SCHEDULE", default_var=None)
```

默认 `None`（只能手动触发），你设一个 `DR_BACKUP_SCHEDULE` 变量，它就变成周期任务。这才是一个能挂上调度的东西。

> **普通人的看法**：两份都是 AWS 官方的元数据导出脚本，随便挑一个，功能差不多。
>
> **资深工程师的洞察**：它们回答的是两个不同的问题。一个回答「我要把历史搬到另一个环境去」，另一个回答「我要在不打扰任何人的情况下留一份副本」。前者可以接受停机，因为停机本来就是迁移窗口的一部分；后者一旦接受停机就自我否定了——**一个你不敢在业务高峰随手跑一次的备份，等于没有备份**，因为真正需要它的那一刻，你也不敢跑。

### 3.3 一张表分清楚

| 维度 | `mwaa_export_data.py`（迁移） | `mwaa-dr` backup DAG（备份） |
|---|---|---|
| 是否暂停全部 DAG | 是（`update dag set is_paused = true`） | 否 |
| 成功后是否自动恢复暂停状态 | 否（只在失败时 `one_failed` 恢复） | 不涉及 |
| 是否写生产元数据库 | 是（`create table active_dags`） | 否（只读 + 写 S3） |
| 能否挂定时调度 | 不应该 | 能（`DR_BACKUP_SCHEDULE`） |
| `trigger` 表 | 显式排除 | 默认包含 |
| 恢复前是否要求空库 | 不要求（`COPY` 进空环境） | 要求（配套 `cleanup` DAG） |
| 适用场景 | 环境改名 / 跨版本迁移 / 蓝绿切换 | 周期性备份 / DR 演练 / 同环境回滚 |

**判据一行**：`grep -n "is_paused" <你的备份脚本>`。有，它是迁移工具；没有，它才可能是备份工具。

---

## 四、四个只有读源码才知道的坑

这一节是我建议你存下来的部分。官方文档不会讲这些，但它们会在你真正需要恢复的那天决定成败。

### 4.1 `variable.csv` 和 `connection.csv` 里是解密后的明文

导出 Variables 的代码是这样的：

```python
query = session.query(Variable)
for y in query.all():
    w.writerow({k[0]: y.key, k[1]: y.get_val(), ...})
```

Connections 那边是 `y.get_password()`。

`get_val()` 和 `get_password()` 都是**解密后**的值。因为必须解密——Fernet key 是 per-environment 的，密文搬到新环境解不开。所以这条路走通的代价是：**你的备份桶从此是一个密码库**，里面是纯文本 CSV，每一行是一个生产系统的凭证。

官方文档在这件事上只留了一句 Note，说如果你要迁移敏感数据「建议为 S3 桶开启默认加密」。这个措辞相对于实际风险，是轻了的。落地时至少要有：

- 专用桶，KMS CMK（不是 SSE-S3）加密，key policy 只放行 MWAA 执行角色
- 桶策略拒绝非 TLS、拒绝跨账号，开 Block Public Access
- 生命周期规则短期过期（备份的价值随时间衰减，泄露风险不衰减）
- **更好的做法是让这两张表根本不值得备份**：把 Variables/Connections 搬到 Secrets Manager backend，元数据库里就没东西可泄露了。`mwaa-dr` 为这种情况专门留了策略开关，设成 `DO_NOTHING` 就跳过这两张表的恢复

### 4.2 `active_dags.csv` 的 header 契约不对称

导出端把 `active_dags` 表流成 CSV 时，用的是 `csv.writer(...).writerows(chunk)`——**没有写 header 行**。

导入端读它的时候：

```python
cursor.copy_expert(
    "COPY active_dags FROM STDIN WITH (FORMAT CSV, HEADER TRUE)", f)
```

`HEADER TRUE`。PostgreSQL 会把文件第一行当表头丢掉。而文件第一行是一个真实的 `dag_id`。

推论：迁移完成后，`active_dags` 表里会少一个 DAG，`UPDATE dag SET is_paused=false FROM active_dags` 就不会把它放出来——**有一个本来在跑的 DAG，在新环境里会一直是 paused**，而且没有任何报错。

这是我读代码得出的结论，不是我跑出来的，建议你在自己的环境里验一遍：

```bash
# 导出后：CSV 有多少行
aws s3 cp "s3://$BUCKET/data/active_dags.csv" - | wc -l
# 导入后：新环境里 active_dags 表有多少行，差值应该是 0，不是 1
```

一个静默少一行的 bug，和一个抛异常的 bug，代价差了一个数量级。

### 4.3 CSV 的列名在说谎，而它恰好还能工作

这个最微妙，也最值得内行一笑。导出 Connections 时声明的列名是：

```python
k = ["conn_id", "conn_type", "host", "schema", "login", "password",
     "port", "extra", "is_encrypted", "is_extra_encrypted", "description"]
```

实际写进去的值却是错位的：

| CSV 第 N 列 | 声明的列名 | 实际写入的值 |
|---|---|---|
| 3 | `host` | `description` |
| 4 | `schema` | `host` |
| 7 | `port` | `schema` |
| 8 | `extra` | `port` |
| 9 | `is_encrypted` | `extra` |

看到这里你会以为找到了一个数据错乱的 bug。但导入端是这样读的：

```python
rows.append(Connection(row[0], row[1], row[2], row[3], row[4],
                       row[5], row[6], port, row[8]))
```

**位置参数**。而 `Connection.__init__` 的签名恰好是 `(conn_id, conn_type, description, host, login, password, schema, port, extra)`——和实际写入顺序完全对齐。所以 round-trip 是正确的。

真正的问题是：这个 CSV 文件的契约不是它的列名，而是 `Connection.__init__` 的**参数顺序**。列名只存在于导出脚本的源码里，而且是错的。谁要是照着列名自己写一个 importer（或者拿这个 CSV 去做审计、做 diff、导进别的系统），host 和 description 会对调，schema 和 port 会错位，而且照样不报错。

> **口诀**：一个只有位置契约、没有 header 的数据文件，它的 schema 不在文件里，在读它的那段代码里。备份格式如果依赖「有人记得读的顺序」，它就已经开始腐烂了。

### 4.4 `trigger` 表：两个官方工具的意见是相反的

`mwaa_export_data.py` 里有一段很少见的、写得很诚实的注释：

```python
# NOTE: The trigger table is intentionally excluded from export.
# Starting in Airflow 2.9.0, trigger.kwargs is Fernet-encrypted with a per-environment key.
# Exporting and importing these rows into a different environment causes
# cryptography.fernet.InvalidToken errors that crash the triggerer and scheduler.
```

而 `mwaa-dr` 的默认备份表清单里，`trigger` **在**里面：`variable`、`connection`、`slot_pool`、`log`、`job`、`dag_run`、`trigger`、`task_instance`、`task_fail`、`xcom`。

两个 AWS 官方工具对同一张表给出了相反的答案，而且**两个都对**——因为它们的恢复目标不同：

| 恢复场景 | Fernet key | `trigger` 能不能带 |
|---|---|---|
| 同环境恢复（误删数据、回滚、DR 演练回原环境） | 相同 | 能，`kwargs` 解得开 |
| 跨环境恢复（改名、蓝绿、跨区 DR） | 不同 | 不能，`InvalidToken` 会把 triggerer 和 scheduler 打崩 |

**面试拿分点**：被问到「Airflow 元数据迁移有哪些表不能直接搬」，答「trigger 表」只是及格；答「`trigger.kwargs` 从 2.9.0 起用 per-environment Fernet key 加密，跨环境导入会抛 `InvalidToken` 打崩 triggerer；而且 trigger 本身是 deferred task 的瞬时状态，新环境跑一遍就重建了，所以正确做法是排除而不是修复」——这个答案会被记住，因为它同时给出了机制、后果和取舍。

顺手记住另外几张表的性格，都能在源码里对上：

| 表 | 会不会跟着走 | 为什么 |
|---|---|---|
| `dag`、`dag_tag`、`dag_code`、`serialized_dag` | 不需要 | scheduler 解析 S3 里的 DAG 文件时自动重建 |
| 权限/角色相关表 | 不需要（但要重建） | 由 IAM 执行角色与 FAB 配置生成；那一批 `access_control` 报错就是它没跟过来 |
| `dataset` / `asset` 相关表 | 显式排除 | 2.9.2 起自动生成，导入会撞主键 |
| `slot_pool` | 带，但排除 `default_pool` | 新环境自带 `default_pool`，导进去会冲突 |
| `task_instance` | 带，但过滤掉未终结状态 | 导出条件是 `state NOT IN ('running','restarting','queued','scheduled','up_for_retry','up_for_reschedule')`——**正在跑的任务不在备份里** |
| 导出 DAG 自己的 `dag_run` 行 | 特殊处理 | 否则恢复后它会像 `catchup=True` 一样重跑自己 |

最后那两行值得单独说。`task_instance` 的过滤条件意味着：你的备份语义是「已终结的历史」，不是「此刻的全量状态」。任何一次恢复之后，跨越备份时刻正在运行的那批任务需要人工重跑——这是你 RPO 之外的一笔额外账，AWS 的 DR 博客也把「中断期间的 DAG run 需要手动重跑」写成了显式步骤。

---

## 五、官方 runbook 的 `cd` 目标已经是 404

这一段是时效性最强的，也是最能说明「照着文档抄会翻车」的。

AWS 官方迁移文档到今天（2026-09-30）还这样写：

```bash
git clone https://github.com/aws-samples/amazon-mwaa-examples.git
cd amazon-mwaa-examples/usecases/metadata-migration/{existing-version}-{new-version}/
```

然后让你改 `export_data.py` 里的 `S3_BUCKET`，上传，unpause 那个叫 `db_export` 的 DAG。

自己验一下：

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  https://raw.githubusercontent.com/aws-samples/amazon-mwaa-examples/main/usecases/metadata-migration/2.5.1-2.10.1/export_data.py
# 404
```

`usecases/metadata-migration/` 目录现在只剩两个文件：`.airflowignore` 和 `README.md`。README 的全部技术内容是一句话：

> Metadata import and export scripts are now part of the [MWAA Disaster Recovery project](https://pypi.org/project/mwaa-dr/).

脚本搬家了，文档没跟上。所以如果你在事故当天照着官方文档执行，你会卡在一个不存在的目录上——而那一刻旧环境可能还活着，导出窗口正在关闭。

更值得注意的是新家的支持矩阵。`mwaa-dr` 当前版本 2.2.0，README badge 上的支持版本是：

```text
MWAA 2.10.3 | 2.10.1 | 2.9.2 | 2.8.1 | 2.7.2 | 2.6.3 | 2.5.1 | 2.4.3
```

**没有 2.11。** 而这次事故的目标版本正是 2.11.2。

这不是什么阴谋，看一眼 factory 的代码就明白为什么：

```python
class DRFactory_2_10(DRFactory_2_9):
    def task_instance(self, model):
        return BaseTable(
            name="task_instance",
            columns=[..., "executor",  # New Field
                     ...],
            export_filter="state NOT IN ('running', ...)",
        )
```

每个版本的 factory 都是上一个版本的子类，重写的只有**列发生变化的那几张表**：`task_instance` 在 2.10 多了 `executor`，`log` 多了 `try_number`。也就是说，**备份文件的 schema 是和 Airflow 版本一一绑定的**。一份 2.10.3 上导出的 `task_instance.csv`，`COPY` 进 2.11.2 的库里，要么列数不匹配直接报错，要么更糟——列数恰好对上而语义错位。

> **文档的半衰期短于依赖的半衰期。** 所以判断一条 runbook 能不能用的方式不是「它在官方站点上」，而是它引用的每个路径、每个包版本，今天还 `curl` 得到。在事故里，一条过期的 runbook 比没有 runbook 更贵，因为它消耗的是你最紧张的那几十分钟。

---

## 六、那么生产上到底怎么做

先说清楚：**下面这套我们还没上线**，是事故之后定下的方案，写在这里是因为设计上的取舍比代码本身更值得抄。凡是需要实测验证的地方我都标出来了。

### 6.1 第一步不是写备份，是缩小备份范围

最省事的备份是不需要备份的数据。先给每张表定性，再决定写多少代码：

| 层 | 内容 | 处置 |
|---|---|---|
| **L0 不用备份** | `dag`、`dag_tag`、`dag_code`、`serialized_dag`、`dataset`/`asset` | scheduler 解析 S3 自动重建。备份它们只会增加恢复时的主键冲突 |
| **L1 不该放在这儿** | `variable`、`connection` | 搬去 Secrets Manager backend。一次改造同时解决「明文进 S3」和「备份范围过大」两个问题 |
| **L2 必须备份** | `dag_run`、`task_instance`、`task_fail`、`log`、`job`、`slot_pool`、`xcom` | 这七张表才是审计、SLA 统计、运行历史的真正载体，也就是这次事故真正丢掉的东西 |
| **L3 不要备份** | 跨环境场景下的 `trigger`；权限/角色表 | Fernet key 不通；权限应由 IaC 重建，而不是从 CSV 恢复——否则你的权限模型会漂移到没人能复现的状态 |

L1 那一行值得多说一句：把 Variables/Connections 移出元数据库不只是安全改进，它还改变了事故的形状。这次 `KeyError: ''` 之所以致命，是因为业务代码的配置活在元数据库里；如果它们活在 Secrets Manager 里，同样一次环境替换只会丢历史，不会让 DAG 直接崩。

### 6.2 备份 DAG（真实可跑的代码）

```python
# dags/backup_metadata.py
from airflow import DAG
from mwaa_dr.v_2_10.dr_factory import DRFactory_2_10

factory = DRFactory_2_10(
    dag_id="dr_backup_metadata",
    path_prefix="data",
    storage_type="S3",
)

# 必须赋值给全局变量，否则 DAG 扫不到
dag: DAG = factory.create_backup_dag()
```

配套三件事，缺一不可：

1. 专用 S3 桶（KMS CMK 加密），MWAA 执行角色有读写权限
2. Airflow 变量 `DR_BACKUP_BUCKET` = 桶**名**（不是 ARN）
3. Airflow 变量 `DR_BACKUP_SCHEDULE` = 你的 RPO 对应的 cron。不设就只能手动触发——而「等我需要的时候手动跑一下」，就是这次事故的完整剧本

`requirements.txt` 里加 `mwaa-dr`（它依赖 `smart-open>=7.0.4`）。

**升级到 2.11 时必须自己接一棒**：`mwaa-dr` 还没有 `v_2_11` factory，所以要么继承 `DRFactory_2_10` 重写列发生变化的表，要么先在 [aws-mwaa-local-runner](https://github.com/aws/aws-mwaa-local-runner) 上把 2.11 的 schema diff 跑出来。这一步没有捷径，也别指望文档会告诉你——它连 2.10 的脚本搬家都还没更新。

### 6.3 恢复演练，而不是恢复方案

`mwaa-dr` 的 restore **要求一个空库**，所以它配了一个 `cleanup` DAG。这意味着「在生产环境里试一下恢复」是个危险动作——正确的演练场是 local runner：

```python
factory = DRFactory_2_10(
    dag_id="dr_restore_metadata",
    path_prefix="data",
    storage_type="LOCAL_FS",   # 演练用本地文件系统，不碰 S3
)
dag: DAG = factory.create_restore_dag()
```

恢复时那两个策略变量决定了 Variables/Connections 的行为，默认是 `APPEND`：

| `DR_VARIABLE_RESTORE_STRATEGY` / `DR_CONNECTION_RESTORE_STRATEGY` | 行为 | 什么时候用 |
|---|---|---|
| `DO_NOTHING` | 完全不恢复这两张表 | 已经用 Secrets Manager backend（推荐终态） |
| `APPEND`（默认） | 只补缺失的条目，不覆盖 | 往一个已经配好的新环境里补历史 |
| `REPLACE` | 用备份覆盖现有条目 | 确定备份比当前环境更权威时 |

演练要验的不是「DAG 跑绿了」，是这四条：**Variables 条数对得上、Connections 能实际连通、`dag_run` 的行数和最近 N 天的历史对得上、UI 里 unpause 状态和事故前一致**（这一条正好能顺带验证 4.2 里那个 header 推论）。

### 6.4 把这次的教训变成一道闸门，而不是一条口头规矩

事故复盘里最没用的产物是「下次注意」。这次真正要留下的工程产物是一条 CI 检查——任何会替换有状态资源的 plan 都不允许自动合并：

```bash
terraform plan -out=tfplan
terraform show -json tfplan | jq -e '
  [ .resource_changes[]
    | select(.change.actions == ["delete","create"]
          or .change.actions == ["create","delete"])
    | select(.type | test("mwaa_environment|db_instance|rds_cluster|elasticache|msk_cluster"))
  ] | length == 0
' || { echo "有状态资源将被替换，需要人工签核 + 导出窗口"; exit 1; }
```

它不阻止你替换资源——有时候你真的需要。它只是强制「替换」这件事被一个人看见一次。这就是 senior 和 principal 的分界线：把只靠口头传承的知识，变成一个会失败的检查。

### 6.5 日志组：那个命名习惯的黑色幽默

顺一句，也是唯一的好消息。任务日志在 CloudWatch 的 `airflow-{环境名}-Task` 里，它和 MWAA 环境是两套独立的存储，删环境不删日志。所以这次事故里，旧环境的任务输出还在 `airflow-etl-sit-251-*` 下面，可以用 Logs Insights 捞。

但日志组名是从环境名派生的，新环境写新组，旧组不会被链接进新 UI。官方文档对此有一句加粗的 Important：改名意味着历史任务日志在新环境的 Airflow UI 里访问不到。

黑色幽默在于：**如果当初不把版本号焊进环境名，日志组和元数据库两样都不会丢。** 那个为了「一眼看出跑的是哪个版本」而设计的命名规范，同时炸掉了两样东西。查了一下这个环境的日志组，`243`、`251`、`306`、一次 `rollback`、一次临时变更标记，像地层一样排着——过去几年里，这一幕演过不止一次，只是之前没人回头找过那些历史，所以从来没人把它当事故报出来。

一个流程不报警，不代表它没有代价。有时只是还没人需要被丢掉的那部分状态。

---

## 综合：三种失败模式，各自谁兜底

把整件事收成一张表。列的是「AWS 替你做了什么」和「剩下的必须你自己做」——这条分界线，就是你要写多少代码的答案：

| 失败模式 | AWS 托管的部分 | 留给你的部分 |
|---|---|---|
| **原地版本升级**（名字不变） | 升级前自动快照元数据库、升级组件、`db migrate`、失败自动回滚（最长约 2 小时不可用） | 用 local runner 验 DAG 与 `requirements.txt` 兼容性；手工改过的 DAG 不会被回滚 |
| **环境替换**（名字变了 / 蓝绿 / 跨区） | 无 | 全部：旧环境还活着时导出、新环境导入、日志组处置、恢复后验证 |
| **区域级灾难 / 误删 / 数据损坏** | 多 AZ 容错（单 AZ 故障自动恢复） | 周期性备份 + 跨区复制 + SchedulerHeartbeat 告警 + 定期演练 |

第一行是唯一有安全网的一行，而它的唯一条件是：**别碰 `Name`**。

---

## 立刻可以做的事

1. **`grep -rn "is_paused = true" dags/`**。如果你的「备份」脚本里有这行，它是迁移工具。现在就把它从任何定时调度上摘下来。
2. **`aws s3 ls` 你的备份桶，随便下一个 `connection.csv` 看一眼**。如果里面是明文密码，今天就换 KMS CMK + 收紧桶策略，并把「Variables/Connections 迁到 Secrets Manager」排进 backlog。
3. **`curl` 一遍你 runbook 里引用的每个 GitHub 路径和包版本**。文档搬家了不会通知你。顺手确认你的目标 Airflow 版本在 `mwaa-dr` 的支持矩阵里——如果不在，这就是升级工作量的一部分，不是升级之后再说的事。
4. **把 §6.4 那条 `jq` 加进 CI**，对准你所有有状态资源：MWAA、RDS、ElastiCache、MSK。让「替换」这件事必须被一个人看见一次。
5. **在 local runner 上跑一次完整的 backup → cleanup → restore**，然后对四件事：Variables 条数、Connections 连通性、`dag_run` 行数、unpause 状态。没演练过的恢复方案，和没有恢复方案的区别，只在于你事故那天的心理预期。

我自己接下来要验的第一件事，是 §4.2 那个 `active_dags.csv` 少一行的推论——读代码能推出来，但我还没在真实环境里数过那两个数字。

---

*云厂商替你托管了「它还活着」，从没答应替你托管「它还记得」。而这两件事的分界线，永远不在控制台上，在你有没有把它写成一个会跑的 DAG。*
