---
title: Every sleep in Your Deploy Script Is a Lie
header:
    image: /assets/images/hd_kubenetes_bamboo_deployment.png
date: 2026-04-30
tags:
 - bash
 - kubernetes
 - devops
 - shell-scripting
permalink: /blogs/tech/en/every-sleep-is-a-lie
layout: single
category: tech
---

> "Hope is not a strategy." — traditional SRE maxim

# Every `sleep` in Your Deploy Script Is a Lie

> *From `kubectl wait` to Windows path traps — three layers of bash discipline that separate Senior from Principal.*

---

## A 90-second story before we get clinical

Alex joined a data platform team last Tuesday. By Wednesday night he was on a video call with me at 11pm — exhausted, slightly furious, very confused. He had been "fixing" the team's `./scripts/minikube-init.sh` for six hours straight on his Windows laptop. Five different fixes, three commits reverted, and the cluster still refused to come up cleanly.

He shared his screen. I read the script for thirty seconds and told him:

> *"There are three patterns in this 200-line script that show up in nearly every production deploy script I have ever reviewed. None of them are minikube-specific. None are even Kubernetes-specific. We are going to fix them in the order they will bite you in your career, not in the order you discovered them tonight."*

What follows is what we walked through together. Three lessons, each designed to change how you read scripts, errors, and stateful CLIs forever:

- ✅ **`sleep` is a comment that lies. `kubectl wait` is the comment that runs.**
- ✅ **`set -e` is bash's gentle lie. You need three more flags before "strict" actually means strict.**
- ✅ **Fixing the code does not fix the system.** Persisted state outlives bug fixes.

I lead with the one you can apply at your next standup, not the one Alex hit first. Pedagogical order ≠ chronological order.

---

## 1. `sleep` is the most expensive comment in your bash script

Two-thirds into Alex's script:

```bash
# wait until namespace created
sleep 3

# ... apply more configs ...

# wait for pods to start
while true; do
    n=$(kubectl get pod | grep -v test- | grep Running | wc -l)
    [ "$n" -ge 5 ] && break
    sleep 2
done
```

I asked Alex what this did. *"Wait for the pods to come up."*

I told him this nine-line snippet contains five distinct anti-patterns. He didn't believe me. So we wrote them down.

| # | Anti-pattern | Why it bites |
|---|---|---|
| 1 | `sleep 3` after `kubectl apply` | **Magic number.** Three seconds is enough on a fast laptop, never enough on a stressed CI runner, pure waste in between. The comment "wait for namespace" lies — it really means "I guessed". |
| 2 | `kubectl get \| grep \| grep \| wc -l` | **Parsing human output instead of querying the API.** Any column-width change, status-string rename, or kubectl version bump silently breaks this. |
| 3 | `>= 5` | **Hardcoded business truth.** Today the cluster has five components. When someone adds a sixth deployment, this check is silently lying about readiness. There is no invariant linking the integer `5` to actual desired state. |
| 4 | `while true` with no timeout | **A CI runner killer.** When pods never come up, this loop spins until the runner's wall-clock limit slaughters the whole job — with zero diagnostic output explaining why. |
| 5 | `set -e` cannot save a pipeline | (Section 2. Stay tuned.) |

The deeper crime: this snippet is **user-space code reimplementing what Kubernetes already does for you**. The control plane *is* a reconcile loop. You are racing it instead of asking it.

### Kubernetes already gave you the right primitive

`kubectl wait` is declarative, API-driven, and timeout-bounded:

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

# Multiple conditions OR'd (1.30+) — best for jobs that may either complete or fail
kubectl wait --for=condition=Complete --for=condition=Failed job/foo
```

`kubectl rollout status` is a separate primitive — use it for StatefulSets and DaemonSets (which don't expose an `Available` condition), and whenever you want streaming progress output.

### The replacement we shipped

```bash
WAIT_TIMEOUT="${WAIT_TIMEOUT:-10m}"

