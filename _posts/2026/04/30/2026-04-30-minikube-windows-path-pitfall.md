---
title: "Git Bash on Windows: The MSYS Path Conversion Pitfall"
header:
    image: /assets/images/expect-script-is-your-secret-to-productivity.jpg
date: 2026-04-30
tags:
 - bash
 - windows
 - kubernetes
 - minikube
 - devops
permalink: /blogs/tech/en/minikube-windows-path-pitfall
layout: single
category: tech
---

> "Know your enemy and know yourself." — Sun Tzu, The Art of War

# Git Bash on Windows: The MSYS Path Conversion Pitfall

> A field guide for principal engineers who hit `container path must be absolute`,
> `invalid reference format`, or `unknown flag` errors only on Windows.

## TL;DR

When a shell script written for Linux/macOS is run inside **Git Bash** (or any
MSYS2/MinGW shell) on Windows, the MSYS2 runtime automatically rewrites
arguments that *look like* POSIX paths into Win32 paths before they reach the
target binary. This is silent, undocumented in most tutorials, and is the root
cause of a whole family of "works on my Mac, broken on Windows" bugs.

The canonical symptom we hit:

```text
$ ./scripts/minikube-init.sh
...
StartHost failed: config: '\Program Files\Git\host' container path must be absolute
```

We passed `--mount-string="$ROOT_DIR:/host"`. MSYS rewrote the trailing `/host`
into `C:\Program Files\Git\host` (the install root of Git for Windows), and
the leading drive letter was eaten by quoting/joining, leaving an invalid
`\Program Files\Git\host`.

## How MSYS path conversion works (mental model)

Every argument on the command line goes through this pipeline before the target
process sees it:

```
your literal string  ──►  bash variable expansion  ──►  MSYS2 path conversion  ──►  target binary
                                                              │
                                                              ▼
                                            Heuristic rules (simplified):
                                            - "/foo"        → "<MSYS_ROOT>\foo"
                                            - "/c/Users/x"  → "C:\Users\x"
                                            - "//foo"       → "/foo"            (escape: leave alone)
                                            - "a:/foo"      → split on ':', convert each side
                                            - "--flag=/foo" → convert the value
```

MSYS does this so that GNU tools written for POSIX can pass paths to native
Win32 binaries seamlessly. It is a feature, not a bug. **The bug is that the
heuristic cannot tell apart "host paths" from "paths inside a guest VM /
container"** — both look like `/something` to a string-matcher.

## Why it bites Docker / Minikube / Kubernetes specifically

Any tool that takes `--mount HOST:GUEST`, `-v HOST:GUEST`, or container-side
absolute paths is vulnerable, because the *guest* path is, by definition, a
POSIX-looking string in a context MSYS knows nothing about.

Common offenders:

| Tool       | Argument shape                          | Failure mode                                |
| ---------- | --------------------------------------- | ------------------------------------------- |
| `docker`   | `-v $PWD:/app`                          | `/app` rewritten to `C:\Program Files\...`  |
| `minikube` | `--mount-string="$DIR:/host"`           | Same                                        |
| `kubectl`  | `exec -- /bin/bash -c "..."`            | The `/bin/bash` arg gets path-converted     |
| `aws`      | `--query 'Reservations[0].Instances'`   | Rare, but the leading `/` in JMESPath gets touched |
| `git`      | `git -C / status` etc.                  | Some sub-args                              |

## The fixes — ranked

### 1. `MSYS_NO_PATHCONV=1` (preferred for one-shot calls)

```bash
MSYS_NO_PATHCONV=1 minikube start --mount-string="$DIR:/host" ...
```

- Scope: a single command (best — Parnas information hiding).
- Caveat: it disables conversion for **all** args. If you also rely on MSYS to
  convert `/c/Users/...` into `C:\Users\...`, you must do that conversion
  yourself with `cygpath -m`.

### 2. `MSYS2_ARG_CONV_EXCL='*'`

The MSYS2 (Arch-flavoured) equivalent. Belt-and-suspenders together with #1
gives you a portable "stop touching my args" toggle:

```bash
env MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' some-tool ...
```

### 3. Double-leading-slash escape

```bash
docker run -v "$PWD"://app image
```

- Scope: per-argument, no env var.
- Cost: cryptic. Future readers will not know why the slash is doubled.
- Use only for ad-hoc one-liners, never in committed scripts.

### 4. `cygpath` for explicit host-side conversion

