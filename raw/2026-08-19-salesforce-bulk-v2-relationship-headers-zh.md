---
title: "报错信息一直是对的：Salesforce Bulk API v2 的关系字段表头"
date: 2026-08-19
categories: [engineering, salesforce, debugging]
tags: [salesforce, bulk-api, csv, polymorphic, data-integration, debugging]
---

一条数据管道静默失败了三周。每次跑，第一个对象加载正常，下一个必挂，报错永远是同一句：

```
InvalidBatch : type is not needed for non polymorphic foreign key references: Parent
```

这句话我们读了几十遍。查了 org 元数据，升级给了 Salesforce 团队，甚至起草了工单。唯独没做的一件事——直到最后才做——是**照字面意思理解这句话**。

最终的修复是删掉 8 个字符。

## 背景

管道通过 Bulk API v2 upsert 把申请人数据同步进 Salesforce，两个对象按顺序加载：

1. `Account`（Person Account）——以 `ApplicantId__c` 为键
2. `ContactPointEmail`——以 `ExternalId__c` 为键，且每行都要关联回它的父 Account

因为我们是按**业务键**而不是 Salesforce Id 加载的，父级关联要用一个特殊的 CSV 列来表达。那一列当时写的是：

```
Account:Parent.ApplicantId__c
```

Account 每次都成功——784 条，0 失败。ContactPointEmail 每次都失败，而且 processed 是 0，failed 也是 0。

最后这个细节其实是第一条真线索，我们直接滑过去了。

## 怎样正确阅读一次 Bulk v2 失败

Bulk API v2 ingest 是三次调用：

```
POST  /services/data/v65.0/jobs/ingest              → 建 job
PUT   /services/data/v65.0/jobs/ingest/{id}/batches → 上传 CSV
GET   /services/data/v65.0/jobs/ingest/{id}         → 轮询状态
```

坑在于：**即使表头完全是垃圾，CSV 上传照样返回 `201 Created`。** Salesforce 在上传阶段根本不校验列名。你先拿到一个喜气洋洋的 201，几秒后 job 才翻成 `Failed`。

```json
{
  "id": "750XXXXXXXXXXXXXXX",
  "object": "ContactPointEmail",
  "state": "Failed",
  "numberRecordsProcessed": 0,
  "numberRecordsFailed": 0,
  "errorMessage": "InvalidBatch : type is not needed for non polymorphic foreign key references: Parent"
}
```

这两个计数器要**合起来读**：

| processed | failed | 含义 |
|---:|---:|---|
| 0 | 0 | **表头/批次被拒。** 一行都没被求值过。 |
| 700 | 84 | 行被求值了，84 行撞了校验规则。去拉 `failedResults`。 |
| 784 | 0 | 干净加载。 |

`0 / 0` 意味着问题是**结构性**的——是你 CSV 的 schema，不是内容。此时没有 `failedResults` 可拉，因为 Salesforce 压根没走到看某一行的那一步。如果你看到 `0 / 0` 还在翻脏数据，停下来，你找错层了。

## 弯路一：所谓的元数据「悖论」

既然报错说 "non polymorphic"，我们就去问 org 自己怎么认为。描述一个字段的 Tooling API 对象有两个，它们看起来在互相打架：

```sql
-- 这是个什么字段？
SELECT QualifiedApiName, DataType, IsPolymorphicForeignKey, RelationshipName
FROM FieldDefinition
WHERE EntityDefinition.QualifiedApiName = 'ContactPointEmail'
  AND QualifiedApiName = 'ParentId'
```
```
DataType                = Master-Detail(Account)
IsPolymorphicForeignKey = true          ← 「它就是多态的」
RelationshipName        = Parent
```

```sql
-- 它实际能指向什么？
SELECT QualifiedApiName, DataType, ReferenceTo
FROM EntityParticle
WHERE EntityDefinition.QualifiedApiName = 'ContactPointEmail'
  AND QualifiedApiName = 'ParentId'
```
```
ReferenceTo = { referenceTo: ["Account"] }   ← 只有一个目标
```

一个标志位说「多态」，一个列表只有一项。我们围绕这个矛盾建了一整套理论：Bulk v2 一定是按 `referenceTo` 的**条目数**而不是标志位来判断的，所以 org 配置不一致，得让 Salesforce 从源头修。

这套理论**机制上是对的，作为结论却毫无用处。** 是的，Bulk v2 确实按条目数判断。但那不是待修的 bug——那是写在文档里的规则，而且它早就把答案告诉我们了：`referenceTo` 只有一项 ⇒ 别发类型前缀。完。

我们把一句大白话指令，硬生生变成了元数据悬案，只因为 "polymorphic" 这个词出现在两个地方，而我们锚定了更方便甩锅的那一个。

## 弯路二：没复现就采信

Salesforce 团队回复说，他们用这个表头成功创建了一条记录：

```
ExternalId__c    Parent:Account:ApplicantId__c    EmailAddress    UsageType__c
```