kubectl wait --for=jsonpath='{.status.phase}'=Active \
    namespace/airflow --timeout=30s

kubectl rollout status statefulset/postgres -n airflow --timeout="$WAIT_TIMEOUT"

if ! kubectl wait --for=condition=Complete job/db-init \
        -n airflow --timeout="$WAIT_TIMEOUT"; then
    echo "❌ db-init did not complete. Recent logs:"
    kubectl logs -n airflow job/db-init --tail=100 || true
    exit 1
fi

kubectl wait --for=condition=Available deployment --all \
    -n airflow --timeout="$WAIT_TIMEOUT"
```

Five wins, none of them about line count:

1. **No magic numbers.** No business truth encoded as `>= 5`.
2. **No screen-scraping.** API queries, not stdout parsing.
3. **Bounded.** `--timeout` makes failure observable, not eternal.
4. **Diagnostic on failure.** A failing wait dumps the last 100 lines of the relevant logs. *A failing script must produce more output than a passing one* — the highest-leverage habit in on-call work.
5. **Forward-compatible.** `deployment --all` adapts to new deployments without edits — Open/Closed Principle applied to ops scripts.

### This applies far beyond Kubernetes

Every time you see `sleep N` immediately following one of these, treat it as a race condition disguised as documentation:

```
sleep N  +  kubectl apply
sleep N  +  helm install
sleep N  +  docker run
sleep N  +  terraform apply
sleep N  +  aws cloudformation deploy
sleep N  +  systemctl start
```

All of these tools have their own `wait` / `--wait` / `rollout status` primitive. **User-space polling is always second-best.**

### The aphorism to internalise

> **`sleep` is a comment that lies. `kubectl wait` is the comment that runs.**

`sleep N` is a self-documenting "I guessed how long this needs". It is a comment that the runtime has been forced to execute. Once you start spotting them, you cannot unsee them — and you will save yourself a 3am page.

---

## 2. `set -e` is bash's gentle lie

Alex's script started with `set -e`. Most scripts do. Most engineers think that means "exit on any error". It doesn't.

I asked Alex to open a fresh shell and run:

```bash
set -e
false | true
echo "I am still running"
```

The terminal printed *"I am still running"*. Alex's face was the face I have made on this discovery a hundred times.

### Why `set -e` is blind to pipelines

In bash, the exit code of `a | b` is the exit code of `b`. Whatever happened to `a` is gone. So in our earlier offender:

```bash
kubectl get pod | grep -v test- | grep Running | wc -l
```

If `kubectl get pod` blows up because cluster auth expired:

1. `kubectl` writes its error to stderr and exits 1
2. `grep -v test-` reads empty stdin, finds no matches, exits 1 (yes — `grep` exits 1 when nothing matches)
3. `grep Running` does the same
4. `wc -l` reads empty stdin, prints `0`, exits 0
5. The pipeline overall exits 0. **`set -e` sees nothing.**

Downstream, `[ $n -ge 5 ]` evaluates `0 -ge 5`, never breaks the loop, and the script spins forever — exactly the failure mode we just spent a chapter fixing.

**Two bugs cancel each other out and the script appears to "work"**. This is one of the most common ways production scripts die slowly.

### The unofficial bash strict mode

```bash
set -euo pipefail
```

Each flag patches a specific design decision bash made in the 80s for backwards compatibility. None of them is optional in 2026:

| Flag | Patches |
|---|---|
| `-e` | "Keep going after a failed command." |
| `-u` | "Treat unset variables as empty strings." (This is the line that turns `rm -rf "$DIR/$SUBDIR"` into `rm -rf "$DIR/"` when `SUBDIR` is mistyped — the canonical homedir-vapouriser.) |
| `-o pipefail` | "A pipeline's exit code is the last stage's exit code." |

Aaron Maxwell coined this trio "the unofficial bash strict mode". It is the difference between a script that fails fast in dev and one that fails mysteriously at 3am in prod.

### The traps `set -e` *still* doesn't catch (interview gold)

Even with strict mode on, bash has surprising blind spots. A principal must know all of them:

| Scenario | Does `set -e` fire? | Fix |
|---|---|---|
| `cmd \|\| true` | ❌ No (this is explicit suppression) | — |
| `if cmd; then ...` | ❌ No (the test is by design) | — |
| `cmd && other`, the non-final command | ❌ No | — |
| **Command substitution `$(failing_cmd)`** | ❌ **No!** | `shopt -s inherit_errexit` |
| Function called as `f \|\| handle` | ❌ No (errexit is suppressed inside) | `shopt -s inherit_errexit` |

The command-substitution one is the meanest:

```bash
set -e
DIR=$(this_command_does_not_exist)   # silently fails, but set -e shrugs
echo "DIR=[$DIR]"                      # still runs; DIR is empty
rm -rf "$DIR/cache"                    # 💀 rm -rf "/cache"
```

Any production-ready bash script's minimum viable closing line:

```bash
set -euo pipefail
shopt -s inherit_errexit
```

### What about `IFS=$'\n\t'`?

The classic Maxwell post adds `IFS=$'\n\t'` to neutralise word splitting in `for x in $UNQUOTED`. I deliberately leave it out unless I see code that needs it. Every line of boilerplate has to earn its place; if you are quoting your variables and using arrays for lists (you should be), the IFS line is cognitive overhead with zero payoff. Parnas applied to discipline: **complexity is a cost, even when it's "best-practice" complexity.**

### One more: `trap ERR` for postmortems

`set -e` exits on failure but **doesn't tell you which line died**. One line transforms silent script death into a useful incident-response artifact:

```bash
trap 'echo "❌ failed at line $LINENO: $BASH_COMMAND" >&2' ERR
```

Mandatory in every CI deploy script. Five seconds to add, saves the on-call engineer thirty minutes of bisecting at 3am.

### The principle that survives bash

> **Defaults are political. New code must opt into strictness.**

Bash's defaults are tuned for backwards compatibility with 1989 scripts, not for your 2026 production pipeline. Strict mode is not a fashion choice. It is the absolute minimum civilised baseline. The same principle applies to log levels, CORS policies, k8s NetworkPolicies, and IAM roles: **defaults are the politics of "what was acceptable when this was built", not "what is correct for what you're building now".**

---

## 3. The origin story — Windows paths and the trap of "fixed it but still broken"

By now Alex has rewritten the wait loop, hardened the script with strict mode, added `trap ERR`. Theoretically airtight. He reruns. Fifteen seconds in:

```
❌  Exiting due to GUEST_PROVISION:
    config: '\Program Files\Git\host' container path must be absolute
