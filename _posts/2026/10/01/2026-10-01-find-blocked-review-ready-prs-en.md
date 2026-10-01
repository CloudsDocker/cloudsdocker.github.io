---
title: Can You Find Every Blocked, Review-Ready PR in Under a Minute?
header:
    image: /assets/images/bg_raw/BB1msIHt.jpg
date: 2026-10-01
tags:
 - github-cli
 - git
 - pull-requests
 - shell
 - developer-productivity
permalink: /blogs/tech/en/find-blocked-review-ready-prs
lang: en
layout: single
category: tech
---
# Can You Find Every Blocked, Review-Ready PR in Under a Minute?

*Define “ready” and “blocked” as searchable facts, then choose the index that actually contains them.*

Which pull requests in your repository are non-drafts, approved, and currently failing checks?

Run this from any authenticated shell, replacing `OWNER/REPO`:

```bash
gh pr list --repo OWNER/REPO --state open \
  --search 'draft:false review:approved status:failure'
```

That is a useful operational definition of a blocked, review-ready PR: it is open, no longer a draft, has an approval indexed by GitHub search, and has a failing status. It will not capture every reason a pull request can be blocked. A missing human approval, an unresolved conversation, a merge queue, or a branch-protection rule may need different signals.

The promise here is narrower and more useful: by the end, you will be able to find a pull request by its metadata, inspect it, and know when to switch from GitHub’s PR index to local Git history.

The early surprise is mundane enough to waste a lot of time: `gh pr list` defaults to open pull requests. If you are looking for the merged change from two months ago, this returns nothing until you add `--state all` or `--state merged`.

| Searchable condition | Query fragment | What it means |
|---|---|---|
| Ready to review | `draft:false` | Excludes drafts |
| Review signal present | `review:approved` | Finds PRs with an indexed approval |
| CI is blocking | `status:failure` | Finds failing commit-status/check signals |
| Historical search | `--state all` | Includes closed and merged PRs |

> 📌 **Takeaway:** A PR query is only as complete as the fields you made searchable. “Blocked” is a policy word; `status:failure` is a queryable fact.

## Start with the smallest drawer

Suppose you changed a dependency constraint in `pyproject.toml`, merged the pull request, and now need the discussion or the diff. Search the repository where it happened first:

```bash
gh pr list --repo OWNER/REPO --author @me --state all \
  --search "sftp pyproject"
```

`@me` resolves to the authenticated GitHub user. `--search` passes a GitHub search query, so keyword terms can be combined with search qualifiers. The exact fields and qualifiers available depend on GitHub’s pull-request search index; treat the web search bar as a useful way to validate a query before scripting it.

A filename keyword can still be useful, but only as a text search:

```bash
gh pr list --repo OWNER/REPO --author @me --state all \
  --search "pyproject.toml"
```

That finds pull requests whose indexed text mentions `pyproject.toml`; it does not find every pull request that changed that path. If the question is about changed files, use Git history or build a paginated GraphQL/client-side report instead.

Or fetch structured output and filter the titles locally:

```bash
gh pr list --repo OWNER/REPO --author @me --state all \
  --limit 100 --json title,number,url \
  --jq '.[] | select(.title | test("sftp"; "i"))'
```

That last command only tests titles because that is what it asks for. It is not a full-content search disguised as JSON processing. The distinction matters when the memorable text lived in a PR description or a review comment.

## The query language handles dates, labels, reviewers, and branches

GitHub search qualifiers turn `gh pr list` into more than a title filter:

```bash
# Created after June 2025
gh pr list --repo OWNER/REPO --author @me --state all \
  --search "created:>2025-06-01"

# A date range plus a keyword
gh pr list --repo OWNER/REPO --author @me --state all \
  --search "created:2025-06-01..2025-08-31 sftp"

# Recently updated
gh pr list --repo OWNER/REPO --author @me --state all \
  --search "updated:>2025-09-01"
```

Some filters are first-class flags rather than search text:

```bash
gh pr list --repo OWNER/REPO --label "bug"
gh pr list --repo OWNER/REPO --label "hotfix" --label "production"

gh pr list --repo OWNER/REPO --search "reviewed-by:USERNAME"
gh pr list --repo OWNER/REPO --search "review-requested:@me"

gh pr list --repo OWNER/REPO --base main
gh pr list --repo OWNER/REPO --base develop
```

Multiple `--label` flags are an intersection: the PR must carry each requested label. That is often what you want for an operational queue, and often not what you want for broad archaeology.

I would not start with a cross-repository search by default. Searching one repository gives you a smaller result set and a clearer mental model. The best counter-case is a monorepo split, a repository migration, or a change whose location you genuinely do not know. Then the wider index earns its cost.

**My opinion: search the smallest index that could contain the answer.** It is less clever than searching everything, which is why it works under pressure.

## `gh pr list` and `gh search prs` answer different questions

`gh pr list` is scoped to one repository. Supplying `--repo OWNER/REPO` makes that scope explicit, though the CLI can infer a repository from the current Git checkout in many cases. `gh search prs` uses GitHub’s broader search endpoint and can span repositories or owners.

