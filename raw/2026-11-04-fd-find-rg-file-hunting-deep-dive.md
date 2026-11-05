---
title: "Digging All the Way Down From One fd Command: The CLI File-Hunting Toolkit (fd / find / rg / touch)"
date: 2026-11-04
categories: [shell, cli, productivity]
tags: [fd, find, ripgrep, xargs, touch, timestamps]
---

Here's how it started: I just wanted to tweak `fd -t f -e md` to list "the 5 most recently modified md files."

One tiny request — and like pulling a loose thread, it unraveled the entire CLI file-hunting toolchain: `fd`, `find`, `rg`, `xargs`, `touch`. Each tool's obscure tricks, how they divide labor, and a pile of traps hiding inside file timestamps. This post stitches that whole "dig all the way down" session into one coherent walkthrough, following the order a programmer would actually hit each piece.

If you've been getting by on `find . -name` and `ls -lt | head`, this will probably bump your command-line game up a notch.

---

## Stop 1: The original request

**Direct answer:**

```bash
fd -t f -e md -X ls -t | head -5
```

Breaking it down:

- `fd -t f -e md`: find all `.md` files (`-t f` = files only, `-e md` = filter by extension).
- `-X`: hand every result to the following command at once — effectively `ls -t file1 file2 ...`. Lowercase `-x` runs the command once *per file*, which would make sorting meaningless.
- `ls -t`: sort by modification time, newest first.
- `head -5`: keep only the top 5.

Want the modification times too:

```bash
fd -t f -e md -X ls -lt | head -6
```

Note `head -6` here, because `ls -l` prints an extra `total N` line — take 5 and you'd lose a file.

**First trap:** `fd` skips hidden files *and* `.gitignore`d files by default. If your `.md` lives in something like `.claude/`, it gets "eaten." Add `-H` (hidden) or `-I` (ignore the ignore-files).

This answer works, but it takes a detour — `ls -t | head` sorts *then* truncates. There are more direct ways, as we'll see.

---

## Stop 2: fd's time windows and lesser-known tricks

### Filter by time instead of sorting

**Direct answer:**

```bash
fd -e md --changed-within 2d
```

That's "md files changed in the last 2 days." No `ls`, no `head` — the time condition goes straight into the query.

- Units are flexible: `30min`, `10h`, `2d`, `1week`.
- Absolute times work too: `--changed-within "2026-11-01"` or `"2026-11-01 10:00:00"`.
- Flip it with `--changed-before` to find stale, zombie docs — great for cleaning out old notes.
- For a range, stack both: `--changed-within 30d --changed-before 7d` means "changed between 7 and 30 days ago."

**The distinction:** `--changed-within` only *filters*, it doesn't sort. For "newest first" you still need `-X ls -lt`. So: fixed count (newest 5) → `ls -t | head`; fixed time (changed today) → `--changed-within`.

### Filenames with spaces don't break it

**Direct answer:** fd's built-in `-x` / `-X` is usually enough — it doesn't go through shell word-splitting, so `my notes.md` won't get chopped into `my` and `notes.md`.

Only when you insist on piping do you need this combo:

```bash
fd -e md -0 | xargs -0 ls -t
```

`-0` makes fd separate results with NUL bytes, and `xargs -0` splits on NUL. Spaces, quotes, even newlines in filenames — all handled.

**An obscure trap:** `-X` (uppercase) auto-batches when there are a lot of files, because command lines have a length limit. Once batched, `ls -t` only sorts *within each batch*, so "globally newest 5" can be wrong. `xargs` has the same flaw. Fine for a few hundred md files; be careful scanning all of `node_modules` or a monorepo.

### `-x` placeholders — most people only know `{}`

There's a whole set:

| Placeholder | Meaning | Example `src/a/foo.md` |
|---|---|---|
| `{}` | full path | `src/a/foo.md` |
| `{/}` | filename | `foo.md` |
| `{//}` | parent dir | `src/a` |
| `{.}` | path without extension | `src/a/foo` |
| `{/.}` | filename without extension | `foo` |

For example, batch-convert md to html:

```bash
fd -e md -x pandoc {} -o {.}.html
```

### Other handy flags

- **Find by size:** `fd -S +1m` for larger than 1MB, `-S -10k` for smaller than 10KB.
- **Exclude dirs:** `fd -E node_modules -E .git` — just stack more `-E`s.
- **Limit depth:** `-d 2` only descends two levels; absurdly fast in big repos.
- **Match the full path:** `-p` makes the regex match the whole path, not just the filename.
- **Everything mode:** `-u` equals `-H -I` — hidden files and gitignore'd files all included, solving the "file got eaten" problem in one shot.

