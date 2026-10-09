---
title: 'Pre‑Commit Security: A Deep Dive into Gitleaks'
header:
    image: /assets/images/bg_raw/BB1msB1N.jpg
date: 2026-10-06
tags:
 - gitleaks
 - pre-commit
 - secret-scanning
 - git
 - security
 - ci
permalink: /blogs/tech/en/gitleaks-precommit-staged-scan
lang: en
layout: single
category: tech
---
> "Security is a process, not a product." — Bruce Schneier

# Pre‑Commit Security: A Deep Dive into Gitleaks

*Why `--all-files` can still leave your Git history untouched.*

> "The only secure computer is one that's unplugged, locked in a safe, and buried 20 feet under the ground in a secret location... and I'm not even too sure about that one." — Dennis Hughes

“`pre-commit run --all-files gitleaks` scans the whole repository.” That is a reasonable assumption, and it is wrong for a common Gitleaks hook configuration.

Consider a common real-world incident pattern: a developer discovers that an old `.env.example` file in a long-lived repository contains a credential left by a former teammate. Before opening a cleanup pull request, they run `pre-commit run --all-files gitleaks`, see no finding, and conclude the repository is clean. In the common hook configuration discussed below, the command may have scanned only the files currently staged for the cleanup commit—not the old checked-out file or the commit that introduced it. The credential can remain in Git history even though the “full” scan appeared to pass.

By the end of this post, you should be able to tell whether your command scans staged changes, checked-out files, or Git history—and choose the right CI command for each.

Run this in a repository that has the hook configured:

```sh
pre-commit run --all-files gitleaks -v
```

Then inspect the hook definition. If it uses `pass_filenames: false` and invokes Gitleaks with `--staged`, `--all-files` does not widen Gitleaks's scan.

## The filename list may be ignored

`pre-commit` is a framework for managing Git hooks through YAML. `run --all-files` tells it to select all tracked files rather than only staged files. The final `gitleaks` selects one hook by ID.

That logic works for hooks that accept filenames. A representative Gitleaks hook is configured like this:

```yaml
entry: gitleaks git --pre-commit --redact --staged --verbose
language: golang
pass_filenames: false
```

The decisive line is `pass_filenames: false`. Pre-commit does not pass its selected file list to this hook. Gitleaks instead asks Git for the staged diff because the entry includes `--staged`.

**A scanner can only scan the scope its entry point asks Git to expose.**

That makes these commands equivalent in scan scope for this particular hook:

```sh
pre-commit run gitleaks
pre-commit run --all-files gitleaks
```

The second command can still cause pre-commit to select more files for other hooks. It just cannot override a Gitleaks entry that ignores filenames and explicitly reads the index.

> 📌 **Takeaway:** `--all-files` changes pre-commit's filename selection, not a hook's internal Git query.

| What you want to inspect | Useful mechanism | What it cannot prove |
|---|---|---|
| A pending commit | `gitleaks git --pre-commit --staged` | Whether an older commit contains a secret |
| Available Git history | `gitleaks git` | Whether the CI checkout omitted older history |
| Files in a directory | `gitleaks dir` | Whether a deleted or historical file contained a secret |
| Text from another tool | `gitleaks stdin` | Git provenance or commit history |

This is the surprise worth remembering: `--all-files` is often described as a full scan, but for this hook it can scan no more than the staged content. With nothing staged, there may be nothing for Gitleaks to inspect.

## Gitleaks has two detection strategies, neither is magic

Gitleaks is implemented in Go and commonly configured through `.gitleaks.toml`. Its rules combine recognizable patterns—such as credential formats with stable prefixes—with entropy checks for token-like strings that have no stable format.

Shannon entropy measures how unpredictable the character distribution is. A random-looking string can cross a configured entropy threshold and become suspicious even when it does not match a known provider format. That is useful, but it also explains false positives: encoded test fixtures, hashes, and random identifiers can look secret-shaped.

