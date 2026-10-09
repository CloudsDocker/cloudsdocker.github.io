---
title: A Green Check Can Mean Nothing Ran
header:
    image: /assets/images/bg_raw/BingWallpaper (16).jpg
date: 2026-09-24
tags:
 - git
 - release-engineering
 - dependency-management
 - pre-commit
 - airflow
permalink: /blogs/tech/en/green-check-nothing-ran
layout: single
category: tech
---
# A Green Check Can Mean Nothing Ran

*How to read unfamiliar release commands as evidence, not instructions.*

```bash
git grep "apache-airflow = " pyproject.toml
git rev-list --count origin/master..origin/develop && \
  git rev-list --count origin/develop..origin/master
```

Those are commands, not evidence. Without their output, they do not tell us an installed package version, a branch distance, or whether either branch is healthy.

They do reveal the questions someone thought worth asking: what dependency constraint is declared, and whether two release branches have drifted apart.

That distinction matters because engineering tooling produces a dangerous kind of green: a successful command that checked nothing useful. By the end of this post, you should be able to classify a release command by what it proves, what it assumes, and how it can quietly lie.

> **A green check is evidence only after you know what was checked.**

## The first question is not “what did it print?”

A command is a fossil of the problem that led to it. Read the problem before the syntax.

| Signal | The question it actually answers | What it cannot establish | Silent-failure trigger |
|---|---|---|---|
| `git grep ... pyproject.toml` | Does this exact text occur in this tracked file? | Installed or deployed version | A different TOML shape, path, or dependency file |
| `git rev-list --count A..B` | How many commits are reachable from B but not A? | Size, safety, or content of the change | Stale remote-tracking refs |
| `git merge-base A B` | What common history anchors a merge? | Whether the resulting code is correct | Rewritten or incomplete history |
| `pre-commit run` | Do staged files pass configured hooks? | Whether unstaged or existing code passes | An empty index |

This is the reusable model: distinguish **declaration**, **resolved dependency state**, **installed runtime**, **commit topology**, and **tree content**. They are related. They are not interchangeable.

A dependency declaration in `pyproject.toml` states intent. A lock file records one resolved dependency graph. `poetry show apache-airflow` or `pip show apache-airflow` reports what an environment has installed. A container image or managed deployment may be the runtime authority instead. Treating any one of these as all four creates version drift with excellent manners.

For an Airflow-based service, this matters more than usual. Airflow, its provider packages, Python version, and constraints have compatibility relationships. Pinning only one package can look safe while the rest of the graph moves. The practical question is: which artifact is authoritative for the environment that actually parses and runs DAGs?

## Text search is reconnaissance, not TOML parsing

`git grep` is useful because it searches tracked files and avoids the usual pile of ignored local artifacts. But this pattern is narrower than it looks:

```bash
git grep "apache-airflow = " pyproject.toml
```

It misses valid declarations with different whitespace, a table-style dependency declaration, a PEP 621 dependency array, a nested project in a monorepo, or a dependency held in requirements or constraints files. No output means only that this exact search found no match.

That is why “we found nothing” should expand the search rather than close the investigation:

```bash
git ls-files '*pyproject.toml' '*requirements*.txt' 'Dockerfile*'
git grep -n -i -E 'apache[-_]airflow' -- \
  '*pyproject.toml' '*requirements*.txt' 'Dockerfile*'
```

For automation, parse TOML rather than teaching a regular expression every legal spelling of TOML. Text search is excellent for a quick question; it is a poor authority for structured configuration.

The same rule applies to caret constraints. In Poetry, `^2.7.0` permits versions from `2.7.0` up to, but not including, `3.0.0`. That describes an allowed range, not the installed version. The lock file and runtime inspection answer different questions.

## Branch counts measure topology, not risk

Git ranges are directional:

```bash
git rev-list --count origin/master..origin/develop
```

means commits reachable from `origin/develop` but not from `origin/master`. Reversing the range asks the reverse question.

Checking both directions is valuable. If develop-only commits are nonzero and master-only commits are zero, develop is simply ahead. If both are nonzero, the branches have diverged: each contains history the other lacks. A production hotfix that was not merged back is one common explanation, but it is not the only one.

Fetch first. `origin/master` and `origin/develop` are local remote-tracking references, not a live query against the server.

```bash
git fetch --all --prune
git rev-list --left-right --count origin/master...origin/develop
```

With the three-dot range and `--left-right`, the first number is commits unique to the left side and the second is commits unique to the right. This is clearer than two commands joined with `&&`, and it avoids losing the second observation when the first command fails.

The surprise is that commit counts can still mislead. A cherry-pick, squash merge, or rebase can preserve a patch while giving it a new commit ID. Topologically, the commit remains unique. Content-wise, its change may already exist on the other branch.

