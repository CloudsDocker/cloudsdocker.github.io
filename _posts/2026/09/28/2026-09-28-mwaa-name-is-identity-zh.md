---
title: '`DeleteEnvironment` 比 `UpdateEnvironment` 更诚实'
header:
    image: /assets/images/bg_raw/BingWallpaper (6).jpg
date: 2026-09-28
tags:
 - aws
 - terraform
 - airflow
 - cloud-infrastructure
 - devops
permalink: /blogs/tech/zh/mwaa-name-is-identity
lang: zh
layout: single
category: tech
---
> “程序必须写得让人读懂，偶尔才需要让机器执行。” — Donald Knuth

# `DeleteEnvironment` 比 `UpdateEnvironment` 更诚实

*托管 Airflow 升级时，环境名为什么不能顺手改掉。*

你的 Terraform 计划里，有没有一个资源把“改名”显示成替换，而你只盯着了版本号？

先运行这一条：

```bash
terraform plan -out=tfplan && terraform show -json tfplan | \
  jq -r '.resource_changes[] | select(.change.actions == ["delete", "create"] or .change.actions == ["create", "delete"]) | .address'
```

它列出的不是“有改动的资源”，而是可能先消失、再出现的资源。看完这篇，你应该能分清：一次托管 Airflow 的升级，究竟是原地更新，还是借升级之名换了一栋新楼；也能在 apply 前查证，而不是在空白的 Web UI 里猜。

一次升级中，版本字段和环境名一起改了。后者只是把版本编码进名称，乍看是无害的可读性改进：

```diff
-airflow_version = "旧版本"
+airflow_version = "新版本"
-name            = "工作负载-环境-旧版本缩写"
+name            = "工作负载-环境-新版本缩写"
```

部署后，控制台显示 `AVAILABLE`，最近一次更新显示成功；依赖安装日志和调度器日志也没有异常。随后，DAG 列表却陆续出现 `Broken DAG`：一类是 DAG 的访问控制引用了不存在的角色；另一处应用代码则报出了下面这个错误：

```text
airflow.exceptions.AirflowException: The access_control mapping for DAG 'X'
includes a role named 'some-role', but that role does not exist
```

```text
KeyError: ''
```

后一个 `KeyError` 本身只能说明某次字典访问使用了空字符串键，不能单凭它断定 Airflow Variable 缺失或元数据库为空。结合角色丢失及对环境状态的检查，才确认原有角色和变量所在的元数据库状态没有保留下来。

**健康检查只能证明它活着，不能证明它还是你以为的那个它。**

## CloudTrail 里有两次调用，不是一次更新

不要从绿灯推断资源身份。去审计日志里找动词：

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=DeleteEnvironment \
  --query 'Events[*].[EventTime,EventName,Resources[0].ResourceName]' \
  --output text

aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=CreateEnvironment \
  --query 'Events[*].[EventTime,EventName,Resources[0].ResourceName]' \
  --output text
```

这次记录显示的是先 `DeleteEnvironment`，后 `CreateEnvironment`，而不是 `UpdateEnvironment`。控制台没有撒谎：新环境确实可用。错的是把“可用”理解成了“原来的环境已升级”。

| 你看到的信号 | 它真正回答的问题 | 它没有回答的问题 |
|---|---|---|
| `AVAILABLE` | 当前环境是否健康 | 是否保留了原环境的身份和状态 |
| `LastUpdate: SUCCESS` | 当前操作是否完成 | 操作是更新还是替换 |
| Terraform 字段 diff | 哪些声明值变了 | 变更是否跨过资源身份边界 |

## 名字不在 Update 请求体里，就不是可修改配置

这件事的关键不在 Terraform 的缩进，而在服务 API 的形状。

MWAA 的更新接口以环境名定位目标：`/environments/{Name}`。可更新的请求内容包括 Airflow 版本、配置选项、DAG 路径、环境规格、执行角色、网络配置、工作节点相关设置等；`Name` 用来说明“更新谁”，而不是作为“把名字改成什么”的可写字段。

所以改名不是“支持、但风险很高”的更新。对于这个 API，改名这个动作根本不存在。要得到新名字，只能创建一个新环境，并处置旧环境。

Terraform 将 `name`、`airflow_version`、`max_workers` 排在同一个资源块里，是很方便的声明方式，也很容易让人误会它们是同一类属性。它们不是：前两者里，版本通常是配置；名称是服务识别资源的键。字段在界面上并列，生命周期却完全不对称。

> 📌 **截图版判断法**：字段不在 Update API 的请求体里，就把它当作身份字段；先检查替换计划，再讨论升级。

我倾向于把“去文档里找 immutable 标记”排在第二位。更可靠的做法是直接读对应 Update API 的请求字段：字段在不在，通常比一句宽泛的说明更能回答“能否原地改”。反过来，这也不是对所有云服务都足够的结论：有些服务的 API 能接收字段，却会异步替换底层实例。因此 API、Terraform plan 和服务迁移文档应当一起看。

## 旧日志组只能提示历史，不能替你证明替换

进一步查看日志组时，会看到多个历史环境名留下的组：旧版本缩写、一次回滚标记、一次临时变更标记，以及这次的新名称。它们像地层一样排开。

这些名称说明命名规则曾经变化，也提醒人们去追问每次变更的资源生命周期；但仅凭历史日志组，不能证明此前每次改名都触发了替换。要作出这个判断，需要把每次变更对应的 Terraform plan 与审计事件关联起来。

这类问题不只藏在不敢删除的遗留代码里，也藏在重复成功的运维流程里。一个流程没有报警，不代表它没有代价；有时只是还没人需要被丢掉的状态。

## 真要升级，先选对路径

如果目的只是升级 Airflow，保留环境名，只变更 Airflow 版本，并在 apply 前确认计划没有替换该环境。托管服务的原地升级路径会处理其支持范围内的元数据迁移；实际可保留的内容及版本兼容边界，应以目标版本的 MWAA 文档和升级前检查为准。

如果业务确实要求新环境名，那就把它当迁移，不要叫升级。旧环境还活着时，按当前服务文档提供的元数据导出流程导出；新环境准备好后再导入，并验证 Variables、Connections、DAG 运行记录及权限配置等所需状态。不同 Airflow 与 MWAA 版本支持的导出对象和迁移工具可能不同，不能把某个环境的脚本名当成通用命令。

旧环境删除之后，导出窗口就关闭了。独立存在的日志组或许还能保留任务输出，帮助人工追溯发生过什么；但日志不是元数据库，也无法自动恢复 Web UI 中的运行历史、变量或权限状态。

## 把“替换”当成有状态资源的迁居

这里值得保留的不是某个服务的踩坑清单，而是一条更通用的判断：资源替换不是配置变化的副作用，它是一场迁居。迁居之前要先问，哪些状态跟着资源走，哪些状态留在外部，哪些状态根本没有副本。

这个原则的边界也很清楚：无状态、可完全从声明重建的资源，替换未必值得大惊小怪。但只要资源承载数据库、密钥引用、运行历史、队列内容或人工配置，替换就必须进入变更设计，而不能只出现在 plan 的一行文字里。

**明天就能用的提问：我改的字段，是服务配置，还是服务用来认出“这一个”的身份证？**

下次看到带版本号的资源名，别急着夸它清楚。先跑一次 plan：你的“版本升级”，会不会其实在搬家？