Scanning cost grows with the bytes examined and the rules applied; regular-expression matching is a meaningful part of that cost. Gitleaks uses concurrency internally, but concurrency does not make an unbounded history free.

## A client hook is feedback, not enforcement

A local hook provides fast feedback. It is also bypassable with `git commit --no-verify`. That does not make it useless. It makes it a reminder rather than the final control.

A practical defense has separate jobs:

1. **Local pre-commit scanning** catches mistakes before a commit is created.
2. **CI scanning** makes a pull request or merge gate enforceable by the service running CI.
3. **Server-side push protection** can reject a push before the secret reaches the shared remote, where the platform supports it.
4. **Runtime detection and credential revocation** reduce exposure when a credential escapes anyway.

Public secret-scanning programs can notify participating providers about exposed credentials; some providers can then revoke or invalidate them. That is valuable containment, not prevention.

My contestable view: **a repository with only a pre-commit secret hook does not have a secret-control boundary.** The strongest counterargument is developer experience: mandatory remote checks can be slow, noisy, and block legitimate work. That is real. The answer is to tune rules and provide a documented exception path, not to pretend a bypassable client hook is a gate.

## Full-history CI needs a different command

If the purpose is a baseline or a history audit, invoke Gitleaks directly rather than relying on a staged pre-commit hook:

```yaml
- name: Scan available Git history
  run: gitleaks git --redact --verbose --exit-code 1
```

The checkout must contain the history you intend to scan. A shallow checkout cannot reveal commits it did not fetch.

For a large monorepo, do not necessarily scan all history on every change. A workable policy is an initial full-history baseline, incremental checks for new changes, and periodic full scans. A baseline file can record reviewed findings; allowlists can exclude known-safe paths, patterns, commit identifiers, or stopwords; and an inline `# gitleaks:allow` marker can document a narrow exception where the rule supports it.

The scanner should fail closed, but the escape hatch must be explicit. Otherwise people reach for `--no-verify`, and the control becomes ceremonial.

## A secret in history is already an incident

Pre-commit only sees the commit being prepared. It cannot stop a credential that was committed last week.

If a real credential enters Git history, deleting the file is not remediation. The old commit still contains it. Treat the credential as exposed: rotate or revoke it, then remove it from history with a tool such as `git filter-repo` where rewriting history is appropriate. Rotation is the urgent step; history cleanup reduces continued accidental distribution and discovery.

The useful mental model is simple: Git history is a record, not a trash can. A secret committed into it should be assumed recoverable by anyone who can access that history.

## The primary control is keeping secrets out of source

Secret scanning is a catch net, not the primary control. The better architecture stores secrets in a dedicated secret manager, injects short-lived credentials at runtime, and leaves only references—not values—in the repository. Systems such as a vault service, cloud secret manager, or a CLI-backed reference scheme can support that pattern.

In higher-regulation environments, the same mechanics carry more audit weight. Controls may also include signed commits, immutable audit logs, automated rotation, and canary tokens: deliberately planted fake credentials whose use can indicate that someone or something attempted to use or contacted the token. Token use alone does not establish that code or logs were accessed. Requirements such as SOX or PCI DSS can make evidence of these controls important, but the exact obligations depend on the system and assessment scope.

There are related tools and directions worth evaluating rather than treating as interchangeable facts: TruffleHog can verify some credential types with providers, which may reduce false positives but adds network and policy considerations; newer Gitleaks documentation uses `git`, `dir`, and `stdin` subcommands, so check `gitleaks --help` for the version installed in your environment; alternative hook runners, including Rust-based ones, may reduce setup overhead. Classifier-assisted triage for secrets is also plausible, but latency, cost, and false decisions are reasons it is not a default local-hook dependency.

Supply-chain controls such as SLSA, Sigstore, and SBOMs belong to the wider security program. They do not turn a committed password into a non-secret.

Before relying on your current setup, inspect the Gitleaks `entry` in `.pre-commit-config.yaml` or its upstream hook definition. Does it read filenames, the staged diff, or history—and does that match the boundary you think it protects?
