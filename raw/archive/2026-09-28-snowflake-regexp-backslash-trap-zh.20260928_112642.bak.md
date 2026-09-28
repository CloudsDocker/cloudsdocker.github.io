---
title: "无报错、零结果：Snowflake 正则静默失败的生产事故复盘"
date: 2026-09-28
categories: [tech]
tags: [Snowflake, SQL, Regex, Production-Incident, Data-Engineering]
header:
  image: /assets/images/bg/20251014_150456.jpg
---

> "The most dangerous bugs are the ones that succeed." — 每一个被零行 SUCCESS 骗过的工程师

# 无报错、零结果：Snowflake 正则悄悄吃掉反斜杠的生产事故

## 故事：一个连续跑了 15 次 SUCCESS 却没搬过一行数据的 Job

上周我接手了一个 iLearn 考勤同步 DAG 的问题——Airflow 上一切绿灯，control table 里全是 SUCCESS，Salesforce 那边一行考勤数据都没有。

查了 Snowflake 控制表，15 个连续的运行记录长这样：

| 状态 | 抽取行数 | Upsert 行数 |
|------|---------|------------|
| SUCCESS | 0 | 0 |
| SUCCESS | 0 | 0 |
| … ×15 | 0 | 0 |

零行 SUCCESS 是 data pipeline 里最阴险的 failure mode：不报错，不告警，watermark 照样推进，数据窗口静静地滑过去。等你发现时，已经欠了一周的数据。

## 根因：两层解析器的反斜杠陷阱

我们的 Python DAG 代码里有一条 Snowflake SQL：

```python
# Python 源码
cur.execute("""
    ...
    AND REGEXP_LIKE(gi."itemname", '^Week\\s+[0-9]+$', 'i')
    ...
""")
```

看起来没问题对吧？`\\s` 在 Python 里就是 `\s`，是"空白字符"的正则 class。

**但 Snowflake 不是 Python。**

这条 SQL 到达 Snowflake 之前，要过两道解析：

```
Python 源码          SQL 文本 (on the wire)       Snowflake 字符串值        正则引擎
  '\\s'        →          '\s'              →          's'            →    字面量 s
```

### 第一层：Python 字符串

`'\\s'` → Python 识别 `\\` 为一个反斜杠字符 → 生成字符串 `\s`

### 第二层：Snowflake SQL 字符串字面量

SQL 引擎收到 `'\s'`。它检查：`\s` 是已知的转义吗？

| 转义 | Snowflake 认识吗 | 结果 |
|------|:---:|------|
| `\\` | ✅ | 一个 `\` |
| `\'` | ✅ | 一个 `'` |
| `\n` | ✅ | 换行 |
| **`\s`** | **❌** | **反斜杠被丢弃，只剩 `s`** |

**Snowflake 对未知转义的处理方式是：静默丢弃反斜杠，保留后面的字符。不报错，不警告。**

所以正则引擎最终收到的 pattern 是 `^Weeks+[0-9]+$` —— 匹配的是一个或多个字母 `s` 跟在 `Week` 后面，而不是空白字符。`Week 4`？不匹配。`Week 01`？不匹配。

## 验证：从 Snowflake 查询历史抓到"作案现场"

我们可以用 `GET_QUERY_OPERATOR_STATS` 看 Snowflake 实际编译的 filter：

```sql
SELECT operator_id, operator_type, operator_attributes
FROM TABLE(GET_QUERY_OPERATOR_STATS('<query_id>'))
WHERE operator_type = 'Filter';
```

结果：

```
filter_condition: GI."itemname" REGEXP_LIKE '^Weeks+[0-9]+$'
```

`\s` 确确实实变成了字面量 `s`。

同一个时间窗口，两种 pattern 的对比：

| Pattern | 匹配的行数 |
|---------|-----------|
| `^Weeks+[0-9]+$`（被吃掉后） | **0** |
| `^Week[[:space:]]+[0-9]+$`（POSIX） | **1,887** |

## 修复：用 POSIX 字符类，彻底绕过反斜杠

```sql
-- ❌ 之前：反斜杠被 Snowflake 字符串解析器吞掉
AND REGEXP_LIKE(gi."itemname", '^Week\s+[0-9]+$', 'i')

-- ✅ 之后：POSIX 字符类，零个反斜杠
AND REGEXP_LIKE(gi."itemname", '^Week[[:space:]]+[0-9]+$', 'i')
```

`[[:space:]]` 是 POSIX 字符类，和 `\s` 语义一样（匹配空白），但整个写法里没有反斜杠，所以没有任何一层解析器能吃掉它。

### 对照表

| 你的意图 | ❌ 别用 | ✅ 改用 |
|---------|--------|--------|
| 空白 | `\s` | `[[:space:]]` |
| 数字 | `\d` | `[[:digit:]]` 或 `[0-9]` |
| 字母数字 | `\w` | `[[:alnum:]]` |

## 为什么这比 FAILED 更危险

一个 FAILED 的 DAG run 会：
- 触发告警邮件
- 不推进 watermark（下次重试同一个窗口）
- 在 control table 留下错误信息

一个 0 行 SUCCESS 的 DAG run 会：
- **不触发任何告警**
- **watermark 照常推进**（数据窗口永久丢失）
- 看起来一切正常

当你发现时，已经有 15 个窗口的数据白白滑过去了。修复 SQL 后还不够——你必须 replay 那些丢失的窗口：

```json
{"jobs": ["attendance"], "watermark_from": 1789633681, "watermark_to": 1790238481}
```

但如果你在修复 SQL **之前** replay，只会再写一条 SUCCESS + 0 rows 的记录。

## 为什么单元测试没拦住

我们的测试是这样写的：

```python
def test_extract_attendance_sql_filters():
    ...
    assert 'REGEXP_LIKE' in sql  # ← 这能拦住什么？
```

`'REGEXP_LIKE' in sql` 只检查函数名存在，完全不检查 pattern 的内容。修复后的测试：

```python
assert "REGEXP_LIKE(gi.\"itemname\", '^Week[[:space:]]+[0-9]+$', 'i')" in sql
assert '\\s' not in sql  # 确保没有反斜杠 class 残留
```

## 给自己的 Review Checklist

以后每次在 Python 里写要发往 Snowflake 的 `REGEXP_LIKE`：

- [ ] SQL 文本里有 `\s` / `\d` / `\w` 吗？→ 换成 POSIX class
- [ ] 单元测试是否 assert 了完整的 pattern 字符串（不只是函数名）？
- [ ] 跑一次后如果 0 rows，是去 `GET_QUERY_OPERATOR_STATS` 看编译后的 filter 了吗？
- [ ] 如果是 `.sql` 文件（不经 Python），`\\s` 是安全的（SQL 解析器把 `\\` 变成 `\`）。但 `[[:space:]]` 仍然更稳。

## 结语

这个 bug 的本质不是"正则写错了"——如果你在 Python 里 `re.match('^Week\\s+[0-9]+$', 'Week 4')`，它是能匹配的。Bug 在于**你以为只有一层解析器，实际上有两层**，而中间那层会静默吞掉你的 metacharacter。

在数据工程里，最可怕的不是报错，而是"成功地什么都没做"。

---

*如果你也在 Snowflake 上写 REGEXP_LIKE，检查一下你的反斜杠还在不在。*
