---
title: Bulk 任务成功了，字段还是错的：Salesforce 下拉框的三种静默失败
header:
    image: /assets/images/hd_json_mapping_error.png
date: 2026-11-04
tags:
 - salesforce
 - data-engineering
 - debugging
 - testing
permalink: /blogs/tech/zh/salesforce-picklist-silent-failures
lang: zh
layout: single
category: tech
---

> 量两次，锯一次。 —— 木匠格言

# Bulk 任务成功了，字段还是错的

*从"部署后被 UAT 打回"到"PR 之前就知道会错"——把一次缺陷变成一个可以带走的 skill*

UAT 发回来一张缺陷单，测试结果是这样的：

```
[ 6/18] ContactPointEmail  Ascender 9700xxxx-AMAIL  →  9VlAD000005139H0AQ  FAIL  2/3 fields
    AscenderExternalId__c   PASS  expected=9700xxxx-AMAIL  actual=9700xxxx-AMAIL
    UsageType__c            FAIL  expected=AMAIL           actual=(null)
    EmailAddress            PASS  expected=c***            actual=c***
```

18 条可测记录，3 条进了 Salesforce，3 条的 `UsageType__c` 全是空的。Airflow 是绿的，Bulk API 的 job 是 `JobComplete`，失败行数是 0。

原因看起来也很快：dbt 模型里那一列叫 `"UsageType"`，不是 `"UsageType__c"`。改一个表头，开 PR，看起来五分钟的活。

这个判断漏掉了票上已经写好的后半段。

## 零、答案在评论里，我没点开

| 时间 | 票上已经有的东西 |
|---|---|
| 10 月 20 日 | 测试期望 `UsageType__c = AMAIL`，实际是 null |
| 10 月 22 日 | 评论写明：`MAIL_TYPE` 要写入 `UsageType__c`，不是标准字段 `UsageType` |
| 10 月 26 日 11:16 | 映射页第 15 版。那一行写着 `AMAIL` → `Work`，`EMAIL` → `Internal Staff`，`WSS` → `Internal Research`，`PMAIL` → `Personal` |
| 10 月 26 日 11:18 | 同一张票的评论：页面已按这个映射更新，下面是截图和链接 |
| 11 月 4 日 | 我读到「page updated」，没有打开页面，也没有打开截图，然后开了 PR |

`expected=AMAIL` 是票里最具体的一行。它写于 10 月 20 日，早于 10 月 26 日的映射。我让更具体、但更旧的那一行，压过了更晚的决定。

设计文档里原来有一条待确认：「原始代码可能要映射成 `Work` / `Home`」。我把它改成了「BA 已确认，直接送原始代码」。没有人确认过。我删掉了唯一会拦住自己的那句警告，换上一句自己写出来的确认。

评审问到下拉框之后，我才打开那一页。翻译在那里放了九天。

> 链接不算读过。截图不算读过。点开之前，它只是一行蓝色的字。

然后 PR 上的代码评审留了一句话：

> 如果 `UsageType__c` 是受限下拉框（restricted picklist），原始的 Ascender 代码（AMAIL、EMAIL、WSS、PMAIL）必须是合法的下拉值，否则 Bulk upsert 会报 `INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST`。

我去 org 里查了。它说对了。**我的第一版修复，修好了表头，然后把一个不合法的值送进了一个下拉框。**

这篇文章讲三件事：

- 为什么"Bulk 任务成功"对下拉框字段几乎什么都证明不了——三种失败里只有一种会报错，而且报错的那种是最友好的。
- 部署之前用四条 SOQL 和一条 SQL 把它查清楚，不靠猜。
- 文章末尾有一个完整的 agent skill，复制进你的 `~/.cursor/skills/` 或 `~/.claude/skills/` 就能用。下次你（或你的 AI 助手）改 Salesforce 字段映射时，它会在 PR 之前把这套检查跑一遍。

顺序上，我先讲失败的形态，再讲检查，最后讲为什么要把检查做成 skill。排查时的真实顺序正好相反。

## 一、第一种静默失败：表头写错，Salesforce 照收

`ContactPointEmail` 上同时存在两个字段：

```sql
SELECT QualifiedApiName, DataType, Length, IsNillable
FROM FieldDefinition
WHERE EntityDefinition.QualifiedApiName = 'ContactPointEmail'
  AND QualifiedApiName IN ('UsageType__c', 'UsageType')
```

| QualifiedApiName | DataType | Length |
|---|---|---|
| `UsageType` | Picklist | 40 |
| `UsageType__c` | Picklist | 255 |

