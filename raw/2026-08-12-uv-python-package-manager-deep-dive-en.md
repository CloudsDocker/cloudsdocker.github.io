---
title: "What Makes uv Fast: A Deep Dive Starting from One Scratchpad Command"
date: 2026-08-12
categories: [engineering, python, tooling]
tags: [uv, pip, venv, python-packaging, shell, ci-cd]
---

While debugging a nonstandard-etl project, a throwaway `uv venv` + `uv pip install`
command triggered a rabbit hole: from "it works" to "why is it so fast" to "how do you
actually use it properly." This post is the write-up of that exploration.

## Part 1: What That Command Actually Does

The original command looked like this (paths sanitized):

```bash
SP=/path/to/scratchpad
uv venv --python 3.11 "$SP/venv311"
uv pip install --python "$SP/venv311/bin/python" \
  'boto3>=1.28.11,<2' 'requests>=2.31.0,<3' 'pandas>=2.1.4,<3' \
  'numpy>=1.26.3,<2' 'pyarrow>=17.0.0,<18' \
  'pytest>=7.4.2,<8' 'pytest-cov>=4.1.0,<5' 'moto>=4.2.3,<5' \
  'edr-common-python @ git+ssh://git@github.com/your-org/edr-common-python.git'
```

One-line summary: **use `uv` to create a clean Python 3.11 virtual environment inside a
project's scratchpad directory, then install a full toolchain that can talk to AWS, run
tests, and pull from a private company repo.**

The packages fall into three groups — like kitting out a new recruit:

| Category | Packages | What they're for |
|---|---|---|
| 🛠️ Working gear | `boto3`, `requests`, `pandas`, `numpy`, `pyarrow` | Talk to AWS, make HTTP calls, wrangle tabular data, read/write Parquet |
| 🧪 Safety gear | `pytest`, `pytest-cov`, `moto` | Run tests, measure coverage, and **pretend** to talk to AWS (moto mocks AWS, no real cloud spend) |
| 🔒 The secret weapon | `edr-common-python` (pulled via `git+ssh://` from a private repo) | An internal shared library — installing it requires a properly configured local SSH key |

Hard-won lessons:

1. If the `git+ssh://` line fails, it's a missing SSH key 99% of the time. Run
   `ssh -T git@github.com` to check before blaming `uv`.
2. `scratchpad` means exactly what it says — throwaway. These environments are rarely
   reused; rebuilding from scratch each time is the point, since it guarantees a clean slate.

## Part 2: What Actually Makes uv Faster Than pip/venv

The core trick: a dependency resolver written in Rust, paired with a global cache. It
turns package installation from "brew fresh coffee every time" into "grab a cold brew
from the fridge." The same `requirements.txt` that takes `pip` 30 seconds takes `uv`
1-2 seconds — that's not marketing copy, it's a reproducible number.

An analogy:

- **`pip`'s approach**: every time an order comes in, walk back to the warehouse,
  re-read the ingredient list, recompute compatibility, then fetch fresh from the
  supplier. Slow but straightforward.
- **`venv`'s approach**: open a brand-new kitchen (virtual environment) for every order
  — kitchens don't interfere with each other, but every kitchen has to set up its own
  pots and pans from scratch.
- **`uv`'s approach**: it does the job of `pip` + `venv` + `pip-tools` all by itself,
  and keeps a "central warehouse" (the global cache at `~/.cache/uv`) — once a given
  package version has been downloaded and unpacked, every future project and virtual
  environment gets it via a hard link instead of re-downloading and re-extracting.
  That's the secret behind the "instant" feeling.

Hard-won lessons:

1. The resolver really is stronger. `pip`'s resolver is notorious for "first-come,
   first-installed, backtrack on conflict," which can hang or produce incompatible
   combinations on complex dependency trees. `uv` uses the more modern PubGrub
   algorithm (same family as Rust's `cargo` and Dart's `pub`), and reports conflicts
   with much clearer errors.
2. `uv venv` isn't the same binary as `python -m venv`, but it produces the same
   environment layout — your old `source venv/bin/activate` muscle memory still works.
3. The global cache is a double-edged sword: leave `~/.cache/uv` unattended long enough
   and it will grow, so run `uv cache clean` occasionally.

## Part 3: `uv pip install` vs `uv add` (There's No Such Thing as `uv install`)