三段式。我们的也是三段式，只是顺序不同。像到足够权威，又不同到刚好能解释差异。很有诱惑力。

所以我们跑了它。不是跑一个变体——是拿**那个一模一样的字符串**，打**同一个 org**，走**管道实际用的那条代码路径**。

## 实验

整个调查最后浓缩成一个循环。一个小 bash 函数，一行 CSV，五种表头写法：

```bash
run() {
  python3 - "$1" > /tmp/p.json <<'PY'
import json, sys
h = sys.argv[1]
print(json.dumps({
  "csv_data": f"ExternalId__c,{h},EmailAddress,UsageType__c\n"
              f"APPLICANT-001,APPLICANT-001,test@example.edu,Personal",
  "salesforce_object": "ContactPointEmail",
  "external_id_field_name": "ExternalId__c",
}))
PY
  printf '%-40s ' "$1"
  curl -s -X POST http://localhost:18080/bulk-load \
    -H 'Content-Type: application/json' \
    -H 'x-salesforce-org: SANDBOX' \
    -d @/tmp/p.json \
  | python3 -c "
import json,sys
d = json.load(sys.stdin)
print('SUCCESS  %d processed' % d['data']['records_processed']) if d.get('success') \
  else print('FAILED   ' + d['error']['details'].split('Debug Info')[0].strip())
"
}

run 'Parent:Account:ApplicantId__c'    # SF 团队声称可用的
run 'Account:Parent:ApplicantId__c'
run 'Account:Parent.ApplicantId__c'    # 我们代码发的
run 'Parent:Account.ApplicantId__c'
run 'Parent.ApplicantId__c'
```

结果：

| 表头列 | 结果 |
|---|---|
| `Parent:Account:ApplicantId__c` | `InvalidBatch : Field name not found : Parent:Account:ApplicantId__c` |
| `Account:Parent:ApplicantId__c` | `InvalidBatch : Field name not found : Account:Parent:ApplicantId__c` |
| `Account:Parent.ApplicantId__c` | `InvalidBatch : type is not needed for non polymorphic foreign key references: Parent` |
| `Parent:Account.ApplicantId__c` | `InvalidBatch : Unable to find relationship: Account` |
| **`Parent.ApplicantId__c`** | **SUCCESS —— 1 processed, 0 failed** |

那个「声称可用」的表头根本不可用。正序不行，反序也不行。

三周的推演，靠变换一个字符串，90 秒给出了答案。

## 从报错反推语法

下面这段是最值得拿去跟团队分享的，因为它的适用范围远超这个 bug 本身。**三次失败彼此都不一样，而每一处不同都在告诉你解析器是怎么工作的。**

对比第 3、4 行：

- `Parent:Account.X` → *"Unable to find relationship: **Account**"*

  Salesforce 把冒号和点之间的 token 读成了关系名。所以语法是 `ObjectType:RelationshipName.MatchField`。

- `Account:Parent.X` → *"type is not needed..."*

  这个其实**解析正确了**——类型 `Account`，关系 `Parent`。Salesforce 完全懂我们要什么，然后按策略拒绝，不是按语法拒绝。

再看第 1、2 行，全冒号的两个：

- → *"Field name not found: `<整串>`"*

  没有点，就没有可切分的地方。Salesforce 直接放弃关系解析，把整串当成一个字面字段名。**没有点的三段式表头，根本不是关系引用。**

所以报错从来不矛盾。它们是同一个解析器三个不同阶段——分词、解析、策略校验——发回的三份精确报告。只是我们没把它们当成一个序列来读。

> **通用的调试心得：** 当一个系统对*相似*的输入给出*不同*的报错，这个差异就是免费文档。故意扰动输入来「收割」报错信息，往往比翻文档更快——而且更权威，因为那是实现本身在说话。

## 底层模型：每个 lookup 都有两个名字

现在讲整个 bug 赖以成立的那个概念。

Salesforce 里每个 lookup / master-detail 字段都带**两个**名字。CSV 关系表头用的是第二个：

| 字段 API 名（存 Id 的那个） | 关系名（表头里用这个） |
|---|---|
| `ParentId` | `Parent` |
| `AccountId` | `Account` |
| `OwnerId` | `Owner` |
| `RecordTypeId` | `RecordType` |
| `ParentApplication__c`（自定义） | `ParentApplication__r` |

规则：**标准** lookup 去掉结尾的 `Id`；**自定义** lookup 把 `__c` 换成 `__r`。

这两种约定通常就并存在同一个文件里。取自我们的 record builder：

```python
{
    'Parent.ApplicantId__c':                  parent_id,   # 标准 → 无后缀
    'RecordType.Name':                        'Student',   # 标准 → 无后缀
    'Account.ApplicantId__c':                 parent_id,   # 标准 → 无后缀
    'ParentApplication__r.ExternalId__c':     parent_app,  # 自定义 → __r
}
```

