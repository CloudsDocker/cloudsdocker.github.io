---
title: 三道门：MWAA 权限错误解析与修复
header:
    image: /assets/images/bg_raw/BingWallpaper (14).jpg
date: 2026-10-22
tags:
 - airflow
 - mwaa
 - iam
 - permissions
 - terraform
 - debugging
permalink: /blogs/tech/zh/mwaa-permissions-triple-door
alt_url: /blogs/tech/en/mwaa-permissions-missing-roles
lang: zh
layout: single
category: tech
---
> "名者，实之宾也。——《庄子·逍遥游》

# 三道门：MWAA 权限错误解析与修复

*从“权限就是给人开门”到“有些权限是给代码对账”——看懂 MWAA 的三道门*

上周巡检 SIT 的时候，我在 DAGProcessing 日志里看到这一行：
```
airflow.exceptions.AirflowException: The access_control mapping for DAG 'Company__Wellbeing' includes a role named 'dev-team-developers', but that role does not exist
```
我当时的判断是：**快好了**。7 天前这类错误有 70 条，最近 3 天只剩 2 条，曲线一路往下走，看起来就是切换后的余震。我在巡检结论里写了“残留 2 条，确认时间戳即可”，然后去忙别的。

一周后复查，同一类错误 7 天内 21 条，最新一条是前一天晚上。于是我直接去数据库查询角色列表：
```
$ airflow roles list
name
=====
Admin
Op
Public
User
Viewer
```
九个自定义角色**一个都没有**。这并不是“快好了”，而是从环境切换那天起就一直没好。

更离谱的是，我顺手告诉组里：“角色缺了，其他团队的同事可能看不到自己的 DAG。” 这句话也错了。去 Terraform 里翻 IAM 策略后才发现：在我们的 MWAA 上，根本没有任何人会以 `dev-team-developers` 这种角色登录。

## 一、先建立地图：三道门
把 MWAA 想成一栋写字楼：
| 门 | 写字楼里的对应物 | 在 MWAA 里是什么 | 存在哪 | 谁来管 |
|---|---|---|---|---|
| **第一道：IAM** | 大楼门禁：你能不能进楼、进来之后挂哪种工牌 | `airflow:CreateWebLoginToken` 策略，把 IAM 身份映射成一个 Airflow 角色名 | AWS IAM（Terraform） | 云平台团队 |
| **第二道：FAB 角色** | 工牌等级：这张工牌能开哪些门 | Flask-AppBuilder 的 role → permission（action × resource） | Airflow 元数据库 | Airflow 自己 + 管理员 |
| **第三道：DAG 级 `access_control`** | 每间会议室门口的预订单：这间屋子归哪个部门 | DAG 代码里的 `access_control={…}`，同步成 `DAG:<dag_id>` 上的权限 | 写在代码里，同步进元数据库 | 写 DAG 的人 |

### 第一道门——IAM 与 Web 登录 Token
- **目标**：判断“谁”想要进入 Airflow UI。所有请求首先经过 AWS IAM，确认是否拥有 `airflow:CreateWebLoginToken` 权限。
- **实现细节**：该策略在 Terraform 配置里定义，授予特定 IAM 角色或用户组访问权限。成功后，Airflow 生成一个短期有效的 Web 登录 Token，并把 IAM 的身份映射为 Airflow 内部的角色名（例如 `admin`、`operator`）。
- **边界**：如果 IAM 策略被撤销或改动，登录即失效；但这一步不涉及任何元数据库操作，单纯在 AWS 层完成。

### 第二道门——Flask‑AppBuilder 角色与权限
- **目标**：控制“工牌”能开哪些门。Airflow 的前端是基于 Flask‑AppBuilder（FAB），它提供了 RBAC 系统。
- **实现细节**：在 Airflow 配置里声明 `role` 与一组 `permission`，每个 permission 是 `(action, resource)` 的组合，例如 `('dags', 'read')`。这些角色与权限被写入 Airflow 元数据库（通常是 PostgreSQL 或 SQLite），供后台查询。
- **边界**：元数据库的迁移、清空或重建会导致所有 FAB 角色消失，随后任何基于 FAB 的 UI 权限检查都会失败。

