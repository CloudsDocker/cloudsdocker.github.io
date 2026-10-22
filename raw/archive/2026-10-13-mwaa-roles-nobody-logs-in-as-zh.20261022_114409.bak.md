---
title: 没有人会以它登录的角色：MWAA 权限的三道门
header:
    image: /assets/images/hd_kerberos.png
date: 2026-10-13
tags:
 - airflow
 - mwaa
 - aws
 - security
 - devops
permalink: /blogs/tech/zh/mwaa-roles-nobody-logs-in-as
layout: single
category: tech
---

> 名者，实之宾也。——《庄子·逍遥游》

# 九个没有人会登录的角色，一个都不能少

*从"权限就是给人开门"到"有些权限是给代码对账"——看懂 MWAA 的三道门*

上周巡检 SIT 的时候，我在 DAGProcessing 日志里看到这一行：

```
airflow.exceptions.AirflowException: The access_control mapping for DAG 'Insurance__Wellbeing'
includes a role named 'edr-developers', but that role does not exist
```

我当时的判断是：**快好了**。7 天前这类错误有 70 条，最近 3 天只剩 2 条，曲线一路往下走，看起来就是切换后的余震。我在巡检结论里写了"残留 2 条，确认时间戳即可"，然后去忙别的了。

一周后复查，同一类错误 7 天内 21 条，最新一条是前一天晚上。我直接去问数据库：

```
$ airflow roles list
name
======
Admin
Op
Public
User
Viewer
```

九个自定义角色，**一个都没有**。不是"快好了"，是从环境切换那天起就从来没好过。

更离谱的是第二个判断。我顺手告诉组里："角色缺了，其他团队的同事可能看不到自己的 DAG。"这句话也是错的。去 Terraform 里翻 IAM 策略之后才发现：**在我们的 MWAA 上，压根没有任何一个人会以 `edr-developers` 这种角色登录。**

一个没人登录的角色，缺了为什么会报错？既然会报错，为什么 DAG 又照跑不误？要把这两个"为什么"讲清楚，得先把 MWAA 的权限拆成三道门。

读完这篇你会带走：

- **IAM 是大门，FAB 角色是工牌，`access_control` 是会议室门口的预订单**：三者各管一段，搞混任何两个都会误判。
- **错误条数少，不等于快修好了**：这个报错只在 DAG 变化时才触发，它的计数测的是"代码改了多少次"，不是"问题还剩多少"。
- **在托管服务上，runbook 里的命令要先验证能不能执行**：我们写进 runbook 的建角色命令，MWAA 根本不允许跑。

顺序说明：先讲三道门各自是什么（入门），再顺着一次真实报错把第三道门的源码走一遍（深入），最后讲修复过程和怎么验证"真的好了"。

---

## 一、先建立地图：三道门

把 MWAA 想成一栋写字楼：

| 门 | 写字楼里的对应物 | 在 MWAA 里是什么 | 存在哪 | 谁来管 |
|---|---|---|---|---|
| **第一道：IAM** | 大楼门禁：你能不能进楼、进来之后挂哪种工牌 | `airflow:CreateWebLoginToken` 策略，把 IAM 身份映射成一个 Airflow 角色名 | AWS IAM（Terraform） | 云平台团队 |
| **第二道：FAB 角色** | 工牌等级：这张工牌能开哪些门 | Flask-AppBuilder 的 role → permission（action × resource） | Airflow 元数据库 | Airflow 自己 + 管理员 |
| **第三道：DAG 级 `access_control`** | 每间会议室门口的预订单：这间屋子归哪个部门 | DAG 代码里的 `access_control={...}`，同步成 `DAG:<dag_id>` 上的权限 | 写在代码里，同步进元数据库 | 写 DAG 的人 |

关键在"存在哪"那一列。**第一道门在 AWS，第二、三道门在 Airflow 的元数据库里。**换环境名会导致元数据库被清空（这件事我在[《DeleteEnvironment 比 UpdateEnvironment 更诚实》](/blogs/tech/zh/mwaa-name-is-identity)里写过），这时第一道门毫发无伤，后两道门全部归零。症状就是：大家都能正常登录，看起来一切正常。

---

## 二、第一道门：IAM 决定你挂哪张工牌

MWAA 的 Web UI 登录走的是 `CreateWebLoginToken`。我们的 IAM 策略长这样（Terraform 配置，真实片段）：

```yaml
- "airflow:CreateWebLoginToken"
resources:
  - "arn:aws:airflow:ap-southeast-2:${aws_account_id}:role/${channel}-${env}/User"
  - "arn:aws:airflow:ap-southeast-2:${aws_account_id}:role/${channel}-${env}-*/User"
```