There is no `uv install` command — `uv` ships two entirely separate "install packages"
interfaces, and `uv pip install` is deliberately the "backward-compatible" one of the two.

**Camp one: `uv pip *` (compatibility layer, mimics the traditional pip workflow)**

```bash
uv pip install boto3    # install straight into the current/specified venv
uv pip compile          # equivalent to pip-tools' compile
uv pip sync             # equivalent to pip-tools' sync
```

Its whole purpose: your existing `requirements.txt` + `pip install -r` workflow doesn't
need to change a single character — swap `pip` for `uv pip` and get a free 10-100x
speedup. The command in Part 1 is exactly this pattern.

**Camp two: `uv add` / `uv sync` / `uv run` (uv's native "project" workflow)**

```bash
uv add boto3            # add a dependency to pyproject.toml, update uv.lock, install it
uv sync                 # reproduce the environment exactly per uv.lock (use in CI / team settings)
uv run script.py        # ensures dependencies are installed, then runs the script
```

This is the workflow `uv` actually wants you to use going forward, managing
`pyproject.toml` + `uv.lock`. Semantically it's "add an entry to the project manifest,"
not "blindly install a package" — hence `add`, not `install`.

Hard-won lessons:

1. The two interfaces are unaware of each other. Packages installed via `uv pip install`
   don't get written into `pyproject.toml`/`uv.lock`, and `uv add` doesn't look at
   whatever you manually `uv pip install`ed. Mixing them is fighting yourself with both
   hands — avoid it in team settings.
2. One-off, throwaway sandboxes are a good fit for `uv pip install`; long-lived projects
   should use `uv add` + `uv.lock`.
3. There's a third, easily confused command: `uv tool install` — for installing global
   CLI tools (similar to `pipx install`). It's unrelated to the other two; what it
   installs doesn't land in any venv, it goes straight onto your PATH.

## Part 4: The Full `uv add` + `uv.lock` Workflow

Three steps: `uv init` to scaffold a project → `uv add xxx` to add dependencies
(automatically writes to `pyproject.toml` and creates/updates `uv.lock`) → `uv sync` or
`uv run` to reproduce the exact same environment on any machine. The core idea:
`pyproject.toml` says "what I want," `uv.lock` says "the exact version and hash that
was actually installed." Both files go into git — a teammate clones the repo, runs
`uv sync`, and ends up with an environment identical to yours.

```bash
# 1. Scaffold a project (generates pyproject.toml + an empty .venv)
uv init my-etl-project
cd my-etl-project

# 2. Add dependencies — this does three things at once:
#    installs into .venv / writes to pyproject.toml / updates uv.lock
uv add boto3 pandas pyarrow

# 3. Environment-specific dependencies via groups
#    (the old pip-era equivalent of requirements-dev.txt)
uv add --dev pytest pytest-cov moto

# 4. A teammate clones your project and reproduces your environment in one line
uv sync

# 5. Skip manual activation, just run
uv run pytest
```

Compared with the scratchpad command from Part 1:

| | Scratchpad command (`uv pip install`) | Project workflow (`uv add`) |
|---|---|---|
| Purpose | One-off, discard after use | Long-lived, shared across team/CI |
| Version tracking | None — relies entirely on manually typed version ranges | `uv.lock` pins to exact hash |
| Reproducing it | Copy-paste the long command again | One line: `uv sync` |

Hard-won lessons:

1. `uv add` by default records a "loose" constraint, while `uv.lock` is the "exact"
   constraint. `pyproject.toml` will show ranges like `boto3>=1.28.11,<2` (the same
   style used in the hand-typed scratchpad command), but what actually determines
   whether today's install is `1.28.11` or `1.35.0` is `uv.lock`. Ranges are for
   humans, the lockfile is for machines — commit both, neither is optional.
2. `uv.lock` conflicts are a new source of merge noise for teams. When multiple people
   `uv add` different packages at once, this large auto-generated file merges badly.
   Adopting the convention "whoever changes dependencies rebases first, then `add`s"
   saves a lot of pain.
3. Always use `uv sync --frozen` in CI, never plain `uv sync` or `uv add`. `--frozen`
   refuses any "quietly bump the lockfile" behavior — if the lockfile doesn't match, it
   fails loudly instead of silently updating. This is the key switch that guarantees
   your CI environment matches your local environment **exactly**, and it's the step
   newcomers most often forget.
