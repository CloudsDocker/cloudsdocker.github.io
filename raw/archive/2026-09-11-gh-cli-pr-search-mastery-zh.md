---
title: "GitHub CLI 搜 PR 的十八般武艺：从入门到骚操作"
date: 2026-09-11
categories: [engineering, cli]
tags: [github-cli, git, productivity, pr-workflow, shell]
---

# GitHub CLI 搜 PR 的十八般武艺：从入门到骚操作

> 场景：你在一个大型 monorepo 里改了 `pyproject.toml` 的 sftp 版本，PR 合了，过了两个月想找回来。网页上翻 PR 列表翻到手酸？`gh` 一行命令搞定。

---

## Part 1: 最直接的答案

```bash
gh pr list --repo qantasloyalty/edr-airflow-dags --author @me --state all --search "sftp pyproject"
```

拆解一下：

| 参数 | 干嘛的 |
|------|--------|
| `--author @me` | 只看你自己创建的 PR。`@me` 是魔法词，自动替换成你当前登录的 GitHub 用户名 |
| `--state all` | 包含 open + closed + merged。**不加的话默认只显示 open**，这是最常见的坑 |
| `--search "sftp pyproject"` | 用 GitHub 搜索语法在标题/描述里模糊匹配关键词 |

### 搜不到怎么办？

如果标题里没写 "sftp"，换个思路——按文件名搜或者暴力 grep：

```bash
# 按文件名关键词搜
gh pr list --repo qantasloyalty/edr-airflow-dags --author @me --state all \
  --search "pyproject.toml"

# 暴力拉全部再 grep（简单粗暴但有效）
gh pr list --repo qantasloyalty/edr-airflow-dags --author @me --state all \
  --limit 100 --json title,number,url | grep -i sftp
```

---

## Part 2: 更多过滤技巧

### 按日期筛

`--search` 里直接塞 GitHub 搜索语法：

```bash
# 2025年6月之后创建的
gh pr list --repo qantasloyalty/edr-airflow-dags --author @me --state all \
  --search "created:>2025-06-01"

# 某个时间段内的
gh pr list ... --search "created:2025-06-01..2025-08-31 sftp"

# 最近更新过的
gh pr list ... --search "updated:>2025-09-01"
```

### 按 label 筛

```bash
gh pr list ... --label "bug"
gh pr list ... --label "hotfix" --label "production"   # 多个 label = AND 关系
```

### 按 reviewer 筛

```bash
gh pr list ... --search "reviewed-by:zhangsan"

# 反过来，找别人请你 review 的
gh pr list ... --search "review-requested:@me"
```

### 按 base branch 筛

```bash
gh pr list ... --base main        # 只看合进 main 的
gh pr list ... --base develop
```

> 💡 **隐藏技巧**：`--search` 本质就是 GitHub 网页搜索框的语法，网页上能搜的这里都能用。把 `--search` 当作"万能后门"就对了。

### 输出格式控制

```bash
# JSON 输出，方便管道处理
gh pr list ... --json number,title,state,url,createdAt

# 用 --jq 直接过滤 JSON（不需要外部 jq）
gh pr list ... --json number,title,url --jq '.[] | select(.title | test("sftp"; "i"))'

# 只要 PR 编号
gh pr list ... --json number -q ".[].number"
```

---

## Part 3: 找到 PR 后的快速操作

假设搜到了 PR `#142`：

```bash
# 🔍 快速看 diff（不用 checkout，直接看改了啥）
gh pr diff 142 --repo qantasloyalty/edr-airflow-dags

# 👀 看 PR 详情（描述、review 状态、CI 结果）
gh pr view 142 --repo qantasloyalty/edr-airflow-dags

# 📂 想在本地跑？一键 checkout 到那个分支
gh pr checkout 142 --repo qantasloyalty/edr-airflow-dags

# 💬 直接在命令行加 review comment
gh pr review 142 --approve
gh pr review 142 --comment --body "LGTM 🚀"
gh pr review 142 --request-changes --body "pyproject.toml 里版本号锁死了，要用 ~= 吗？"

# 🌐 懒得命令行看？直接弹浏览器
gh pr view 142 --web
```

### 骚操作组合技

搜到之后一条龙——搜 → 浏览器打开第一个结果：

```bash
gh pr list --repo qantasloyalty/edr-airflow-dags --author @me --state all \
  --search "sftp" --json number -q ".[0].number" \
  | xargs -I{} gh pr view {} --web --repo qantasloyalty/edr-airflow-dags
```

批量导出所有匹配 PR 的 diff：

```bash
gh pr list ... --search "sftp" --json number -q ".[].number" \
  | xargs -I{} sh -c 'echo "=== PR #{} ===" && gh pr diff {} --repo qantasloyalty/edr-airflow-dags'
```

---

## Part 4: `gh pr list` vs `gh search prs`——别搞混了

这俩长得像，但定位完全不同：

| | `gh pr list` | `gh search prs` |
|---|---|---|
| **作用域** | 只能搜 **一个 repo** | 可以 **跨所有 repo** 搜 |
| **必须指定 repo** | ✅ 是的 | ❌ 不需要 |
| **搜索深度** | 标题 + GitHub search 语法 | 全文搜索（标题 + 描述 + 评论） |
| **典型场景** | "这个 repo 里我的 PR" | "我在整个 org 里改过 sftp 的 PR" |
| **排序灵活性** | `--sort` 支持有限 | 支持 `--sort` + `--order` 多字段 |
| **速率限制** | 用 REST API，配额宽裕 | 用 Search API，有更严格的速率限制 |