注意 ARN 的最后一段：`role/<环境名>/<Airflow 角色名>`。**这一段决定你登录后在 Airflow 里是谁。**我们一共只有五份这样的策略，分别指向 `Admin`、`Op`、`User`、`Viewer`、`Public`。

所以第一个反直觉的事实是：

| 你以为 | 实际上 |
|---|---|
| EDR 团队的人登录后是 `edr-developers` | 他们登录后是 `User` 或 `Op` |
| 缺了 `edr-developers`，EDR 的人就看不到自己的 DAG | `User` 本来就有全局的 DAG 权限，什么都看得见 |
| 角色是给人用的 | 在我们的配置里，那九个自定义角色**一个用户都没有** |

第一道门还有两个坑，都是真实踩过的。

**坑一：通配符的宽度。**SIT 早期的策略写的是 `${env}-???`。IAM 的 `?` 恰好匹配一个字符，所以它能匹配 `-251`，却匹配不上 `-2112`。新环境一上线，控制台跳转 Web UI 直接显示 "Oops, something went wrong"，而环境状态是 `AVAILABLE`、更新状态是 `SUCCESS`，看起来像是 MWAA 坏了。真正的问题出在策略里那三个问号。

**坑二：三种入口，三套授权。**

| 入口 | IAM 动作 | 我们的结果 |
|---|---|---|
| Web UI | `airflow:CreateWebLoginToken`（映射到角色） | ✅ 映射到 Admin |
| MWAA CLI | `airflow:CreateCliToken`（按环境授权） | ✅ 能用，但很多子命令被 MWAA 禁用 |
| REST API | `airflow:InvokeRestApi`（也要映射到角色） | ❌ `No Airflow role granted in IAM` |

这张表在第五章修复时会派上用场。

> 大门只回答"你是谁、挂哪张工牌"，不回答"你能进哪间屋"。

---

## 三、第二道门：FAB 角色是一组"动作 × 资源"

Airflow 2.x 的 Web UI 构建在 Flask-AppBuilder（FAB）上。FAB 的权限模型只有三个概念：

- **action**：动作，比如 `can_read`、`can_edit`、`can_create`、`can_delete`
- **resource**：资源，比如 `DAGs`、`DAG Runs`、`Connections`、`Variables`
- **permission**：action × resource 的一个组合；**role** 就是一组 permission

五个默认角色，可以理解为逐级叠加：

| 角色 | 大致能做什么 |
|---|---|
| `Public` | 什么都不能做（匿名） |
| `Viewer` | 只读：看 DAG、看运行、看日志 |
| `User` | Viewer + 操作 DAG（暂停/恢复、触发、清除、标记状态） |
| `Op` | User + 运维配置（Connections、Variables、Pools 等） |
| `Admin` | 全部，包括管理用户和角色 |

**面试拿分点**：资源分两个层级。`DAGs` 是全局资源，有了 `can_edit on DAGs` 就能操作所有 DAG；`DAG:FF__CHARM__Core` 是 DAG 级资源，只管这一个 DAG。默认角色拿的都是全局权限，所以 `User` 什么都看得见。只有当某个角色**没有**全局权限时，DAG 级权限才真正起到"划地盘"的作用。

这些数据存在元数据库里，表名都以 `ab_` 开头（`ab_role`、`ab_permission_view`、`ab_permission_view_role`……）。所以 MWAA 环境一被替换，这些表就跟着元数据库一起没了，而且没有地方可以恢复。

> 工牌等级写在楼里的花名册上，楼拆了，花名册也跟着没了。

---

## 四、第三道门：`access_control`，一份必须对上的账（深入）

### 4.1 代码里长什么样

我们仓库里两百多个 DAG，几乎每个都有这一行：

```python
with DAG(
    dag_id="FF__CHARM__Core",
    schedule="15 0 * * *",
    access_control={"edr-developers": {"can_edit"}},
    ...
) as dag:
```

意思是：给 `edr-developers` 这个角色，授予 `DAG:FF__CHARM__Core` 上的 `can_edit`。各团队按目录用自己的角色：

| 角色 | 目录 | SIT 引用数 | PRD 引用数 |
|---|---|---|---|
| `edr-developers` | `edr/` | 133 | 210 |
| `tds-developers` | `tds/` | 70 | 69 |
| `cim-developers` | `cim/` | 49 | 46 |
| `fraud-developers` | `fraud/` | 1 | 5 |
| `air-developers` / `airflow-developers` / `edr-test-developers` | 其他 | 少量 | 少量 |
| `fst-developers` / `loy-commercial-ops-developers` | 只在 PRD | 0 | 1 / 2 |