### 第三道门——DAG 级 `access_control`
- **目标**：细粒度地决定“这间屋子（DAG）归谁”。
- **实现细节**：在 DAG 定义文件里加入 `access_control={‘role1’: [‘perm1’, …], ‘role2’: …}`，Airflow 解析后把它写入元数据库的 `dags` 表中，以 `DAG:<dag_id>` 为主键。此表与 FAB 的角色/权限关联，实现“谁能看、谁能编辑、谁能运行”三种操作。
- **边界**：任何修改 DAG 代码后，部署时 Airflow 会重新同步 `access_control`；如果元数据库被清空，所有自定义的 `access_control` 都会消失。

### 环境切换与元数据库的命运
在 MWAA 的多环境（如 dev、staging、prod）中，每个环境都对应一套独立的 Airflow 元数据库。**当你把环境名改成别的名字时，Airflow 会自动创建一个全新的元数据库实例**，而原来的数据库内容（包括 FAB 角色和 DAG `access_control`）会被抛弃。IAM 门在 AWS 层保持不变，但第二、三道门却全部归零。

这就是我在《[DeleteEnvironment 比 UpdateEnvironment 更诚实](/blogs/tech/zh/mwaa-name-is-identity)》里写过的经验：环境名更改导致元数据库被清空，结果是“大家都能正常登录，看起来一切正常”，但实际上 **所有业务 DAG 的访问权限全失效**。因此，在做任何环境迁移之前，务必先备份或导出 Airflow 元数据库，再手动恢复角色与 `access_control` 配置。

## 二、第一道门：IAM 决定你挂哪张工牌
MWAA 的 Web UI 登录走的是 `CreateWebLoginToken`。我们的 IAM 策略长这样（Terraform 配置，真实片段）：
```
yaml
- "airflow:CreateWebLoginToken"
resources:
  - "arn:aws:airflow:ap-southeast-2:${aws_account_id}:role/${channel}-${env}/User"
  - "arn:aws:airflow:ap-southeast-2:${aws_account_id}:role/${channel}-${env}-*/User"
```
注意 ARN 的最后一段：`role/<环境名>/<Airflow 角色名>`。**这一段决定你登录后在 Airflow 里是谁**。我们一共只有五份这样的策略，分别指向 `Admin`、`Op`、`User`、`Viewer`、`Public`。

所以第一个反直觉的事实是：
| 你以为 | 实际上 |
|---|---|
| EDR 团队的人登录后是 `dev-team-developers` | 他们登录后是 `User` 或 `Op` |
| 缺了 `dev-team-developers`，EDR 的人就看不到自己的 DAG | `User` 本来就有全局的 DAG 权限，什么都看得见 |
| 角色是给人用的 | 在我们的配置里，那九个自定义角色**一个用户都没有** |

第一道门还有两个坑，都是真实踩过的。

### 坑一：通配符的宽度
SIT 早期的策略写的是 `${env}-???`。IAM 的 `?` 恰好匹配一个字符，所以它能匹配 `-251`，却匹配不上 `-2112`。新环境一上线，控制台跳转 Web UI 直接显示 “Oops, something went wrong”，而环境状态是 `AVAILABLE`、更新状态是 `SUCCESS`，看起来像是 MWAA 坏了。真正的问题出在策略里那三个问号。

### 坑二：三种入口，三套授权
| 入口 | IAM 动作 | 我们的结果 |
|---|---|---|
| Web UI | `airflow:CreateWebLoginToken`（映射到角色） | ✅ 映射到 Admin |
| MWAA CLI | `airflow:CreateCliToken`（按环境授权） | ✅ 能用，但很多子命令被 MWAA 禁用 |
| REST API | `airflow:InvokeRestApi`（也要映射到角色） | ❌ `No Airflow role granted in IAM` |

这张表在第五章修复时会派上用场。

> 大门只回答“你是谁、挂哪张工牌”，不回答“你能进哪间屋”。

## 三、第二道门：FAB 角色是一组“动作 × 资源”
Airflow 2.x 的 Web UI 是建立在 **Flask‑AppBuilder（FAB）** 框架之上的。FAB 为权限控制提供了三层概念，构成了整个系统的安全模型。

- **action**：表示可以执行的操作，例如 `can_read`、`can_edit`、`can_create`、`can_delete` 等。
- **resource**：代表被保护的对象，如 `DAGs`、`DAG Runs`、`Connections`、`Variables` 等。
- **permission**：是 action 与 resource 的笛卡尔积，描述对某种资源能执行哪类动作；一个 **role** 由若干 permission 组合而成。

