---
title: "CI 脚本自救指南：从 gh CLI 查失败 job 到 set -euo pipefail"
date: 2026-07-27
categories: [engineering, ci-cd, shell]
tags: [github-actions, gh-cli, bash, jq, shell-scripting, ci-observability]
---

# CI 脚本自救指南：从 gh CLI 查失败 job 到 set -euo pipefail

这篇笔记记录两个几乎每天都会用到、但很少有人真正拆开讲清楚的 CI 脚本片段：
一个是用 `gh` CLI + `jq` 查询 GitHub Actions 失败 job 的实战命令，
另一个是几乎该出现在每个 shell 脚本开头、却经常被忽略的三件套：`set -euo pipefail`。

---

## Part 1：用 gh CLI 查询失败的 GitHub Actions Job

```bash
env -u GITHUB_TOKEN -u GH_TOKEN gh run view 29978986441 --repo qantasloyalty/edr-nonstandard-etl --json jobs -q '.jobs[] | select(.conclusion=="failure") | {name, databaseId}'
```

### 30秒版本

这行命令做的事就是：别再去网页上一个个点开 job 看红叉了，用 API 把"谁挂了"这件事变成一行结构化数据。
`gh run view <id>` 拉取这次 workflow run 的完整 job 树，`--json jobs` 让它吐 JSON 而不是人类友好的表格，
`jq` 再从这堆 JSON 里筛出 `conclusion == "failure"` 的 job，只留下名字和数据库 ID——方便接下来直接
`gh run view --log --job=<id>` 去调日志。本质上这是**把 CI 状态当数据库来查询**，而不是当网页来阅读。

### Under the Hood

**`env -u GITHUB_TOKEN -u GH_TOKEN`**：先把这两个环境变量从子进程环境里"挖掉"。`gh` CLI 的认证优先级是：
环境变量 > `gh auth login` 存的 keyring/config 里的 token。如果机器上同时装了别的工具（CI runner、别的脚本）
污染了这两个变量，指向了错误账号或过期 token，`gh` 会优先用错的那个，导致 403 或权限不匹配。`-u` 强制
这次调用退回去用 `gh auth login` 存的凭证——这是显式覆盖隐式全局状态的防御性写法。

**`gh run view <id> --json jobs`**：底层打的是 GitHub REST API 的
`GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs`。返回结构里每个 job 有 `status`
（`queued`/`in_progress`/`completed`）和 `conclusion`（`success`/`failure`/`cancelled`/`skipped`/`null`）
两个正交字段——这是个常见的坑：`status` 讲的是"跑完没"，`conclusion` 讲的是"跑得好不好"，两者必须联合
判断，不然可能把还在跑的 job 误判成失败。

**`-q '...'`**：是 `--jq` 的简写，`gh` 内置了 jq 解析器。`select(.conclusion=="failure")` 是 jq 的过滤
谓词，对数组做流式扫描，`O(n)` 遍历 job 数，通常个位数到几十，毫秒级。

### 面试官追问链

**Q1: 如果 run 还没跑完就查询，conclusion 是什么？会不会漏报？**
`conclusion` 是 `null`，`select` 天然过滤掉它——不会误报，但也不会告诉你"还有 job 在跑，现在下结论太早"。
生产脚本得先检查外层 run-level 的 `status == "completed"`。

**Q2: 有没有 rate limit 风险？**
有。`gh` 走 REST API，认证用户配额 5000 req/hour。单次调用没事，但塞进每分钟轮询的看板脚本，几十个 repo
乘起来很快撑爆。正解是用 GitHub Webhooks（`workflow_run` 事件）做推送式通知，而不是轮询拉取。

**Q3: jq 的 select 在超大 job 列表下会不会慢？**
不会。jq 是流式处理，线性扫描几百个元素仍是微秒级，瓶颈根本不在本地 filter，而在 API 的网络往返延迟
（200ms-1s）。优化重点该放在减少 round-trip 数，而不是本地逻辑。

**Q4: gh 命令本身失败会怎样？**
静默失败风险很大。如果没检查 `$?`，下游脚本可能拿着空结果当成"没有失败的 job"——典型的错误吞噬故障
模式，该用 `set -euo pipefail`（见下文）或显式检查退出码来防。

**Q5: databaseId 和 job name 是什么关系？**
`databaseId` 是全局唯一的稳定数字主键，`name` 可以重复（matrix job 会有同名多实例）。拿到 id 后用
`gh run view --job=<id> --log-failed` 才能精确定位到失败的具体 step——先查索引再查详情页的标准套路。

### 大厂怎么用

Google 的 TAP 和 Meta 的 Sandcastle 早就不让人工去 grep 日志了——都是结构化事件流 + 自动化根因聚类。
核心模式和这条命令的哲学一样：把 CI 状态当一等公民数据对象。更进一步，大厂通常还会做**失败聚类**——
一次变更炸了 50 个 job，可能只是 1 个共享依赖挂了导致连锁失败，不聚类展示会让值班工程师被淹没在重复
告警里（Alert Fatigue 在 CI 领域的体现）。

### 高风险场景怎么变

金融交易系统里，CI 失败检测的紧迫度被拉满——部署失败没被秒级发现，风控模块带 bug 跑几分钟可能就是
几百万美金敞口。这时轮询模式直接淘汰，换成：**同步阻塞式 deployment gate**（CI 不全绿不允许部署）+
**Canary 自动回滚**（生产指标异常触发秒级回滚，不依赖人工跑命令排查）。

### 2026年在卷什么

