---
title: 同一行报错，五种命运：一次 MWAA 插件加载的解剖
header:
    image: /assets/images/how_to_save_expect_script_run_output_to_file_locally.jpg
date: 2026-10-07
tags:
 - airflow
 - mwaa
 - aws
 - python
 - devops
permalink: /blogs/tech/zh/mwaa-one-error-five-fates
layout: single
category: tech
---

> 横看成岭侧成峰，远近高低各不同。——苏轼《题西林壁》

# 你那行 `ModuleNotFoundError`，在五个组件里有五种死法

*从"读报错文本"到"看报错落点"——区分资深与新手的那一步*

组里刚接手新 MWAA 环境的同事，截了一屏红给我：Airflow 的 Web UI 上，**103 行** `Failed to import plugin ... ModuleNotFoundError: No module named 'teradatasql'` / `googleapiclient` / `airflow.providers.sftp`，密密麻麻。他盯着我们前一天刚合进去的那个 `plugins/.airflowignore`，问了一句很合理的话：

> "是不是我们这个改动，把插件加载搞坏了？"

我让他先别动代码，去触发几个 `Test_*` 冒烟 DAG 看看。结果更吓人——**四条全红**：`Test_snowflake` 红在 `JWT token is invalid`，`Test_Excel_Ecs` 红在 `TaskDefinition not found`，`CIM__QFF` 的 `OPEN_BUSINESS_DATE` 红在一个容器 `exitCode 1`。他基本已经准备回滚了。

我拦住他。这四条红，加上那 103 行红，**没有一条是插件问题**，更没有一条是那个 `.airflowignore` 造成的。但要讲清楚"为什么不是"，得先拆开一个所有人都以为自己懂、其实没几个人真懂的东西：**在 MWAA 里，`plugins/` 这一份代码，被五个组件用五种完全不同的方式"读"。同一行 `ModuleNotFoundError`，在 WebServer 是化妆品，在 Worker 是心脏病，在 Fargate 容器里根本不是它的事。**

如果你也维护过 MWAA、或者任何"一份代码、多个进程各跑一遍"的系统，这篇就是为你写的。读完你会拿到三个直觉：

- **判断一个报错致不致命，第一步永远是问"哪个组件、哪一层打的"，而不是读报错文本。**
- **`.airflowignore` 治的是 WebServer 的"扫描"，不是执行的"import"——这两条加载路径根本不是同一条。**
- **一个"只靠错误消失来证明"的改动，证据必须锚在进程重启上，否则你量的是空气。**

下面按"最有用优先"排，不按我当时排查的时间顺序。

---

## 一、第一屏红：103 行 broken plugin，但没有一个 DAG 坏

先看那行红字的原文——注意路径和它真正缺的东西：

```text
[plugins_manager.py:305] ERROR - Failed to import plugin
  /usr/local/airflow/plugins/plugins/hooks/gdrive_hook.py
ModuleNotFoundError: No module named 'googleapiclient'
...hooks/teradata_ctlfw_hook.py   → No module named 'teradatasql'
...hooks/sftp_hook.py             → No module named 'airflow.providers.sftp'
```

打这行的是 `plugins_manager.py` ——Airflow 的**插件管理器**。它在进程启动时会去**遍历整个 `plugins/` 目录，把每个 `.py` 都 import 一遍**，目的是找出里面继承了 `AirflowPlugin` 的类，好把它们注册成 UI 视图、菜单、timetable、listener 之类。

问题是：我们 `plugins/` 下面根本没有一个真正的 `AirflowPlugin`。那里面全是自定义的 hook / operator / sensor，DAG 用 `from plugins.hooks.xxx import ...` 直接引。它们**不是 Airflow 插件**，只是**放在插件目录里的普通 Python 模块**。插件管理器不知道这件事，照样挨个 eager import，于是一 import 就撞上 `teradatasql`、`googleapiclient` 这些第三方重依赖——而这些依赖**在 WebServer 上根本没装**。

**为什么只有 WebServer 缺依赖？** 这才是整件事的根——一个漂亮的**对称性破缺**。MWAA 的 WebServer 在 `PUBLIC_ONLY` 模式下跑在 **AWS 托管的 VPC** 里，**没有出网**。`requirements.txt` 在 WebServer 上安装时，第一个包就 `No matching distribution found` 全批中止。而 Scheduler / Worker 跑在**你自己的 VPC**里、能出网，依赖装得好好的。

