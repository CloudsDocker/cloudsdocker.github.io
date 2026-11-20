## 1. Command Anatomy: `uvx bandit -q -s B101`

This command executes an ephemeral, quiet security scan of Python code while suppressing the most common false positive in Python testing (`assert` statements).

| Token | Component | SME Breakdown |
| --- | --- | --- |
| **`uvx`** | Ephemeral Tool Runner | An alias for `uv tool run` (built in Rust by Astral). It downloads and runs `bandit` in an isolated, temporary virtual environment without polluting your global Python environment or `pyproject.toml` dependencies. |
| **`bandit`** | SAST Engine | PyCQA's Static Application Security Testing (SAST) tool for Python. It parses Python source files into an **Abstract Syntax Tree (AST)** and runs security plugins against the AST nodes to flag vulnerabilities. |
| **`-q`** | Quiet Mode | Suppresses progress bars, informational banners, and summary noise, outputting **only** when security findings are detected. Ideal for CI/CD logs and pre-commit hooks. |
| **`-s B101`** | Skip Rule `B101` | Skips test ID **`B101` (`assert_used`)**. Bandit flags `assert` statements because running Python with the optimize flag (`python -O`) strips all `assert` calls, which can bypass security checks if developers misuse `assert` for authentication or validation. However, `pytest` relies heavily on `assert`, so teams routinely skip `B101` globally or on test directories. |

> **SME Note:** On its own, `uvx bandit -q -s B101` needs a target path to scan. In practice, you will run it recursively against your source directory:
> ```bash
> uvx bandit -q -s B101 -r src/
> 
> ```
> 
> 

---

## 2. Deep Dive: Mastering Bandit as an SME

To operate at an SME level with Bandit, you need to move beyond basic CLI flags and leverage its enterprise workflow features:

* **Severity vs. Confidence Filtering:** Bandit scores every finding on two axes—**Severity** (Low, Medium, High) and **Confidence** (Low, Medium, High). Use `-ll` (Medium+ severity) and `-ii` (Medium+ confidence) to eliminate alert fatigue in legacy codebases.
* **Baseline Scanning (`-b`):** When introducing Bandit to a massive legacy repo, you cannot fix 500 findings overnight. Generate a JSON baseline of existing issues (`bandit -r src/ -f json -o baseline.json`), then run future CI checks with `-b baseline.json` so the pipeline **only fails on newly introduced vulnerabilities**.
* **SARIF Integration:** Install or run with the SARIF extra (`uvx --from "bandit[sarif]" bandit -r src/ -f sarif -o results.sarif`) to upload findings directly into GitHub Advanced Security, GitLab Security Dashboard, or Azure DevOps.
* **Declarative Configuration:** Avoid long CLI strings by storing rules in `pyproject.toml` (natively supported via `tomllib` on Python 3.11+):
```toml
[tool.bandit]
exclude_dirs = ["tests", ".venv"]
skips = ["B101"]

```



---

## 3. Tooling Comparison: Bandit vs. Ruff vs. The Ecosystem

The Python tooling landscape has undergone a massive shift toward Rust-based consolidation. **Ruff** (created by Astral, which OpenAI announced plans to acquire in March 2026) reimplemented the majority of Bandit's security rules under its `S` (`flake8-bandit`) rule prefix.

| Dimension | **Bandit** | **Ruff (`--select S`)** | **Pylint / Flake8** | **Mypy / Pyright** |
| --- | --- | --- | --- | --- |
| **Primary Role** | Dedicated Python SAST | All-in-one Linter & Formatter (900+ rules) | Traditional Linting & Code Smells | Static Type Checking |
| **Engine / Language** | Python (AST-based) | Rust (Custom AST engine) | Python | Python (Mypy) / TypeScript (Pyright) |
| **Scan Speed** | ~1,000 lines/sec (~5 min on large repos) | ~25,000+ lines/sec (~12 sec on same repo; ~25x–100x faster) | Slow (minutes on large repos) | Moderate to Fast |
| **Security Coverage** | **Deepest native Python AST security rules** (including niche crypto & ML/torch rules) | **~90%+ parity** with Bandit's core rules; minor gaps in exotic/newest checks | Minimal (requires plugins) | None (prevents type bugs, not exploits) |
| **Auto-Fix** | No | Yes (`ruff check --fix`) | No | No |
| **Compliance / Reporting** | Built-in SARIF, HTML, XML, CSV, Baseline | SARIF, JSON, GitHub, GitLab | Text, JSON | Text, JSON |

### When does Bandit still beat Ruff?

