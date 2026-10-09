---
title: 你以为只是改了个名字，AWS 却把整栋楼推倒重建了
header:
    image: /assets/images/hd_aws_certificat.png
date: 2026-09-28
tags:
 - aws
 - airflow
 - terraform
 - devops
 - cloud-infrastructure
permalink: /blogs/tech/zh/aws-mwaa-rename-not-update
layout: single
category: tech
lang: zh
---

> "白马者，马与白也。马与白，马也？故曰：白马非马。" —— 公孙龙

---

# 你以为只是改了个名字，AWS 却把整栋楼推倒重建了

*一次两行的 Terraform diff，怎么把一个跑了三年的 Airflow 环境连根拔起*

---

上周我们把一套托管 Airflow（AWS MWAA）从 2.10.3 升级到 2.11.2。Dev 环境先跑了一遍，一切正常，DAG 一个没炸。轮到 SIT 环境的时候，我提的那个 Terraform PR 只改了两行：

```diff
-airflow_version: "2.10.3"
+airflow_version: "2.11.2"
-name: ${channel}-${env}-251
+name: ${channel}-${env}-2112
```

`251` 是 2.5.1 的缩写，`2112` 是 2.11.2 的缩写——这是我们这套仓库沿用多年的命名习惯，环境名里带着版本号，一眼就知道现在跑的是哪个 Airflow 版本。看起来无害到不能再无害。

Apply 之后，控制台显示 `Status: AVAILABLE`，`LastUpdate: SUCCESS`。我按流程去查了 CloudWatch，requirements 安装日志干干净净，scheduler 也在正常吐日志。我合上电脑，觉得这事儿完了。

十分钟后，DAG 列表里开始刷屏——`Broken DAG` 一个接一个冒出来。一批是权限报错，另一批是变量报错，查日志之后才确认第二批精确数字是 **195 个**：

```
airflow.exceptions.AirflowException: The access_control mapping for DAG 'X'
includes a role named 'finance-developers', but that role does not exist
```

```
File "db_context_hook.py", line 32, in get_database_name
    mapper = context_database_map[self.environment][self.database_context]
             ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
KeyError: ''
```

一个是 FAB 权限角色凭空消失了，一个是 Airflow Variable 变成了空字符串。两种报错，指向同一件事：**这个环境的元数据库，是全新的、空的。**

我正对着这堆报错发懵，团队里的 Dean 在群里补了一刀：

> "界面上一条历史记录都没有，这肯定是个新数据库。"

那一刻我才意识到，我以为自己只是升级了一个 Airflow 版本，AWS 却听成了：把这栋楼炸了，在原地盖一栋新的。

这篇想讲清楚的就是这件事。搞懂之后，你不仅能避免我们这次的坑，还会对"云资源的身份到底是什么"这件事，建立一个会跟着你走的直觉——这个直觉用在 MWAA 上，也一样能用在 RDS、EKS、任何一个你没细看过 Update API 长什么样的云资源上。

**30 秒读完你能带走的三句话：**

- "改名字"在大多数系统里是免费的元数据操作，在云资源的世界里，名字往往就是身份本身——一旦这个等价关系不成立，损失是不可逆的。
- 一个资源的 Update 接口如果压根没有某个字段，那这个字段就不是"能改但有风险"，而是从设计上就不可变——这个区别，决定了你该怎么读文档、怎么做 code review。
- Terraform 的 diff 只会告诉你"这一行变了"，不会告诉你"这一行的变化，跨过了一条只有云厂商自己知道的身份边界"。

这篇是按"先讲清楚发生了什么，再往上抽到原理，最后给清单"的顺序写的，不是按我当时排查的顺序——真实排查会绕很多弯路，你不需要跟我一起绕。

---

### 第一章：破案——两次调用，不是一次更新

`Status: AVAILABLE` 骗不了人也不会骗人，它说的是真话：现在这个环境确实健康。问题是，"现在这个环境"和"我以为在升级的那个环境"，根本不是同一个个体。

要证实这一点，光靠猜不行，得去 CloudTrail 里把两个 API 调用的时间戳摆出来：

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=DeleteEnvironment \
  --query 'Events[*].[EventTime,Resources[0].ResourceName]' --output text

aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=CreateEnvironment \
  --query 'Events[*].[EventTime,Resources[0].ResourceName]' --output text
```

结果摆在那儿，没有任何含糊空间：

```
10:58:46  DeleteEnvironment  etl-sit-251
11:26:12  CreateEnvironment  etl-sit-2112
```

两条记录，两个不同的 API 名字，中间隔了 28 分钟。这不是一次"更新"打了两条日志——`UpdateEnvironment` 这个动作，在 CloudTrail 里压根不会留下这种痕迹。这就是先删、再建，一次完完整整的拆除与重建。

> **普通人的看法**：控制台绿灯亮了，日志也没报错，升级肯定成功了。
> **资深工程师的洞察**：健康检查回答的是"它现在活着吗"，从来不回答"它是不是我以为的那个它"。这是两个完全不同的问题，前者查不出后者的答案。

---

### 第二章：刨根——身份字段和配置字段，从来不对称

案子破了，但更值得深挖的问题是：**为什么改一个字符串会导致销毁重建？** 这才是能让你以后少踩坑的那一层。

答案不在 Terraform 文档里，在 AWS 自己的 MWAA API 参考手册里。我去翻了 `UpdateEnvironment` 这个接口的请求体，结果发现了一件很反直觉的事：

```
PATCH /environments/{Name} HTTP/1.1
{
   "AirflowConfigurationOptions": {...},
   "AirflowVersion": "...",
   "DagS3Path": "...",
   "EnvironmentClass": "...",
   "ExecutionRoleArn": "...",
   "MaxWorkers": ...,
   "NetworkConfiguration": {...},
   "WorkerReplacementStrategy": "...",
   ... (还有十几个字段)
}
```

`Name` 只出现在 URL 路径里，用来指定"我要更新哪一个已存在的环境"——**它从来没有出现在请求体里**。也就是说，"改名字"根本不是一个"支持但有风险"的降级操作，它是一个从 API 设计层面就不存在的操作。你无法对 AWS 说"把这个环境改个名字"，你只能说"建一个新的，删一个旧的"——而这正是 CloudTrail 里看到的那两条记录的由来。

这里有一个值得单独拎出来说的心智模型：**对称性破缺**。

Terraform 的资源定义把 `name`、`airflow_version`、`max_workers` 摆在同一个缩进层级里，看起来是一组对等的、可以互相替换修改的配置项。这是一个干净但会骗人的抽象——它把"配置属性"和"身份属性"画成了同一种东西。真实世界里，这些字段并不对称：改 `max_workers` 是配置层面的调整，改 `name` 是在动这个资源的身份证号。抽象在哪个点上突然从"平滑"变成"有坑"，就是对称性破缺发生的地方，而它永远藏在文档最不起眼的那一行里，不会写在 README 的显眼位置。

> **第一性原则**：判断一个字段能不能改，永远别问"这个字段听起来像配置还是像身份"，去读 Update 接口的请求体，它有没有这个字段，才是唯一的事实来源。

**面试拿分点**：如果面试官问你"如何判断一个云资源属性是否可以原地更新"，"看文档写没写 immutable"是及格答案；"去查对应 Update API 的请求体字段列表，看这个属性在不在里面"，才是能让人记住你的答案——因为它把"猜"变成了"查证"。

---

### 第三章：代码考古——这件事，其实已经发生过好几次

Dean 那句"界面上没有历史记录"点醒我去查了 CloudWatch 日志组，结果发现了比这次事故本身更让人后背发凉的东西：

```
airflow-etl-sit-243-*
airflow-etl-sit-251-*
airflow-etl-sit-306-*
airflow-etl-sit-DATA-9395-*
airflow-etl-sit-rollback-*
airflow-etl-sit-2112-*
```

六组日志组，创建时间最早的一个可以追溯到三年前。每一个后缀，都是当年某一次"升级"留下的化石——`243`、`251`、`306`……这套把版本号编进环境名字的命名习惯，三年里已经在无声无息地上演过至少五次同样的拆除重建，每一次都悄悄清空了当时的 Postgres 元数据库，只是从来没人在那之后急着要找回历史数据，所以从来没人发现这其实是一场事故，而不是"升级"。

这就是**代码考古学**最让人不舒服的地方：它不只发生在一段没人敢删的老代码里，也发生在一条重复执行了很多年的运维流程里。没人写下"这个命名规则会导致数据丢失"，因为写下这条规则的人，可能压根不知道自己在设计一个定时炸弹——他只是想让环境名字看起来清楚一点。

| | 表面看起来的样子 | 实际发生的事 |
|---|---|---|
| PR 的 diff | 改了两个字符串字段 | 触发了一次完整的资源销毁重建 |
| 控制台状态 | `AVAILABLE` / `SUCCESS` | 一个全新的、空的元数据库 |
| 命名规则的本意 | 让人一眼看出当前版本 | 把版本号焊死进了资源的身份证里 |
| 过去三年发生的次数 | 0（从没人报告过事故） | 至少 5 次（日志组就是证据） |

---

### 第四章：正确姿势——AWS 其实给过一条不流血的路

最讽刺的是，AWS 官方明确支持"原地升级"，而且这条路径会自动帮你把元数据库快照下来、升级后再还原回去——变量、连接、DAG 运行历史、暂停状态，全部原样保留，一行手动操作都不需要。前提只有一个：**别碰 `Name`，只改 `AirflowVersion`**。

如果因为某些原因确实需要换一个新的环境名字，AWS 也写好了正规流程，而不是让你自己摸索：先在**旧环境**（它还活着的时候）跑一个 `db_export` DAG，把 `variable`、`dag_run` 历史、`xcom` 等表导出到 S3；再在新环境里跑 `db_import` DAG 导回来。整个过程的关键约束就一条：**导出必须在旧环境被删除之前完成，这条路一旦环境没了就永久关闭，没有任何补救办法。**

| 场景 | 该怎么做 | 结果 |
|---|---|---|
| 只是升级 Airflow 版本 | 只改 `AirflowVersion`，`Name` 保持不变 | AWS 自动快照+还原，什么都不丢 |
| 一定要换新的环境名字 | 先在旧环境跑 `db_export`，新环境跑 `db_import` | 数据搬过去了，但两边 DAG 在迁移期间都会被自动暂停 |
| 像我们这次一样，先斩后奏 | ——（已经来不及了） | 元数据永久丢失，只能靠 CloudWatch 日志翻回一部分任务输出 |

值得说清楚的是最后一行：CloudWatch 里的任务日志和调度日志，是独立于 MWAA 环境本身存在的，环境删了，这些日志组不会被自动清理，也不会自动关联到新环境的 UI 上——所以我们至少还能从 `airflow-etl-sit-251-*` 里把具体某次任务跑出来的原始输出捞回来，只是再也拿不回 UI 上那种带图形的运行历史时间线了。这不是运气好，是 CloudWatch Logs 和 MWAA 的元数据库本来就是两套完全不相关的存储，一套侥幸活了下来，另一套没有。

---

### 收尾：两个问题，一个答案

把这次事故压缩成两个你以后每次做类似变更前都该问自己的问题：

1. **这是更新，还是替换？** 别靠直觉猜，去翻对应 Update API 的请求体字段列表，你要改的那个字段在不在里面。
2. **如果注定是替换，数据准备好搬家了吗？** 官方的 export/import 流程必须在旧资源还活着的时候跑，过期不候。

**立刻可以做的事：**

1. 打开你自己项目里管云资源的 Terraform/CloudFormation 定义，把每一个会触发 force-replace 的字段过一遍，标出来——不要等 diff 出现的那一刻才知道。
2. 下次要写一个"版本升级"类的 PR，先去读对应云服务 Update API 的请求体字段列表，亲自确认你要改的字段真的在里面。
3. 如果你的资源命名规则里也藏着版本号，去查一下：这个规则用了多久，每次"升级"背后是不是也悄悄销毁过什么，只是从来没人回头看过。
4. 给团队里所有带状态的关键资源，建一个"改动前先导出"的强制清单，而不是指望大家都记得——部落知识迟早会传丢一代人。

---

*云厂商从不撒谎，它只是从不主动告诉你，哪些字段其实是名字，哪些名字其实是身份——那条线，只有撞上去的时候才会显形。*
