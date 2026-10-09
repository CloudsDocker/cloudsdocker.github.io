---
title: "Mastering PR Search with GitHub CLI: From Basics to Power Moves"
date: 2026-09-11
categories: [engineering, cli]
tags: [github-cli, git, productivity, pr-workflow, shell]
---

# Mastering PR Search with GitHub CLI: From Basics to Power Moves

> Scenario: You fixed an SFTP version in `pyproject.toml` two months ago in a large monorepo. The PR is merged and buried. Scrolling through the GitHub web UI? Life's too short. One `gh` command gets you there.

---

## Part 1: The Direct Answer

```bash
gh pr list --repo qantasloyalty/edr-airflow-dags --author @me --state all --search "sftp pyproject"
```

Breaking it down:

| Flag | What it does |
|------|--------------|
| `--author @me` | Only your PRs. `@me` is a magic token — resolves to your authenticated GitHub username |
| `--state all` | Includes open + closed + merged. **Without this, you only see open PRs** — the most common gotcha |
| `--search "sftp pyproject"` | Fuzzy matches keywords in title/description using GitHub search syntax |

### What if it returns nothing?

The title might not contain "sftp". Try alternative approaches:

```bash
# Search by filename keyword
gh pr list --repo qantasloyalty/edr-airflow-dags --author @me --state all \
  --search "pyproject.toml"

# Brute-force: pull everything, then grep
gh pr list --repo qantasloyalty/edr-airflow-dags --author @me --state all \
  --limit 100 --json title,number,url | grep -i sftp
```

---

## Part 2: Advanced Filtering

### By Date

Pipe GitHub search qualifiers straight into `--search`:

```bash
# Created after June 2025
gh pr list --repo qantasloyalty/edr-airflow-dags --author @me --state all \
  --search "created:>2025-06-01"

# Within a date range
gh pr list ... --search "created:2025-06-01..2025-08-31 sftp"

# Recently updated
gh pr list ... --search "updated:>2025-09-01"
```

### By Label

```bash
gh pr list ... --label "bug"
gh pr list ... --label "hotfix" --label "production"   # Multiple labels = AND
```

### By Reviewer

```bash
gh pr list ... --search "reviewed-by:zhangsan"

# Reverse: PRs where YOU were requested as reviewer
gh pr list ... --search "review-requested:@me"
```

### By Base Branch

```bash
gh pr list ... --base main
gh pr list ... --base develop
```

> 💡 **Pro tip**: `--search` accepts the exact same syntax as the GitHub web search bar. Anything you can search on the website works here. Think of `--search` as your universal escape hatch.

### Output Format Control

```bash
# JSON output for piping
gh pr list ... --json number,title,state,url,createdAt

# Built-in jq filtering (no external jq needed)
gh pr list ... --json number,title,url --jq '.[] | select(.title | test("sftp"; "i"))'

# Just the PR numbers
gh pr list ... --json number -q ".[].number"
```

---

## Part 3: Post-Search Actions

Say you found PR `#142`:

```bash
# 🔍 Quick diff (no checkout needed)
gh pr diff 142 --repo qantasloyalty/edr-airflow-dags

# 👀 PR details (description, review status, CI results)
gh pr view 142 --repo qantasloyalty/edr-airflow-dags

# 📂 Want to run it locally? One-command checkout
gh pr checkout 142 --repo qantasloyalty/edr-airflow-dags

# 💬 Review from the command line
gh pr review 142 --approve
gh pr review 142 --comment --body "LGTM 🚀"
gh pr review 142 --request-changes --body "Should we use ~= instead of pinning the version?"

# 🌐 Just open it in the browser
gh pr view 142 --web
```

### Combo Moves

Search → open the first result in browser, one pipeline:

```bash
gh pr list --repo qantasloyalty/edr-airflow-dags --author @me --state all \
  --search "sftp" --json number -q ".[0].number" \
  | xargs -I{} gh pr view {} --web --repo qantasloyalty/edr-airflow-dags
```

Batch-export diffs for all matching PRs:

```bash
gh pr list ... --search "sftp" --json number -q ".[].number" \
  | xargs -I{} sh -c 'echo "=== PR #{} ===" && gh pr diff {} --repo qantasloyalty/edr-airflow-dags'
```

---

## Part 4: `gh pr list` vs `gh search prs` — Know the Difference

These look similar but serve fundamentally different purposes:

| | `gh pr list` | `gh search prs` |
|---|---|---|
| **Scope** | Single repo only | Cross-repo, cross-org |
| **Requires `--repo`** | ✅ Yes | ❌ No |
| **Search depth** | Title + GitHub search qualifiers | Full-text (title + body + comments) |
| **Best for** | "My PRs in this repo" | "Every PR I ever touched sftp in" |
| **Sort flexibility** | Limited `--sort` | Full `--sort` + `--order` |
| **Rate limits** | REST API — generous | Search API — stricter limits |