Use topology to find candidates, then inspect content:

```bash
git log --oneline --no-merges --cherry-pick --right-only \
  origin/develop...origin/master
git diff --stat origin/develop origin/master
```

`git log` tells the story of commits. `git diff` tells the current tree difference. Make merge decisions from the latter.

There is one further limit: `--no-merges` hides merge commits. Conflict resolution can introduce code that exists only in a merge commit. If the history matters, inspect merge commits too, not just the linear-looking list.

## Three dots mean different things in different commands

Git gives `...` two related but non-identical meanings. This is a frequent source of correct-looking mistakes.

```bash
# Commit sets: both sides' unique commits
git rev-list --left-right --count A...B

# Content: changes from the merge base to B
git diff A...B
```

For `git diff`, `A...B` is equivalent to diffing `merge-base(A, B)` against `B`. It answers: “what did B change since the shared base?” That makes it a good pre-merge inspection command:

```bash
git diff --stat HEAD...origin/master -- pyproject.toml poetry.lock
```

It isolates what the other side changed to dependency files. It does not predict merge conflicts, and it is not a substitute for checking the final merged tree.

## “No commit” is not “no change”

The line between reading and writing is where most release mistakes start.

`git merge --no-commit origin/master` does modify the index and working tree when it performs a real merge. It only postpones creating the merge commit. It is not a dry run.

There is a sharper edge: a fast-forward merge has no merge commit to postpone, so `--no-commit` alone cannot stop the branch pointer from moving. If you intentionally want a reviewable, stoppable merge operation, use:

```bash
git merge --no-commit --no-ff origin/master
```

Or use a temporary worktree when the requirement is truly “inspect without touching this checkout.”

If a merge is in progress, finish it deliberately or abort it deliberately:

```bash
git status
git merge --abort
```

Do not treat a repository in merging state as normal working space. The next `git commit -am "small change"` can complete the merge and attach unrelated tracked edits to it. Git is behaving correctly; the commit message is the thing that becomes false.

I disagree with the common habit of merging a production branch directly into every feature branch “to keep it current.” For a branch intended to merge back into an integration branch, synchronize with that integration branch. If production-only fixes need back-merging, make that a visible, separately reviewed release-maintenance change. The strongest counterargument is practical: sometimes a developer needs a production fix locally before the integration branch catches up. In that case, a temporary local merge or a narrowly justified cherry-pick can be reasonable. It should not become the final PR history by accident.

## A reset can disable the check you run afterward

`git reset --hard origin/develop` is not inherently wrong. It moves the current branch, resets the index, and overwrites tracked working-tree files to match the target. It does not remove untracked or ignored files, and it does not modify the remote.

Its danger is scope. Before using it, save a recovery path:

```bash
git stash -u
git reset --hard origin/develop
```

Committed work can generally be found through reflog. Work that existed only as unstaged edits may not be recoverable through Git. On a shared branch, rewriting and force-pushing after a hard reset is a different class of risk; use `git revert` for published history.

After a reset, this command often offers false comfort:

```bash
poetry run pre-commit run
```

Without `--all-files` or explicit files, `pre-commit run` normally operates on staged files. A hard reset empties the index. The hooks can report `Skipped` and exit successfully because there were zero files to examine.

Run the question you mean:

```bash
poetry run pre-commit run --all-files
```

Then distinguish `Passed` from `Skipped`. A formatter that modifies files may also exit nonzero on its first run; inspect the diff, stage the accepted changes, and run it again. Keep formatting changes out of a merge commit when possible. A commit should have one explainable purpose.

The same discipline applies to Sonar exclusions. Excluding code from coverage can be appropriate when ordinary line coverage is not meaningful. Excluding code from analysis is much stronger: it hides issues, vulnerabilities, and smells as well as coverage. A green quality gate is not proof that the code was examined.

## Make the evidence chain explicit

Before a dependency upgrade or branch reconciliation, run this short sequence and record what each answer means:

```bash
git fetch --all --prune
git status --short
git rev-parse --abbrev-ref HEAD
git rev-list --left-right --count origin/master...origin/develop
git log --oneline --no-merges --cherry-pick --right-only \
  origin/develop...origin/master
git diff --stat HEAD...origin/master -- pyproject.toml poetry.lock
poetry run pre-commit run --all-files
```

If the current branch command prints `HEAD`, you are detached; do not use that literal value as a branch name in scripts or image tags. In CI, prefer the CI platform’s branch variables because many checkouts intentionally use a detached commit.

The checklist costs little. The cost is that it makes ambiguity visible before you can erase it with a convenient command.

Before your next `--hard`, `--no-commit`, `-am`, or chained push, ask one question: **what evidence would prove that this command did the work I think it did?**