### 跨 repo 搜的例子

```bash
# 在整个 qantasloyalty org 里搜你改 sftp 的 PR
gh search prs "sftp pyproject" --owner qantasloyalty --author @me

# 限定语言
gh search prs "sftp" --owner qantasloyalty --language python

# 只看已合并的
gh search prs "sftp" --owner qantasloyalty --merged
```

> 🎯 **一句话总结**：
> - `gh pr list` = 在**一个抽屉**里翻东西——知道在哪就用它
> - `gh search prs` = 在**整个房间**里找东西——不确定在哪就用它

---

## Part 5: Deep Dive——你可能不知道的高级技巧

### 1. `gh api` 直接调 GraphQL

当 `gh pr list` 的过滤满足不了你时，终极武器是直接用 GraphQL：

```bash
gh api graphql -f query='
{
  repository(owner: "qantasloyalty", name: "edr-airflow-dags") {
    pullRequests(last: 10, states: [MERGED], orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        number
        title
        mergedAt
        files(first: 5) {
          nodes { path }
        }
      }
    }
  }
}'
```

这样能搜到**具体改了哪些文件**的 PR——`gh pr list` 做不到这个粒度。

### 2. `gh alias` 把常用搜索变一键命令

```bash
# 创建一个 alias
gh alias set my-prs 'pr list --author @me --state all'

# 以后用起来
gh my-prs --repo qantasloyalty/edr-airflow-dags --search "sftp"

# 更复杂的 alias，带默认 repo
gh alias set edr-prs 'pr list --repo qantasloyalty/edr-airflow-dags --author @me --state all'

# 一个字都不用多打
gh edr-prs --search "sftp"
```

### 3. 配合 `fzf` 交互式选择

```bash
# 搜出来的 PR 用 fzf 交互选择，选中后直接打开
gh pr list --repo qantasloyalty/edr-airflow-dags --author @me --state all --limit 50 \
  | fzf --preview 'gh pr view {1} --repo qantasloyalty/edr-airflow-dags' \
  | awk '{print $1}' \
  | xargs -I{} gh pr view {} --web --repo qantasloyalty/edr-airflow-dags
```

### 4. JSON 输出 + `jq` 做报表

```bash
# 统计你每个月合了多少 PR
gh pr list --repo qantasloyalty/edr-airflow-dags --author @me --state merged \
  --limit 200 --json mergedAt \
  --jq '[.[] | .mergedAt[:7]] | group_by(.) | map({month: .[0], count: length})'
```

---

## Part 6: Bonus——最被低估的一招：`git log --grep`

所有上面的方法都需要调 GitHub API，都要网络请求。但有一招**纯本地、零延迟**，很多人不知道：

```bash
git log --grep="#12799" -n 5
```

### 为什么能用？

因为 GitHub 合并 PR 时，默认的 merge commit message 长这样：

```
Merge pull request #12799 from feature/fix-sftp-version

Fix sftp version constraint in pyproject.toml
```

PR 编号天然就嵌在 git 历史里。所以 `git log --grep` 本质上是在**本地 git 历史**里搜，不走网络，瞬间出结果。

### 实用变体

```bash
# 搜 PR 编号，看详细 diff
git log --grep="#12799" -n 1 -p

# 搜关键词（不知道 PR 号也行）
git log --grep="sftp" --oneline -n 10

# 只搜 merge commit（过滤掉普通 commit 的噪音）
git log --grep="#12799" --merges -n 5

# 组合：搜关键词 + 只看你的提交
git log --grep="sftp" --author="todd" --oneline -n 10

# 搜到之后想看那个 commit 改了哪些文件
git log --grep="#12799" -n 1 --stat
```

### 什么时候用这招 vs `gh pr list`？

| 场景 | 用谁 |
|------|------|
| 知道 PR 编号，想快速确认内容 | `git log --grep="#12799"` ⚡ |
| 不知道编号，按关键词模糊搜 | `gh pr list --search` |
| 想看 PR 的评论、review、CI 状态 | `gh pr view` |
| 没有本地 clone | 只能用 `gh` |
| 网络不通/飞机上 | `git log` 唯一的选择 ✈️ |

> 🧠 **心智模型**：`git log --grep` 搜的是**代码历史**（commit message），`gh pr list` 搜的是 **GitHub 的 PR 元数据**（标题、描述、label、reviewer）。两个维度，互补不替代。

---

## 速查表

| 我想... | 命令 |
|---------|------|
| 搜我在某 repo 的所有 PR | `gh pr list --repo REPO --author @me --state all` |
| 按关键词筛 | 加 `--search "keyword"` |
| 按日期筛 | `--search "created:>2025-06-01"` |
| 跨 repo 搜 | `gh search prs "keyword" --owner ORG --author @me` |
| 看 diff | `gh pr diff NUMBER --repo REPO` |
| 一键浏览器打开 | `gh pr view NUMBER --web` |
| 创建常用搜索快捷键 | `gh alias set NAME 'pr list ...'` |
| 本地秒搜已知 PR 编号 | `git log --grep="#12799" -n 5` |
| 离线搜关键词 | `git log --grep="sftp" --oneline -n 10` |

---

*工具用对了，效率翻倍。GitHub CLI 的精髓不是替代网页，而是让你在终端里"搜-看-操作"一条龙，手不用离开键盘。*
