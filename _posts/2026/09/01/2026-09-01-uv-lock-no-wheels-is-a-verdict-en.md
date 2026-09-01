---
title: Missing a Rust compiler? Don't rustup. Read uv.lock
header:
    image: /assets/images/hd_linux_tips.jpg
date: 2026-09-01
tags:
 - python
 - uv
 - packaging
 - dependencies
 - devops
permalink: /blogs/tech/en/uv-lock-no-wheels-is-a-verdict
layout: single
category: tech
---

> The map is not the territory. — Alfred Korzybski

---

# Missing a Rust compiler? Don't rustup. Read uv.lock

*From `can't find Rust compiler` to reading artifact tags — delete "install the toolchain" as your first reflex*

This morning `uv sync` died on `tiktoken==0.3.3`. The log was theatrical:

```
error: can't find Rust compiler
running build_rust
```

Then came a 2023-era pamphlet: upgrade pip, or fetch a compiler from rustup.rs.

I have been doing this work for twenty years. I have watched too many good engineers `curl | sh` at this exact line. That move is not stupid. It answers the **wrong question**. The verdict is not the last line of stderr. It is whether `uv.lock` has a `wheels = [...]` block for that package.

No wheels means you are holding a manuscript (sdist), not a printed book (wheel). The Rust compiler is a chisel. You can carve. A staff engineer asks first: **why am I in a print shop?**

**You should leave with three instincts:**

- `uv.lock` is the court transcript, `uv tree` is the family tree, `uv sync` is just the bailiff
- sdist / wheel / crate are not three file extensions. They are the unit of publication in three different ecosystems
- `cp313` is not decoration. It is an ABI ticket. The wrong ticket cannot be wished into existence by a newer pip

The order below is pedagogical — what to open first — not the order the error arrived.

---

## 1. Three maps: lock, tree, sync

`uv` splits work that used to be smeared across pip, poetry, and virtualenv. I checked these flags against 0.11.16's help text:

| Command | What it mutates | Question it answers | What it is not for |
|---|---|---|---|
| `uv lock` | Only `uv.lock` | "What versions do these constraints resolve to *now*?" | Installing. A clean resolve is not a runnable app |
| `uv tree` | Nothing, by default | "Who pulled whom in?" | Bumping versions. It is a map, not a steering wheel |
| `uv sync` | `.venv` to match the lock | "Does the disk match the transcript?" | A cue to upgrade pip. Resolve already succeeded |

This morning: `Resolved 143 packages in 2ms` — **resolve worked**. Death was in build. The package existed. The *artifact* required a factory.

### `uv lock`: turn a wish list into a transcript

`pyproject.toml` is the wish: `genai>=2.1.0`. `uv.lock` is the fact: the resolver picked `genai==2.1.0`, which wanted `tiktoken`, pinned `0.3.3`, **sdist only**.

Flags you will see in CI and review:

```bash
uv lock              # re-resolve from pyproject, rewrite the lock if needed
uv lock --check      # fail CI if the lock no longer matches the constraints
uv lock --dry-run    # show the delta, write nothing
uv lock -P tiktoken  # allow one package to move; keep the rest pinned
uv lock -U           # allow upgrades (implies --refresh)
```

`uv sync` and `uv tree` share a pair of guards people swap by accident:

| Flag | Meaning |
|---|---|
| `--frozen` | **Do not re-lock.** Read the file as-is |
| `--locked` | Re-resolve if you must, but fail if the lock would change |

`--frozen` is a closed-book exam. `--locked` is open-book with "do not erase the answer key."

> Constraints are legislation. The lock is case law. When the team argues, open the case file first.

### `uv tree`: ask who invited this guest

uv's own hint is a hand-rolled invert:

> `tiktoken` (v0.3.3) was included because `clients` (v0.1.0) depends on `genai` (v2.1.0) which depends on `tiktoken`

Same sentence, as a command:

```bash
uv tree --frozen -d 2
uv tree --frozen --package genai
uv tree --frozen --invert --package tiktoken
uv tree --frozen --show-sizes
uv tree --frozen --python-version 3.13 --python-platform aarch64-apple-darwin
```

| Flag | Job |
|---|---|
| `--invert --package X` | Grow the tree backwards: who depends on X. **First command on a build failure** |
| `--package X` | One subtree |
| `--depth` | Stop FastMCP from flooding the terminal |
| `--show-sizes` | Compressed wheel sizes. A 25KB tarball and a 1MB whl are not the same object |
| `--outdated` | How far each node sits from latest |
| `--python-version` / `--python-platform` | Filter as if you were that interpreter on that OS. One lock, two different wheel stories |
| `--no-dedupe` | Repeat shared deps instead of `(*)` — use when "why two copies?" matters |

This morning, while that lock still existed, invert would have been (reconstructed from the hint and the lock we read *then*, not a live reprint):

```
tiktoken v0.3.3
└── genai v2.1.0
    └── clients v0.1.0
```

By the time I wrote this, `genai` was already gone from `pyproject.toml`. The live top of the tree is:

```
clients v0.1.0
├── beautifulsoup4 v4.15.0
├── fastmcp v3.4.7
├── google v3.0.0
├── google-genai v2.21.0
├── inquirerpy v0.3.4
├── langchain-ollama v1.1.0
├── trafilatura v2.2.0
└── typer v0.27.1
```

`uv tree --frozen` no longer mentions `tiktoken`. That is not a cache flush. That is what a family tree looks like after you cut the branch that imported the fossil.

📌 **takeaway:** invert first, rustup last. The hint and `--invert` are the same sentence.

---

## 2. sdist, wheel, crate: three worlds, three "packages"

Juniors hear three zip formats. They are not in the same courtroom.

| Word | Whose unit of publication | What is inside | Do *you* compile |
|---|---|---|---|
| **crate** | Rust / Cargo | `Cargo.toml` + `.rs`. tiktoken's hot path is a Rust BPE | Compiling a crate needs `rustc` |
| **sdist** | Python / PyPI | A `.tar.gz` manuscript: sources + a PEP 517 backend | **Yes.** Isolated env, `build_wheel` |
| **wheel** | Python / PyPI | A `.whl` (a zip). Pure Python, or a prebuilt `.so` / `.dylib` | **No.** Unpack into site-packages |

They form a pipeline, not a synonym list:

```
Rust crate   (the implementation)
    │  rustc + maturin / setuptools-rust  — on the *author's* CI
    ▼
Python wheel (cp313-macosx_11_0_arm64.whl)
    │  uploaded to PyPI
    ▼
your uv sync — matching tags → unpack; no match → fall back to sdist
    │
    ▼
sdist runs the same pipeline on *your* laptop  — and asks you for rustc
```

Know the era, not just the error: `tiktoken==0.3.3` shipped in March 2023. CPython 3.13 did not exist. The author's CI could not mint a `cp313` ticket. PyPI is not being stingy. Time does not issue IOUs.

The lock said this in plain TOML — sdist, no wheels block:

```toml
[[package]]
name = "tiktoken"
version = "0.3.3"
sdist = { url = ".../tiktoken-0.3.3.tar.gz", size = 25347 }
```

Note the lock had **no** `wheels = [ ... ]` block.

A later build wears its ticket on the filename:

```
tiktoken-0.12.0-cp313-cp313-macosx_11_0_arm64.whl
```

25KB cannot hold a compiled dylib. ~1MB can. `--show-sizes` makes the asymmetry visible.

> The artifact is the product. The compiler is the factory. If the factory is missing, ask whether you walked into the wrong shop.

📌 **takeaway:** A crate is Rust's package, an sdist is Python's manuscript, a wheel is the box you unpack. They are not three extensions for the same object.

---

## 3. `cp313` is an ABI ticket, not a version sticker

PEP 425 / 427 split a wheel name into five fields:

```
{distribution}-{version}-{python tag}-{abi tag}-{platform tag}.whl
     tiktoken      0.12.0      cp313         cp313     macosx_11_0_arm64
```

| Tag | Plain language | Mismatch means |
|---|---|---|
| `cp313` | Built for CPython 3.13 | A 3.12 interpreter treats it as someone else's lunch |
| second `cp313` | ABI: linked against 3.13's C API | `cp313t` is the free-threaded variant — a different ticket |
| `macosx_11_0_arm64` | macOS 11+, ARM64 | Intel Macs, Linux CI, Windows each need their own |
| `manylinux_2_28_x86_64` | Linux built on a new-enough glibc | Old distros may refuse it |
| `py3-none-any` | Pure Python, no native code | The only "one wheel everywhere" story |
| `abi3` | Stable ABI, one wheel across several CPythons | Rare, and only when the extension opted in |

`.python-version` saying `3.13` plus `requires-python = ">=3.13"` is you walking into the 3.13 window on purpose. That window has no March 2023 native ticket. uv falls back to sdist. Then: `running build_rust`.

"Upgrade pip, a prebuilt wheel may be available" is **copy printed inside the sdist for pip users**. It is not uv's diagnosis. uv already builds in isolation. A newer pip cannot invent a cp313 wheel that was never uploaded.

Five whys, stopped at the mechanism:

1. Why rustc? — Because a Rust extension is being compiled.
2. Why compile? — Because no matching wheel.
3. Why none? — 0.3.3 shipped before 3.13 existed.
4. Why 0.3.3? — `clients` depended on a 2023 PyPI project named `genai`, which pulled tiktoken.
5. Why `genai`? — The name looks like Google's SDK. The code does `import google.generativeai`, and the same file also lists `google-genai`.

That last why is not packaging. It is **walking into the wrong courtroom because the sign was short**.

🩸 **hard-won:** rustc can clear the symptom and launder a bad dependency into "works on my machine." The next CI image without a chisel reprints the same fine.

📌 **takeaway:** `cp313` is an ABI ticket. A newer pip cannot mint a ticket that was never uploaded.

---

## 4. Delete "install the compiler" as the default move