### 4.2 一行声明，怎么变成一条报错

把 SIT 那条报错的调用栈（Airflow 2.11.2）抽出来，是这样一条链：

```
DAG processor 解析 DAG 文件
 └─ DagBag._serialize_dag_capturing_errors      dagbag.py:693
     └─ DagBag._sync_perm_for_dag               dagbag.py:749
         └─ security_manager.sync_perm_for_dag  fab/.../override.py:1153
             └─ _sync_dag_view_permissions      fab/.../override.py:1220  ← raise
```

抛异常的那段源码（下面引的是 fab provider 2.4.1 的版本，逻辑和 2.11 用的一致，只是行号不同）：

```python
# Adding the access control permissions
for rolename, resource_actions in access_control.items():
    role = self.find_role(rolename)
    if not role:
        raise AirflowException(
            f"The access_control mapping for DAG '{dag_id}' includes a role named "
            f"'{rolename}', but that role does not exist"
        )
```

逻辑非常朴素：拿着 `access_control` 里的角色名去 `ab_role` 表里查，查不到就抛异常。它不会顺手帮你建角色。

### 4.3 为什么 DAG 照跑，报错却这么少

这正是我上周误判的根源。从调用栈的顺序和实际表现能读出两件事：

1. **权限同步发生在序列化之后。**DAG 已经序列化写进库了，scheduler 读的是序列化版本，所以调度和执行完全不受影响。CHARM、QBR 那几条批处理在 SIT 每天照常跑，没有一个 task 因为这件事失败。
2. **只有 DAG 内容变化时，才会走到权限同步。**DAG 不变就不同步，不同步就不报错。所以每个文件只在自己被改动、或者内容随时间变化的那一刻报一次。

所以这条报错的计数，测的是"有多少 DAG 最近变过"，而不是"问题还剩多少"。"7 天 70 条降到 3 天 2 条"那条下降曲线，反映的是代码改动变少了，跟修没修好没有关系。

| 指标 | 我当时以为它在测 | 它实际在测 |
|---|---|---|
| "role does not exist" 的条数 | 问题还剩多少 | 最近有多少 DAG 被重新序列化 |
| 条数下降 | 正在自愈 | 代码改动变少了 |
| 可靠的判据 | —— | `roles list` 里有没有这个角色，以及角色身上挂了多少 DAG 权限 |

### 4.4 它还会反向收回权限

同一个函数的前半段，有一段很容易被忽略的逻辑：

```python
# Revoking stale permissions for all possible DAG level resources
for perm in existing_dag_perms:
    non_admin_roles = [role for role in perm.role if role.name != "Admin"]
    for role in non_admin_roles:
        ...
        if perm.action.name not in target_perms_for_role:
            self.remove_permission_from_role(role, perm)
```

也就是说，对任何非 Admin 角色，**只要 `access_control` 里没写，DAG 级权限就会在下次同步时被收回。**你在 UI 上手动给某个角色加的 DAG 级权限，活不过下一次同步。`access_control` 是 DAG 级权限的唯一事实来源，这也是为什么它更像一份账本，而不是一个开关。

> 代码里写下的每个名字，数据库里都必须有一个对应的实体。有没有人用，那是另一回事。

---

## 五、修复：runbook 里那条命令，在 MWAA 上跑不了

缺角色，建上就好。我们的 runbook 里写着用 MWAA CLI：

```bash
curl -X POST "https://$HOST/aws_mwaa/cli" -H "Authorization: Bearer $CLI_TOKEN" \
  --data-raw "roles create edr-developers ..."
```

真跑的时候，MWAA 回的是：

```
HTTP/1.1 400 BAD REQUEST
this sub command is not allowed: create
```

MWAA 的 CLI 端点只开放一部分子命令。`roles list` 可以执行，`roles create` 不行。这就解释了为什么九个角色从切换那天起就不存在：**runbook 里写了一个从来没被验证过的步骤，后来的人照着做了，失败也没人注意。**这是典型的部落知识没有变成工程产物：大家都"知道"该建角色，但没人检查它到底建没建成。

第二章那张三种入口的表，这里就用上了：

| 尝试 | 结果 |
|---|---|
| MWAA CLI `roles create` | ❌ 400，子命令不允许 |
| `aws mwaa invoke-rest-api` | ❌ `No Airflow role granted in IAM` |
| Web UI 登录（映射到 Admin）→ Security → List Roles → 添加 | ✅ |