```bash
HOST=$(cygpath -m "$ROOT_DIR")     # /c/Users/x  ->  C:/Users/x
```

`cygpath -w` gives backslashes, `-m` gives forward slashes (the "mixed" form
that Docker, Java, and most CLI tools accept). **Always use `-m` for tool
arguments**; reserve `-w` for human display.

### 5. Cross-platform guard (production pattern)

This is the pattern we shipped in `scripts/minikube-init.sh`:

```bash
case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)
        HOST_MOUNT_SRC="$(cygpath -m "$ROOT_DIR")"
        NO_PATHCONV="MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL=*"
        ;;
    *)
        HOST_MOUNT_SRC="$ROOT_DIR"
        NO_PATHCONV=""
        ;;
esac

env $NO_PATHCONV minikube start --mount-string="${HOST_MOUNT_SRC}:/host" ...
```

Properties:
- No-op on Linux/macOS (the `*)` branch).
- Quirk localised to **one** call site (information hiding / Parnas).
- Uses `env VAR=val cmd` so the variable lives only for that process — no
  global shell pollution.
- Self-documenting: `case "$(uname -s)"` makes the platform-specific branch
  obvious to future readers.

## Diagnostic recipe (60-second triage)

When a Windows-only "looks like a path got mangled" error fires:

1. **Echo the args first**, before the tool sees them:
   ```bash
   set -x   # or:
   echo "ARG=[$arg]"
   ```
   You will see the rewritten value and the bug becomes obvious.
2. **Run with `MSYS_NO_PATHCONV=1`** once. If the error changes, MSYS is the
   culprit. If it stays the same, look elsewhere.
3. **Check `uname -s`** to confirm you are in `MINGW*` / `MSYS*`.
4. **Reproduce in `cmd.exe` or PowerShell**. If it works there, definitively
   MSYS.

## Other latent landmines in the same script class

While fixing the path-conversion bug, audit any shell script for these high-
frequency siblings (all real production outages I have seen):

| # | Smell                                                       | Why it bites                                                          | Fix                                            |
| - | ----------------------------------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------- |
| 1 | `set -e` without `set -o pipefail`                          | `cmd1 \| cmd2` swallows `cmd1` failures                               | `set -euo pipefail`                            |
| 2 | `... \| grep X \| wc -l` then `[ $n -ge 5 ]`                | BSD vs GNU `wc` whitespace; `grep` failing returns 1 → `set -e` kills | `kubectl wait --for=condition=Ready pod --all` |
| 3 | `for f in $DIR/*.yaml`                                      | unquoted glob; spaces in path break it                                | `for f in "$DIR"/*.yaml`                       |
| 4 | `envsubst < file`                                           | Silently substitutes empty string for undefined vars                  | `envsubst '${KNOWN_VAR}' <file` (allow-list)   |
| 5 | `sleep 3` after `kubectl apply`                             | Race condition disguised as documentation                             | `kubectl wait --for=condition=...`             |
| 6 | `alias kubectl='minikube kubectl --'` w/o `expand_aliases`  | Aliases don't expand in non-interactive scripts                       | Use a function, not an alias                   |
| 7 | `pwd` returning `/c/Users/...` on Windows                   | Some tools want `C:/Users/...`                                        | `cygpath -m "$(pwd)"`                          |
| 8 | `$ROOT_DIR` unquoted in `--flag=$ROOT_DIR`                  | Spaces in path break the flag                                         | Always quote: `--flag="$ROOT_DIR"`             |
| 9 | No timeout on `while true` health-check loops               | CI hangs forever                                                      | `timeout 600` or a counter + `exit 1`          |
|10 | `set -e` + `cd foo &> /dev/null && pwd`                     | `cd` failure is silently fine because of subshell + redirect          | Check `cd` return value explicitly             |

## Persisted state beats code (the "fixed it but it's still broken" trap)

After applying every fix above, you may *still* see the original error:

```
✨  Using the docker driver based on existing profile
🤦  StartHost failed: config: '\Program Files\Git\host' container path must be absolute
```

Note the line `Using the docker driver based on existing profile`. Minikube
persists the parameters of your **first** successful (or partially-successful)
`minikube start` to `~/.minikube/profiles/<profile>/config.json`. Subsequent
`minikube start` invocations **resume from that file and silently ignore most
CLI flags**, including `--mount-string`. So a profile created by a buggy run
stays buggy until the profile itself is deleted.

This is not minikube-specific. The same pattern shows up in:

- `docker compose` (project state in `docker-compose.yml` + named volumes)
- `terraform` (state file vs. `.tf` configs)
- `kubectl config` (contexts/clusters/users)
- `gcloud config configurations`
- `aws configure --profile`
- npm/pip lockfiles vs. manifests
- any CLI that has the words "profile", "workspace", "context", or "project"

### The mental model

```
                    STATE on disk (profile / state file / lockfile)
                    ──────────────────────────────────────────────
                    │   clean                     polluted
        OLD code    │   buggy first run           buggy + cached
                    │   creates pollution         (where you are)
                    │
        NEW code    │   ✅ correct                ❌ resume reads
                    │   first time                old polluted state
```

Fixing the code only moves you down a row. To move *across*, you must delete
the state. `git pull` cannot un-cook an egg.

### Defensive script pattern

`scripts/minikube-init.sh` accepts a `--clean` flag that runs `minikube delete
-p mq-minikube` before starting. Use it whenever:

1. You have just upgraded a stateful CLI (`minikube`, `terraform`, `helm`...).
2. A previous run crashed with a config error.
3. You changed any flag that the tool persists (mount paths, CPU/memory,
   driver, kubernetes version).

Generalised pattern for any stateful CLI:

```bash
# Always idempotent: --clean wipes persisted state, then reinitialises.
if [[ "${1:-}" == "--clean" ]]; then
    <tool> reset / delete / destroy --yes
fi
<tool> init / start / apply
```

### Interview-grade phrasing

> *"Stateful CLIs persist their last-known-good config to disk and resume from
> it on the next invocation. That means a code fix to flag handling does
> nothing until the persisted state is also cleaned. I treat any CLI with the
> words 'profile', 'workspace', or 'context' as having a hidden state machine,
> and I always provide a `--clean` escape hatch in init scripts so the team
> can recover from corrupted state with one command instead of remembering
> tribal knowledge."*

## Bonus pattern: replace `sleep` + `grep` with `kubectl wait`

A sibling smell we removed from `scripts/minikube-init.sh` while we were here:

```bash
# Before — race condition disguised as code
sleep 3
while true; do
    n=$(kubectl get pod | grep -v test- | grep Running | wc -l)
    [ "$n" -ge 5 ] && break
    sleep 2
done

# After — declarative, API-driven, with diagnostics on failure
kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/airflow --timeout=30s
kubectl rollout status statefulset/postgres -n airflow --timeout=10m
kubectl wait --for=condition=Complete job/airflow-db-init -n airflow --timeout=10m \
    || { kubectl logs -n airflow job/airflow-db-init --tail=100; exit 1; }
kubectl wait --for=condition=Available deployment --all -n airflow --timeout=10m
```

Why the rewrite is principal-grade, not just shorter:

1. **No magic numbers.** The old `>= 5` encoded a business fact (number of
   Airflow components) into shell. Adding a new deployment silently broke
   the check.
2. **No screen-scraping.** Parsing `kubectl get` human output is fragile;
   `--for=condition=...` queries the API directly.
3. **Bounded.** `--timeout` makes failure observable; the old `while true`
   could spin until the CI runner killed the whole job.
4. **Diagnostic.** A failed wait dumps the relevant `kubectl logs`. **A failing
   script must produce more output than a succeeding one** — this is the
   single biggest leverage move for on-call sanity.
5. **Forward-compatible.** `deployment --all` adapts to new deployments
   without edits — Open/Closed Principle applied to ops scripts.

**The rule of thumb to internalise:**

> *`sleep` is a comment that lies. `kubectl wait` is the comment that runs.*

If you see a `sleep N` immediately after a `kubectl apply`, `helm install`,
`docker run`, `terraform apply` — assume race condition until proven otherwise.

### `kubectl wait` cheat sheet (memorise this)

```bash
# By condition name
kubectl wait --for=condition=Ready pod/foo --timeout=60s
kubectl wait --for=condition=Available deployment --all -n ns --timeout=10m
kubectl wait --for=condition=Complete job/foo -n ns --timeout=10m

# By jsonpath (1.23+) — covers any field on any resource
kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/ns --timeout=30s
kubectl wait --for=jsonpath='{.status.loadBalancer.ingress[0].ip}' svc/foo

# By lifecycle event
kubectl wait --for=delete pod/foo --timeout=60s
kubectl wait --for=create deployment/foo  # 1.31+

# Multiple conditions OR'd (1.30+) — best for Jobs that may Fail
kubectl wait --for=condition=Complete --for=condition=Failed job/foo
```

