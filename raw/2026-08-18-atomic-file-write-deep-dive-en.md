---
title: "The One-Line write_text That Started It All: POSIX, Crash Consistency and Filesystem Boundaries in Atomic File Writes"
date: 2026-08-18
categories: [engineering, python, systems]
tags: [atomic-write, fsync, posix, rename, filesystem, crash-consistency, python]
---

## It all started with this line

I needed to persist a run's metrics from the CLI of an LLM evaluation harness. What
I wrote was this:

```python
metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
```

**This is the line almost every developer writes**, and it even looks careful —
`json.dumps` serialises fully before writing (better than `json.dump(fh)`), and
`encoding="utf-8"` is explicit (better than a bare `write_text`). Nobody stops this
in code review.

It has at least four problems, and **every one of them is silent**:

1. **`write_text` is not atomic.** It's `open(w)` → truncate → write → close. If the
   process dies partway (Ctrl-C, OOM kill, container eviction), what's left on disk
   isn't "no file" — it's **a JSON file with a perfectly correct name and a truncated
   body**. Downstream, `json.load` raises `JSONDecodeError`, which reads as "this run
   failed" rather than "this run's bookkeeping broke."
2. **Concurrent readers see a half file.** A monitoring dashboard, another CI step,
   a `tail` — anyone opening that path during those few milliseconds gets incomplete
   content, and cannot tell.
3. **After a power loss the contents may be empty.** The data only reaches the kernel
   page cache; nothing here guarantees it hits the platter.
4. **Permissions follow the umask**, so they're inconsistent across environments.

My situation made it worse: that metrics file was **the sole deliverable of the whole
eval**, holding everything a paid run produced. A second Ctrl-C landing inside that
line turns a few hundred dollars of experiment into a corrupt JSON.

So I replaced it with this:

```python
def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    """temp file in same dir → fsync → os.replace (rename is atomic within a fs)."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)          # atomic
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
```

Eight lines. Looks serious. I was fairly pleased with it.

**Then I reviewed it and found two real bugs and one major omission.**

They sit on three different pits — POSIX semantics, filesystem implementation
boundaries, and crash consistency — and what's in those pits (fsyncing the
*directory*, the true boundary of `EXDEV`, the `mkstemp` prefix trap) is stuff plenty
of senior engineers have never had reason to think through.

This post is the full walkthrough: first a line-by-line dissection of those eight
lines, then two of those lines expanded into topics of their own.

---

# Part 1: Line by Line

## 🎯 The 30-Second Version

This function exists to solve one thing: **`open(w)` is not one operation, it's three.**

```
open(path, "w")  →  truncate (file instantly becomes 0 bytes)
fh.write(...)    →  fill it back in, gradually
fh.close()
```

Between the truncate and the completed write, there is a file on disk with a
**perfectly correct name and a mutilated body**. If the process dies right then
(Ctrl-C, OOM kill, container eviction, power loss), what you get is not "no file"
— it's **a file that lies to you**.

The atomic-write idea: **never modify in place; only ever flip a name, instantly.**

Analogy: **signing a contract.** A draft can go through thirty revisions and every
one of them has exactly zero legal force. The moment the pen lifts, force goes from
0 to 100. **There is no state called "60% executed."** `os.replace` is that signature.

---

## ⚙️ Under the Hood, Line by Line

### `fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")`

Three arguments, each solving a specific problem.

**`dir=path.parent` — the single most important argument in the function.**

`rename(2)` is atomic **only within one filesystem**. Cross-filesystem rename
returns `EXDEV` (Invalid cross-device link) outright, because rename fundamentally
means "repoint a directory entry at an inode," and an inode number means nothing
in a different filesystem.

