---
title: 你能在 60 秒内找出“该你审、已阻塞、快过期”的所有 PR 吗？
header:
    image: /assets/images/bg_raw/BingWallpaper (11).jpg
date: 2026-10-01
tags:
 - github-cli
 - git
 - pull-requests
 - shell
 - developer-productivity
permalink: /blogs/tech/zh/find-prs-with-gh
lang: zh
layout: single
category: tech
---
> “空谈廉价，拿出代码。” — Linus Torvalds

# 你能在 60 秒内找出“该你审、已阻塞、快过期”的所有 PR 吗？

*别把 PR 列表当成一张表：终端里至少有三条可用的查询路径。*

“搜 PR，不就是 `gh pr list` 加个 `--search` 吗？”

这句话只对了一半。你当然能这样做；但当你不知道 PR 在哪个仓库、需要查它改了什么文件，或者网络不可用时，换的不是参数，而是查询路径和数据来源。

下面这套分法能让你在一分钟内写出“该我审”“被阻塞”“久未更新”的查询，并知道什么时候该从 `gh` 切到本地 `git`。

先跑一条最常用的。把 `OWNER/REPO` 换成目标仓库：

```bash
gh pr list --repo OWNER/REPO --state open \
  --search 'review-requested:@me' \
  --json number,title,updatedAt,url
```

它找的是**明确请求你 review 的开放 PR**。再加上团队已有的标签和日期约定，就能把待办从“列表里好像有几条”变成可执行的筛选。

| 你要找什么 | 可直接追加的条件 | 它表达的事实 |
|---|---|---|
| 该你审 | `--search 'review-requested:@me'` | 你被请求审查 |
| 已阻塞 | `--label blocked` | 仓库用 `blocked` 标签标记阻塞 |
| 快过期 | `--search 'updated:<YYYY-MM-DD'` | 自团队定义的陈旧阈值以来没有更新 |

**“快过期”不是 GitHub 的内建状态，而是团队对“陈旧”的业务定义。** 先按团队的陈旧策略计算 `YYYY-MM-DD`，再运行查询；标签名和是否要排除 draft，也应当按你们的规则调整。

这张表就是最值得截图的部分：把 PR 工作流里的自然语言，翻译成可验证的筛选条件。

## 一个仓库内，先用 `gh pr list`

假设你改过一个依赖约束，现在只记得关键词和大概文件名。网页翻页很磨人；终端里先从仓库边界开始：

```bash
gh pr list --repo OWNER/REPO --author @me --state all \
  --search 'sftp pyproject'
```

`--author @me` 表示当前登录用户；`--state all` 很关键。`gh pr list` 默认只列开放 PR，漏掉已合并 PR 是这里最常见的误判。

如果标题和描述里没留下关键词，先换成文件名或更稳定的术语：

```bash
gh pr list --repo OWNER/REPO --author @me --state all \
  --search 'pyproject.toml'
```

还找不到，再把候选拉成 JSON，在本地按标题过滤：

```bash
gh pr list --repo OWNER/REPO --author @me --state all \
  --limit 100 --json title,number,url \
  --jq '.[] | select(.title | test("sftp"; "i"))'
```

这里有个容易混淆的边界：`--search` 使用 GitHub 的 PR 搜索语法；它不是“搜索所有改动过的文件内容”。因此，拿文件路径或代码细节做唯一检索条件，结果未必完整。

日期、标签、审查人和目标分支都可以叠加：

```bash
# 某段时间内创建，并且带关键词
gh pr list --repo OWNER/REPO --author @me --state all \
  --search 'created:YYYY-MM-DD..YYYY-MM-DD sftp'

# 团队陈旧阈值之后更新过
gh pr list --repo OWNER/REPO --state all \
  --search 'updated:>YYYY-MM-DD'

# 同时具备多个标签
gh pr list --repo OWNER/REPO --label bug --label hotfix

# 只看合入某分支的 PR
gh pr list --repo OWNER/REPO --base main
```

多个 `--label` 是叠加条件：要同时命中。审查维度也可以写进搜索：`reviewed-by:USERNAME` 查某人审过的 PR，`review-requested:@me` 查需要你处理的 PR。

找到编号之后，终端不必退出工作流：

```bash
gh pr diff PR_NUMBER --repo OWNER/REPO
gh pr view PR_NUMBER --repo OWNER/REPO
gh pr checkout PR_NUMBER --repo OWNER/REPO
gh pr review PR_NUMBER --approve
gh pr review PR_NUMBER --comment --body 'LGTM'
gh pr review PR_NUMBER --request-changes --body '请检查版本约束是否符合预期'
gh pr view PR_NUMBER --web --repo OWNER/REPO
```