`kubectl rollout status` is a separate primitive — use it for StatefulSets
and DaemonSets (which don't expose an `Available` condition), and whenever
you want streaming progress output.

## Interview-ready talking points (use these verbatim)

When asked "tell me about a tricky bug you debugged":

> *"On Windows, our minikube bootstrap script failed with a baffling error
> that the container path `\Program Files\Git\host` was not absolute — but
> we never wrote that path. Tracing it back, I realised the MSYS2 runtime
> behind Git Bash was rewriting our `/host` argument into a Win32 path using
> the Git install directory as a fallback root. The fix wasn't just an
> `MSYS_NO_PATHCONV=1` — that's the symptom-fix. The deeper fix was to make
> the script **environment-aware**: detect the shell flavour with `uname -s`,
> use `cygpath -m` to deterministically produce the host-side path, and scope
> the `NO_PATHCONV` toggle to a single `env`-prefixed call so the quirk lives
> next to its cause. That's Parnas-style information hiding applied to shell
> scripting."*

This hits four interview-grade signals:
1. **Root cause vs. symptom discipline.**
2. **Cross-context awareness** (host shell vs. guest VM vs. container).
3. **Software design vocabulary** (information hiding, scope minimisation).
4. **Operational pragmatism** (it ships, it's portable, it self-documents).

## Mental models worth carrying forward

- **Information directionality**: every layer between you and the kernel may
  rewrite your input. Whenever a value crosses a context boundary (shell →
  binary, host → container, frontend → backend), assume rewriting until proven
  otherwise.
- **Parnas information hiding (1972)**: encapsulate environmental quirks at
  their narrowest scope. A `MSYS_NO_PATHCONV=1` at file-top is a leak; the
  same flag scoped to one `env` invocation is a contract.
- **First-principles debugging**: don't ask "why doesn't it work?", ask "what
  bytes does the target process actually receive?". `set -x`, `strace`,
  `Process Monitor`, `tcpdump` — pick the one that closes the observability
  gap.
- **Knowing your runtime (知人论世)**: a shell script's behaviour is a
  function of `(script, shell, OS, locale, PATH)`. Pretending the shell is
  transparent is the #1 source of "works on my machine" bugs.
- **Inversion**: when stuck, list everything the system *guarantees* it will
  NOT do, and check each. ("MSYS will not touch arguments without a leading
  slash" → instantly tells you *why* `--mount-string` is touched and `-p` is
  not.)

## A 2-week internalisation plan

| Day  | Drill                                                                                  |
| ---- | -------------------------------------------------------------------------------------- |
|  1–2 | Reproduce the bug in a fresh repo. Toggle `MSYS_NO_PATHCONV` and observe with `set -x`.|
|  3   | Read `git-for-windows/git#577` and `kubernetes/minikube#15025` end-to-end.             |
|  4   | Audit every shell script in your current repo with the 10-smell checklist above.       |
|  5   | Add a `lint-shell` CI step using `shellcheck` and `shfmt`.                             |
|  6   | Re-implement the fix from memory, no notes. Then diff against the committed version.  |
|  7   | Write a 5-minute lightning talk titled "Why your `/host` became `C:\Program Files\Git\host`." Deliver it to a teammate. |
|  8–10| Find one more Windows-only failure in another OSS project's tracker. Diagnose it, post a PR. |
| 11–14| Generalise: write a `scripts/lib/portable.sh` with `portable_host_path()` and `portable_run_no_pathconv()` helpers, adopt across the codebase. |

The point of the plan is **deliberate practice with feedback**, not memorisation. By day 14 you will spot path-conversion bugs the way a chef spots burnt butter — by smell, before it's served.

## References

- Git for Windows issue [#577](https://github.com/git-for-windows/git/issues/577): "Bash translates path parameter in Unix format to windows format, need a way to suppress it"
- Minikube issue [#15025](https://github.com/kubernetes/minikube/issues/15025): "container path must be absolute"
- Minikube PR [#9263](https://github.com/kubernetes/minikube/pull/9263): "fix mounting for docker driver in windows"
- Stack Overflow: [How can I suppress path expansion in the Git-for-Windows bash?](https://stackoverflow.com/questions/71341356/)
- Parnas, D.L. (1972). *On the Criteria To Be Used in Decomposing Systems into Modules.* Communications of the ACM.
