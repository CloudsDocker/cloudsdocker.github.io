---
title: "Trusting the Filesystem: mtime, glob, and fnmatch Under the Hood"
date: 2026-08-01
categories: [engineering, python, filesystems]
tags: [python, pathlib, glob, fnmatch, mtime, syscalls, code-review]
---

A code review of a small helper function turned into a three-part rabbit hole:
why `mtime` is a shaky source of truth, how `glob` actually finds your files,
and what `fnmatch` is silently doing underneath it. Three questions, one
underlying lesson — most of the "obvious" filesystem APIs are thinner
abstractions than they look.

## Part 1: Reviewing `list_raw_files` — Why mtime Isn't as Trustworthy as It Looks

The starting point was this function:

```python
def list_raw_files(n: int = 20) -> list[str]:
    """The n most recently touched drafts in raw/, newest first. Ordered by mtime rather than
    by name: only some drafts carry a date prefix, so the filenames do not sort chronologically."""
    drafts = sorted(BLOG_RAW_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [p.name for p in drafts[:n]]
```

It scans `raw/` for markdown files and returns the N most recently modified,
newest first. The core engineering decision buried in the docstring: **the
filename can't be trusted, so mtime is used as the source of truth instead.**
That's a classic trade-off — naming conventions are human-enforced and leak;
`mtime` is filesystem metadata updated unconditionally on every write.

### Under the Hood

`BLOG_RAW_DIR.glob("*.md")` uses `os.scandir()` internally (pathlib moved off
the older `os.listdir()` + per-file `stat()` pattern years ago), but `glob`
only returns `Path` objects matched by name — no stat info attached.

The real work happens in `p.stat()`: an explicit `stat(2)` syscall reading the
inode's `struct stat`, where `st_mtime` records the last time the file's
*content* was written. Precision depends on the filesystem — ext4 gives
nanosecond resolution, but plenty of older or network filesystems only give
you whole seconds.

Complexity breakdown:
- `glob` traversal: O(k), where k is the directory entry count
- `stat()` per file: another O(k) syscalls, each a user→kernel context switch
- `sorted()`: O(k log k)
- Slice to top n: O(n)

Overall O(k log k), **but the real bottleneck isn't the sort — it's k
independent syscalls.** With tens of thousands of files in `raw/`, that's
tens of thousands of context switches to fetch data you'll mostly discard.

One optimization worth knowing: `os.scandir()`'s `DirEntry` objects often
cache stat info during the directory walk itself (especially on Windows, and
in some Linux cases), so calling `.stat()` on them doesn't trigger a fresh
syscall. `pathlib.Path.glob()` abstracts that layer away — every `.stat()`
call on a bare `Path` is a brand-new syscall. If you need to squeeze
performance, drop to `os.scandir()` directly.

### The Interviewer's Follow-Up Chain

**Q: What breaks with 100,000 files in `raw/`?**
A: Two things. First, 100,000 `stat()` calls — even at ~1μs each, that's
100ms+ of pure syscall overhead, most of it wasted since you only want the
top 20. Second, `sorted()` builds and fully sorts a 100k-element list when
you only need top-N. Use `heapq.nlargest(n, drafts, key=...)` instead —
O(k log n) instead of O(k log k).

**Q: Is mtime actually reliable?**
A: At least three failure modes:
1. **Precision** — older filesystems (some NFS mounts, FAT32) only resolve to
   the second; ties within that second sort in whatever order `glob` happened
   to return them, which is effectively undefined.
2. **git checkout / rsync rewrite mtime** — if `raw/` was ever cloned or
   restored from backup, every file's mtime becomes the checkout time, not
   the real authoring time. History is gone.
3. **Editor "atomic save" patterns** — many editors write to a temp file and
   rename over the original; usually fine, but "preserve attributes" modes
   can carry the old mtime forward.

**Q: Any concurrency / TOCTOU risk?**
A: Yes, mild but real. Between `glob()` listing files and `stat()` reading
mtime, a file can be deleted — `p.stat()` then raises `FileNotFoundError` and
crashes the whole function. If this is a publish-time script and someone
deletes a draft in another terminal, you get an unhandled exception instead
of a clean skip. Production code should wrap it: `try: ... except
FileNotFoundError: continue`.