> 同一份 `requirements.txt`、同一份 `plugins/`，因为**跑它的进程所在的网络环境不对称**，在 WebServer 上塌、在 Worker 上好。这就是"同一行报错五种命运"的物理根源。

修复不是去给 WebServer 补依赖（你补不了，它没网），而是**告诉插件管理器：这些目录压根别扫**。一个 `plugins/.airflowignore` 就够：

```text
# 这些是 DAG 直接 import 的自定义 hook/operator，不是 Airflow 插件，
# 别让插件管理器 eager import 它们的第三方依赖，省得 WebServer 刷满 Broken plugin。
hooks
operators
sensors
transfers
models
utils
exceptions.py
```

| | 普通人的看法 | 资深工程师的洞察 |
|---|---|---|
| 看到 103 行红 | "插件系统坏了，依赖没装齐，赶紧补依赖/回滚" | "WebServer 在无网 VPC 里，依赖本就装不上；这是扫描噪音，不是功能故障" |
| `.airflowignore` 的作用 | "忽略一些文件" | "把不该被当插件的模块移出插件管理器的 eager 扫描范围" |
| 影响面 | "动了插件加载，怕影响 DAG" | "只动 WebServer 的扫描，碰不到执行路径" |

**一句话：那 103 行是 WebServer 在无网环境里做了一件它不该做的事（扫描非插件模块），不是你的代码坏了。**

---

## 二、为什么 `.airflowignore` 能"只关 WebServer 的嘴"，却不动执行

新同事最怕的是："你让插件管理器别加载 `operators/`，那 DAG 里 `from plugins.operators.xxx import` 不就也 import 不到了？"

不会。因为**插件的加载有两条完全独立的路径**，`.airflowignore` 只掐断其中一条：

| | 路径 A：插件管理器扫描 | 路径 B：`sys.path` import |
|---|---|---|
| 谁触发 | 进程启动时 `plugins_manager` 主动遍历 `plugins/` | DAG/任务代码里的 `from plugins.x import Y` |
| 目的 | 找 `AirflowPlugin` 子类去注册 UI/宏/timetable | 真正拿到那个 hook/operator 类来用 |
| 走不走 `.airflowignore` | **走**——被 ignore 的目录不扫 | **完全不走**——`plugins/` 在 `sys.path` 上，import 该成还成 |
| 失败后果 | WebServer UI 刷 Broken plugin（化妆品） | DAG 解析失败 / 任务 import 报错（心脏病） |

`.airflowignore` 只影响**路径 A**。路径 B 是标准的 Python import 机制：MWAA 把 `plugins/` 挂在 `sys.path` 上，任何进程里 `from plugins.operators.xxx import Foo` 照常工作，跟插件管理器扫不扫它一点关系没有。

证据？我们改动上线后，去查 dev 环境 **DAGProcessing（DAG 解析器）** 的日志，专门 grep import/parse 错误：

```text
filter-pattern: ?"ModuleNotFoundError" ?"ImportError" ?"Broken DAG"
结果: 0
```

而这个环境里 **263 个 DAG，有 262 个都 `import` 了 `plugins.utils` 和 `plugins.operators`**。如果 `.airflowignore` 真的掐断了执行侧的 import，这里会是一片 `ModuleNotFoundError: No module named 'plugins....'` 的血海。是 0，就证明路径 B 毫发无损。

> `.airflowignore` 是一把只对"路径 A"生效的剪刀。你剪的是 WebServer 的 eager 扫描，不是 DAG 的 import——这两件事共用一个目录，但走的是两套机制。

这里顺带埋一个**代码考古学**的雷：那个 `.airflowignore` 的注释里我特意写了一句"**如果以后真加了一个 Airflow 插件（UI view/timetable/listener），必须把它从这些 pattern 里排除，否则会被静默忽略**"。因为三个月后没人记得这个文件为什么在这，而它恰恰会让一个**真插件**神不知鬼不觉地不生效。把"为什么"写进文件，是把部落知识变成工程产物的最低成本动作。

---

## 三、怎么证明"红没了"：把时间锚在 gunicorn 重启上