一个是标准字段，一个是项目自己加的自定义字段。业务、报表、下游流程读的是 `__c` 那个。我们写的是标准那个。

Bulk API v2 不会帮你分辨"你想写哪个"。表头是一个合法字段名，它就写进去。job 成功，计数器好看，业务字段是空的。

| 普通人的看法 | 资深工程师的洞察 |
|---|---|
| 字段名写错了 Salesforce 会报 `InvalidBatch` | 只有字段**不存在**时才报。写错成**另一个存在的字段**，没有任何信号 |
| 看 job 成功就行 | job 成功只证明"每个表头都是某个合法字段"，不证明是**对的**那个 |

> 表头是契约，不是拼写。拼对了一个错的字段，比拼错更难发现。

## 二、第二种静默失败：下拉框不受限时，垃圾值照收

修完表头，我回头看了一眼 org 里已经存在的 Ascender 邮件记录：

```sql
SELECT UsageType, UsageType__c, AscenderExternalId__c
FROM ContactPointEmail
WHERE AscenderExternalId__c != null
ORDER BY LastModifiedDate DESC
LIMIT 20
```

| UsageType | UsageType__c | AscenderExternalId__c |
|---|---|---|
| `WSS` | null | `2004xxxx-WSS` |
| `AMAIL` | null | `2004xxxx-AMAIL` |
| `PMAIL` | null | `2004xxxx-PMAIL` |
| `EMAIL` | null | `2004xxxx-EMAIL` |

再查标准字段 `UsageType` 的合法值：

```sql
SELECT Value, Label, IsActive
FROM PicklistValueInfo
WHERE EntityParticle.EntityDefinition.QualifiedApiName = 'ContactPointEmail'
  AND EntityParticle.QualifiedApiName = 'UsageType'
```

`Internal Research`、`Internal Student`、`Mailing`、`Personal`、`Internal Staff`、`Work`。

没有 `AMAIL`，没有 `WSS`。可是它们就躺在那里。

这就是**不受限下拉框**的行为：值列表只是 UI 的建议，API 写什么它存什么。你得到的是一个报表筛选不到、流程判断不了、页面上显示成灰色"非法值"的字段。数据进去了，意义没进去。

> 不受限的下拉框是一个不会说"不"的接口。它不报错，不等于它同意。

## 三、第三种失败：受限下拉框——唯一会报错的那一种

`UsageType__c` 的合法值：

```sql
SELECT Value, Label, IsActive, IsDefaultValue
FROM PicklistValueInfo
WHERE EntityParticle.EntityDefinition.QualifiedApiName = 'ContactPointEmail'
  AND EntityParticle.QualifiedApiName = 'UsageType__c'
```

`Work`、`Personal`、`Internal Staff`、`Internal Research`、`Internal Student`。五个。

我想再确认它是不是"受限"的，于是试了：

```sql
SELECT QualifiedApiName, IsRestrictedPicklist
FROM EntityParticle
WHERE EntityDefinition.QualifiedApiName = 'ContactPointEmail'
```

```
No such column 'IsRestrictedPicklist' on entity 'EntityParticle'.
```

**SOQL 查不到"受限"这个属性。** 它在 Setup 的字段定义页面上（"Restrict picklist to the values defined in the value set"），或者在 sObject describe 结果的 `restrictedPicklist` 里，但不在你最顺手的那条查询里。

这一节的反直觉之处在这里：

| 下拉框类型 | 送入原始代码 `AMAIL` 时 | 你什么时候知道 |
|---|---|---|
| 受限 | 行失败：`INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST` | 第一次加载，Bulk 失败报告里 |
| 不受限 | 静默存入一个非法值 | UAT，或者生产报表对不上数的那天 |

**会报错的那一种是最友好的。** 它把问题留在了离你最近的地方。不报错的那一种，把问题推给了测试、推给了 BA、推给了三个月后看报表的人。

所以"它是不是受限的"这个问题，答案并不改变修法。查不到就按受限处理——两种情况下，正确的做法都是**不要送原始代码进去**。

> 先问值合不合法，再问 Salesforce 会不会拦你。前一个问题有标准答案，后一个只是运气。

## 四、第一性原理：62 对 5

源头的代码空间有多大？

```sql
SELECT mail_type, COUNT(*) AS n
FROM hr.mailing
GROUP BY mail_type
ORDER BY n DESC
```

结果是 **62 个不同的 `MAIL_TYPE`**。前几个：

| MAIL_TYPE | 行数 |
|---|---|
| `WSS` | 57,560 |
| `AMAIL` | 54,151 |
| `PMAIL` | 32,294 |
| `BDRM` | 13,986 |
| `PH` | 12,714 |
| `EMAIL` | 12,415 |
| `FAX` | 5,919 |
| … | 后面还有 55 个，有的只有 2 行 |