**Q: Smarter approach when n is much smaller than the total file count?**
A: `heapq.nlargest` avoids a full sort. At real scale (millions of files),
the better fix is maintaining an actual index (e.g., a SQLite table of
path + mtime) instead of scanning the directory on every call — the line
between "filesystem as database" and "actually build an index."

**Q: Failure modes if the directory doesn't exist or isn't readable?**
A: `Path.glob()` on a missing directory silently returns an empty iterator —
easy to misread as "empty directory" instead of "directory doesn't exist."
`PermissionError` on the other hand is raised loudly during traversal. This
function currently handles neither case explicitly — a silent-failure trap
that's miserable to debug.

### How Big Tech Actually Uses This

This pattern is "directory as lightweight database," and at real scale
nobody uses it raw — but the underlying idea shows up everywhere:

- **Log rotation** — logrotate and friends often lean on mtime to decide
  what to archive or delete, but mature systems (Kubernetes logging stacks)
  have moved to filename-encoded timestamps plus an index service, because
  in containerized environments the underlying filesystem (overlayfs) can be
  short-lived and mtime semantics get unreliable.
- **S3 / HDFS metadata** — object stores never trust the underlying disk's
  inode mtime for business logic; `LastModified` is maintained by the
  storage layer itself, because distributed replicas can't guarantee
  filesystem-level metadata consistency.
- **Build system caching (Make, Bazel)** — many build tools use mtime to
  decide what needs rebuilding, and it's notoriously fragile (the classic
  "clock skew causes an incremental build to skip a real change" bug).
  That's exactly why Bazel moved to **content hashing** instead of
  timestamps as its source of truth.

### The High-Stakes Version

In an audited, regulated context, this pattern as-written would get bounced
by compliance:

- **mtime is forgeable, so it has no audit value.** Anyone with write access
  can call `os.utime()` and claim a file is three days older than it is.
  Regulated systems (SOX, SEC 17a-4) require tamper-evident timestamps —
  WORM storage, external timestamp authorities (RFC 3161), or hash chains —
  not trust in local filesystem metadata.
- **Precision and monotonicity** — matching engines and order books need
  nanosecond, monotonically increasing clocks. `st_mtime` is a wall-clock
  timestamp, subject to NTP corrections and potential backward jumps — the
  classic "used the wrong clock source" bug (wall clock vs. monotonic clock).
- The usual fix: a centralized metadata service is the source of truth for
  "latest file," never the filesystem directly.

### What's Cutting-Edge Right Now (2026)

- `os.scandir()` / cached `DirEntry.stat()` remains the standard optimization,
  but for hot paths, more teams reach for `inotify`/`fanotify` (via
  `watchdog` or similar) — event-driven instead of polling.
- The `uv` ecosystem has brought Rust-based file tools (`fd`, the traversal
  ideas behind `ripgrep`) into more Python workflows via PyO3 for large
  directory trees.
- For blogging/CMS use cases specifically, the standard fix is an explicit
  `date:` field in Jekyll/Hugo front matter — sidestepping mtime reliability
  entirely. A `YYYY-MM-DD-slug.md` naming convention is really a manual
  patch for the same problem; the more robust move is reading the front
  matter `date` field first and falling back to mtime only when it's absent.

### The Cross-Discipline Lens

This is **relative dating in stratigraphy**. Geologists trust deposition
order — lower layers are older — over some arbitrary mark scratched on a
rock (the equivalent of a filename prefix). But stratigraphy has the same
failure mode: earthquakes and eruptions scramble layers (the equivalent of a
`git checkout` rewriting mtime), which is exactly when geologists switch to
**radiometric dating** — an independent, absolute signal that doesn't depend
on relative ordering at all. Moving from mtime to an external timestamp
authority in a high-stakes system is the same upgrade: from reading layer
order to measuring isotopic decay.

### Mic Drop

> mtime is a timestamp that looks free but carries the same trust problem as
> a filename — the real production answer is always "sort by it, never audit
> by it."

---

## Part 2: glob — Wildcards Aren't a Filesystem Feature, They're a Regex in Disguise

### What It Is

`glob` (short for *global*, dating back to 1970s Unix shells) is wildcard
path matching — not a regex, but ultimately compiled down into one under the
hood. Python has two entry points:

```python
import glob                 # functional API, returns list[str]
from pathlib import Path    # object-oriented API, returns a generator of Path
```