在默认安装中，Airflow 提供了五个预设角色。它们可以看作按权限层级逐步叠加的集合：
| 角色 | 大致能做什么 |
|---|---|
| `Public` | 什么都不能做（匿名访问） |
| `Viewer` | 只读：查看 DAG、运行状态、日志 |
| `User` | Viewer + 对 DAG 的基本操作（暂停/恢复、触发、清除、标记状态） |
| `Op` | User + 运维配置权限（管理 Connections、Variables、Pools 等） |
| `Admin` | 完全控制：包括用户与角色的管理 |

> **面试拿分点**：资源层级分为两种。`
>DAGs` 是全局资源，拥有 `can_edit on DAGs` 就能对所有 DAG 进行修改；而 `DAG:FF__MIGRATION__Core` 属于 DAG‑级别资源，只作用于单个 DAG。默认角色均使用全局权限，因此即使你是 `User`，也能看到全部 DAG。只有当某个角色**缺失**全局权限时，DAG 级的权限才会真正发挥“划地盘”的效果。

所有与权限相关的数据都保存在元数据库中，表名以 `ab_` 开头（如 `ab_role`、`ab_permission_view`、`ab_permission_view_role` 等）。这意味着，当 MWAA 环境被替换或迁移时，这些表会随元数据库一起消失，并且没有官方的恢复路径。

> 工牌等级写在楼里的花名册上，楼拆了，花名册也跟着没了。

## 四、第三道门：`access_control`，一份必须对上的账（深入）
### 4.1 代码里长什么样
在我们的仓库中已有两百余条 DAG 定义，每个几乎都含有类似的声明：
```
with DAG(
    dag_id="Company__Wellbeing",
    schedule="15 0 * * *",
    access_control={"dev-team-developers": {"can_edit"}},
    ...
) as dag:
```
这行的语义非常直白：给角色 **`dev‑team‑developers`** 在 DAG `Company__Wellbeing` 上授予 `can_edit` 权限。不同团队通过目录结构为自己的角色命名，示例如下。
| 角色 | 所属目录 | SIT 引用数 | PRD 引用数 |
|---|---|---|---|
| `dev-team-developers` | `dev/` | 133 | 210 |
| `analytics-developers` | `analytics/` | 70 | 69 |
| `support-developers` | `support/` | 49 | 46 |
| `fraud-developers` | `fraud/` | 1 | 5 |
| `infra-developers` / `workflow-developers` / `dev-test-developers` | 其他 | 少量 | 少量 |
| `ops-developers` / `commercial-ops-developers` | 只在 PRD | 0 | 1/2 |

> **小结**：一行声明，角色与 DAG 的映射关系已被硬编码进 DAG 文件。若后续代码未同步到数据库，则权限会失效。

### 4.2 一行声明，怎么变成一条报错
从 SIT 环境的错误堆栈（Airflow 2.11.2）中抽取关键链路：
```
DAG processor 解析 DAG 文件
 └─ DagBag._serialize_dag_capturing_errors      dagbag.py:693
     └─ DagBag._sync_perm_for_dag               dagbag.py:749
         └─ security_manager.sync_perm_for_dag  fab/.../override.py:1153
             └─ _sync_dag_view_permissions      fab/.../override.py:1220  ← raise
```
对应的抛异常代码（fab‑provider 2.4.1 与 Airflow 2.11 的逻辑保持一致，只是行号不同）如下：
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
该段逻辑极为朴素：遍历 `access_control` 中声明的每个角色名，在数据库（`ab_role` 表）中查找对应条目；若不存在则抛出异常。**它不会自动创建缺失的角色**，这正是报错出现的根源。

### 4.3 为什么 DAG 照跑，报错却这么少
从调用栈顺序与实际表现可以读出两条关键信息：
1. **权限同步发生在 DAG 序列化之后**。DAG 已经被写入数据库并由 Scheduler 读取；因此调度和执行阶段不受此错误影响，SIT 中的 MIGRATIONS、DEP 等批处理仍按预期运行。
2. **仅当 DAG 内容变化时才触发权限同步**。若文件内容保持不变，Airflow 会跳过同步步骤，自然也就不会抛错。因此报错计数实际上衡量的是“最近有多少 DAG 被重新序列化”，而非“还存在哪些未解决的角色缺失”。