### Cross-Repo Examples

```bash
# Search across an entire org
gh search prs "sftp pyproject" --owner qantasloyalty --author @me

# Filter by language
gh search prs "sftp" --owner qantasloyalty --language python

# Only merged PRs
gh search prs "sftp" --owner qantasloyalty --merged
```

> 🎯 **The mental model**:
> - `gh pr list` = searching **one drawer** — fast and precise when you know where to look
> - `gh search prs` = searching **the entire room** — use it when you're not sure which repo

---

## Part 5: Deep Dive — Power User Techniques

### 1. `gh api` with GraphQL

When `gh pr list` filters aren't granular enough, go straight to GraphQL:

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

This lets you search by **which files were changed** — something `gh pr list` can't do at all.

### 2. `gh alias` for One-Command Shortcuts

```bash
# Create an alias
gh alias set my-prs 'pr list --author @me --state all'

# Use it
gh my-prs --repo qantasloyalty/edr-airflow-dags --search "sftp"

# Even better — bake in the repo
gh alias set edr-prs 'pr list --repo qantasloyalty/edr-airflow-dags --author @me --state all'

# Now it's just
gh edr-prs --search "sftp"
```

### 3. Interactive Selection with `fzf`

```bash
# Search → interactive fuzzy picker → preview → open in browser
gh pr list --repo qantasloyalty/edr-airflow-dags --author @me --state all --limit 50 \
  | fzf --preview 'gh pr view {1} --repo qantasloyalty/edr-airflow-dags' \
  | awk '{print $1}' \
  | xargs -I{} gh pr view {} --web --repo qantasloyalty/edr-airflow-dags
```

### 4. JSON Output + `jq` for Reporting

```bash
# Count your merged PRs per month
gh pr list --repo qantasloyalty/edr-airflow-dags --author @me --state merged \
  --limit 200 --json mergedAt \
  --jq '[.[] | .mergedAt[:7]] | group_by(.) | map({month: .[0], count: length})'
```

---

## Part 6: Bonus — The Most Underrated Trick: `git log --grep`

Every method above hits the GitHub API — requires network, auth, and a round trip. But there's one trick that's **purely local, zero latency**, and surprisingly few people know about it:

```bash
git log --grep="#12799" -n 5
```

### Why does this work?

Because GitHub's default merge commit message looks like this:

```
Merge pull request #12799 from feature/fix-sftp-version

Fix sftp version constraint in pyproject.toml
```

The PR number is baked right into your git history. `git log --grep` searches **local commit messages** — no network, instant results.

### Practical Variants

```bash
# Search by PR number and show the full diff
git log --grep="#12799" -n 1 -p

# Search by keyword (don't know the PR number? no problem)
git log --grep="sftp" --oneline -n 10

# Only show merge commits (filter out noisy feature commits)
git log --grep="#12799" --merges -n 5

# Combine: keyword + your commits only
git log --grep="sftp" --author="todd" --oneline -n 10

# Found it — now show which files were changed
git log --grep="#12799" -n 1 --stat
```

### When to Use This vs `gh pr list`

| Scenario | Use |
|----------|-----|
| Know the PR number, want quick confirmation | `git log --grep="#12799"` ⚡ |
| Don't know the number, fuzzy keyword search | `gh pr list --search` |
| Need PR comments, reviews, CI status | `gh pr view` |
| Don't have a local clone | `gh` is your only option |
| No network / on a plane | `git log` is the only game in town ✈️ |

> 🧠 **Mental model**: `git log --grep` searches **code history** (commit messages). `gh pr list` searches **GitHub's PR metadata** (title, description, labels, reviewers). Two different dimensions — complementary, not interchangeable.

---

## Quick Reference

| I want to... | Command |
|--------------|---------|
| Search my PRs in a repo | `gh pr list --repo REPO --author @me --state all` |
| Filter by keyword | Add `--search "keyword"` |
| Filter by date | `--search "created:>2025-06-01"` |
| Search across repos | `gh search prs "keyword" --owner ORG --author @me` |
| View a diff | `gh pr diff NUMBER --repo REPO` |
| Open in browser | `gh pr view NUMBER --web` |
| Create a shortcut | `gh alias set NAME 'pr list ...'` |
| Search by changed files | Use `gh api graphql` (see above) |
| Instant local search by PR number | `git log --grep="#12799" -n 5` |
| Offline keyword search | `git log --grep="sftp" --oneline -n 10` |

---

*The power of GitHub CLI isn't replacing the web UI — it's keeping your hands on the keyboard through the entire search → inspect → act workflow. Once you internalize these patterns, PR archaeology becomes a 5-second task instead of a 5-minute scroll.*
