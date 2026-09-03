---
title: "The Trailing Slash: A Small Character That Changes Everything"
description: "Why `cp -R src/ dest/` and `cp -R src dest/` do different things on macOS — and why the same slash means the opposite in rsync."
tags: [unix, macos, shell, cp, rsync, gotchas]
---

# The Trailing Slash: A Small Character That Changes Everything

It starts with a command that looks completely reasonable:

```bash
cp -R mq-airflow/ projects/ilearn/
```

The intent: copy the folder `mq-airflow` into `projects/ilearn/`, so you end up
with `projects/ilearn/mq-airflow/`.

What actually happens on macOS: every file that *was* inside `mq-airflow` is now
sprayed directly into `projects/ilearn/`. No `mq-airflow` folder in sight.

The culprit is one character — the slash after the **source** path.

## The Fix

Drop the trailing slash on the source:

```bash
cp -R mq-airflow projects/ilearn/
```

That gives you `projects/ilearn/mq-airflow/` with everything inside it.

Two caveats before we get into the *why*:

- **`projects/ilearn/` must already exist.** If it doesn't, `cp` will create a
  copy *named* `ilearn` instead of copying into it. Run `mkdir -p projects/ilearn`
  first. Keeping the trailing slash on the **destination** helps here — it makes
  `cp` error out loudly rather than silently doing the wrong thing.
- **If `projects/ilearn/mq-airflow` already exists**, `cp -R` *merges* into it
  rather than replacing it, so stale files can linger. For a guaranteed-clean
  copy, delete the target first or use `rsync`:

  ```bash
  rsync -a --delete mq-airflow/ projects/ilearn/mq-airflow/
  ```

  Note that `rsync` uses the **opposite** convention — there, the trailing slash
  on the source is the one you *want*. More on that below.

---

## Part 1: The Kernel-Level Rule

POSIX specifies that a pathname ending in one or more slashes is resolved
**as if a single `.` were appended**.

So `foo/` is effectively `foo/.`. That has two consequences.

### 1. It asserts "this is a directory"

```bash
touch f
cat f     # works
cat f/    # cat: f/: Not a directory
```

`f/.` requires `f` to be a directory. It's a regular file, so you get `ENOTDIR`.

### 2. It dereferences a symlink

`link` is the link itself. `link/` is whatever it points at.

```bash
mkdir realdir && ln -s realdir link
ls -ld link    # lrwxr-xr-x ... link -> realdir
ls -ld link/   # drwxr-xr-x ... link//
```

This one is genuinely dangerous:

```bash
rm link         # removes the symlink; realdir untouched
rm link/        # error — it's a directory
rm -rf link/    # historically ate the *contents of realdir*
```

Tab completion loves to append slashes to symlinks, which is exactly how people
end up deleting the wrong thing.

---

## Part 2: The Conventions Tools Layer On Top

Individual programs add their own meanings *beyond* the kernel rule. This is
where the inconsistency really comes from.

### `cp` (BSD — i.e. macOS)

A trailing slash on the **source** means "the contents of":

```bash
cp -R mq-airflow/ projects/ilearn/   # contents scattered into ilearn/
cp -R mq-airflow  projects/ilearn/   # creates ilearn/mq-airflow/
```

> ⚠️ **This is not how GNU `cp` behaves on Linux**, where the slash is
> essentially ignored and you get `dest/src` either way. The same command can
> produce different results on your Mac and on your Linux server.

Don't trust memory — verify on whatever machine you're actually on:

```bash
mkdir -p t/src/sub t/dest && touch t/src/a
cp -R t/src/ t/dest/ && find t/dest
```

### `rsync` (the opposite convention, and the strictest about it)

| Form | Meaning |
| --- | --- |
| `rsync -a src/ dest/` | copy the **contents** of `src` |
| `rsync -a src dest/`  | copy the **directory** `src` itself |

The destination slash is irrelevant. This is why `--delete` plus a wrong slash
is a classic way to lose data.

### `mv`

Mostly just follows the kernel rule. `mv a b/` requires `b` to be an existing
directory — which makes it a decent safety habit, since it errors out instead of
silently renaming `a` to `b`.

### `ln -s`

`ln -s target link/` places the link *inside* `link` if `link` is a directory.

### `find`

`find dir/` vs `find dir` affects whether top-level symlinks are followed, and
changes the paths printed in the output.

---

## Part 3: The Same Idea Shows Up Everywhere

Once you recognise "trailing slash = directory-ness", you start seeing it well
beyond file tools:

- **`.gitignore`** — `build` matches files *and* directories; `build/` matches
  only directories.
- **Dockerfile `COPY`** — `COPY src /dest` vs `COPY src/ /dest/` is the same
  contents-vs-directory ambiguity, and a frequent source of confusing builds.
- **nginx `proxy_pass`** — `proxy_pass http://backend;` vs
  `proxy_pass http://backend/;` changes whether the location prefix is stripped
  from the forwarded URI. Notorious.
- **URLs** — `/about` and `/about/` are technically different resources, which
  affects relative link resolution and canonicalisation.

---

## A Defensive Habit

Destination slashes make `cp` and `mv` fail *loudly* when the target doesn't
exist. Source slashes are the ambiguous ones. So:

> **Slash the destination, never the source** — unless you're using `rsync`,
> where you deliberately slash the source.

## Build the Intuition Yourself

Reading about this only gets you so far. Spend ten minutes in a scratch
directory:

```bash
mkdir /tmp/slashlab && cd /tmp/slashlab
```

Run each variant, then `find .` to see what actually happened. No risk of
nuking anything real.

And if you're cleaning up after the original mistake: run `ls mq-airflow` and
compare against `projects/ilearn/` **before** deleting anything.