Naive take: missing compiler → install compiler.

Seasoned take: missing compiler → I am installing something that should not have arrived as source.

| Move | What it optimizes | What it hides |
|---|---|---|
| `rustup`, retry `uv sync` | Pass rate on this laptop | A lying graph, a fatter image, the next hire hitting the same wall |
| `uv add tiktoken>=0.12` while keeping the wrong `genai` | The fossil accidentally reaches a ticketed tokenizer | You still keep a 2023 name around |
| Delete `genai` from `pyproject.toml`, then `uv lock` | Deps match imports | The next failure may be `import google.generativeai` with no declared package. That is a **cleaner** failure |
| `uv sync --no-build` | Policy: no on-laptop factories | Hard-fail when only an sdist exists — a CI gate |

Interview point: `--no-build` is not meanness. It turns "we don't compile native extensions on laptops" from tribal memory into an artifact.

Policy gate — unpack only, never open the factory:

```bash
uv sync --frozen --no-build
```

If you *intentionally* build internal crates from source, that is a different pipeline: a private wheelhouse, a pinned rustc, a cache. Factory design. Not a reflex after stderr.

> Occam is brutal here: "there is no cp313 wheel" needs no extra plot about an old pip.

📌 **takeaway:** Fix the graph. Equipping a bad dependency with a factory is the expensive option.

---

## One picture, three maps

```
pyproject.toml          wishes / legislation
        │  uv lock
        ▼
uv.lock                 case law: versions + sdist/wheels
        │  uv tree --invert
        ▼
family tree             who invited the fossil
        │  wheels present? tag contain cp313?
        ▼
uv sync                 unpack  or  open a factory
```

| You see | Open this map first |
|---|---|
| `Resolved N packages` then `build_rust` | That package's `sdist` / `wheels` in the lock |
| `was included because A depends on B` | `uv tree --invert --package <the one that exploded>` |
| A pure-Python package compiling | Is `--no-binary` on |
| A tiny Python bump breaks everything | python / abi tags |
| Laptop syncs, CI does not | The tree after `--python-platform` |

📌 **takeaway:** Symptom lives in sync. Evidence lives in the lock. The culprit lives in the tree.

---

## 🧭 Elevation: four principles that survive the next package

Fixing `tiktoken` is a leaf. These four travel.

### Principle 1: Artifact before toolchain

**Mechanism:** The installer matches wheel tags first, and only then falls back to sdist. Only sdist asks you for rustc / gcc / a JDK.  
**Off-domain:** A library desk asks whether a printed copy exists before sending you to the scriptorium. If the scriptorium is out of ink, you do not buy a printing press. You walk back and ask why there is no print run.  
**举一反三 / Generalize:** When the error says "missing compiler," search for the artifact (wheel, jar, image) first. Add a factory last.

### Principle 2: Draw the family tree before surgery

**Mechanism:** The resolver walks a graph. The package that exploded is often not the one you typed on line one of `pyproject.toml`.  
**Off-domain:** Someone breaks a glass at a party. Ask who brought the guest, before you sue the glassmaker.  
**举一反三 / Generalize:** `uv tree --invert`, `mvn dependency:tree`, `npm ls`, `go mod why` — same muscle.

### Principle 3: Write "no factories" as a flag

**Mechanism:** `--no-build`, `--frozen`, `uv lock --check` turn a hallway rule into a nonzero exit.  
**Off-domain:** "Please lock the door" is tribal knowledge. A badge that dies at 7pm is an artifact.  
**举一反三 / Generalize:** If you are about to write "please note" in a README, ask whether CI can fail instead.

### Principle 4: A short name is not an identity document

**Mechanism:** PyPI project name, Python import name, and the name in the product docs are three systems. `genai`, `google-genai`, and `google.generativeai` can all be true and still refuse to recognize each other.  
**Off-domain:** Three restaurants named "Chengdu Stir-Fry." The plate you ordered may come from a different supply chain.  
**举一反三 / Generalize:** For any "I installed it but the import is wrong" incident, draw a three-column table before you debate versions.

---

## Do this today

1. In your own repo, run `uv tree --frozen --invert --package <whatever just failed>`. Paste that into the PR, not only stderr.
2. Open `uv.lock`, find the package. Count: is there a `wheels` block? Does any filename carry *your* tags (`cp313`, `macosx`, `manylinux`, `win_amd64`)?
3. Put `uv lock --check` in CI. A green build should not survive a fork between lock and `pyproject.toml`.
4. Try `uv sync --frozen --no-build` on native deps. Failure is useful — it fails at policy, not on a colleague's PATH.
5. Audit short names in `pyproject.toml`. `genai` and `google-genai` are not the same courtroom. Dependency name, import name, and the name in the docs must be one graph.
6. Write the three-command sequence — invert, inspect wheels, only then toolchain — into the README. That is the deliverable. Do not make the next person re-derive it.

---

*The last line of stderr is a symptom. The missing `wheels` block is the verdict. Chisels are cheap. The wrong shop is not.*