**The biggest trap:** `-x` runs in parallel by default, so output order is non-deterministic. For ordered output add `-j 1`. Parallel is fast for batch edits, but your logs will be scrambled.

---

## Stop 3: fd and rg, working together

**Direct answer:** fd decides *which files*, rg decides *what's inside them*. Separation of duties.

```bash
fd -e md --changed-within 2d -X rg -H "TODO"
```

That's "among md files changed in the last 2 days, where's a TODO written."

**Why the `-H`:** when `rg` receives a single file, it doesn't print the filename by default. If `-X` happens to hand it exactly one result, the output has no filename and you're left wondering "which file is this line from?" `-H` (`--with-filename`) forces the filename to show.

### rg can sort by time all by itself

```bash
rg --files -g '*.md' --sortr modified | head -5
```

This answers the original question with *zero* fd involved. `rg --files` lists files without searching content, and `--sortr modified` sorts by mtime descending (`--sort` is ascending, oldest first). fd smiles quietly and hands over the "I'm just a file finder" crown.

**Trap:** once you turn on `--sort`, rg degrades to single-threaded and slows down in big repos. So "narrow with fd first, then search content with rg" is often faster on large codebases.

### Or go the other way: search content first, then sort by time

```bash
rg -l -0 "TODO" -g '*.md' | xargs -0 ls -t
```

`-l` prints only matching filenames, `-0` + `xargs -0` guards against spaces, `ls -t` sorts by time.

Also: fd and rg both honor `.gitignore` and skip hidden files by default, so as a duo they're "consistent" — you won't hit the weird case where fd finds a file but rg can't search it. To open everything up, add `-u` on both sides.

---

## Stop 4: The core differences between fd and find

**Direct answer:** fd is the "nice daily-driver sports car," find is the "truck that's everywhere." Use fd when you can, but the scenarios below call for find.

| | fd | find |
|---|---|---|
| Default matching | regex (`-g` for glob) | glob (`-name`) |
| Case | smart-case (all-lowercase = case-insensitive) | case-sensitive (`-iname` to ignore) |
| Hidden/gitignore | skipped by default | sees everything |
| Parallelism | parallel by default | single-threaded |
| Ubiquity | needs installing (`fdfind` on Debian/Ubuntu) | POSIX built-in |

**When you *must* use find:**

1. **fd isn't installed on the server.** You SSH into a clean prod box, fd isn't there, find always is. The most practical reason of all.
2. **Find by permission:** `find . -perm -u+x`. fd has no `-perm`.
3. **Custom output format:** GNU find's `-printf` is powerful. The classic "newest 5 files with timestamps":

   ```bash
   find . -name '*.md' -printf '%T@ %p\n' | sort -nr | head -5
   ```

   `%T@` is the mtime as a Unix timestamp — sorts accurately and reliably.
4. **Complex boolean logic:** find supports `-o` (or), `-not`, parenthesized grouping.
   e.g. `find . \( -name '*.log' -o -name '*.tmp' \) -mtime +30 -delete` means "delete all logs or tmps older than 30 days" in one command.
5. **`-prune` to skip subtrees:** precisely avoid descending into a directory. fd's `-E` is similar, but find's form composes flexibly with other conditions.
6. **`-delete`, `-links`, `-newer <file>`** and other obscure predicates — fd either lacks them or needs a workaround.

**The biggest trap:** argument order matters with `find ... -delete` — `-delete` must come *after* the conditions. Write `find . -delete -name '*.tmp'` and find deletes first, evaluates second — i.e. "delete everything." Before deleting, swap `-delete` for `-print` and do a dry run. Life-saving habit.

**One-line rule:** interactive, everyday finding → fd; portable scripts, or permissions/formatting/complex logic → find.

---

## Stop 5: find's `-exec {} +` vs `\;` vs xargs

**Direct answer:** `\;` is "order takeout once per file," `+` is "batch up one order." Use `+` when you can — it's dozens of times faster.

```bash
# Launch ls once per file; 1000 files = 1000 launches
find . -name '*.md' -exec ls -l {} \;

# Batch into one command: ls -l a.md b.md c.md ...
find . -name '*.md' -exec ls -l {} +
```

**Why `\;` needs the backslash:** `;` means "end of command" in the shell. Unescaped, the shell splits the command in half before find ever sees it. `';'` works too.

**The three compared:**