`.airflowignore` 这种改动最难的地方在于：**它没有任何正向输出**。你没法截一张"成功"的图——它的成功，就是那 103 行红**消失**。而"证明某个东西不存在了"，是验证里最容易糊弄自己的一类。

我带着新同事踩了三个坑，每踩一个，结论的可信度就上一个台阶：

**坑 1：部署到 S3 ≠ 环境生效了。** MWAA 是**精确 pin** `PluginsS3ObjectVersion` 的，不是"自动拉 S3 最新"。改动 push 到 S3 只是第一步，必须 terraform 把版本号 bump 上去、`UpdateEnvironment` 跑完，`get-environment` 看到**新版本号 + Status=AVAILABLE + LastUpdate=SUCCESS**，才算真的在跑新代码。`LastUpdate.CreatedAt` 就是你 before/after 的那条线。

**坑 2：插件 import 错误一辈子只打一次——在 WebServer（gunicorn）启动那一刻。** WebServer 日志组里 99% 是 ELB 的 `/health` 访问日志，`plugins_manager.py:305` 那种红只在 gunicorn 重新扫描 `plugins/` 时出现。我第一次取了个"最近 12 小时"的固定窗口，**0 命中**——不是因为没错误，是因为那 12 小时里 WebServer 根本没重启。**必须先把时间锚在 gunicorn 重启上**：

```bash
# 先找重启时刻
aws logs filter-log-events --log-group-name airflow-edr-dev-2112-WebServer \
  --filter-pattern '"Starting gunicorn"' --query 'events[*].timestamp'
```

**坑 3：AFTER 的"0"，只有配上一次"真的重启过"才算数。** 否则 0 是假阴性——WebServer 没重扫，当然没新错误。所以 AFTER 窗口里既要数错误（期望 0），又要证明 gunicorn 在更新后真的 `Booting worker` 了。

对齐这三点后，before/after 一拉，铁证：

| 窗口 | 时刻 (UTC) | plugins.zip | broken-plugin import 错误 |
|---|---|---|---|
| **BEFORE** | 旧 WebServer 启动那刻 | 旧版，无 `.airflowignore` | **103** |
| 环境更新 | 2026-10-06 22:13 | → 新版（含 `.airflowignore`） | — |
| **AFTER** | 22:19 WebServer 重启 | 新版 | **0** |

> 直觉口诀：**先定位 gunicorn 重启点，再在重启点数错误；一个 0 只有配上一次真重启才算证据；MWAA 跑的永远是 pin 住的版本，不是 S3 的 latest。**

---

## 四、四条 `Test_*` 全红，零个是插件：组件边界之外的世界

回到新同事最慌的那四条冒烟红。它们恰恰是这篇 spine 的最佳标本——**全部跑到了插件边界之外，死在了各自不同的组件、不同的身份、不同的日志里**。

先立一条判据：**对一个 ECS 支撑的任务，"插件 OK"的标准不是任务变绿，而是日志里自定义 operator 成功 `import` 并进了 `execute()`。** 只要进了 `execute()`，插件侧就清白了——后面死在哪，是别的组件的事。

| 冒烟任务 | 真正死在哪 | 缺的是什么 | 身份/日志落点 |
|---|---|---|---|
| `Test_snowflake` | `250001 (08001) JWT token is invalid`——连上了 host，认证被拒 | Snowflake 用户的 key-pair 公钥没注册/被轮换 | Airflow Task 日志（Snowflake 服务端拒绝） |
| `Test_Excel_Ecs` | `botocore ClientException: RunTask ... TaskDefinition not found` | ECS task definition 没在新账户注册 | Airflow Task 日志（AWS API 拒绝） |
| `CIM__QFF / OPEN_BUSINESS_DATE` | 容器**起来了**，`exitCode 1` | ECS **task role** 缺 `secretsmanager:GetSecretValue` | **容器自己的 CloudWatch 日志**，不在 Airflow 里 |

第三条最有教学价值。Airflow Task 日志里你只看到一句干巴巴的 `This task is not in success state ... exitCode 1`——**真因根本不在 Airflow**。它在 Fargate 容器自己的日志组 `dev/edr/ecs/edr-dev-teradata-utilities` 里：