**点之后**的部分是*按哪个字段去匹配*。所以 `Parent.ApplicantId__c` 读作：「找到 `ApplicantId__c` 等于本单元格值的那条父记录，并关联过去。」你是在按业务键做 join，而不是按 Salesforce Id——这正是这套语法存在的全部理由，也是「不在自己这边存 Salesforce Id 也能幂等重跑」的前提。

## 三种表头形态

```
FieldApiName                             ← 普通标量列
RelationshipName.MatchField              ← 单目标 lookup   （2 段）
ObjectType:RelationshipName.MatchField   ← 多态 lookup     （3 段）
```

那条让我们赔了三周的关键规则：

> 3 段式**不是**一种「更显式」的可选风格。Salesforce 只在关系确实有多个可能目标类型时才接受它，否则**直接拒绝**。

「写得更明确」不是免费的。给一个本来就不可能有歧义的关系指定类型，是错误，不是有益的冗余。

## 哪些关系才是真多态

下面这些才是真正需要 `ObjectType:` 前缀的：

| 关系 | 字段 | 可指向 | 常在哪遇到 |
|---|---|---|---|
| `Owner` | `OwnerId` | User **或** Group（队列） | 几乎所有对象 |
| `Who` | `WhoId` | Contact **或** Lead | Task、Event |
| `What` | `WhatId` | Account、Opportunity、Case、自定义对象… | Task、Event |
| `Parent` | `ParentId` | 几乎任何东西 | Note、Attachment、ContentDocumentLink |

合法的 3 段式长这样：`Owner:User.Username`、`What:Account.MyExtId__c`。实战中最常撞上的是 `Owner`——分配给队列还是分配给用户，是经典场景。

注意 `Parent` 也在这张表里。这就是为什么我们的困惑是「合理」而不是「愚蠢」：在 `Note` 和 `Attachment` 上，`Parent` 确实是极度多态的；在 `ContactPointEmail` 上不是。**关系名告诉你的是语义（「我的归属记录」），不是基数。** 永远不要从名字去推断表头形态。

`RecordType.Name` 是同一套机制，只是常见到让人忘了它也是关系穿透：`RecordTypeId` 是指向 `RecordType` 的单目标 lookup，按 `Name` 而不是外部 Id 匹配。两段，无前缀——因为它只可能指向 RecordType。

## 30 秒自查

加任何 lookup 列之前，该问的**不是**「这字段在哪儿被描述成多态了吗」，而是：

> **在这个具体的 org 里，这个具体的关系能指向几种对象类型？**

而且你永远不需要猜：

```sql
SELECT QualifiedApiName, RelationshipName, DataType, ReferenceTo
FROM EntityParticle
WHERE EntityDefinition.QualifiedApiName = 'ContactPointEmail'
  AND QualifiedApiName = 'ParentId'
```

`ReferenceTo` 直接给你列表。**一项 → 2 段，无前缀。两项及以上 → 3 段，必须带前缀。**

注意「在这个具体的 org 里」这个限定。功能启用和 license 会改变一个关系在不同 org 之间的目标列表。同一个表头在一个沙箱能用、在另一个沙箱合法地失败——这正是我们把管道切到新 org 之后发生的事，也是为什么这次故障看起来像凭空冒出来的。

## 修复

```diff
-# Bulk v2 多态关系表头：
-# ObjectType:RelationshipName.IndexedFieldName
-CONTACT_POINT_PARENT_EXT_ID = 'Account:Parent.ApplicantId__c'
+# Bulk v2 关系表头：RelationshipName.IndexedFieldName
+CONTACT_POINT_PARENT_EXT_ID = 'Parent.ApplicantId__c'
```

一个常量，email、phone、address 三个 builder 共用。三周，八个字符。

## 小结

**先信报错，再信你脑子里那套系统模型。** "type is not needed for non polymorphic foreign key references" 一点都不晦涩：它点了字段名，陈述了事实，还告诉你该删什么。我们把它当成一个需要被解释掉的症状，而不是一条需要被执行的指令——因为我们已经先入为主地认定这个字段**是**多态的。

**`0 processed / 0 failed` 是 schema 错误，不是数据错误。** 不同的计数器组合对应完全不同的排查方向。一行都没被读过的时候，别去找脏数据。

**在采信一个说法、或者被它卡住之前，先复现它。** 「我们成功插入了」这句话是善意的，而且在*某个工具里*几乎肯定是真的。Data Loader、Workbench、Bulk v1 接受的表头语法，Bulk v2 REST 并不接受。另一套机制里的成功，不构成对你这套机制的证据。

**扰动输入去收割报错。** 五个变体花了 90 秒，直接从实现本身拿到了解析器的语法。这比三周的翻元数据加起草升级邮件划算得多。

**升级问题要带复现，不要带理论。** 我们差点为一个最终完全无关的元数据不一致提了平台工单。一张测试矩阵就能避免这件事——顺便还能省下另一个团队的时间。
