---
title: "The Night pip Stopped Working: Two Walls in Ubuntu 24.04 and the One venv Move That Disarms Both"
date: 2026-10-01
categories: [engineering, python, linux]
tags: [pip, venv, PEP668, ubuntu, ensurepip, pipenv]
---

# The Night pip Stopped Working: Two Walls in Ubuntu 24.04 and the One venv Move That Disarms Both

The task was supposed to be trivial. I'd edited a few repos' `Pipfile`s to point their package source at the company's internal Nexus proxy. All that was left was to run `pipenv lock` on a machine with VPN access and regenerate the lock file.

That one command tipped over the first domino:

```text
$ pipenv lock
command not found: pipenv

$ python3 -m pip install --user pipenv
/usr/bin/python3: No module named pip

$ python3 -m ensurepip --upgrade
ensurepip is disabled in Debian/Ubuntu for the system python.
```

How does "install pipenv" collapse all the way down to "there's no pip, and even ensurepip is turned off"? And more unsettling: **is this a lock my company put on my machine? Why have I never hit this before?**

This post walks the whole thing down to the source: the two walls, the single switch they both hinge on, and why one cheap `venv` disarms both.

---

## TL;DR

- Modern Ubuntu (24.04) puts **two walls** in front of the **system Python** to stop you installing into it:
  - **Wall 1 — PEP 668**: an `EXTERNALLY-MANAGED` marker file sits next to the interpreter; pip sees it and refuses with `externally-managed-environment`.
  - **Wall 2 — Debian-disabled ensurepip**: downstream patched `ensurepip` to `sys.exit(1)` in the system Python.
- `--user` **does not save you** — it still targets the system interpreter's package set, so Wall 1 still applies.
- Both walls hinge on the **same switch**: `sys.prefix != sys.base_prefix`. Stand inside a venv and that's true, so **both walls stand down at once**.
- Hence the four-line venv fix: inside a venv, pip is already present, there's no marker file, and ensurepip steps aside.
- This is **not a company lock** — it's a stock distro default. You hadn't seen it because your older boxes were 22.04, or because pyenv/conda/docker kept you off the system Python entirely.

---

## The big picture: two walls, guarding the same thing

Every failed command hit a guard Debian/Ubuntu adds to the **system** Python. All of them ask one question: **"Are you trying to modify the system Python itself?"**

| Command | Wall that stopped it |
|---|---|
| `pip install --user … pipenv` | **Wall 1** — PEP 668 `EXTERNALLY-MANAGED` marker |
| `python3 -m ensurepip --upgrade` | **Wall 2** — Debian's patched, disabled `ensurepip` |
| `/usr/bin/python3 -m pip …` (first error) | pip isn't even installed for system python (Debian unbundles it) |

## Wall 1 — PEP 668's `EXTERNALLY-MANAGED`

Read it yourself:

```bash
cat /usr/lib/python3.12/EXTERNALLY-MANAGED
```

It's **not code** — it's a plain INI file. Its *existence* is the signal. On startup pip checks whether an `EXTERNALLY-MANAGED` file sits in the interpreter's stdlib dir; if so it refuses and prints that file's `Error=` text verbatim.

The rationale (PEP 668, 2022): on a distro where `apt`/`dpkg` own `/usr/lib/python3/...`, letting pip write there too means two package managers fighting over the same files — a recipe for broken system tools. So the distro drops this marker to tell pip: **"hands off this Python."**

Key consequence: **`--user` doesn't help.** `pip install --user` still targets the *system* interpreter's package set, so the marker still applies.

## Wall 2 — Debian's disabled `ensurepip`

```bash
sed -n '8,40p' /usr/lib/python3.12/ensurepip/__init__.py
```

The function that prints your error:

```python
if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
    return                       # inside a venv? bail early, do NOT refuse

# only reached in the SYSTEM python:
print('''ensurepip is disabled in Debian/Ubuntu for the system python. ...''')
sys.exit(1)
```

**This one line is the whole secret.** Debian didn't blanket-disable ensurepip — it disabled it *only when `sys.prefix == sys.base_prefix`*.

## The real switch: `sys.prefix` vs `sys.base_prefix`

- `sys.base_prefix` = where the **real** Python install lives (`/usr`).
- `sys.prefix` = where the **currently active** environment lives.

In the system Python they're identical. Inside a venv, `sys.prefix` becomes the venv dir while `base_prefix` still points at `/usr`. Proven live on the box:

```text
System python:   prefix=/usr             base_prefix=/usr           → SAME  → both walls active
Inside a venv:   prefix=/tmp/demo-venv   base_prefix=/usr           → DIFFER → walls stand down
```

That `prefix != base_prefix` check is *literally* how ensurepip decides to step aside, and a venv dir has **no `EXTERNALLY-MANAGED` file**, so pip's Wall-1 check also comes up empty. **One act — entering a venv — disarms both walls.** Not a flag, not `sudo`, not `--user`.

## The fix, line by line