### Wildcard Syntax

| Symbol | Meaning | Example | Matches |
|---|---|---|---|
| `*` | any number of chars (not `/`) | `*.md` | `foo.md`, not `sub/foo.md` |
| `?` | exactly one char | `202?.md` | `2024.md`, not `20245.md` |
| `[seq]` | one char from a set | `[0-9]*.md` | `2024-01-01-x.md` |
| `[!seq]` | one char not in a set | `[!_]*.py` | files not starting with `_` |
| `**` | recursive directory match | `**/*.md` | md files in any subdirectory |

```python
import glob

glob.glob("raw/*.md")
# ['raw/2024-01-01-hello.md', 'raw/notes.md']

# Recursive: recursive=True is mandatory, or ** silently degrades to *
glob.glob("raw/**/*.md", recursive=True)
# ['raw/2024-01-01-hello.md', 'raw/drafts/wip.md', 'raw/drafts/2026/x.md']

glob.glob("raw/202[3-5]-*.md")
# Only matches 2023/2024/2025-prefixed files; 2026 is excluded
```

### `glob.glob()` vs `Path.glob()`

```python
import glob
from pathlib import Path

files: list[str] = glob.glob("raw/*.md")          # eager, str paths
files: list[Path] = list(Path("raw").glob("*.md")) # lazy generator, Path objects
```

The bigger difference is recursive semantics:

```python
Path("raw").glob("**/*.md")                       # ** is native, no flag needed

glob.glob("raw/**/*.md", recursive=True)           # must opt in explicitly
```

This is a classic interview trap: **forget `recursive=True` and `**` silently
degrades into two ordinary `*` matches** — no error, it just quietly stops
being recursive, which is hard to notice because the code "looks correct."

### Under the Hood

The most overlooked fact: **the kernel has no idea what `*` means.** `glob()`
is entirely userspace, implemented in two steps.

**Step 1 — translate the pattern into regex:**

```python
import fnmatch
print(fnmatch.translate("*.md"))
# '(?s:.*\\.md)\\Z'
```

**Step 2 — walk the directory and filter with regex:**

```python
# glob roughly does this internally:
import os, re

pattern = re.compile(fnmatch.translate("*.md"))
matches = [entry.name for entry in os.scandir("raw")
           if pattern.match(entry.name)]
```

So `glob("raw/*.md")` really costs: **one directory traversal (readdir
syscalls) + one regex match per entry.** It's a linear scan, not any kind of
indexed lookup — more files means proportionally slower.

**Recursive globbing is more expensive still** — `**` is effectively a
recursive `os.walk()`, multiplying `opendir`/`readdir`/`closedir` calls
across every nested subdirectory.

### Common Traps

**Trap 1 — hidden files are skipped by default**

```python
glob.glob("raw/*")
# Won't match .gitkeep, .DS_Store, etc.
glob.glob("raw/.*")   # explicit opt-in required
```
Inherited from Unix shell behavior — protects against accidental `rm *`
wiping out dotfiles.

**Trap 2 — order is undefined, filesystem-dependent**

```python
glob.glob("raw/*.md")
# On ext4, often inode creation order or hash-bucket order —
# not alphabetical, not chronological
```
This is exactly why the earlier `list_raw_files` code manually sorts by
mtime — **never rely on glob's return order; it's unspecified and can vary
across filesystems and Python versions.**

**Trap 3 — special characters need escaping**

```python
filename = "report[final].md"
glob.glob(filename)                    # misinterpreted as a character class!
glob.glob(glob.escape(filename))        # correct
```

**Trap 4 — symlink recursion edge cases**

```python
# A symlink loop inside raw/ can, in edge cases, cause infinite recursion
Path("raw").glob("**/*.md")
# Python 3.13 added follow_symlinks to control this explicitly
```

**Trap 5 — case sensitivity is platform-dependent**

```python
# Linux/macOS (case-sensitive fs): *.MD does not match file.md
# Windows: *.MD matches file.md
# Cross-platform tools must normalize explicitly, never rely on glob's default
```

### Applying It Back to `list_raw_files`