目标端的值空间：**5 个**。

字段映射，本质上是一个从源值域到目标值域的函数。对于下拉框，这个函数必须满足一条：**在过滤后的源值域上，每一个值都映射到目标值域里的一个合法值，或者被有意识地映射成 null。**

`usage_type as "UsageType__c"` 是什么函数？恒等函数。它把 `AMAIL` 映射到 `AMAIL`——一个不在目标值域里的值。第一版 PR 在数学上就是错的，不需要等部署来证明。

合法的那个函数，10 月 26 日就已经写在映射页上，不是评审之后才补的：

| 源 `MAIL_TYPE` | 目标 `UsageType__c` |
|---|---|
| `AMAIL` | `Work` |
| `EMAIL` | `Internal Staff` |
| `WSS` | `Internal Research` |
| `PMAIL` | `Personal` |

四个目标值都在那五个里面。同一个 org 里学生数据的同步早就是这么做的——它把学生邮件类型翻译成 `Internal Student`、`Personal`，从来不送原始代码。**标准答案一直在隔壁的模型里。**

```sql
case deduped.mail_type
    when 'AMAIL' then 'Work'
    when 'EMAIL' then 'Internal Staff'
    when 'WSS' then 'Internal Research'
    when 'PMAIL' then 'Personal'
end as usage_type
```

注意没有 `else mail_type`。把原始值透传下去，正是这个 bug 本身。

> 映射是函数，不是改名。改名只动了表头，函数才决定值。

## 五、把检查变成一个 skill

这件事里没有一个步骤是难的。四条 SOQL、一条 SQL、一个 `CASE`，映射页上还有现成的对照表。我漏掉的不是技巧，是那条没点开的链接，外加一句没有出处的「已确认」。

我入行二十年，这类坑踩过不止一次：一个 enum、一个 picklist、一个下游系统的代码表。每次都是"这次记住了"，下次换个项目、换个字段，又从 UAT 缺陷单里重新学一遍。

这就是**部落知识**：它存在于修过这个 bug 的人脑子里，存在于某条 Slack 消息里，存在于一个已经合并的 PR 描述里。它不会在你下次改映射的时候主动跳出来。

把它变成工程产物，有几种选择：

| 形式 | 什么时候生效 | 代价 |
|---|---|---|
| PR 模板里加一条 checklist | 开 PR 时，靠人自觉 | 很快就被勾选成习惯动作 |
| dbt `accepted_values` 测试 | 每次 `dbt test` | 只守住你已经知道的值列表，不会去 org 里查 |
| 运行时监控 null 率 | 部署之后 | 已经晚了 |
| Agent skill | AI 助手判断你在改 Salesforce 映射时，自动加载 | 要写清楚触发条件 |

我的选择是 skill 加 dbt 测试。dbt 测试把「当前合法的值」钉死在代码里。skill 的第 0 步更早：先打开票里的每一条链接和截图，按时间读，测试里的 `expected=` 写在映射决定之前，就以映射为准。然后才去目标 org 里核对字段和值。设计文档里没有引文的「已确认」，不许写进去。

越来越多的代码是 AI 助手帮我们写的。它写 `usage_type as "UsageType__c"` 写得和我一样快，也和我一样不会自己去查 org 元数据。skill 的意义在于：**它让"资深工程师会多问的那一句"变成助手每次都会问的那一句。**

> 只存在于人脑子里的经验，每换一个项目就要重交一次学费。

## 六、带走它：完整的 skill

把下面的内容保存为 `~/.cursor/skills/salesforce-picklist-precheck/SKILL.md`（Cursor），或者 `~/.claude/skills/salesforce-picklist-precheck/SKILL.md`（Claude Code）。把 `<Object>`、`<Field>`、`<source_table>` 换成你自己的。

~~~markdown
---
name: salesforce-picklist-precheck
description: >-
  Pre-merge check that every value a pipeline writes into a Salesforce picklist
  field is an active value on the target org, and that the CSV header is the
  field that is actually read. Use before opening or approving a PR that adds,
  renames, or remaps a column feeding Salesforce Bulk API (dbt output models,
  CSV headers, __c fields), when a mapping doc lists source codes, or when a
  reviewer mentions picklist, restricted picklist, or
  INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST.
---

# Salesforce picklist pre-check

A Bulk upsert can succeed and still leave the field wrong. Check the target
org's field definition before the PR, not after UAT.

## Workflow