1. **Strict Security & Compliance Audits:** Bandit's native severity/confidence matrix, baseline diffing (`-b`), and HTML/CSV audit reports are purpose-built for AppSec teams.
2. **Rule Parity Gaps:** Ruff does not yet port 100% of Bandit's newest or most specialized plugins (such as certain cryptographic edge cases or specific `torch.load` / trojan source checks).
3. **Inline Suppression Separation:** Keeping `# nosec` (Bandit) separate from `# noqa` (Ruff) allows AppSec teams to audit security bypasses independently of style/lint bypasses.

---

## 4. How Leading World Companies & Projects Use These Tools

### Ruff (The Modern Industry Standard)

Ruff has become the de facto standard across the world's largest Python codebases, replacing Flake8, Black, isort, pyupgrade, and—for many teams—Bandit's everyday checks:

* **Apache Airflow:** Reduced pre-commit linting time from **1 minute 40 seconds down to 6 seconds** after migrating to Ruff.
* **FastAPI:** Uses Ruff for both linting and formatting, replacing five separate tools (`flake8`, `autoflake`, `isort`, `pyupgrade`, `black`).
* **Pandas & SciPy:** Run Ruff across massive scientific computing codebases (Pandas lints in ~3.35 seconds).
* **Hugging Face, Pydantic, Jupyter, & Apache Superset:** All rely on Ruff in their core CI pipelines.
* **Dagster:** Reported a **~1000x speed-up** over Pylint across 50+ monorepo modules.
* **Enterprise CI Cost Savings:** Large engineering orgs moving from legacy Python linters to Ruff have reported saving tens of thousands of dollars per month in CI runner compute bills.

### Bandit (The Enterprise Security Staple)

* **OpenStack:** Bandit was originally built by the **OpenStack Security Project** to secure massive cloud infrastructure codebases before being transferred to PyCQA.
* **Enterprise Cloud & Regulated Industries:** Bandit remains embedded in enterprise DevSecOps pipelines (often distributed via container images on `ghcr.io` or cloud marketplaces like Microsoft Marketplace) as a dedicated SAST gate alongside tools like Semgrep or Snyk.

---

## 5. The SME Playbook: Recommended Production Setup

As an SME, you should **not** force developers to wait minutes for Bandit locally, nor should you rely solely on a linter if you are in a high-compliance environment. Use a **two-tier architecture**:

1. **Local Dev & Pre-Commit (Speed First — Ruff):**
Enable Ruff's `S` (Bandit) rules in `pyproject.toml` so developers get instant, millisecond-level security feedback right in VS Code or on `git commit`.
```bash
uvx ruff check --select S --fix src/
uvx ruff format src/

```


