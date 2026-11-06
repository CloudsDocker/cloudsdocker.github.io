---
title: "Poetry in CI/Docker: From a Three-Part Sanity Check to Production-Grade Deployments"
date: 2026-11-06
categories: [engineering, python, devops]
tags: [poetry, docker, ci-cd, github-actions, python-packaging, best-practices]
---

# Poetry in CI/Docker: From a Three-Part Sanity Check to Production-Grade Deployments

While tidying up a CI pipeline recently, I took a deep dive into Poetry's operational patterns. Starting from a seemingly simple pre-commit check command, I ended up revisiting Docker multi-stage builds and CI caching strategies. Here's everything I found.

---

## Part 1: Dissecting a Three-Part Sanity Check

```bash
git branch --show-current && poetry check --lock && git -c core.whitespace=cr-at-eol diff --check
```

Three checks chained with `&&` — each runs only if the previous one succeeds. A classic **pre-commit gate**.

### Breaking It Down

**`git branch --show-current`** — Prints the current branch name. Pure output, no side effects. Often used in scripts to dynamically capture the branch name for downstream logic.

**`poetry check --lock`** — Verifies that `poetry.lock` is consistent with `pyproject.toml`. If you added a dependency but forgot to run `poetry lock`, this catches it. Prevents the classic "works on my machine, blows up in CI" scenario.

**`git -c core.whitespace=cr-at-eol diff --check`** — Scans the git diff for whitespace errors (trailing spaces, mixed tabs) while **tolerating Windows-style `\r\n` line endings**. The `-c core.whitespace=cr-at-eol` is a temporary config override — essential for cross-platform projects. `diff --check` is read-only; it returns a non-zero exit code on violations.

### The Intent

> Am I on the right branch? → Is the lockfile in sync? → Is the code free of dirty whitespace?

All three pass or nothing proceeds. Fail-safe by design.

---

## Part 2: Poetry's Big Three — check vs lock vs install

In one sentence: **check is the inspector, lock is the procurement planner, install is the warehouse worker.**

| | `poetry check` | `poetry lock` | `poetry install` |
|---|---|---|---|
| **What it does** | Read-only config validation | Resolves deps, writes lockfile | Actually installs packages |
| **Modifies files?** | ❌ Nothing | ✅ Writes `poetry.lock` | ❌ No config changes, but populates `.venv` |
| **Needs network?** | ❌ Pure local | ✅ Queries PyPI | ✅ Downloads packages |
| **Speed** | Milliseconds | Can be slow | Depends on package count |
| **CI role** | Gate check | Rarely run in CI | Environment setup |

### `poetry check`

Validates `pyproject.toml` structure. With `--lock`, also verifies the lockfile is in sync. No installs, no network, pure static analysis.

### `poetry lock`

Resolves all dependencies (including transitive ones) to exact versions based on `pyproject.toml` constraints, then writes them to `poetry.lock`.

- `poetry lock` → Full re-resolve, may upgrade versions
- `poetry lock --no-update` → Only add missing entries, don't touch existing ones (safer)

### `poetry install`

Reads `poetry.lock` and installs packages into the virtual environment.

- `poetry install` → All deps + your project itself
- `poetry install --no-root` → Deps only, skip the project package (common in CI)
- `poetry install --sync` → Strict sync — removes packages not in the lockfile (recommended for CI)

### The Standard Workflow

```
Edit pyproject.toml
    ↓
poetry lock          # Re-resolve the lockfile
    ↓
poetry install       # Install locally
    ↓
git add pyproject.toml poetry.lock   # Always commit both!
    ↓
CI: poetry check --lock → poetry install --sync
```

**Golden rule: `pyproject.toml` and `poetry.lock` are always committed together. Separate them and things break.**

---

## Part 3: `poetry install --sync` Best Practices for CI & Docker

### Why `--sync` Is Non-Negotiable

Without `--sync`, this happens:

```
Previously installed pandas 2.0
→ Remove pandas from pyproject.toml
→ poetry install
→ pandas is STILL in the environment! Code runs fine!
→ Deploy to production → 💥
```

With `--sync`: **the environment matches the lockfile exactly. Extra packages get removed. No ghosts.**

### Docker Best Practice Template

```dockerfile
FROM python:3.12-slim

# 1. Install poetry; skip virtualenv inside the container
ENV POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

# 2. Copy dependency files first → leverage Docker layer caching
COPY pyproject.toml poetry.lock ./

# 3. Install deps only, not the project itself
RUN poetry install --sync --no-root --only=main \
    && rm -rf $POETRY_CACHE_DIR

# 4. Copy source code (code changes don't trigger dep reinstall)
COPY . .

# 5. Install the project package itself
RUN poetry install --only-root
```

**Key techniques explained:**

| Technique | Why |
|---|---|
| `VIRTUALENVS_CREATE=false` | The container IS the isolation — no nested virtualenv needed |
| COPY lockfiles before code | Docker layer caching — deps unchanged means no reinstall |
| `--no-root` | Don't install the project package until the source code arrives |
| `--only=main` | Skip dev dependencies (pytest, black aren't needed in production) |
| Clean the cache | Smaller image — the cache is useless inside the final container |

### GitHub Actions Best Practice

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - name: Cache poetry
        uses: actions/cache@v4
        with:
          path: |
            ~/.local
            .venv
          key: poetry-${{ hashFiles('poetry.lock') }}
      
      - name: Install poetry
        run: pipx install poetry
      
      - name: Install deps
        run: |
          poetry config virtualenvs.in-project true
          poetry check --lock
          poetry install --sync
      
      - name: Test
        run: poetry run pytest
```

**CI key points:**

- `virtualenvs.in-project true` — Puts `.venv` inside the project so `actions/cache` can reach it
- `hashFiles('poetry.lock')` as cache key — Only reinstall when dependencies actually change
- `check --lock` before `install` — Inspect before you install; fail fast on lockfile drift

### Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Forgot `--sync` | Removed packages persist as ghost deps | Always use `--sync` |
| Virtualenv enabled in Docker | Image bloated by 100MB+, path confusion | `VIRTUALENVS_CREATE=false` |
| `COPY . .` before dep install | Every code change triggers a full reinstall | COPY lockfiles first |
| No CI caching | 3-minute dep install on every run | Cache on `poetry.lock` hash |

---

## TL;DR

> In Docker, disable virtualenvs. In CI, use in-project venvs. Copy lockfiles before source code. Always use `--sync`. Ghost dependencies die in the light.