- AI 驱动的失败归因（Copilot for CI、Sentry CI insight 等自动生成"大概率是 XX 依赖冲突"的诊断）
- CI 可观测性接入 OpenTelemetry，和生产监控栈打通，不再是孤岛
- `gh` CLI 往 GraphQL 迁移，复杂嵌套查询一次拉全，减少 round-trip
- 纯轮询 + Slack webhook 拼凑告警的老办法正在被认为是 legacy

### 跨学科视角

这套"过滤噪声、只看真正异常"的思路，和医学上的**分诊（Triage）系统**是一回事：急诊室按病情严重程度
分类处理，`select(.severity=="critical")` 本质上就是同一个操作。CI 可观测性、急诊分诊、传染病溯源、
金融风控告警，最终都在解决同一个数学结构：信号和噪声的比例。

### 一句话总结

> CI 可观测性的本质不是把日志打印得更好看，而是把运行状态当成可查询的结构化数据——conclusion 字段的
> 语义正确性，永远比 jq 写得多花哨更重要。

---

## Part 2：set -euo pipefail 到底在干什么

```bash
set -euo pipefail
```

### 30秒版本

Bash 默认的错误处理哲学是"能跑就跑，挂了也装看不见"——一条命令失败了，脚本假装无事发生，继续执行下
一条，直到某个后果灾难性的地方才炸。`set -euo pipefail` 是给 bash 装上一个熔断器，让它从"打不死的
小强"变成"一点异常就立刻停下来"的保守模式。这是写生产级 shell 脚本的最低及格线，不加这行的脚本本质
上是在裸奔。

### Under the Hood

**`-e` (errexit)**：任何命令退出码非 0，脚本立即终止。但 `&&`、`||`、`if` 条件里、管道非最后一个命令
的返回值，都不会触发 `-e`。比如 `foo() { false; }; foo && echo ok` 里 `false` 的失败不会让脚本退出，
因为它是 `&&` 左边的条件判断。

**`-u` (nounset)**：引用未定义变量时报错退出，而不是静默展开成空字符串。默认行为下
`rm -rf $UNDEFINED_VAR/*` 如果变量没设置，会展开成 `rm -rf /*`——不是段子，是真实发生过的删库事故
模式。`-u` 把这种低级错误从运行时灾难变成立刻报错。

**`-o pipefail`**：三者里最容易被忽略但最重要。默认情况下 `cmd1 | cmd2 | cmd3` 的退出码只看最后一个
命令——`false | true` 的退出码是 `0`。`pipefail` 让整条管道任意一节失败就失败，这在
`gh run view ... | jq ...` 这类管道场景下是必须开的开关，否则前面挂了但后面处理了空输入还是 exit 0，
失败检测脚本会检测不到自己的失败。

### 面试官追问链

**Q1: -e 有哪些"看起来会退出但实际不会"的坑？**
除了 `&&`/`||`/`if` 条件外，函数返回值赋值给变量（`x=$(may_fail)`）在某些版本表现不一致；subshell 里
的失败也不会传播到父 shell 的 `-e` 状态。

**Q2: -u 会不会误伤合法的"变量可能不存在"场景？**
会。解法是 `${VAR:-default}` 或 `${VAR:-}` 显式给默认值，把"隐式未定义"变成"显式声明为空"。

**Q3: 这三个 flag 和 trap ERR 是什么关系？**
`set -e` 只负责退出，不负责善后。生产脚本通常配 `trap cleanup EXIT` 在退出前做资源清理（删临时文件、
释放锁、发告警）——熔断器和应急预案，分工不同，缺一不可。

**Q4: 后台进程场景下 -e 还管用吗？**
不管用。后台进程失败不会触发前台脚本的 `-e`，因为 shell 立刻返回控制权。必须显式 `wait $pid` 检查
`$?`，或用 `wait -n` 拿到任意后台任务的失败信号。

**Q5: 如果必须允许某条命令失败怎么办？**
用 `cmd || true` 或 `if ! cmd; then ...; fi` 显式声明"这条允许它挂"，而不是整个关掉 `-e`。

### 大厂怎么用

Google Shell Style Guide 强制所有生产脚本开头必须有 `set -euo pipefail`，并用 ShellCheck 做 CI 门禁，
不合规直接拦 PR。因为 shell 脚本在大厂基础设施里承担大量胶水层角色，隐式失败往往导致"流水线跑完了
却什么都没做"，比崩溃更难排查——日志显示成功，实际是假成功。

### 高风险场景怎么变

`set -euo pipefail` 只是必要不充分条件。关键系统的部署脚本通常还会叠加：强制 `set -x` 做审计日志、
幂等性设计（中途失败重跑必须能安全续跑）、以及直接禁止裸 shell 进生产部署路径，改用 Terraform/Ansible
这类带状态机和回滚语义的工具。

### 2026年在卷什么

ShellCheck 集成进 pre-commit hook 已是标配；"no bare shell in CI"原则越来越流行，复杂逻辑迁移到
Python/Go，shell 只保留在最简单的胶水调用层；`shfmt` + `shellcheck` 是 shell 生态的事实 lint/format
标准。

### 跨学科视角

这套机制和核电站的**失效安全设计（fail-safe design）**是同一个思想内核。核反应堆的控制棒默认设计成
"断电就自动落下、反应停止"——把默认状态设成安全状态，而不是要求操作员时刻警觉去手动叫停。
`set -euo pipefail` 把 bash 的默认行为从"乐观假设一切正常"翻转成"悲观假设任何异常都值得立刻停下"。

### 一句话总结

> `set -euo pipefail` 本质上不是三个 flag，而是把 bash 从"沉默容错"强制掰成"快速失败"——但它堵不住
> 后台进程和函数返回值这两个天生盲区，真正的生产纪律永远是知道这行代码堵住了什么、没堵住什么。