*(Always run `ruff check --fix` before `ruff format` so autofixes don't break formatting.)*
2. **CI/CD Security Gate (Depth & Compliance — Bandit):**
If your organization requires SARIF security dashboards, baseline tracking, or 100% coverage of Bandit's specialized plugins, run Bandit asynchronously in CI:
```bash
uvx --from "bandit[sarif]" bandit -q -s B101 -ll -r src/ -f sarif -o bandit.sarif

```


To take you from zero to SME on Ruff using the **ICAP framework** (Passive → Active → Constructive → Interactive), we will use your exact virtual environment as a live sandbox.

First, set a shell alias so every command below runs directly from your isolated install:

```bash
export RUFF="/tmp/edr-common-python-ruff-sme/bin/ruff"
$RUFF --version

```

---

## Stage 1: Passive (P) — The SME Mental Model

Before touching code, internalize the three architectural truths that separate Ruff SMEs from casual users:

1. **Two Distinct Engines in One Binary:**
* **`ruff check` (The Linter):** Analyzes your AST against 900+ rules (replacing Flake8, isort, pyupgrade, Bandit, and parts of Pylint) to catch bugs, unused imports, security flaws, and outdated syntax.
* **`ruff format` (The Formatter):** A near-drop-in replacement for Black (>99.9% compatible) that only touches whitespace, quotes, trailing commas, and line wrapping.


2. **The Golden Execution Order:**
Always run **`ruff check --fix` BEFORE `ruff format**`. If you format first, the linter's auto-fixes (like sorting imports or rewriting comprehensions) can break the formatting you just applied.
3. **Never Use `select = ["ALL"]`:**
Enabling all rules at once triggers conflicting rules and massive noise. SMEs roll out rules in **Tiers**:

| Tier | Rule Prefixes | What It Enforces | Best For |
| --- | --- | --- | --- |
| **Tier 1 (Baseline)** | `E`, `W`, `F`, `I` | PEP 8 errors/warnings, Pyflakes (unused vars/imports), isort (import sorting) | Day 1 on any legacy repo |
| **Tier 2 (Modern SME)** | `B`, `UP`, `SIM`, `C4`, `RUF` | Bugbear (bug-prone patterns), pyupgrade (modern Python syntax), simplify, comprehensions, Ruff-native | Standard production services |
| **Tier 3 (Hardened)** | `S`, `D`, `PL`, `ANN` | Bandit security rules (`S`), docstrings (`D`), Pylint (`PL`), type annotations (`ANN`) | Security-critical / enterprise code |

---

## Stage 2: Active (A) — Hands-On Sandbox Lab

Now manipulate Ruff directly in your `/tmp` environment to see **Safe vs. Unsafe fixes**, **Rule Inspection**, and **Formatting** in action.

### 1. Create a deliberately flawed Python file

```bash
cat << 'EOF' > /tmp/edr-common-python-ruff-sme/lab.py
import sys, os
import subprocess

def run_cmd(user_input, items=[]):
    assert user_input != ""
    if len(items) > 0:
        x = [i for i in items]
        subprocess.Popen(user_input, shell=True)
    return True
EOF

```

### 2. Run a diagnostic scan (Tier 1 + Tier 2 + Bandit Security `S`)

```bash
$RUFF check --select E,W,F,I,B,UP,SIM,S /tmp/edr-common-python-ruff-sme/lab.py

```

**What to observe:** Ruff will flag `F401` (unused `os`/`sys`), `B006` (mutable default argument `items=[]`), `S101` (`assert` used — Bandit's `B101` equivalent), and `S602` (`subprocess` with `shell=True`).

### 3. Inspect a rule like an SME

Instead of Googling an error code, query Ruff's built-in documentation:

```bash
$RUFF rule B006
$RUFF rule S602

```

### 4. Apply Safe Fixes, then Format

```bash
$RUFF check --select E,W,F,I,B,UP,SIM,S --fix /tmp/edr-common-python-ruff-sme/lab.py
$RUFF format /tmp/edr-common-python-ruff-sme/lab.py
cat /tmp/edr-common-python-ruff-sme/lab.py

```

**What to observe:** Ruff automatically removes the unused imports and fixes formatting, but **refuses** to auto-fix `B006` or `S602` because changing runtime behavior is an **unsafe fix** (requiring `--unsafe-fixes` or manual intervention).

---

## Stage 3: Constructive (C) — Architecting Production Config

CLI flags don't scale across teams. To move to the Constructive stage, create a production-grade `pyproject.toml` in your sandbox that encodes your team's standards—including **per-file ignores** (so `assert` is allowed in `tests/` but blocked in `src/`).

Create `/tmp/edr-common-python-ruff-sme/pyproject.toml` with this template, then **modify it** to fit your own project's Python version and line length:

```toml
[tool.ruff]
target-version = "py312"
line-length = 100
exclude = [".venv", "migrations"]

[tool.ruff.lint]
# Tier 1 + Tier 2 + Bandit Security (S)
select = ["E", "W", "F", "I", "B", "UP", "SIM", "C4", "S", "RUF"]

# Ignore rules that conflict with the formatter or are too noisy
ignore = ["E501"]

[tool.ruff.lint.per-file-ignores]
# Allow assert (S101) and hardcoded test passwords (S105) ONLY in test files
"tests/**/*.py" = ["S101", "S105"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true

```

Test your config against your lab file:

```bash
$RUFF check --config /tmp/edr-common-python-ruff-sme/pyproject.toml /tmp/edr-common-python-ruff-sme/lab.py

```

**Your Constructive Task:**

1. Add a `# noqa: S602` (or `# ruff: ignore[S602]`) inline suppression to `lab.py` and re-run the check to verify it clears.
2. Rename `lab.py` into a `tests/test_lab.py` folder and verify that `S101` (`assert`) automatically stops triggering while `S602` still fails.

---

## Stage 4: Interactive (I) — The SME Gauntlet

To lock in SME mastery, let's work through a real-world engineering scenario together.

**The Scenario:**
You just inherited a 150,000-line legacy Python repository with **no** linter, **no** formatter, and 40 active developers. Management wants Ruff enforced in CI/CD by next Friday, and AppSec wants Bandit security rules (`S`) active—**without** blocking current feature PRs with 4,000 legacy lint errors.

Reply with your proposed strategy for:

1. Which **Tier** of rules you would turn on in Week 1 vs. Month 2.
2. How you would prevent the 4,000 existing violations from breaking every developer's PR on Day 1.
3. What exact two commands you would put in the GitHub Actions CI step (and in what order).

Once you share your plan, I'll critique it from a Principal Engineer / AppSec perspective and show you the exact Ruff flags (`--diff`, `--exit-zero`, `--add-noqa`, or git-diff scoping) used by top engineering teams to pull this off cleanly.