```

Alex squints. **`\Program Files\Git\host`?** He has never typed that. He greps the entire repo. Nothing.

Welcome to the most cognitively expensive 30 minutes of debugging he will have all year.

### Your shell is not transparent

The string Alex typed was `/host`. The string minikube received was `\Program Files\Git\host`. The extra `\Program Files\Git\` part is — not a coincidence — the install path of Git for Windows.

That fingerprint is the calling card of **MSYS2 path conversion**. Git Bash is not "bash on Windows". It is bash *running on top of an MSYS2 runtime* — a translation layer designed to let POSIX-style command lines invoke native Win32 binaries seamlessly. Helpful 95% of the time. Catastrophic the other 5%.

```
your literal string  ──►  bash variable expansion  ──►  ⚠️ MSYS2 path rewrite  ──►  target binary
                                                              │
                                                              ▼
                                            Heuristic (simplified):
                                            "/foo"        →  <MSYS_ROOT>\foo
                                            "/c/Users/x"  →  C:\Users\x
                                            "//foo"       →  /foo            (escape)
                                            "a:/foo"      →  split on `:`, convert each side
                                            "--flag=/foo" →  convert the value
```

MSYS pattern-matches on the **shape** of the string. It cannot distinguish "a path on the host" from "a path inside a container". Both are `/something` to a string-matcher.

> **Semantics live in your head. Syntax lives in your tools.**

Every layer between you and the kernel may rewrite your input. Whenever a value crosses a boundary — shell to binary, host to container, frontend to backend, ORM to SQL — assume rewriting until you have proof otherwise. I call this **information directionality**: data is never neutral as it crosses contexts; each layer applies its own conversion rules silently.

### The principal-grade fix (not the Stack Overflow magic)

The internet's favourite "fix" is to write `//host` (double slash to suppress conversion). It works. It is also undocumented magic that no future reader will understand. Three months from now your colleague will "clean up that weird double slash" and you will get paged at 11pm.