```python
# Original: single-level only
drafts = sorted(BLOG_RAW_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)

# If raw/ has year-based subdirectories, ** is needed
drafts = sorted(BLOG_RAW_DIR.glob("**/*.md"), key=lambda p: p.stat().st_mtime, reverse=True)

# Excluding raw/drafts/archive/ and staying top-level: plain * is correct here —
# the choice isn't "which is more powerful," it's "which matches your actual layout"
```

### Mic Drop

> glob isn't a filesystem capability — it's regex wrapped in syntactic
> sugar at the application layer. Its speed, ordering, and case behavior are
> all decided by the underlying `readdir` syscall and filesystem
> implementation, so what looks like one unified standard is quietly a
> different answer on every platform.

---

## Part 3: fnmatch — The Engine Underneath glob

### What It Is

`fnmatch` (File Name Match) is the lowest-level wildcard matching module in
the standard library — everything `glob` does is really "directory traversal
+ fnmatch filtering." Understanding fnmatch means understanding glob's
actual engine room.

```python
import fnmatch

fnmatch.fnmatch("report.md", "*.md")    # True
fnmatch.fnmatch("REPORT.MD", "*.md")    # True (!) — looks case-insensitive
```

Important clarification up front: `fnmatch.fnmatch()` and `glob` do **not**
follow the same case-sensitivity rules.

### Four Core Functions

```python
fnmatch.fnmatch(name, pattern)      # single match, case rule from OS (normcase)
fnmatch.fnmatchcase(name, pattern)  # single match, always case-sensitive
fnmatch.filter(names, pattern)      # batch filter, list -> list
fnmatch.translate(pattern)          # compile a glob pattern into a regex string
```

```python
files = ["report.md", "REPORT.MD", "draft.MD", "notes.txt"]

fnmatch.filter(files, "*.md")
# On Linux: ['report.md', 'REPORT.MD', 'draft.MD'] — all three match!
```

### Under the Hood: `normcase` Is the Real Case-Sensitivity Switch

This is the most counterintuitive part of fnmatch. `fnmatch.fnmatch()`
internally runs both `name` and `pattern` through `os.path.normcase()`
before comparing:

```python
# Simplified version of what fnmatch.fnmatch actually does
def fnmatch(name, pattern):
    name = os.path.normcase(name)
    pattern = os.path.normcase(pattern)
    return fnmatchcase(name, pattern)
```

And `os.path.normcase()`'s behavior is platform-dependent:

```python
# Linux / macOS (case-sensitive filesystem)
os.path.normcase("REPORT.MD")   # 'REPORT.MD' — untouched

# Windows (case-insensitive filesystem)
os.path.normcase("REPORT.MD")   # 'report.md' — auto-lowercased
```

**The real story**: on Linux, `fnmatch.fnmatch("REPORT.MD", "*.md")`
returns `True` — **not because fnmatch itself is case-insensitive, but
because Linux's normcase is a no-op, and the compiled regex is
case-sensitive by default anyway.** The apparent "insensitivity" is a side
effect of normcase preprocessing, not a deliberate design choice in the
matching logic.

Verify it:

```python
fnmatch.fnmatchcase("REPORT.MD", "*.md")  # False, on every platform
# fnmatchcase skips normcase entirely — raw case-sensitive comparison
```

**This is a classic "works fine in local dev, breaks weirdly after moving to
a different OS" trap** — if you develop your publish script on macOS
(case-sensitive) and deploy to a case-sensitive CI container, no problem. But
migrate the dev environment to Windows one day, and `*.md` vs `*.MD` suddenly
matches a different set of files.

### `translate()`: The Wildcard-to-Regex Translation Table

This is fnmatch's actual core — every match ultimately routes through this
one function.

```python
fnmatch.translate("*.md")
# '(?s:.*\\.md)\\Z'

fnmatch.translate("draft?.md")
# '(?s:draft.\\.md)\\Z'

fnmatch.translate("[0-9]*.md")
# '(?s:[0-9].*\\.md)\\Z'

fnmatch.translate("report[!_]*.md")
# '(?s:report[^_].*\\.md)\\Z'  —  [!...] becomes regex [^...]
```

Translation table:

| glob syntax | regex equivalent | note |
|---|---|---|
| `*` | `.*` | greedy match, doesn't understand path separators |
| `?` | `.` | exactly one char |
| `[abc]` | `[abc]` | character class, nearly identical syntax |
| `[!abc]` | `[^abc]` | negated class, `!` becomes `^` |
| literal chars | `re.escape()`'d | regex special chars like `.` get escaped |