这解释了为何我们在 7 天内看到 70 条错误，随后降至 3 天只剩 2 条——代码改动变少，而不是问题自愈。
| 指标 | 当时的误读 | 实际测量 |
|---|---|---|
| "role does not exist" 的条数 | 剩余未解决的问题数量 | 最近被重新序列化的 DAG 数量 |
| 条数下降 | 正在自愈 | 代码改动变少 |
| 可靠判据 | —— | `roles list` 中是否存在该角色以及其挂载的 DAG 权限 |

> **洞见**：报错频率是“触发点”的指标，而非“剩余风险”。监控时需关注实际权限状态，而非错误计数。

### 4.4 它还会反向收回权限
同一函数的前半段包含了一个容易被忽视的撤销逻辑：
```python
# Revoking stale permissions for all possible DAG level resources
for perm in existing_dag_perms:
    non_admin_roles = [role for role in perm.role if role.name != "Admin"]
    for role in non_admin_roles:
        ...
        if perm.action.name not in target_perms_for_role:
            self.remove_permission_from_role(role, perm)
```
这段代码的含义是：**对于任何非 Admin 角色，只要在 `access_control` 中未声明对应权限，DAG 级别的访问权将在下次同步时被撤回**。也就是说，如果你在 UI 手动为某个角色添加了 DAG 权限，它会在下一次权限同步时消失。

> **结论**：`access_control` 是 DAG 权限的唯一事实来源，类似账本而非开关；每一次写入都代表一条不可逆转的记录。

## 五、修复：runbook 里那条命令，在 MWAA 上跑不了
缺角色，建上就好。我们的 runbook 里写着用 MWAA CLI：
```
curl -X POST "https://$HOST/aws_mwaa/cli" -H "Authorization: Bearer $CLI_TOKEN" \
  --data-raw "roles create team-developers ..."
```
真跑的时候，MWAA 回的是：
```
HTTP/1.1 400 BAD REQUEST
this sub command is not allowed: create
```
MWAA 的 CLI 端点只开放一部分子命令。`roles list` 可以执行，`roles create` 不行。这就解释了为什么九个角色从切换那天起就不存在：**runbook 里写了一个从来没被验证过的步骤，后来的人照着做了，失败也没人注意**。这是典型的部落知识没有变成工程产物：大家都“知道”该建角色，但没人检查它到底建没建成。

第二章那张三种入口的表，这里就用上了：
| 尝试 | 结果 |
|---|---|
| MWAA CLI `roles create` | ❌ 400，子命令不允许 |
| `aws mwaa invoke-rest-api` | ❌ `No Airflow role granted in IAM` |
| Web UI 登录（映射到 Admin）→ Security → List Roles → 添加 | ✅ |

最后的做法是用 `create-web-login-token` 拿到一个 Admin 会话，走 FAB 的 `/roles/add` 表单。效果和在 UI 上手动点完全一样，只是可以脚本化、能重复执行：
```
J=$(aws mwaa create-web-login-token --name "$ENV" --output json)
W=$(echo "$J" | jq -r .WebToken); H=$(echo "$J" | jq -r .WebServerHostname)
curl -s -c jar -b jar -X POST "https://$H/aws_mwaa/login" --data-urlencode "token=$W"
for r in team-developers pod-developers ops-developers ...; do
  CSRF=$(curl -s -c jar -b jar "https://$H/roles/add" \
         | grep -o 'name="csrf_token" type="hidden" value="[^"]*' | sed 's/.*value="//')
curl -s -c jar -b jar -X POST "https://$H/roles/add" \
     -H "Referer: https://$H/roles/add" \
     --data-urlencode "csrf_token=$CSRF" --data-urlencode "name=$r"
done   # 302 = 建好了
```
角色只需要一个名字，不用给任何基础权限，因为它们本来就没有用户。

建好之后，还要把那些“不变就不同步”的 DAG 强制同步一遍。仓库里正好有一个现成的 DAG 干这件事：
```
RESERIALIZE_DAGS = BashOperator(bash_command="airflow dags reserialize", task_id="RESERIALIZE_DAGS")
SYNC_PERM = BashOperator(bash_command="airflow sync-perm", task_id="SYNC_PERM")
RESERIALIZE_DAGS >> SYNC_PERM
```
取消暂停，触发，大约一分半钟跑完，再暂停回去。

