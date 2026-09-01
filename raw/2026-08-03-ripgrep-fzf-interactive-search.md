---
title: "From `rg | head` to an Interactive Search Cockpit: ripgrep + fzf Done Right"
date: 2026-08-03
categories: [engineering, shell, developer-tools]
tags: [ripgrep, fzf, cli, zsh, neovim, gitops]
---

Most of us start a search the same way: type a `grep`-shaped command, pipe it into `head` to stop it flooding the terminal, and then squint at the truncated output trying to reconstruct where each match actually lives. It works — until it doesn't. The moment the answer sits at line 81, you're back to editing the command and running it again.

This post walks up a ladder. We start from a real command a colleague ran to audit a fleet of ArgoCD apps, unpack why it's fragile, and end with an interactive search function you can drop into your `.zshrc` that turns "grep and squint" into "filter, preview, jump."

## Part 1: What this command actually does

Here's the starting point — a GitOps audit query:

```bash
rg -n "targetRevision|kubernetes/prod|kubernetes/dev|path:" dit-gitops-mqu/apps --glob '*.yaml' | head -80
```

In one sentence: it scans every `.yaml` file under `dit-gitops-mqu/apps` for lines containing any of four keywords — `targetRevision`, `kubernetes/prod`, `kubernetes/dev`, or `path:` — prints them with line numbers, and shows only the first 80 results.

The intent is a classic review task: *"Which ArgoCD apps track which branch (`targetRevision`), point at which environment (prod/dev), and what `path` are they wired to — without opening every file by hand."*

Piece by piece:

- `rg -n "A|B|C|D"` — ripgrep's regex OR; a line matching **any** of the four keywords gets printed. `-n` attaches line numbers so you can jump back to the source.
- `dit-gitops-mqu/apps` — scopes the search to one directory instead of the whole repo.
- `--glob '*.yaml'` — restricts matching to YAML files, filtering out `.md`, `.sh`, and other noise.
- `| head -80` — caps the output so it doesn't flood your screen. Convenient — but also the seed of the problem we fix later.

## Part 2: The ripgrep tricks most people never reach for

`rg` beats `grep` on three defaults: it recurses automatically, it respects your `.gitignore` automatically, and it's multi-threaded automatically. Same lazy one-liner, 5–10× faster, and it won't drag `node_modules` or `.git` into your results.

Assuming you already know the basics, here are the moves that pay off daily:

**1. Filter by file type with `-t` / `-T` instead of hand-rolling globs**

```bash
rg -t yaml "targetRevision"
```

`rg --type-list` shows every built-in type — yaml, py, go, ts, and dozens more are pre-defined, so you rarely need a raw glob pattern.

**2. Show context with `-A` / `-B` / `-C`**

```bash
rg -n -B2 -A2 "targetRevision"
```

A bare matching line often isn't enough — you can't tell *which app's* `targetRevision` you're looking at. `-C3` pulls three lines on either side, far faster than re-`cat`-ing the file.

**3. Extract just the match with `-o`**

```bash
rg -o "kubernetes/(prod|dev)"
```

Pair it with `sort | uniq -c` and you get a count of prod vs. dev occurrences — no manual tallying.

**4. Structured output with `--json`**

```bash
rg --json "targetRevision" | jq '.data.lines.text'
```

For an audit like ours, `--json` is a natural fit: you're probably about to batch-process, count, or feed results into a script rather than read them line by line with your eyes.

**5. Just the filenames (`-l`) or just the counts (`-c`)**

```bash
rg -l "targetRevision" dit-gitops-mqu/apps    # which files matched
rg -c "targetRevision" dit-gitops-mqu/apps    # how many matches per file
```

Use `-l` / `-c` to map the terrain first, then decide what to expand. Breadth before depth — the standard shape of any audit task, and the exact opposite of leading with `head -80` and brute-forcing it.

**6. Full-power regex with `-P` (PCRE2)**

```bash
rg -P "(?<=path:\s).*prod.*"
```

When you need lookahead/lookbehind, `-P` switches to the PCRE2 engine (rg's default engine is faster but less featureful). No need to reach for a different tool.

## Part 3: Wiring `rg` into `fzf` for interactive search

Here's the payoff. Treat `rg` as the **data source** and `fzf` as the **interaction layer**:

```bash
rg --line-number --no-heading "pattern" \
  | fzf --delimiter : --preview 'bat --color=always {1} --highlight-line {2}'
```

Now you're not waiting for `head -80` to truncate and guessing — you filter matches live, preview file contents as you move, and can jump straight into your editor on the selected line. This is essentially what Telescope / fzf-lua do inside Neovim, except it works in a bare terminal too.

Why each layer is configured the way it is:

**`--no-heading` is the critical switch.** By default `rg` groups by file and prints the filename on its own line without a colon — which means `fzf` can't split columns on `:`. `--no-heading` flattens every result into `file:line:content`, which `fzf` can parse.

**`--delimiter :` — and a warning about `--with-nth`.** It's tempting to use `fzf --with-nth` to hide the filename and line-number columns and show only the content. Don't. `--with-nth` strips those columns at the *selection* stage, so you're staring at a line of code with no idea which file or line it came from. The right move: let `--delimiter` govern *how columns are split* for the `--preview` command, but **don't strip columns from the display** — you still see the full `file:line:content` while picking, and the preview pane handles the surrounding context separately.

**The jump-to-editor finish:**

```bash
rg --line-number --no-heading "pattern" \
  | fzf --delimiter : --preview 'bat --color=always {1} --highlight-line {2}' \
  | awk -F: '{print $1" +"$2}' \
  | xargs -o nvim
```

That last step uses `awk -F:` rather than `cut` on purpose: `awk` leaves room to add logic later (say, a condition to skip certain files), whereas `cut` is a fixed field extractor with no room to grow.

**Package it as a `rgf` function in your `.zshrc`:**

```bash
rgf() {
  rg --line-number --no-heading "$1" ${2:-.} \
    | fzf --delimiter : \
          --preview 'bat --color=always {1} --highlight-line {2}' \
          --preview-window '~3' \
    | awk -F: '{print $1" +"$2}' \
    | xargs -ro nvim
}
```

Usage is just `rgf targetRevision dit-gitops-mqu/apps`. No more hand-stitching `rg | head` and counting line numbers by eye to jump into a file.

## Takeaway

The arc here is the same arc for most CLI craftsmanship: a quick-and-dirty command gets the job *started*, but the friction it leaves behind — truncation, no context, no jump — is exactly what a small amount of composition removes. `rg` gives you fast, precise, scriptable matches; `fzf` gives you a cockpit to fly them. Twelve lines in your `.zshrc` and "grep and squint" becomes "filter, preview, jump."