That last row matters: `translate("report.md")`'s `.` gets escaped to `\.`
and is *not* treated as regex's "match any character." This is why glob
syntax is safer than hand-written regex for user input — typing `*.md`
won't accidentally match `reportXmd` because of regex `.` semantics.

**What's that `(?s:...)` prefix?** — an inline `re.DOTALL` flag, letting `.`
also match newlines. Not particularly meaningful for filenames (which
rarely contain newlines), but keeps behavior consistent.

### The Interviewer's Follow-Up Chain

**Q: fnmatch vs. hand-written `re` — when do you pick which?**
A: If you're matching "user-friendly wildcard patterns" (someone typing
`*.log`), use fnmatch. If you need precise control — capture groups,
lookaheads, quantifier ranges — go straight to `re`. fnmatch's expressive
power is a strict subset of `re`, trading flexibility for simplicity.

**Q: How does `fnmatch.filter` perform on large lists — can you precompile?**
A: Every call to `fnmatch.fnmatch()` re-runs `translate()` internally, so
calling it repeatedly with the same pattern inside a loop is wasteful:

```python
# Bad: re-translates + recompiles every iteration
for name in huge_list:
    if fnmatch.fnmatch(name, "*.md"):
        ...

# Good: compile once
pattern = re.compile(fnmatch.translate("*.md"))
for name in huge_list:
    if pattern.match(name):
        ...
```
CPython does cache `translate()` results internally via
`functools.lru_cache` (`_compile_pattern`), so repeated calls with the same
pattern don't actually recompile — but the function-call overhead (argument
validation, cache lookup) still exists. Manually caching the compiled `re`
object in a hot path is always faster.

**Q: Can fnmatch prevent path traversal attacks — e.g., a user passing
`../../etc/passwd` as a pattern?**
A: No, and this is a real security trap. `fnmatch` is pure string pattern
matching with no path-semantics awareness. `*` won't cross a literal `/`,
but a pattern containing literal `..` or `/` is simply `re.escape()`'d and
preserved in the compiled regex — it isn't filtered out or flagged. The real
risk is downstream: if a matched path gets passed straight to `open()`
without `Path.resolve()` and a boundary check, that's the actual
vulnerability. fnmatch has no permission semantics, and shouldn't — that
responsibility belongs to the caller.

**Q: Does fnmatch treat Windows' `\` path separator specially?**
A: No. fnmatch has no concept of path separators at all — the whole string
is an opaque token. `*` greedily matches `/` and `\` alike. That differs
from real shell globbing (in bash, `*` doesn't cross `/`), which is a
Python-fnmatch-specific quirk that trips up people with shell intuitions.
The thing that actually stops `*` from crossing directories is `glob`
calling fnmatch layer-by-layer during traversal — fnmatch itself has no such
boundary concept.

**Q: Any ReDoS (regex denial of service) risk?**
A: Theoretically minimal. `translate()` produces simple, linearly-concatenated
regex with no nested quantifiers or classic backtracking-explosion structures
(like `(a+)+`) — no exponential blowup. But an extremely long input pattern
(hundreds of thousands of characters) still costs linear compile time — that's
plain DoS, not ReDoS, and the mitigation is capping input pattern length.

### How Big Tech Uses This: From fnmatch to .gitignore Syntax

`.gitignore`, `.dockerignore`, and `pyproject.toml`'s `include`/`exclude`
rules are all essentially dialects built on fnmatch-style syntax. Once you
see this layer, the pattern is everywhere:

```python
import fnmatch

def should_ignore(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, p) for p in patterns)

should_ignore("raw/draft.md", ["*.pyc", "raw/draft.*", "__pycache__/*"])
# True
```

Bazel's `BUILD` file glob rules and Kubernetes' `.helmignore` all follow the
same "pattern → regex → per-entry match" pipeline underneath, just with
extra dialect-specific syntax layered on (gitignore's recursive `**`,
negation with `!`, root-anchoring with a leading `/`).

### Mic Drop

> fnmatch isn't "simpler regex" — it's a restricted regex compiler wearing a
> friendly face. Its famously misunderstood "case-insensitivity" is really
> just a side effect of `os.path.normcase`, not a deliberate property of the
> matching logic itself.