## 六、怎么证明“真的好了"
在经历了**条数持续下降**的痛苦之后，我彻底抛弃了仅凭报错计数来评判系统是否恢复的做法。取而代之的是三条完全独立且互补的验证手段：
1. **RESERIALIZE_DAGS 任务日志** – 我把所有 `does not exist` 的错误行从约 580 行中筛选出来，确认其数量降至零。
2. **DAGProcessing 日志中的角色声明** – 在启动 DAG 后的日志里搜索 `role named`，确认没有再出现缺失角色的报错。
3. **每个角色身上挂的 `can edit on DAG:*` 数量** – 用脚本统计数据库中每个角色拥有的 DAG 级权限数量，并与代码里的 `access_control` 引用次数做对比。若两者一致，即可确认账本已对齐。

> **结论**：错误计数下降并不等于问题解决；真正的健康指标是“所有声明的角色都存在，且其 DAG 级权限与代码保持同步”。

## 三道门，一张表
| | IAM（大门） | FAB 角色（工牌） | `access_control`（预订单） |
|---|---|---|---|
| 回答的问题 | 你是谁、挂哪张工牌 | 这张工牌能开哪些门 | 这间屋子归谁 |
| 存在哪 | AWS IAM | 元数据库 | 代码 → 元数据库 |
| 换环境名之后 | 不受影响 | **清空** | 代码还在，账本清空 |
| 典型故障 | `???` 通配符宽度不够 | 默认角色之外全部丢失 | 引用了不存在的角色 |
| 典型误判 | 以为是 MWAA 坏了 | 以为有人登录用它 | 以为条数少就是快好了 |

> 我的立场是：**在用 IAM 映射登录的 MWAA 上，`access_control` 基本不再承担“挡人”的职责，但这些角色一个都不该删，也不该让它们缺着。**
>
> 原因不是权限控制，而是这份账：代码里写了，数据库里就必须有。真要摆脱它，就得改两百多个 DAG 文件去掉 `access_control`，换来的只是少建九个空角色，不划算。所以更好的做法是把“建角色、强制同步、对账”写进每次切换环境的检查清单。

## 立刻可以做的事
1. **先把两份角色清单拿出来比对**
   - 在 MWAA 环境里执行 `aws mwaa list-roles`，得到 AWS 端实际配置的 IAM 角色列表。
   - 同步到代码仓库中跑 `git grep -hoE '"[a-z-]+-developers"' -- dags/ | sort | uniq -c`，把 DAG 目录里出现的所有角色名称聚合成一份清单。两份名单逐行对比，确认每个在代码里声明的角色都真的存在于 AWS。

2. **核查 `CreateWebLoginToken` 策略**
   - 打开 IAM 控制台或通过 CLI 拉取策略 JSON：`
     aws iam get-policy --policy-arn <POLICY_ARN> | jq '.Policy.PolicyVersionList[0].Document'
   `
   - 查看 ARN 最后一段（即角色名）映射到哪些角色。若全是默认角色（如 `aws-mwaa-*`），说明自定义角色并未被授权，用户在使用自定义角色时会看到“缺少 DAG 访问”错误。

3. **搜索通配符导致的潜在失效**
   - 在 IAM 策略目录下跑：`
     git grep -n '???' -- <iam 策略目录>
   `
   - 这类粗糙的三问号或星号通配符会在环境名扩展（例如从 `dev` 到 `development-01`）后失效。提前定位并用精确 ARN 替换，避免未来环境改动导致权限不可用。

4. **验证托管服务命令是否可执行**
   - MWAA CLI 在官方文档里列出的子命令只是“建议”，实际能否调用取决于账号 IAM 权限。把 runbook 里每一条针对托管服务的命令都手动跑一次，确认没有被拒绝。

5. **量化角色拥有的 DAG 权限**
   - 不要只看报错数量，而是统计每个角色在 IAM 策略中挂载了多少 DAG 资源。可以用脚本扫描策略 JSON，提取 `Resource` 字段里出现的 `arn:aws:mwaa:*:*:dag/*`，然后与代码中引用次数做一对比。
   - 这一步能让你清楚地看到哪些角色实际上被授予了权限，哪些仅在错误日志里出现，却根本没用到。

---

*权限这件事，不是每个名字背后都有一个人。但代码写下的每一个名字，数据库里都得有一个实体对上。*