A principal closes the loop with explicit ownership of every layer:

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

# shellcheck disable=SC2086
env $NO_PATHCONV minikube start \
    --mount --mount-string="${HOST_MOUNT_SRC}:/host" \
    -p platform-minikube
```

Four design choices, each with a justification:

| Choice | Why |
|---|---|
| `case "$(uname -s)"` | The script declares which environment it knows about. Linux/macOS skip the branch entirely; the quirk does not pollute non-affected platforms. |
| `cygpath -m` | Explicit translation beats implicit rewriting. `-m` produces forward-slash mixed paths (`C:/Users/...`) which Docker, Java, and almost every CLI accept. |
| `MSYS_NO_PATHCONV=1` scoped via `env` prefix | Parnas information hiding (1972) applied to shell. The quirk lives **next to its cause**, not at the top of the file. |
| Comment explains *why*, not *what* | Code says what; comments say why. Three years from now this case branch is the only thing keeping the next hire sane. |

Alex applies the fix. Reruns. Holds his breath.

```
Mounting C:/Users/.../proj to /host in Minikube VM
✨  Using the docker driver based on existing profile
🤦  StartHost failed: config: '\Program Files\Git\host' container path must be absolute
```

His shoulders sag. *"It's identical. I changed nothing."*

He had, in fact, changed everything. He just hadn't fixed the system.

### Fixing the code does not fix the system

Look at the second line: **`Using the docker driver based on existing profile`**. Minikube is telling Alex, in plain English, *"I did not use your new flags. I read my old config from disk."*

On the very first `minikube start --mount-string=...`, minikube serialised every parameter into:

```
~/.minikube/profiles/<profile-name>/config.json
```

Every subsequent `minikube start` is a **resume**, not a fresh invocation. The CLI flags you pass on resume are largely ignored — `--mount-string` certainly is. So when the *first* run failed half-way through (because of the path conversion bug we just fixed), it nevertheless wrote the broken `--mount-string` into config.json. From that point forward, no amount of code-level fixing helps. The pollution had moved off the script and onto the disk.

Minikube's own message even tells you so: *"Running `minikube delete -p <profile>` may fix it"*. The project is officially admitting the profile state has poisoned itself.

#### The 2D model: code vs. state

```
                        STATE on disk (~/.minikube/profiles/<name>/config.json)
                        ─────────────────────────────────────────────────────────
                        │   clean                       polluted
        OLD code (bug)  │   buggy first run             buggy + cached
                        │   creates pollution           
                        │
        NEW code (fix)  │   ✅ works first time         ❌ resume reads
                        │                                old polluted state
                        │                                ◄── Alex was here
                        ─────────────────────────────────────────────────────────