```bash
sudo apt-get install -y python3-venv
```
Debian splits the stdlib across packages. The pip-bootstrap wheels `venv` needs live in a separate package (`python3-venv` / `python3-pip-whl`), not in base Python. Without it, `python3 -m venv` creates a venv with **no pip inside**. This guarantees the wheels are present.

```bash
python3 -m venv ~/.venvs/lock && source ~/.venvs/lock/bin/activate
```
- `python3 -m venv ~/.venvs/lock` builds a new environment: a `bin/python` symlinked back to `/usr/bin/python3.12`, a `pyvenv.cfg` recording `home = /usr/bin` (that's what makes `base_prefix` point at `/usr`), and — because the wheels exist — it runs its *own* internal ensurepip to drop `pip` into the venv. That internal ensurepip hits the `prefix != base_prefix` early return and proceeds. Result: a fresh venv already ships `bin/pip`.
- `source .../activate` just prepends the venv's `bin/` to `$PATH` (and sets `$VIRTUAL_ENV`), so `python`/`pip` now resolve to the venv's copies, not `/usr/bin`'s.

```bash
pip install --index-url https://nexus.qantasloyalty.io/repository/pypi-all/simple pipenv
```
- This `pip` is the venv's pip → no `EXTERNALLY-MANAGED` wall → install proceeds.
- `--index-url` **replaces** the default `https://pypi.org/simple` for *this install*, pulling pipenv from the internal Nexus proxy (public PyPI is likely firewalled). Nexus `pypi-all` is a transparent proxy, so the packages/hashes match PyPI.

```bash
cd edr-pgp && pipenv lock
```
- `pipenv lock` reads the repo's `Pipfile`, resolves the dependency graph, and writes `Pipfile.lock` with pinned versions + hashes. It takes its index from the **`Pipfile`'s `[[source]]`** (already pointed at Nexus) — **not** the `--index-url` above (that only governed installing pipenv itself).

> **Two index URLs, two jobs.** The `--index-url` flag sources *pipenv the tool*; the `Pipfile`'s `[[source]]` sources *the project's locked deps*. Conflating them is the classic "I set the index but the lock still points at pypi" bug.

---

## The interviewer's follow-up chain

**Q1: Why is `pip install --user` refused on new Ubuntu? Isn't `--user` the safe, user-local install?**
Because the real dividing line isn't *user vs global* — it's *system interpreter vs venv interpreter*. `--user` still writes against the **system** interpreter's package set, so PEP 668 blocks it just like a global install. This intuition trap catches a lot of people.

**Q2: How does a venv actually bypass it? Is it a copy of Python?**
Not a copy. A venv is a thin **redirect**: a `pyvenv.cfg` plus symlinks that change `sys.prefix` while leaving `base_prefix` pointing home. Both guards are built on exactly that `prefix != base_prefix` distinction, which is why one cheap `python3 -m venv` disarms both at once.

**Q3: Is this a security lock my company added?**
No. Check ownership with `dpkg -S`:
```bash
dpkg -S /usr/lib/python3.12/EXTERNALLY-MANAGED    # libpython3.12-stdlib
dpkg -S /usr/lib/python3.12/ensurepip/__init__.py # python3.12-venv
```
Both files belong to **stock Ubuntu packages**, not anything the company added. Your company's only contribution to this pain is the **network** layer — the firewall + Nexus proxy (hence `--index-url`). The Python side is vanilla Ubuntu 24.04, identical worldwide.

**Q4: Then why have I never hit this before?**
Because **PEP 668 enforcement is recent**, and you were probably on "doesn't touch the system Python" setups:
- Ubuntu **20.04 / 22.04 LTS** → **no marker**; `pip install --user` just worked (many corporate WSL images were 22.04 until ~2024).
- Debian 12 bookworm (Jun 2023), Ubuntu 23.04 → first to ship it.
- Ubuntu **24.04 LTS (Apr 2024)** → ships it, and it's the LTS most IT teams rebaselined new WSL images onto. **That's the jump you just lived through.**
- Also, **pyenv / conda / docker** all use non-apt-managed Pythons, which carry no marker — a pyenv `3.11.5` on the same box has **no** `EXTERNALLY-MANAGED` next to it. Your usual habits had been shielding you.

**Q5: On any locked-down corporate box, how do I quickly tell "company lock" from "distro default"?**
`dpkg -S <file>`. If the file belongs to a distro package (like `libpython3.12-stdlib` above), it's upstream policy — you'd hit it on your home laptop too. Only unowned or company-placed files are the "company" layer. Separating *distro default* from *corporate hardening* is the first cut that keeps you from wasting a night fighting the wrong thing.

---

**Bottom line:** nothing exotic happened that night, and nothing was locked just for me. I crossed the Ubuntu 22.04 → 24.04 line where upstream Python finally began enforcing PEP 668 — and my pyenv / old-LTS habits had simply kept that wall out of sight until then. Any fresh Ubuntu 24.04 or Debian 12 box anywhere behaves exactly the same.