| | `-exec ... \;` | `-exec ... {} +` | `\| xargs` |
|---|---|---|---|
| Invocations | once per file | batched, fewest | batched |
| `{}` position | anywhere | must sit right before `+` | needs `-I{}` to go mid-command |
| Parallel | no | no | yes with `-P 4` |
| Empty filenames | handled correctly | handled correctly | needs `-print0 \| xargs -0` |
| Usable as a test | yes | no | no |

**Obscure trick 1: `\;` can act as a test condition**

```bash
find . -name '*.md' -exec grep -q "TODO" {} \; -print
```

`grep -q` returns 0 on a match, so `-exec` evaluates "true," and the following `-print` runs. You get "filenames containing TODO" directly. `+` can't do this — it always returns true, and the real result only arrives at the very end.

**Obscure trick 2: what if `{}` must be last?** For copying, the target dir has to come last:

```bash
find . -name '*.md' -exec cp -t /backup {} +
```

GNU `cp -t` lets you put the target dir first, so `{}` can bring up the rear. `mv -t` works the same. macOS's BSD `cp` has no `-t`, so there you're stuck with `\;` or xargs.

**Obscure trick 3: `-execdir` and `-ok`**

- `-execdir`: cd into the file's directory first, then run; `{}` becomes `./filename`. Safer in world-writable dirs like `/tmp` — it avoids symlink-swap attacks.
- `-ok`: prompts y/n before each run. A seatbelt for batch deletes.

**Three traps:**

1. **`+` also batches.** With too many files it still gets split into multiple batches, so the earlier "`ls -t | head -5` global sort is unreliable" warning applies here too.
2. **`xargs` runs once even on empty input.** If `find` finds nothing, `xargs rm` still fires an argument-less `rm` once. GNU's `-r` (`--no-run-if-empty`) fixes it. `find -exec +` simply doesn't run on no matches — more sensible there.
3. **Exit codes differ.** With `+`, any failing batch makes find return non-zero overall. With `\;`, a failure only affects that one evaluation; find itself still exits 0. Watch out when your script keys off exit codes.

**How to choose:**

- Need a test condition, or per-file handling → `\;`
- Plain batch operation → `+`
- Need parallelism, or piping to another tool → `-print0 | xargs -0 -P 4`

---

## Stop 6: find's time predicates `-mtime` / `-mmin` / `-newer`

**Direct answer:** `-mtime` counts whole 24-hour chunks *and rounds down*, so `-mtime 1` is not "1 day ago," it's "between 24 and 48 hours ago."

```bash
find . -name '*.md' -mtime -2    # changed within 48 hours
find . -name '*.md' -mtime +7    # untouched for 7+ days (actually ≥ 8 days)
find . -name '*.md' -mtime 0     # changed in the last 24 hours
```

**What the three forms mean:**

| Form | Meaning | Plain English |
|---|---|---|
| `-mtime -n` | fewer than n 24-hour chunks | within the last n days |
| `-mtime n` | exactly n chunks (after rounding) | the n-th day window |
| `-mtime +n` | more than n chunks | older than n+1 days |

**Why is `+7` "≥ 8 days"?** find rounds the file's age *down* to whole days before comparing. A file from 7.9 days ago rounds to 7, which is not greater than 7, so `+7` misses it. It must hit a full 8 days — rounding to 8 — to count as `> 7`. This is the single most classic `-mtime` trap.

**For precision, skip `-mtime` and use `-mmin`:**

```bash
find . -name '*.md' -mmin -30    # last 30 minutes
find . -name '*.md' -mmin +1440  # over 24 hours, counted in minutes, no rounding trap
```

**Obscure trick 1: `-daystart`, count from "midnight today"**

```bash
find . -name '*.md' -daystart -mtime 0
```

Without it, "0" means "the past 24 hours." With it, it becomes "since midnight today" — i.e. "changed today." Note it must come *before* `-mtime` to take effect.

**Obscure trick 2: `-newer`, use a file as a time ruler**

```bash
find . -name '*.md' -newer README.md
```

"md files newer than README.md." Combined with `touch` for checkpoints, it's excellent:

```bash
touch /tmp/mark          # drop a marker
# ...do work...
find . -newer /tmp/mark  # which files changed during the work
```

**Obscure trick 3: `-newermt`, write dates directly (GNU find)**

```bash
find . -newermt "2026-11-01" ! -newermt "2026-11-04"
```

"changed between Nov 1 and Nov 4." `!` negates, and the two conditions bracket a time window. Far more intuitive than `-mtime`.

**Three traps:**