```

Fixing the code only moves you down a row. Moving across — cleaning the persisted state — is a separate, deliberate action that no amount of `git pull` will trigger.

The aphorism I carry around for this:

> **`git pull` cannot uncook an egg.**

#### This pattern is universal

Minikube is not special. **Any CLI whose vocabulary includes the words `profile`, `workspace`, `context`, `project`, `environment`, or `release` has a hidden state machine living on disk.** A non-exhaustive list of tools where I have personally seen this pattern bite teams:

| Tool | Hidden state |
|---|---|
| `docker compose` | named volumes, networks, container metadata |
| `terraform` | `terraform.tfstate`, lock file, workspaces |
| `kubectl` | `~/.kube/config` contexts/clusters/users |
| `helm` | `helm.sh/release.v1.<name>` Secret in the cluster |
| `gcloud config configurations` | `~/.config/gcloud/` |
| `aws configure --profile` | `~/.aws/credentials`, `~/.aws/config` |
| Conda / venv | `~/.conda/envs/<name>` |
| npm / pip / poetry lock files | `package-lock.json`, `poetry.lock` |
| Git submodules | `.git/modules/` |

Whenever you adopt a tool from this family, ask one question on day one: *"Where does this thing keep its state, and how do I nuke that state?"* Add the answer to your team's README before you write a single line of glue code.

#### The principal-grade hardening

Tribal knowledge — "if it's still broken, run `minikube delete`" — is a smell. It means the next person to hit the wall has to either know the magic incantation or block the team waiting for someone who does. Encode it:

```bash
CLEAN=0
for arg in "$@"; do
    case "$arg" in
        --clean | --force) CLEAN=1 ;;
    esac
done

if [[ "$CLEAN" -eq 1 ]]; then
    echo "🧹 --clean: deleting any existing profile to clear stale config..."
    minikube delete -p platform-minikube || true
fi
```

One line in the README:

> *If your error says "Using existing profile" followed by something weird, rerun with `--clean`.*

That single change — moving recovery from oral tradition into the script — is one of the fastest ways to look senior on a new team.

---

## Closing the loop: three maps you walk away with

These three lessons — declarative readiness, strict mode, code-vs-state — are not about Kubernetes, bash, or minikube. They are three maps of meta-structure that recur in every tool you will ever use.

| Map | What it shows | Where it applies |
|---|---|---|
| **Declarative beats imperative** | When the platform offers a first-class "wait for X" primitive, every line of polling you write is a re-implementation of an existing reconcile loop. | Kubernetes, Docker, Helm, Terraform, systemd — any tool with a built-in wait/rollout |
| **Defaults are political** | Bash's defaults are tuned for backwards compatibility with 1989, not for your 2026 production script. Strict mode is not optional; it is the absolute minimum civilised baseline. | Any shell, any framework, any "out of the box" config |
| **Code vs. state** | Persisted state is a separate dimension from source code. Fixing one without addressing the other is the source of most "but I fixed it!" outages. | Any CLI with profile/context/workspace concepts; any IaC tool with a state file |

Every kubectl, terraform, docker, gcloud, and helm script you have ever written sits on these three maps. Once you can see them, you start reading other people's scripts the way a chess grandmaster reads board positions: not as moves, but as patterns.

---

## What to do this week

If you want this to stick, do three things before Friday:

1. **Audit your most-run deploy script for the three smell families:**
   - any `sleep N` followed by a comment containing "wait for" → replace with `kubectl wait` / `--wait` / `rollout status`
   - any pipeline ending in `wc -l` or `head -n 1` feeding a numeric comparison → replace with API queries
   - any `set -e` without `-u`, `pipefail`, and `inherit_errexit` → upgrade to full strict mode in one commit

2. **Add a `--clean` (or equivalent reset) flag** to any init script that drives a CLI with a `profile`/`context`/`workspace` concept. Document when to use it. You just turned tribal knowledge into a code artifact — that is the day-job of a principal.

3. **Add one line to your team README**: *"If an error message starts with 'Using existing X', rerun with `--clean` before debugging anything else."* That single sentence will save your team a quarter-hour per new joiner forever.

---

## What's next

The next post in this thread is **"Why your second `terraform apply` is not doing what you think"** — same code-vs-state spine, but in the IaC universe, where state drift and provider lock files turn the trap into something much harder to spot.

If this resonated, send it to the colleague who lost yesterday evening to a deploy script's race condition.

---

> *The bug is not in your terminal. It is in the map between you and your tool.*