最后的做法是用 `create-web-login-token` 拿到一个 Admin 会话，走 FAB 的 `/roles/add` 表单。效果和在 UI 上手动点完全一样，只是可以脚本化、能重复执行：

```bash
J=$(aws mwaa create-web-login-token --name "$ENV" --output json)
W=$(echo "$J" | jq -r .WebToken); H=$(echo "$J" | jq -r .WebServerHostname)
curl -s -c jar -b jar -X POST "https://$H/aws_mwaa/login" --data-urlencode "token=$W"
for r in edr-developers tds-developers cim-developers ...; do
  CSRF=$(curl -s -c jar -b jar "https://$H/roles/add" \
         | grep -o 'name="csrf_token" type="hidden" value="[^"]*' | sed 's/.*value="//')
  curl -s -c jar -b jar -X POST "https://$H/roles/add" \
       -H "Referer: https://$H/roles/add" \
       --data-urlencode "csrf_token=$CSRF" --data-urlencode "name=$r"
done   # 302 = 建好了
```

角色只需要一个名字，不用给任何基础权限，因为它们本来就没有用户。

建好之后，还要把那些"不变就不同步"的 DAG 强制同步一遍。仓库里正好有一个现成的 DAG 干这件事：

```python
RESERIALIZE_DAGS = BashOperator(bash_command="airflow dags reserialize", task_id="RESERIALIZE_DAGS")
SYNC_PERM = BashOperator(bash_command="airflow sync-perm", task_id="SYNC_PERM")
RESERIALIZE_DAGS >> SYNC_PERM
```

取消暂停，触发，大约一分半钟跑完，再暂停回去。

---

## 六、怎么证明"真的好了"

吃过"条数在下降"的亏之后，我不再用报错条数当判据，而是用三个互相独立的证据：

| 证据 | 结果 |
|---|---|
| `RESERIALIZE_DAGS` 的任务日志（580 行）里 `does not exist` 的条数 | 0 |
| 建好角色之后，DAGProcessing 里 `"role named"` 的条数 | 0 |
| 每个角色身上挂的 `can edit on DAG:*` 数量 | `edr` 133、`tds` 70、`cim` 49 |

第三条最有说服力：**133、70、49，和代码里 `access_control` 引用这三个角色的次数一个不差。**前两条只能说明"没再报错"，第三条能说明"代码里写的账和数据库里的账对上了"。

---

## 三道门，一张表

| | IAM（大门） | FAB 角色（工牌） | `access_control`（预订单） |
|---|---|---|---|
| 回答的问题 | 你是谁、挂哪张工牌 | 这张工牌能开哪些门 | 这间屋子归谁 |
| 存在哪 | AWS IAM | 元数据库 | 代码 → 元数据库 |
| 换环境名之后 | 不受影响 | **清空** | 代码还在，账本清空 |
| 典型故障 | `???` 通配符宽度不够 | 默认角色之外全部丢失 | 引用了不存在的角色 |
| 典型误判 | 以为是 MWAA 坏了 | 以为有人登录用它 | 以为条数少就是快好了 |

我的立场是：**在用 IAM 映射登录的 MWAA 上，`access_control` 基本不再承担"挡人"的职责，但这些角色一个都不该删，也不该让它们缺着。**原因不是权限控制，而是这份账：代码里写了，数据库里就必须有。真要摆脱它，就得改两百多个 DAG 文件去掉 `access_control`，换来的只是少建九个空角色，不划算。所以更好的做法是把"建角色、强制同步、对账"写进每次切换环境的检查清单。

---

## 立刻可以做的事

1. 在你的 MWAA 上跑一次 `roles list`，再在仓库里跑一次
   `git grep -hoE '"[a-z-]+-developers"' -- dags/ | sort | uniq -c`，两份清单逐一对一下。
2. 打开你的 `CreateWebLoginToken` 策略，看看 ARN 最后一段映射到哪些角色。如果全是默认角色，那就别再跟人说"缺了自定义角色他们会看不到 DAG"。
3. 在你的 IAM 策略里搜一下 `???` 这类定宽通配符：`git grep -n '???' -- <iam 策略目录>`。下一次环境名变长的时候，它就会出问题。
4. 把 runbook 里每一条针对托管服务的命令都真跑一遍。MWAA CLI 有子命令白名单，写进文档不代表能执行。
5. 以后验证权限修复，不要看报错条数，去数角色身上挂了多少 DAG 权限，跟代码引用次数对一对。

---

*权限这件事，不是每个名字背后都有一个人。但代码写下的每一个名字，数据库里都得有一个实体对上。*