1. **`-mtime` is modification time, not creation time.** It only updates when content changes; `mv` (rename) doesn't touch it, but `cp` generates a new time (unless you add `-p`).
2. **Don't trust `-atime` much.** Many systems mount with `relatime`/`noatime`, so access time isn't updated every read.
3. **BSD/macOS find has no `-newermt`.** There, either use `-newer` with a `touch -t`'d ruler file, or fall back to `-mtime`.

**One-line rule:** minute precision → `-mmin`; "after a certain date" → `-newermt`; "newer than a file" → `-newer`; use `-mtime` only for rough day-level queries where you remember the rounding rule.

---

## Stop 7: Fabricate timestamps with `touch` to verify every condition above

**Direct answer:** to verify find's time conditions, don't sit around waiting — use `touch` to time-travel files into the past.

```bash
touch -d "3 days ago" old.md          # GNU touch, accepts plain English
touch -d "2026-11-01 10:30" a.md      # specific date-time
touch -t 202611011030 b.md            # legacy format: YYYYMMDDhhmm
```

**The two flags compared:**

| | `-d` | `-t` |
|---|---|---|
| Syntax | free text, ISO format, `@timestamp` | fixed `[[CC]YY]MMDDhhmm[.ss]` |
| GNU (Linux) | accepts plain English like `"yesterday"` | yes |
| BSD (macOS) | only ISO 8601 like `2026-11-01T10:30:00`, not `"3 days ago"` | yes |

For portable scripts, use `-t` — it runs everywhere.

**Hands-on: build a sandbox and verify Stop 6's "rounding trap" yourself**

```bash
d=$(mktemp -d) && cd "$d"
touch -d "7 days 22 hours ago" almost8.md   # ~7.9 days ago
touch -d "8 days ago" exactly8.md
find . -name '*.md' -mtime +7
```

The expected result: only `exactly8.md` is caught, `almost8.md` slips through. `mktemp -d` makes a temp directory, so break it all you want.

**Obscure tricks:**

1. **`-r` copies another file's time:** `touch -r README.md new.md` sets `new.md`'s time to match `README.md`. Handy with `-newer` tests.
2. **Touch only one time:** `-m` changes mtime only, `-a` changes atime only. This is how you test the difference between `-atime` and `-mtime`.
3. **Use an epoch timestamp:** `touch -d @1730000000 x.md` — paste a timestamp straight from a log.
4. **`-c` doesn't create:** `touch -c file` does nothing if the file doesn't exist, so you won't accidentally spawn an empty file.
5. **Batch-make a staircase of files:**

   ```bash
   for i in 1 2 3 4 5; do touch -d "$i days ago" "f$i.md"; done
   ```

   `f1` through `f5` are each one day apart — perfect for testing conditions like `-mtime -3` at a glance.

**Verify the fabrication worked:**

```bash
ls -l --time-style=long-iso        # GNU
stat -c '%y %n' *.md               # GNU, nanosecond precision
stat -f '%Sm %N' *.md              # BSD/macOS
```

**Four traps:**

1. **ctime can't be faked.** `touch` can change mtime and atime, but ctime (status-change time) is always "now" — the kernel won't let you set it. So `find -ctime` can't be tested with touch.
2. **Timezone pitfall.** `-d "2026-11-01 10:30"` is interpreted in local time. For deterministic results write `-d "2026-11-01 10:30 UTC"` (GNU).
3. **`touch`ing an existing file doesn't wipe its content** — it only updates the time, so it's safe. But on a read-only file you'll get Permission denied.
4. **Time travel won't fool backup and build tools.** `make`, `rsync` and friends decide by timestamp; messing with mtime can make them think "nothing changed" and skip. Don't casually time-travel inside real projects.

---

## Wrap-up: a "pick the tool by the need" cheat sheet

Starting from one line of `fd`, we walked the entire file-hunting chain. Condensed into one-liners:

- **Finding files, interactive** → `fd`; remember `-u` to include hidden files.
- **Fixed count (newest 5)** → `... -X ls -t | head`.
- **Fixed time window (today / last 2 days)** → `fd --changed-within`, or `find -mmin` / `-newermt`.
- **Portable scripts, permissions, fancy output** → `find`; `-printf '%T@ %p\n' | sort -nr` is the sorting trump card.
- **Batch execution** → `+` when you can, `\;` for test conditions, `xargs -P` for parallelism.
- **Searching content** → `rg`, which can `--sortr modified` on its own.
- **Testing time conditions** → `mktemp -d` sandbox + `touch -d` timeline.

A trivial "list the 5 most recent files" question turned into a full review of command-line fundamentals. That's the command line for you: pull on any loose thread and there's a whole set of things worth mastering behind it.