If you leave this at the default `/tmp`, containers will bite you almost every
time: `/tmp` is frequently tmpfs while the output directory is overlayfs or a
mounted volume — two filesystems. `os.replace` raises `OSError: [Errno 18]`. The
nasty part is that **it never fails locally** (everything's on one ext4), and blows
up the moment CI runs it in a container.

This is *eliminating a class of bug architecturally* rather than *catching EXDEV
and degrading to a copy*: **put the temp file next to the target, and cross-device
becomes impossible rather than handled.**

(Expanded in Part 2.)

**`mkstemp`, not `NamedTemporaryFile`, not a hand-built name.**

`mkstemp` is `open(path, O_CREAT | O_EXCL | O_RDWR, 0600)` underneath. Three
properties:

- `O_EXCL` + a random name = **no TOCTOU**. There is no window where you check the
  file doesn't exist, someone creates it first, and you clobber them. This is the
  standard defence against symlink attacks.
- It returns a **raw fd**, not a path. No gap between "got the name" and "opened it."
- Mode **0600** — owner only. A half-written temp file can hold sensitive data.

`NamedTemporaryFile` is wrong here because it defaults to `delete=True` and removes
itself on close, whereas we specifically need the file to survive until the rename.

**`prefix=path.name` — Bug 1.**

The temp file comes out looking like this:

```
cot_gpt-5-mini_dev_natural_limitall_seed42.metrics.jsonab3x9f.tmp
```

Its first N characters are **character-for-character identical to the real artifact**.
Any `glob("*.metrics.json*")`, `ls *metrics*`, or CI script that distinguishes
artifacts by filename will sweep this temp file up.

Fix: a leading dot makes it invisible to glob.

```python
prefix=f".{path.name}."   # → .cot_..._seed42.metrics.json.ab3x9f.tmp
```

(Expanded in Part 3.)

---

### `with os.fdopen(fd, "w", encoding="utf-8") as fh:`

`mkstemp` hands back a **raw fd (an integer)**, which you can't write strings to.
`os.fdopen` wraps it in a `TextIOWrapper` **and transfers ownership of the fd to
that object** — the `with` block's `close()` closes the underlying fd.

That ownership transfer has a consequence: **if `os.fdopen` itself raises (say a
typo'd encoding name), the fd leaks** — neither adopted by fdopen nor closed by you.
The `except` below only unlinks the path; it doesn't close the fd. In a long-running
process that's a descriptor leak.

Strictly, fdopen should be inside the protected region, or you need an `os.close(fd)`
fallback. In practice the encoding is hardcoded so the branch is unreachable — **but
it's worth knowing it exists, because an interviewer will ask exactly when fd
ownership transfers.**

`encoding="utf-8"` must be explicit: before Python 3.15, omitting it follows the
locale, which on Windows is cp1252 / GBK. One CJK character or emoji in your payload
and code that works fine on Linux throws `UnicodeEncodeError` on Windows.

---

### `json.dump(payload, fh, indent=2)` — Bug 2

`json.dump` is **streaming**: it walks the object and writes to `fh` as it goes.

If `payload` contains something unserialisable (`datetime`, `Path`, `Decimal`, a
numpy scalar — all common), the `TypeError` fires **after part of the output has
already been written**.

Inside this function the damage is contained (the temp file gets unlinked), but it
points at a better structure: **serialise fully to a string first, touch I/O only
once that succeeds.**

```python
text = json.dumps(payload, indent=2)   # if it fails, it fails here — disk untouched
```

This is *pushing failure forward into the side-effect-free phase*. A serialisation
error is a pure computation error; it shouldn't be entangled with I/O errors in the
same cleanup path. As a bonus, `json.dumps` + one `fh.write(text)` is one syscall
instead of many small streaming writes.

(The cost is doubling peak memory for large objects. For a metrics file of tens of
KB, irrelevant; for a GB-scale export, stream it.)

---

### `fh.flush()`

**Not optional — and most people get its relationship to fsync wrong.**

Data crosses three layers on its way from your variable to the platter:

```
Python str
   ↓  fh.write()
① Python userspace buffer (TextIOWrapper + BufferedWriter, 8KB default)
   ↓  fh.flush()  →  issues the write(2) syscall
② kernel page cache (read() can see it now, but power loss erases it)
   ↓  os.fsync()  →  forces the device write
③ physical media
```

**`flush()` does only ①→②. `fsync()` does only ②→③.**

So the order can't be swapped and neither can be skipped: fsync without a preceding
flush leaves the data sitting in the userspace buffer where the kernel has never seen
those bytes — **fsync returns success and synchronises nothing.** A silent failure:
you believe you persisted.

(The `with` block flushes on exit, but that happens *after* the fsync. Hence the
manual, earlier flush.)

---

### `os.fsync(fh.fileno())`

Forces the page cache out to physical media. This defends against **power loss /
kernel panic / a VM getting yanked** — not against process crashes.

Process crashes don't need fsync: once data reaches the page cache (②) the kernel
owns it. Your process dying changes nothing, other processes can read it, and it
gets written back eventually.

**So why fsync at all?** Because of one specific disaster sequence:

```
write completes, data in page cache (not on disk)
rename completes, metadata hits disk
power loss
reboot → directory entry points at the new file, whose contents are 0 bytes or garbage
```

That is **metadata landing before data**, and it hands you a file with a correct name
and an empty body — exactly the thing atomic writes exist to prevent, sneaking back
in through the rear door.

ext4 grew a hack for this after 2009 (Ted Ts'o's patch, following the mass "my files
are all zeroes" complaints caused by delayed allocation): renaming over an existing
file triggers writeback of the data. **But that's an ext4 courtesy, not a POSIX
guarantee** — it doesn't necessarily hold on XFS, btrfs, or network filesystems.
So: fsync explicitly.

**Mind the cost**: fsync blocks synchronously waiting for physical confirmation.
Single-digit-to-tens of milliseconds on spinning rust, fractions of a millisecond
to a few ms on SSD, potentially hundreds of ms on network storage. In a loop writing
thousands of small files, fsync will dominate — there you either batch and fsync the
directory once, or accept a weaker guarantee.

---

### `os.replace(tmp, path)` — the signature

**Full definition of the atomicity**: at any instant, any observer opening `path`
sees either the complete old file or the complete new file. **There is no third
state, and no window in which the file is briefly absent.**

Underneath it's `rename(2)`, and POSIX requires that if the new name already exists
it be removed and the rename completed, and that the operation be atomic with
respect to other threads.

**Key point: readers who already have the old file open are unaffected.** Rename
only changes a directory entry; the old inode still has a refcount of +1 from that
open fd. The reader quietly finishes reading the old contents — a free benefit of
Unix's inode/dentry separation, and the reason `logrotate` can rotate logs safely
while a service is running.

**`os.replace`, not `os.rename`**: identical on POSIX, but **on Windows `os.rename`
raises `FileExistsError` when the target exists**. `os.replace` guarantees
cross-platform overwrite semantics (Windows: `MoveFileEx` + `MOVEFILE_REPLACE_EXISTING`).

**Windows caveat** (relevant if you have Windows runners): `MoveFileEx` fails when
the target file is **open in another process** (sharing violation → `PermissionError`).
No such problem on Unix. Antivirus scanning the file you just wrote is a particularly
common trigger — this is why file-writing tools on Windows so often carry retry logic.

---

### 🔴 The major omission: no fsync on the directory

`os.replace` modifies **the contents of a directory** (a directory entry), and a
directory is itself a file whose modifications also land in the page cache first.

```
os.replace returns success
    ↓
the new directory entry is in page cache
    ↓
power loss
    ↓
reboot → the entry never hit disk → the file "rolls back" to the old version,
         or both names are gone
```

To genuinely guarantee that the rename is durable, you must fsync **the parent
directory's fd**:

```python
dir_fd = os.open(path.parent, os.O_RDONLY)
try:
    os.fsync(dir_fd)
finally:
    os.close(dir_fd)
```

This step is present in SQLite, etcd and PostgreSQL's WAL implementations, and it is
**the most common gap between a textbook atomic write and one copied off the internet.**

(You can't fsync a directory on Windows — `os.open` on a directory errors — so it
needs a platform guard.)

---

### `except BaseException:` / `unlink(missing_ok=True)` / `raise`

**`BaseException` rather than `Exception` is correct, and deliberate.**

`KeyboardInterrupt` and `SystemExit` inherit from `BaseException` and **not** from
`Exception`. The entire reason this function exists is "even Ctrl-C must not leave a
mess" — catching only `Exception` means a Ctrl-C leaves the temp file on disk to
accumulate as litter.

`missing_ok=True` covers two cases: a signal arriving immediately after mkstemp
(file exists, delete it), and an exception raised *after* `os.replace` already
succeeded (tmp is gone, and that must not be an error).

A bare `raise` preserves the original traceback. **This function cleans up; it does
not decide.** Whether to retry or give up belongs to the caller. Cleanup and policy
stay separate.

---

## 🔬 The Interviewer's Follow-Up Chain

**Q1: Does this function guarantee atomicity or durability?**

They are **different properties provided by different mechanisms**:

| Property | Protects against | Provided by |
|---|---|---|
| Atomicity | A reader seeing a half file | `os.replace` |
| Durability | Losing content on power loss | `flush` + `fsync` (data) + fsync of the directory (metadata) |

If you only want atomicity, `os.replace` alone is enough. If you want durability,
none of the three syncs is optional. **In container/cloud environments plenty of
teams deliberately take atomicity without durability** — the node dying means the
whole instance is rebuilt, so the fsync cost buys nothing. That should be an explicit
trade-off, not "I copied a function and don't know what it guarantees."

**Q2: What's the problem with permissions?**

A real and common one: `mkstemp` creates the file **0600**. If the target was
originally 0644 (readable by others — nginx, another service account), the atomic
write **silently tightens it to 0600** and that service suddenly can't read it —
with no error at all, just a `PermissionError` downstream.

Fix: `chmod` before the rename, either to a umask-derived mode or to the original
file's mode.

**Q3: Does this hold on NFS?**

Partly, and carefully. `rename` is atomic **on the NFS server**. But NFSv3 client
attribute caching (`acregmin`/`acregmax`, typically 3–60s) means **another client may
keep seeing the old file for a while.** Atomicity isn't violated (nobody sees a half
file) but **visibility lags.**

Also, `unlink`ing an open file on NFS triggers a **silly rename** (the server renames
it to `.nfsXXXX`), so cleanup logic can leave mysterious hidden files behind.

Don't build distributed coordination on a filesystem — that's etcd/Consul's job.

**Q4: What if two processes atomically write the same path concurrently?**

Nothing corrupts, but it is **last-writer-wins with no indication whatsoever.** The
two temp names differ (mkstemp randomises), each writes its own, the two renames
serialise, and the later one wins.

Atomic writes guarantee **you never produce a bad file**; they do **not** guarantee
**you never lose an update.** Preventing lost updates needs a lock (`flock`) or CAS
semantics (`O_EXCL` create, fail if present).

**Q5: Why not `os.sync()`?**

`os.sync()` flushes **every dirty page on the system** — a global operation that can
block for seconds on a busy machine. `fsync(fd)` targets one file. Always the latter.

Related: Linux also has `os.fdatasync()`, which syncs data but not non-essential
metadata (mtime), so it's slightly faster. Pointless for a newly created file (size
is essential metadata and must sync anyway); useful for in-place overwrites.

---

## 🏗️ How This Shows Up at Scale

**SQLite's rollback journal**: the whole D in ACID rests on this dance, and SQLite's
source comments document its history of getting burned on various filesystems —
including that on macOS `fsync` by default **does not actually flush the drive cache**
(you need the `F_FULLFSYNC` fcntl, because Apple decided fsync was too slow). A
textbook case of "same API, different platform, different semantics."

**etcd / Kubernetes**: etcd's WAL write path has a dedicated `fileutil.Fsync` that
routes to `F_FULLFSYNC` on macOS. etcd is extremely sensitive to fsync latency —
the docs demand SSDs and `wal_fsync_duration_seconds` is one of its most critical
metrics. **Slow fsync = missed heartbeats = leader-election churn across the cluster.**

**Kafka goes the other way**: Kafka by default **does not fsync**, relying on
replication for durability. The bet is that the probability of three machines losing
power simultaneously is lower than the throughput cost of fsync. An explicit,
documented trade-off — and proof that fsync isn't always the right call.

**Git**: every object write uses this pattern (temp file → rename into
`.git/objects/xx/yyyy`), and because objects are content-addressed (the filename *is*
the content hash), **rename's last-writer-wins is harmless by construction** — two
processes writing the same hash necessarily write identical bytes. A lovely example
of dissolving a concurrency problem with a data model.

---

## 💸 The High-Stakes Version

- **fsync returning success does not mean the data is on disk.** Linux's famous 2018
  "fsync-gate" (surfaced by the PostgreSQL community): when writeback errors, the
  kernel **clears the dirty flag and reports the error to exactly one subsequent
  fsync**; fsyncs after that return success. PostgreSQL's response was to make fsync
  failure **panic the server** rather than retry — because retrying yields a false
  success. Same rule in finance: **fsync failure = stop, do not retry.**

- **Enterprise storage write caches.** A battery-backed RAID controller makes fsync
  suspiciously fast. That's fine while the battery is healthy and becomes silent data
  loss when it isn't — hence periodic BBU health checks.

- **Taking atomicity without durability is legitimate and common.** In high-write-rate
  scenarios (thousands of small files per second) fsync will simply eat your IOPS
  budget. The pattern: atomic rename for reader consistency, durability delegated
  upward (replication, WAL, object storage). **But that decision has to be in the
  code comment and the design doc**, not an oversight.

- **Audit requirements may forbid in-place overwrites entirely.** Many compliance
  regimes want append-only or write-once: write `metrics.v2.json` rather than
  overwriting `metrics.json`, preserving full history. The goal shifts from "safe
  overwrite" to "safe create," and `os.replace` gives way to `os.link` + `O_EXCL`
  (fail if it exists).

---

## 🚀 Where This Stands in 2026

- **`os.replace` is the only correct cross-platform answer in Python.** `os.rename`
  where an overwrite is intended is essentially a bug. Unchanged since 3.3.

- **io_uring changed the bulk-write picture.** Since Linux 5.x, io_uring supports
  `IORING_OP_FSYNC` and async rename, and storage engines (ScyllaDB, TigerBeetle)
  have gone all-in, sidestepping fsync's synchronous block. Python has no mature
  binding yet — `aiofiles` is a thread-pool wrapper, not real async.

- **The `atomicwrites` library is archived.** The author unmaintained it in 2022, and
  the reasoning is worth reading: most users don't actually need the abstraction, and
  the ones who do should understand what they're doing. **Recommendation: don't take
  the dependency, write these 15 lines in your project** — because you need to tune
  the fsync strategy to your own durability requirements, and a library's choice is
  usually not yours.

- **CoW filesystems change the assumptions.** btrfs / ZFS / bcachefs are copy-on-write
  with inherently transactional metadata updates, making much of the traditional fsync
  dance redundant. But **you can't assume which filesystem your code runs on**, so do
  it anyway.

- **On the way out**: `os.rename` for overwrites, fsyncing data but not the directory,
  hand-managing `NamedTemporaryFile(delete=False)` (one more abstraction layer than
  `mkstemp` and easier to leak an fd through).

---

## 🌉 The Cross-Discipline Lens: Signing a Contract

A merger agreement can go through thirty drafts, with lawyers redlining every clause
and both sides negotiating. **Before signature, every draft has exactly zero legal
force.** You cannot say "this contract is 60% in effect."

At the instant of signature, force jumps from 0 to 100 with no observable
intermediate state. That is `os.replace`.

**Notarisation and filing** are a separate matter: once signed, the document is still
only in your drawer; lodging it with a registry is what survives a fire. That is
`fsync`.

Two independent safeguards answering two different questions:

- "Could anyone ever see a half-executed contract?" → the instantaneity of the
  signature (atomicity)
- "If the office burns down, does the contract still exist?" → off-site filing
  (durability)

**And fsyncing the directory corresponds to "is the registry's own index backed up?"**
— your document is safely archived, but the ledger recording "this document is in
cabinet 7" is still sitting un-transcribed on someone's desk. Fire takes it and you
can't find the document either.

This also explains why Kafka dares skip fsync: it chose "sign one copy of the contract
in each of three cities" over "notarise one copy repeatedly."

---

## 🥋 Part 1 Mic-Drop

> `open(w)` is truncate-then-write, so a crash leaves you not with a missing file but
> with a lying one; the atomic write collapses those two steps into one indivisible
> instant via rename — but don't forget that the rename itself needs an fsync of the
> directory it lives in.

---

# Part 2: EXDEV — What "the Same Filesystem" Actually Means

Above I said rename is atomic only within one filesystem. So where is that boundary?

Three common guesses:

| Guess | Correct? |
|---|---|
| The same folder | ❌ Too strict. **Any two directories** within one filesystem work |
| The same computer | ⚠️ Necessary but nowhere near sufficient. One machine typically has 5–10 filesystems |
| The same hard drive | ❌ Neither necessary nor sufficient |

**The correct boundary is: the same mount point.**

## Why the mount point

Inode numbers are unique only **within one filesystem**. `/` has an inode 12345 and
`/home` has an inode 12345, and they have nothing to do with each other.

What `rename(2)` does is: **add an entry "name → inode 12345" to directory B, then
remove the corresponding entry from directory A.** Not one byte of file content moves.

So a cross-filesystem rename is physically undefinable — inode 12345 in the target
filesystem is somebody else's file. The kernel will not "helpfully" degrade to
copy+delete, because that **isn't atomic** and might mean moving 50GB. It tells you
`EXDEV` and lets you decide.

`mv` appears to move across drives because **`mv` is a program, not a syscall** — it
tries `rename()`, gets EXDEV, and falls back to copy + unlink itself. Which is why
`mv`ing a 50GB file within one drive is instant and across drives takes minutes.
**You've definitely seen this; you may not have wondered why.**

## Three counter-intuitive cases

**① One physical drive ≠ one filesystem**

One SSD partitioned three ways = three filesystems. `/` and `/home` on separate
partitions is an extremely common layout, and rename between them is EXDEV.

**② One filesystem ≠ one physical drive**

LVM, RAID and ZFS pools let a single filesystem span eight disks. **Renaming across
physical drives is perfectly fine** there, because logically it's still one filesystem.

**③ Even within one "drive" you can hit EXDEV**

- **btrfs subvolumes**: same device, mounted by one `mount` command, but rename
  between `/data/@snapshots` and `/data/@current` returns EXDEV. ZFS datasets likewise.
- **Bind mounts** (a Linux-specific trap): after `mount --bind /data /app/data`,
  `/data/x` and `/app/data/y` have **identical `st_dev`**, yet rename still returns
  EXDEV — because the kernel compares `vfsmount`, not just `st_dev`.

That third point matters: **equal `st_dev` is necessary, not sufficient.** Trying to
predict "can I rename this?" from `os.stat().st_dev` misses the bind-mount case.

## Counting the filesystems on your machine

```bash
$ df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme0n1p2  460G  210G  227G  49% /          ← ①
tmpfs           7.8G  1.2M  7.8G   1% /tmp       ← ② in RAM!
/dev/nvme0n1p1  511M   31M  481M   6% /boot/efi  ← ③ another partition, same drive
/dev/sdb1       1.8T  900G  850G  52% /mnt/data  ← ④
```

**Every line is a filesystem. Rename between any two lines is EXDEV.**

To check whether two paths share a filesystem, compare device numbers:

```bash
$ stat -c '%d %n' /tmp/a /home/todd/b
1  /tmp/a
66306  /home/todd/b        # different → guaranteed EXDEV
```

In Python:

```python
Path("/tmp").stat().st_dev == Path("/home/todd").stat().st_dev
```

## Why containers hit this almost every time

A typical Docker container:

```
/           overlayfs      ← image layers
/tmp        tmpfs          ← RAM (many base images configure this)
/app/data   volume/bind    ← mounted volume
/dev/shm    tmpfs
```

**Four different filesystems.**

Which produces the classic failure chain:

```python
# looks entirely harmless
fd, tmp = tempfile.mkstemp()          # → /tmp/xxxx (tmpfs)
...
os.replace(tmp, "/app/data/metrics.json")   # → mounted volume
# OSError: [Errno 18] Invalid cross-device link
```

**And it works perfectly on your Mac** — because macOS's `/tmp` and your project
directory are on the same APFS volume. Code written, tests green, CI explodes on
first container run.

What makes this class of bug particularly unpleasant: it isn't a logic error, it's an
**environment-assumption error**, and it never reproduces locally.

## So the fix is not "detect and handle"

The instinct is to add a fallback:

```python
try:
    os.replace(tmp, path)
except OSError as e:
    if e.errno == errno.EXDEV:
        shutil.move(tmp, path)   # ❌ disaster
```

**This is the worst possible version.** `shutil.move` across devices is copy + unlink,
**entirely non-atomic** — your carefully designed atomic write silently degrades to
the least safe implementation precisely when it's needed most, with no log line to
tell you it happened.

The right move is making EXDEV **structurally impossible**:

```python
tempfile.mkstemp(dir=path.parent, ...)
```

The temp file is born **next door to the target**. They share a directory by
construction; sharing a directory means sharing a mount; sharing a mount means sharing
a filesystem. **No detection, no degradation, no branch — the error class is
eliminated, not handled.**

## What about across machines?

**Across machines EXDEV never even comes up** — you can't reach another machine's
filesystem; there is no syscall. SSH/rsync/S3 are all application protocols and none
of them go through `rename(2)`.

The one exception is network filesystems: once NFS is mounted, `/mnt/nfs` is a normal
filesystem, rename within it is entirely legal, and atomicity is the server's
responsibility. But `/mnt/nfs/a` → `/home/b` is still EXDEV, because those are two
filesystems.

A useful counter-example: **S3 has no rename.** S3 is object storage, not a
filesystem; "rename" is COPY + DELETE, two API calls, and **for an instant both keys
exist — not atomic.** Atomic publication on S3 needs a different mechanism (versions,
pointer objects, conditional writes). Plenty of people port the "write temp, then
rename" habit to S3 and are then baffled by the inconsistent reads.

## 🥋 Part 2 Mic-Drop

> Rename's atomicity comes from the fact that it moves a directory entry and not data
> — and that is exactly why it can't cross filesystems: an inode number outside its own
> filesystem is a meaningless integer. The boundary is a line in `df`, not a drive and
> not a folder.

---

# Part 3: Why the Temp Filename Needs a Leading Dot

Back to `prefix=f".{path.name}."`. Here's the measured result:

```python
import tempfile, os, glob
from pathlib import Path

d = Path("/tmp/globdemo")
target = d / "cot_gpt5_dev_seed42.metrics.json"
target.write_text("{}")

fd1, t1 = tempfile.mkstemp(dir=d, prefix=target.name, suffix=".tmp")          # original
fd2, t2 = tempfile.mkstemp(dir=d, prefix=f".{target.name}.", suffix=".tmp")   # fixed
```

Output:

```
original temp: cot_gpt5_dev_seed42.metrics.jsonym6wfn0y.tmp
fixed temp:    .cot_gpt5_dev_seed42.metrics.json.lcvg6fnw.tmp

glob('*.metrics.json' )  -> ['...metrics.json']                                  ✅ both fine
glob('*.metrics.json*')  -> ['...metrics.json', '...metrics.jsonym6wfn0y.tmp']   ⚠️ original swept in
glob('*metrics*'      )  -> ['...metrics.json', '...metrics.jsonym6wfn0y.tmp']   ⚠️
glob('*'              )  -> ['...metrics.json', '...metrics.jsonym6wfn0y.tmp']   ⚠️

os.listdir sees everything: ['.cot_...tmp', 'cot_...json', 'cot_...jsonym6wfn0y.tmp']
```

**The fixed file appears in none of the four globs, yet `os.listdir` still sees it.**
That's the whole point.

## `mkstemp`'s prefix is concatenated with no separator

```
cot_gpt5_dev_seed42.metrics.jsonym6wfn0y.tmp
                             ↑
                  random chars welded straight onto "json"
```

The formula is `prefix + 8 random chars + suffix`, with **nothing inserted between**.
So the first 33 characters of the temp filename are **byte-identical to the real
artifact.**

It isn't "a temp file" any more. It's "a thing that looks like the artifact with a
slightly longer name."

## Who gets fooled

If your design has **filenames carrying semantics** (say, a complete run is
`.metrics.json` and an incomplete one is `.metrics.partial.json`), there will
absolutely be downstream code matching on filenames:

**CI artifact collection**

```yaml
- uses: actions/upload-artifact@v4
  with:
    path: results/*metrics*       # uploads the half-written JSON as an artifact
```

**Aggregation scripts**

```python
for f in Path("results").glob("*.metrics.json*"):    # wants both .json and .partial.json
    data = json.loads(f.read_text())                 # 💥 JSONDecodeError
```

That trailing `*` exists to match both `.metrics.json` and `.metrics.partial.json` —
**a completely reasonable thing to write** — and it picks up `.tmp` as a side effect.

**Cleanup / sync**

```bash
rsync results/*metrics* backup/       # syncs a file that's actively being written
find results -name '*metrics*' -mtime +30 -delete
```

## When you actually collide

Normally never — the temp file lives for milliseconds and is renamed away. **It exists
in exactly two situations, and both are the moments you most need the directory to be
readable:**

**① Crash residue.** The process is `SIGKILL`ed (OOM killer, `docker stop` timeout,
K8s eviction), so the `except` block **never runs** and the `.tmp` stays on disk
permanently. Your output directory accumulates zombie files that *look like artifacts*
— and carry the full run name, which makes them maximally confusing.

**② The concurrency window.** One run is writing a file while another process (a
monitoring dashboard, another CI step) scans the directory and lands in those few
milliseconds. A one-in-a-thousand bug and miserable to chase.

## Why one dot fixes it

`glob` follows the shell convention: **`*` in a pattern does not match a leading dot.**
CPython's `glob.py` has exactly one function for it:

```python
def _ishidden(path):
    return path[0] in ('.', b'.'[0])
```

Dotfiles match only when the pattern itself starts with a dot. So `.foo.tmp` is
**invisible to `*`, `*metrics*` and `*.metrics.json*` alike.**

**And this is platform-independent** — CPython implements the rule itself rather than
delegating to the OS. `glob("*")` skips dotfiles on Windows too.

**Meanwhile `os.listdir` still sees it**, so your own cleanup logic
(`for f in os.listdir(d): if f.endswith(".tmp")`) is unaffected. **Visible where it
should be, hidden where it shouldn't** — exactly the division you want.

**The trailing dot** is a separate, purely cosmetic matter:

```
.cot_gpt5_dev_seed42.metrics.json.lcvg6fnw.tmp
                                 ↑
              random chars separated — name vs. noise readable at a glance
```

## Eliminating a class, not handling a case

```python
# Approach A: leave the trap and require every caller to remember it
for f in Path("results").glob("*.metrics.json*"):
    if f.suffix == ".tmp":     # every script has to carry this line
        continue
```

This requires **every present and future downstream** to know the convention. You
can't express that filter in CI YAML, and you can't express it in `rsync`. Something
will miss it.

```python
# Approach B: make the temp file nonexistent as far as default tooling is concerned
prefix=f".{path.name}."
```

One line, and every downstream gets safety for free — including the ones you haven't
written.

Same pattern as `dir=path.parent`: **replace a convention you must remember with a
structure you can't violate.**

## Two footnotes

**A leading dot doesn't hide anything on Windows.** Windows "hidden" is a filesystem
attribute bit, not a naming convention, so Explorer shows the `.tmp` regardless. But
**Python's `glob` still skips it** (that `_ishidden` is pure string inspection), so
your scripts are safe and only human eyes see it. Actually hiding it on Windows means
`SetFileAttributesW`, which isn't worth it.

**`.gitignore` gets simpler too:**

```gitignore
results/.*.tmp
```

One line covering every temp file.

---

# The Corrected Implementation

```python
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


def _write_json_atomic(
    path: Path,
    payload: dict[str, Any],
    *,
    durable: bool = True,
    mode: int = 0o644,
) -> None:
    """Write a JSON file atomically.

    Guarantees two distinct things via two distinct mechanisms:

    - **Atomicity** (``os.replace``): any reader sees either the complete old
      file or the complete new one. No half state, and no window in which the
      file is absent. Readers holding the old file open are unaffected and
      finish reading the old contents.
    - **Durability** (``durable=True``): the contents survive power loss. This
      needs three syncs — the userspace buffer, the data pages, and the parent
      directory that carries the new entry. In container environments where a
      node failure means a full rebuild, that cost often buys nothing, so it can
      be turned off; but that must be an explicit decision, not an omission.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Serialise fully first: an unserialisable payload should fail before any
    # I/O happens, not after half a file has been written. A pure computation
    # error does not belong in the I/O cleanup path.
    text = json.dumps(payload, indent=2, ensure_ascii=False)

    # dir=path.parent is the most important argument here: rename is atomic only
    # within one filesystem, and crossing devices returns EXDEV outright. The
    # default /tmp is usually tmpfs inside a container while the output dir is a
    # mounted volume — fine locally, guaranteed to fail in CI.
    #
    # Leading dot: otherwise the temp file starts with the target's full name and
    # gets swept up by glob("*.metrics.json*") and any CI step keyed on filenames.
    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    tmp = Path(tmp_name)

    try:
        # fdopen takes ownership of the fd and closes it on with-exit.
        # encoding must be explicit: omitted, it follows the locale, which is
        # cp1252/GBK on Windows.
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            if durable:
                # flush: userspace buffer → kernel page cache (issues write(2))
                # fsync: page cache → physical media
                # The order is not interchangeable: fsync without flush finds no
                # bytes in the kernel, returns success, and synchronises nothing.
                fh.flush()
                os.fsync(fh.fileno())

        # mkstemp creates 0600. If the target was 0644, the atomic write silently
        # tightens permissions and a downstream service account stops being able
        # to read it, with no error anywhere.
        os.chmod(tmp, mode)

        # The signature. os.rename raises FileExistsError on Windows when the
        # target exists, so this must be replace.
        os.replace(tmp, path)

        if durable and sys.platform != "win32":
            # The most commonly missed step: replace modifies the parent
            # directory's contents, and directory entries also land in page cache
            # first. Without this fsync, power loss can "roll back" the file to
            # the old version — the data persisted, the page recording where it
            # lives did not.
            dir_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)

    except BaseException:
        # BaseException rather than Exception is deliberate: KeyboardInterrupt and
        # SystemExit do not inherit from Exception, and "even Ctrl-C leaves no
        # mess" is the entire reason this function exists.
        #
        # missing_ok covers both a successful replace (tmp already gone) and a
        # signal arriving immediately after mkstemp.
        tmp.unlink(missing_ok=True)
        # Bare raise preserves the original traceback. This function cleans up;
        # whether to retry or give up is the caller's decision.
        raise
```

---

# Back to That First Line

```python
metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
```

Is it wrong? **Depends entirely on what the file is.**

- A **log, a cache, an intermediate artifact you can regenerate at will** → this line
  is perfectly adequate. The 60 lines above are over-engineering.
- A **deliverable** (someone reads it, CI depends on it, it cost money to produce,
  losing it means rerunning) → this line is a silent failure waiting for its trigger.

The test is one sentence: **"Could a half-written version of this file be mistaken for
a complete one?"** If yes, `write_text` is off the table.

And the real lesson isn't "use atomic writes." It's that **this line looks completely
normal, so nobody stops it in review** — its problem isn't syntax, isn't types, isn't
test coverage. Its problem is that the **default mental model of "writing a file" is
wrong**: `open(w)` was never one operation.

---

# Appendix: Checklist

Run through this whenever you write an atomic file write:

- [ ] First ask: **could a half-written version be mistaken for a complete one?** If not → `write_text` is fine, don't over-engineer

- [ ] Temp file **in the target's own directory** (`dir=path.parent`), not `/tmp` — otherwise EXDEV in containers
- [ ] Temp filename **starts with a dot** — otherwise glob and CI sweep it up
- [ ] Use `mkstemp`, don't hand-build the name — `O_EXCL` eliminates TOCTOU
- [ ] **Serialise before touching I/O** — a serialisation error shouldn't produce half a file
- [ ] `flush()` **before** `fsync()` — reversed, the fsync is silently a no-op
- [ ] `os.chmod` to fix permissions — mkstemp is 0600 and silently tightens
- [ ] `os.replace`, not `os.rename` — the latter can't overwrite on Windows
- [ ] **fsync the parent directory** — the most commonly missed step
- [ ] `except BaseException`, not `Exception` — Ctrl-C must still clean up
- [ ] State explicitly whether you want atomicity or durability — that's a trade-off, not an oversight
