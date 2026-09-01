---
title: "curl -d 里塞多行 CSV，为什么 JSON 直接炸了"
date: 2026-08-12
categories: [engineering, shell, debugging]
tags: [curl, json, jq, salesforce, zsh, debugging]
---

调试本地 `ditapi-s-salesforce-v1` 服务的 bulk-load 接口时，一条看起来很正常的 `curl -d '...'` 命令直接把 JSON 解析炸了。根因很典型，也很容易踩——记录一下排查过程和顺手抽出来的 zsh function。

## 问题命令长什么样

```bash
curl -sv -X POST http://localhost:8003/bulk-load \
  -H "x-salesforce-org: S360UAT" \
  -H 'Content-Type: application/json' \
  -d '{"csv_data":"StaffId__c,FirstName,LastName,
    RecordType.Name\n999999901,TESTASC,STAFFEXTID,Staff","salesforce_object":"Account","external_id_field_name":"StaffId__c"}' \
  2>&1 | tail -30
```

意图很简单：调用本地服务，往 Salesforce **S360UAT** 组织的 `Account` 对象做批量 upsert，用 `StaffId__c` 作为外部 ID 字段匹配/创建记录。

## 血泪提醒：真实换行 ≠ 字面量 `\n`

问题出在 `-d` 里的 JSON 字符串混用了两种东西：

1. `LastName,` 后面是终端里**真实敲出来的换行**（多行粘贴导致），不是转义符 `\n`。JSON 字符串内部**不允许出现未转义的原始换行符**——严格的 parser 会直接报 "Invalid control character" 之类的错误。
2. 换行后带了 4 个空格缩进（格式化粘贴带来的），这几个空格混进了 CSV 表头，变成 `"    RecordType.Name"`，前面带空格。就算 JSON 侥幸解析成功，后端按列名映射时也大概率匹配不上。
3. `999999901` 前面那个才是真的字面量 `\n`，这才是你想要的"换行分隔 CSV 行"的写法。

根因：把多行 CSV 直接摁进单行 `-d '...'` 字符串里，是最容易踩这个坑的写法——真实换行 vs `\n` 转义，人眼在终端里根本分不清。

## 正确姿势一：heredoc 写临时文件

```bash
cat > /tmp/payload.json <<'EOF'
{
  "csv_data": "StaffId__c,FirstName,LastName,RecordType.Name\n999999901,TESTASC,STAFFEXTID,Staff",
  "salesforce_object": "Account",
  "external_id_field_name": "StaffId__c"
}
EOF

curl -sv -X POST http://localhost:8003/bulk-load \
  -H "x-salesforce-org: S360UAT" \
  -H 'Content-Type: application/json' \
  --data @/tmp/payload.json 2>&1 | tail -30
```

`<<'EOF'`（引号包住 EOF）会让 heredoc **不做变量展开**，原样写入文件。但 JSON 字符串内部的换行还是得手写成字面量 `\n`，不能真敲回车。

## 正确姿势二：真实多行 CSV 用 `jq -Rs` 自动转义（更不容易出错）

```bash
CSV=$(cat <<'EOF'
StaffId__c,FirstName,LastName,RecordType.Name
999999901,TESTASC,STAFFEXTID,Staff
EOF
)

jq -n --arg csv "$CSV" \
  '{csv_data: $csv, salesforce_object: "Account", external_id_field_name: "StaffId__c"}' \
  > /tmp/payload.json

curl -sv -X POST http://localhost:8003/bulk-load \
  -H "x-salesforce-org: S360UAT" \
  -H 'Content-Type: application/json' \
  --data @/tmp/payload.json 2>&1 | tail -30
```

精髓在 `jq -n --arg csv "$CSV" '{...}'`：真实换行的多行字符串扔给 `--arg`，jq 自动帮你转成合法转义，彻底不用担心手误。以后凡是"CSV / 多行文本塞进 JSON"的场景，都优先用这招。

## curl flags 拆解

| flag | 作用 |
|---|---|
| `-s` (silent) | 不显示进度条 |
| `-v` (verbose) | 打印请求/响应完整过程：`>` 是发出去的请求头，`<` 是收到的响应头，方便看 4xx/5xx、header 对不对 |
| `-X POST` | 显式指定方法（带 `-d` 时 curl 会自动推断成 POST，但显式写更清晰） |
| `2>&1 \| tail -30` | `-v` 的详细信息走 stderr，需要 `2>&1` 重定向到 stdout 才能被 `tail` 截到；`tail -30` 避免刷屏 |

## 抽成 zsh function：dcurl

"打请求 + 顺手看服务端日志尾部"这个模式值得抽成命名函数，和 `gacp`/`klog` 一个套路：

```bash
# 用法: dcurl <endpoint> <json-file> [logfile]
dcurl() {
  local endpoint="$1"
  local payload="$2"
  local logfile="${3:-/tmp/ditapi-s-salesforce-v1.log}"

  command -v jq >/dev/null || { echo "需要 jq"; return 1; }

  curl -sv -X POST "http://localhost:8003${endpoint}" \
    -H "x-salesforce-org: S360UAT" \
    -H 'Content-Type: application/json' \
    --data @"$payload" 2>&1 | tail -30

  echo "---LOG---"
  tail -40 "$logfile"
}
```

后续可以扩展：支持任意 endpoint + 任意 header + 自动 pretty-print JSON 响应；把 `x-salesforce-org` 做成参数方便切 UAT/PROD；甚至在 Airflow DAG 里复用同一套 payload 构造逻辑，避免 bash 和 Python 各写一份。

## 小结

一句话总结：**多行文本永远不要手工塞进单行 shell 字符串**，交给 `jq -Rs` / `jq -n --arg` 处理转义，比人眼分辨"这是真换行还是 `\n`"靠谱一百倍。