- [ ] 0. Read the spec, not the test
- [ ] 1. List outbound headers changed in the diff
- [ ] 2. Resolve each header to a real field + type on every target org
- [ ] 3. Pull active picklist values
- [ ] 4. Profile the distinct source values
- [ ] 5. Map every in-scope source value to an active value (or null, on purpose)
- [ ] 6. Pin the contract with a dbt accepted_values test
- [ ] 7. After the first load, read the stored values back

### 0. Read the spec, not the test

- Open every mapping page, attachment, and screenshot the ticket links. A link or an image is unread until you open it.
- Order the evidence by date. A test's `expected=` written before a later mapping comment is stale. The latest decision wins.
- "Mapping" in a BA comment means value translation, not a header rename.
- Never write "confirmed" into a design doc or PR without quoting who confirmed it and where.

### 2. Field exists, and which one

```sql
SELECT QualifiedApiName, DataType, Length, IsNillable
FROM FieldDefinition
WHERE EntityDefinition.QualifiedApiName = '<Object>'
  AND QualifiedApiName IN ('<Field>__c', '<Field>')
```

If a standard field and a `__c` field share a name, the mapping doc must say
which one. Confirm with the BA.

### 3. Active picklist values

```sql
SELECT Value, Label, IsActive, IsDefaultValue
FROM PicklistValueInfo
WHERE EntityParticle.EntityDefinition.QualifiedApiName = '<Object>'
  AND EntityParticle.QualifiedApiName = '<Field>__c'
```

Write the API `Value`, not the `Label`. SOQL does not expose whether the
picklist is restricted (`EntityParticle.IsRestrictedPicklist` is
`INVALID_FIELD`). Read it from Setup or the describe `restrictedPicklist`
flag. If you cannot confirm it, treat it as restricted.

### 4. Profile the source

```sql
SELECT <code_column>, COUNT(*) AS n
FROM <source_table>
GROUP BY <code_column>
ORDER BY n DESC
```

Compare against the model's WHERE filter, not the mapping doc's.

### 5. Map explicitly

- One `when` per in-scope source value, mapping to an active `Value`.
- No `else <code_column>`. Passing the raw code through is the bug.
- Unmapped in-scope values go to null or quarantine on purpose, with a comment.
- Reuse the values other integrations already write to the same field.

### 6. Pin it in dbt

```yaml
- name: '"<Field>__c"'
  tests:
    - accepted_values:
        values: ['<value 1>', '<value 2>']
```

### 7. Read back after the load

```sql
SELECT <Field>__c, COUNT(Id) cnt
FROM <Object>
WHERE <ExternalId>__c != null
GROUP BY <Field>__c
```

A large null group, or a value outside step 3's list, is a failure even if
Bulk reported zero failed rows.

## Gotchas

- Every sandbox is a separate org. Picklist values drift. Check each target.
- Mapping docs lag the org. If the doc's filter and mapping disagree, raise it.
- A UAT expectation written before a mapping change is stale. Update it with the fix.
- Multi-select picklists take `;`-joined values. Validate each part.
~~~

它没有任何私有依赖：一个能跑 SOQL 的地方（Workbench、`sf data query`、你自己的 API 客户端），一个能查源表的地方，就够了。

## 总结：三种失败，一张表

| 失败 | Salesforce 的反应 | 谁发现 | skill 里拦住它的步骤 |
|---|---|---|---|
| 拿过期的 `expected=` 当规格，链接没点开 | 还没部署 | 你自己，如果第 0 步在 | 第 0 步 |
| 表头写成了另一个存在的字段 | 照收 | UAT | 第 2 步 |
| 原始代码进了不受限下拉框 | 照收，存成非法值 | 报表、BA | 第 3、5 步 |
| 原始代码进了受限下拉框 | 行失败 | 第一次加载 | 第 3、5 步 |
| 源头冒出新代码 | 取决于上面哪一种 | 看运气 | 第 4、6 步 |

## 立刻可以做的事

1. 在你的仓库里搜一下所有写 Salesforce 下拉框字段的 dbt 列：`as "...__c"`，看有没有直接透传源代码、没有 `case` 的。
2. 对每一个这样的字段，跑一次第 3 步的 `PicklistValueInfo` 查询，再跑一次第 7 步的回读查询。null 很多、或者有值不在列表里的，就是你下一张缺陷单。
3. 给这些列加上 `accepted_values` 测试。
4. 把上面的 skill 放进你的 skills 目录。下次改映射，先看第 0 步有没有发生：票里的链接和截图打开了没有，设计文档里的「已确认」有没有引文。

*Bulk 说成功，只是说它收下了。收下，不等于听懂了。*