```text
botocore.exceptions.ClientError: AccessDeniedException when calling GetSecretValue
User: arn:aws:sts::...:assumed-role/edr-dev-teradata-utilities/...
is not authorized to perform: secretsmanager:GetSecretValue
on resource: /edr/airflow/connections/teradata__ARM
```

这里藏着两个最容易混淆的身份概念：

- **这是 ECS 的 _task role_，不是 _execution role_。** execution role 是给 ECS agent 用的（拉镜像、建日志组）；task role 是**容器里的代码**用的身份（读 Secrets Manager、访问 S3）。报 `GetSecretValue` denied 的是 task role。
- **Airflow 的 execution role 和这个 ECS task role 是两套人马。** 任务是 MWAA Worker 用 MWAA 的角色去 `RunTask` 拉起来的，但容器一旦跑起来，它就用**自己**的 task role 去取密钥。两个边界，两个身份。

把四条放一起，结论一句话收口：**它们全是 `edr-dev-2112` 这个新环境的外部接线没补齐（Snowflake 公钥、ECS task def、task role 权限），零个是 DAG/插件的问题。而且它们反过来证明了 `.airflowignore` 没坏任何东西——每个 operator 都正常 import、执行到了外部调用那一刻才被外部系统拒。**

---

## 五、三张地图：组件、身份、日志

把前四章的线收束到一个抽象下——在 MWAA（以及任何"一份代码多进程 + 下游容器"的系统）里排障，你脑子里要同时开三张地图：

| 地图 | 问的问题 | 这次的答案 |
|---|---|---|
| **组件地图** | 这段代码是谁在跑？谁在"读" `plugins/`？ | WebServer 扫描（无网，塌）/ Scheduler·Worker import（有网，好）/ Fargate 容器（另一个运行时） |
| **身份地图** | 这一步用谁的权限？ | MWAA execution role / ECS task role / ECS execution role / Snowflake JWT——四套身份 |
| **日志地图** | 真相被写在哪个日志组？ | WebServer=gunicorn 启动那刻 / DAGProcessing=解析 / Airflow Task=结果 / 容器 CloudWatch=真因 |

新同事的错误不是技术不够，是**只开了"报错文本"这一张地图**：看到 `ModuleNotFoundError` 就以为是依赖问题，看到任务红就以为是改动问题。而这三张地图一旦同时打开，103 行红立刻归类为"WebServer 化妆品"，四条冒烟红立刻归类为"新环境接线缺口"，`.airflowignore` 的清白三十秒内就能证明。

### 立刻可以做的事

1. 翻一下你自己的 `plugins/` 目录：里面有几个是**真** `AirflowPlugin` 子类，几个只是被 DAG 直接 import 的普通模块？如果是后者占多数，而你的 WebServer 又是 `PUBLIC_ONLY`，大概率你 UI 上那堆 Broken plugin 就是这个病——一个 `.airflowignore` 能治。
2. 给你每一个 ECS 支撑的 operator 配一条排障书签：**先去容器自己的 CloudWatch 日志组看 `exitCode`，别在 Airflow Task 日志里猜。**
3. 分清你环境里的 **task role vs execution role**，把"容器取密钥失败"这类问题直接定位到 task role 的 policy，而不是去翻 Airflow 连接。
4. 下次做"只靠错误消失来证明"的改动，先写下你的 before/after 锚点（哪个进程、哪次重启、哪个日志组），再动手——没有锚点的"0"等于没验证。

### 预告

这套 `edr-dev-2112` 的经验，下一步要原样搬去 **stg/prd 的 2.11 切换**。那边还埋着更脏的一类雷：新环境的 metadata DB 是全空的，FAB 角色、Airflow Variable、任务历史全没了——根因我在[《改名即摧毁：MWAA 的 name 就是身份》](/blogs/tech/zh/mwaa-name-is-identity)里挖过，"切换前必须对着旧环境跑的那几件事"写在[《备份不是迁移》](/blogs/tech/zh/mwaa-metadata-backup-not-migration)里。下一篇就是把这三篇的账，在 stg/prd 真刀真枪切一遍的复盘。

---

*报错文本告诉你"哪里疼"，报错落点才告诉你"病在哪"。资深和新手的差别，常常只隔着一个问题：这行红，到底是哪个组件打的？*