## 不知道仓库在哪？换成 `gh search prs`

`gh pr list` 的强项是“这个仓库里的 PR”。当记忆只剩下“我曾在某个仓库改过这个依赖”，应该换成跨仓库搜索：

```bash
gh search prs 'sftp pyproject' --owner OWNER --author @me
gh search prs 'sftp' --owner OWNER --language python
gh search prs 'sftp' --owner OWNER --merged
```

原始笔记里把两者说成“搜索深度不同”。更准确的说法是：它们首先差在**作用域和查询接口**。`gh search prs` 面向 GitHub 的跨仓库 PR 搜索；`gh pr list` 面向一个仓库的 PR 列表，并可附带搜索条件。关键词具体匹配哪些可搜索字段，应以 GitHub 当前的搜索语法为准，不要把它当作代码 diff 搜索器。

| 你知道什么 | 优先工具 | 为什么 |
|---|---|---|
| 仓库确定 | `gh pr list` | 仓库边界已知，筛选直接 |
| 仓库不确定 | `gh search prs` | 能跨仓库收集候选 |
| 已知 PR 编号且本地有历史 | `git log --grep` | 不必发网络请求 |
| 要看评论、审查或 CI | `gh pr view` | 这些是 PR 元数据，不在 Git 提交里 |

**PR 搜索至少有三条查询路径：仓库内 PR 列表、跨仓库 PR 搜索、本地 Git 提交历史。**

我的立场是：不要急着做一个“万能 PR 搜索命令”。最有价值的快捷方式，是把“我现在知道什么”编码进去。反方的理由也成立：固定流程、固定仓库的团队，用一个统一 alias 可以减少输入和培训成本。只是 alias 一旦试图猜测仓库、状态、时间范围和责任人，省下的击键往往会以漏结果的形式还回来。

常用且稳定的默认条件，可以做成 alias：

```bash
gh alias set my-prs 'pr list --author @me --state all'
gh my-prs --repo OWNER/REPO --search 'sftp'
```

如果某个仓库确实是你的固定工作台，也可以把 `--repo OWNER/REPO` 写进 alias；代价是它会把搜索范围悄悄锁死。

## 文件级问题，`gh api graphql` 是检查器，不是魔法搜索

当你已经拿到一批 PR，却要确认各自改过哪些文件，GraphQL 能直接取回文件路径：

```bash
gh api graphql -f query='
{
  repository(owner: "OWNER", name: "REPO") {
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

它会检查最近一批已合并 PR 的前几个文件，而不是在服务端替你搜索“所有改过某文件的 PR”。结果多于 `last: 10` 或每个 PR 多于 `first: 5` 个文件时，还要处理分页。这个限制很重要：GraphQL 给你的是可组合的数据，不会自动替你定义“查全”。

若想交互挑选 PR，`fzf` 很顺手：

```bash
gh pr list --repo OWNER/REPO --author @me --state all --limit 50 \
  --json number,title --jq '.[] | "\(.number)\t\(.title)"' \
  | fzf --delimiter=$'\t' --with-nth=2.. \
        --preview 'gh pr view {1} --repo OWNER/REPO' \
  | cut -f1 \
  | xargs -I{} gh pr view {} --web --repo OWNER/REPO
```

## 网络断了，Git 历史还有一条路

已知 PR 编号时，本地仓库可以直接查 merge commit：

```bash
git log --grep='#PR_NUMBER' -n 5
git log --grep='#PR_NUMBER' -n 1 -p
git log --grep='#PR_NUMBER' --merges -n 5
git log --grep='sftp' --author='NAME' --oneline -n 10
git log --grep='#PR_NUMBER' -n 1 --stat
```

很多通过 merge commit 合并的 PR，会把 PR 编号写进提交信息，因此这招不需要 GitHub API。它搜的是**本地提交消息**，不是 PR 标题、评论、标签或 CI 状态。

也别把它当成必中的离线后门：squash merge、rebase merge、自定义提交信息，或者本地 clone 没有完整历史，都可能让 PR 编号消失。它适合“我有编号，想快速确认改了什么”；没有编号时，`gh` 的 PR 元数据通常更合适。

如果你的仓库把“阻塞”放在标签里、把“陈旧”留给日期判断，今天就按团队策略算出一次阈值，跑一次开头那张表里的三条查询。然后问自己一个更难的问题：你们的 PR 状态，到底有没有被写进机器能检索的字段，还是只存在某个人的记忆里？