| Need | Start with | Why | Cost |
|---|---|---|---|
| My PRs in one repository | `gh pr list` | Small, explicit scope | You must know the repository |
| A PR anywhere under an owner | `gh search prs` | Wider search surface | Search results and limits are more constrained |
| A known merged PR in a local clone | `git log --grep` | No network round trip | Depends on local history and merge strategy |

For a broader search:

```bash
# Search PRs under an owner
gh search prs "sftp pyproject" --owner OWNER --author @me

# Narrow a wider search to repositories you know may contain it
gh search prs "sftp" --repo OWNER/REPO_A --repo OWNER/REPO_B

# Restrict to merged PRs
gh search prs "sftp" --owner OWNER --merged
```

`gh search prs` also offers explicit sorting and ordering controls. Use it when you do not know which drawer holds the document. Do not use it merely because a repository-level command felt too ordinary.

## Once you find it, stay in the terminal

A PR number is enough to inspect or act without checking out a branch:

```bash
# Diff without checkout
gh pr diff <PR_NUMBER> --repo OWNER/REPO

# Details, review state, and checks
gh pr view <PR_NUMBER> --repo OWNER/REPO

# Checkout only when you need a working tree
gh pr checkout <PR_NUMBER> --repo OWNER/REPO

# Submit a review
gh pr review <PR_NUMBER> --approve
gh pr review <PR_NUMBER> --comment --body "LGTM"
gh pr review <PR_NUMBER> --request-changes --body "Could we avoid pinning this version?"

# Open the PR in a browser
gh pr view <PR_NUMBER> --web --repo OWNER/REPO
```

For a search-to-browser handoff, guard the empty-result case instead of letting a pipeline manufacture a confusing command:

```bash
pr=$(gh pr list --repo OWNER/REPO --author @me --state all \
  --search "sftp" --json number --jq '.[0].number')

[ -n "$pr" ] && gh pr view "$pr" --web --repo OWNER/REPO
```

For batch diff output, a shell loop is less surprising than an `xargs` invocation when there are no matches:

```bash
gh pr list --repo OWNER/REPO --search "sftp" --json number \
  --jq '.[].number' |
while read -r pr; do
  printf '=== PR #%s ===\n' "$pr"
  gh pr diff "$pr" --repo OWNER/REPO
done
```

If these searches recur, make the repetition visible:

```bash
gh alias set my-prs 'pr list --author @me --state all'
gh my-prs --repo OWNER/REPO --search "sftp"

# Or deliberately bind an alias to one repository
gh alias set repo-prs 'pr list --repo OWNER/REPO --author @me --state all'
gh repo-prs --search "sftp"
```

An `fzf` picker is useful once result lists get long. Emit tab-separated JSON-derived data so the PR number remains a stable first field:

```bash
gh pr list --repo OWNER/REPO --author @me --state all --limit 50 \
  --json number,title --jq '.[] | "\(.number)\t\(.title)"' |
  fzf --delimiter=$'\t' --with-nth=2.. \
      --preview 'gh pr view {1} --repo OWNER/REPO' |
  cut -f1 |
  xargs -I{} gh pr view {} --web --repo OWNER/REPO
```

## Changed files are a boundary, not a missing flag

When the question becomes “which merged PR changed this file?”, `gh pr list` has no changed-file filter. GraphQL can retrieve changed file paths alongside pull requests:

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

That query does **not** search all pull requests by file path. It retrieves a page of PRs and a page of files for each. A real file-based report needs pagination and client-side filtering, or a separate index designed for that question. Five files are five files, not proof that the PR changed only five files. APIs are very good at making partial pages look like complete answers.

For lightweight reporting, JSON and `--jq` are enough:

```bash
gh pr list --repo OWNER/REPO --author @me --state merged \
  --limit 200 --json mergedAt \
  --jq '[.[] | .mergedAt[:7]] | group_by(.) | map({month: .[0], count: length})'
```

## Your local clone has a different index

For a known PR number, local Git can be faster and can work offline:

```bash
git log --grep="#<PR_NUMBER>" -n 5
git log --grep="#<PR_NUMBER>" -n 1 -p
git log --grep="#<PR_NUMBER>" --merges -n 5
git log --grep="sftp" --oneline -n 10
git log --grep="sftp" --author="<AUTHOR>" --oneline -n 10
git log --grep="#<PR_NUMBER>" -n 1 --stat
```

This works when a fetched merge commit contains a PR number or memorable title text. GitHub commonly creates merge-commit messages that include the PR number, but squash merges, rebase merges, custom commit messages, and incomplete local fetches break that assumption. `git log` searches commit messages; it does not search PR descriptions, labels, reviewers, comments, or CI state.

**Git history remembers what shipped. PR metadata remembers why it was discussed.**

Use the first when you need a local code-history answer. Use the second when you need the review record. They are complementary indexes, not competing commands.

The next time someone says a PR is “blocked,” ask for the queryable condition behind the word. Is it a failing check, a missing approval, a draft, an unresolved conversation, or a queue? Put that condition in the command, then see which supposedly obvious state your repository has failed to record.
