---
title: Your CLI Tool Can't Hide Your Craft
header:
    image: /assets/images/Python-expert-write-code-like-this.jpg
date: 2026-09-01
tags:
 - python
 - cli
 - developer-tools
 - terminal-ui
permalink: /blogs/tech/en/cli-is-a-product-not-a-script
layout: single
category: tech
---

> Between the joints there is space, and the edge of the blade has no thickness. If you insert what has no thickness into an empty space, there is certainly plenty of room for the blade to move.
> — Zhuangzi, "Cook Ding Carves an Ox"

# Your CLI Tool Can't Hide Your Craft

*A `Panel(dict)` crash, a 2,400-year-old butcher, and the real argument for restraint in developer tools*

You've probably seen a crash that looks something like this:

```
Errors found Unable to render {'topic': ..., 'titles': [...]};
A str, Segment or object with __rich_console__ method is required
```

The code behind it is a thirty-second fix:

```python
# the crash
console.print(Panel(data, title=f"Title for {selected_file}"))
# data is a dict: {'topic': ..., 'titles': [...]}
```

Most people patch it and move on — wrap it in `try/except`, `str()` the thing, ship it. It's an internal tool. Nobody outside the team ever sees it.

That's exactly the assumption this post wants to push back on: **the polish of your internal tooling is the one piece of evidence for your professionalism that doesn't require a client to take your word for it.** You can put "senior engineer, ten years" on a proposal. But the first time someone watches you run a CLI you wrote for yourself — a bare dict dumped into a stack trace, versus a tool that clearly knows when to ask a question and when not to — the judgment has already happened.

This post is ordered for teaching, not for the order I hit each thing. By the end you'll have three concrete takeaways:

- What Rich's actual rendering contract is, and why "printing" and "rendering" are not the same operation.
- A genuinely underdocumented `InquirerPy` styling flag: `style_override=False`.
- A concrete test for "does this moment deserve a confirmation prompt," instead of the reflex answer of "add more confirmations, just in case."

## 1. The rendering contract: `Panel` isn't bad at guessing dicts — it never tried to

`rich.Panel` (and most Rich containers) accepts exactly three kinds of input: a string, a `Segment`, or an object implementing `__rich_console__`. A raw `dict` is none of those, so it refuses to render instead of guessing at what you meant.

| The common take | The senior engineer's read |
|---|---|
| "`console.print` should just handle whatever I throw at it — the library's being uptight" | "The render layer's contract is about *what it accepts*, not *what you gave it* — a library that guesses generously is the actually dangerous design" |
| "Wrap it in `try/except` and move on" | "`except` solves 'the program didn't crash.' It doesn't solve 'the user understood what happened.' The crash is often the only moment the tool tells you, unprompted, that you never actually looked at this data" |

The fix pulls the field you actually want to display (the `titles` list) out of the dict and turns it into a string:

```python
titles = data.get("titles", []) if isinstance(data, dict) else data
titles_text = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))
console.print(Panel(titles_text, title=f"Title for {selected_file}"))
```

> The crash isn't the tool failing. It's the tool telling you that you've been *printing* this data, not *rendering* it.

## 2. From printing to interface: a table that actually says something

Once the crash is gone, the real problem shows up: five candidate titles crammed into a wall of text, and the user has to count line breaks to pick one. Upgrading to a color-grouped table costs under ten lines:

```python
TITLE_PALETTE = ["cyan", "magenta", "green", "yellow", "bright_blue"]

table = Table(
    title="✨ Generated Title Options ✨",
    box=box.ROUNDED,
    show_lines=True,
    title_style="bold white on dark_magenta",
)
table.add_column("#", style="bold white", justify="center", width=3)
table.add_column("Title", style="bold")
for i, t in enumerate(titles):
    color = TITLE_PALETTE[i % len(TITLE_PALETTE)]
    table.add_row(f"[{color}]{i + 1}[/{color}]", f"[{color}]{t}[/{color}]")
console.print(table)
```

The color isn't decoration — it's a grouping signal. Each row gets one color, so your eye locks onto a whole row without re-counting index numbers. This is the actual pitch of `rich`: it turns "the terminal only outputs characters" from a constraint into a canvas you can design against.

## 3. `get_style(..., style_override=False)`: borrow the defaults' light, don't rip out the fixture

`InquirerPy`'s styling system has a flag almost no example in the docs bothers to explain, and getting it wrong makes you think you have to reinvent an entire color scheme from scratch:

```python
TITLE_PICKER_STYLE = get_style(
    {
        "questionmark": "#f5a742 bold",
        "pointer": "#f542a7 bold",
        "answer": "#42c5f5 bold",
    },
    style_override=False,
)
```

| `style_override=True` (what most sample code does) | `style_override=False` (what this uses) |
|---|---|
| Every field you didn't set — `instruction`, `checkbox`, `separator`, all of it — collapses to an empty string. The style resets to nothing | Every field you didn't set keeps `InquirerPy`'s tuned default palette (`#61afef`, `#98c379`, and so on) |
| You have to hand-write a dozen-plus fields or the UI looks visibly unfinished | You override the three or four fields you actually care about and let the library's default taste handle the rest |

It's the same instinct as writing CSS that only overrides the properties you care about instead of resetting the whole cascade — except the flag's name is exactly backwards from its behavior: `False` is the setting that means "don't override."

## 4. `console.status()` around a real `await`: turning uncertainty into visible uncertainty

While the tool waits on a real network call — here, waiting on Gemini to generate title candidates — the two most common patterns are both bad: the terminal freezes and the user can't tell if it's hung or working, or you print "Processing..." once and it never updates again.

`Console.status()` used as a context manager runs a spinner for exactly the span of a real `await`:

```python
with console.status("[bold cyan]Asking Gemini for title ideas...[/bold cyan]", spinner="dots"):
    result = await mcp_client.call_tool("suggest_N_titles", {...})
```

The detail that trips people up: calling `status()` on its own displays nothing. It returns a `Status` object, and only entering it as a `with` block (or calling `.start()` manually) actually kicks off the background-refreshing spinner. That was a real, hidden bug in an earlier version of this same code: `console.status("fetching raw files....")` was called bare, never inside a `with`, so that status line never actually rendered — it just sat there as dead code that looked correct at a glance.

## 5. Cook Ding's ox: confirmation prompts belong only at the actual joints

The Zhuangzi quote at the top is usually flattened to "practice makes perfect," but the more useful half of the story is the part that gets cut: Cook Ding's blade stays sharp for nineteen years not because he moves fast, but because he follows the natural structure of the animal and only cuts where a joint already has space — never forcing the blade through bone.

A confirmation prompt is that blade. Add too many, and users develop the reflex of mashing Enter through a wall of "are you sure?" — which means the one prompt that actually mattered gets clicked through too. That's the same failure mode as crying wolf. Add too few, and one misclick moves the wrong file into an archive folder. The fix isn't "add one more safety net" — it's finding the actual joint:

```python
publish_languages = await inquirer.checkbox(
    message="🌐 Publish which language version(s)?",
    choices=[Choice("zh", ...), Choice("en", ...)],
).execute_async()

confirmed = await inquirer.confirm(
    message=f"Publish {selected_file} as {'/'.join(publish_languages)} with this title?",
    default=False,   # the point: declining isn't opt-out, it's the default
).execute_async()
```

| What gets a confirmation here | Why |
|---|---|
| Publish: two real Gemini calls (real cost), files written into a separate repo, the source note moved into `archive/` | Irreversible or genuinely costly, and nothing earlier in the flow (picking a title, picking languages) already made that consequence visible |
| The language checkbox itself, every keystroke in the title fuzzy search | Reversible, free, changeable at any moment — a confirmation there is pure friction |

`default=False` is a deliberate choice too: this action spends money and moves files, so hitting Enter without thinking shouldn't read as consent.

## Pulling it together: five decisions, five kinds of user cost

| Decision | What it protects against |
|---|---|
| `Panel` takes a string, not a dict | Readability cost — can the user parse the output at all |
| Color-grouped `Table` | Scanning cost — does the user have to count to pick the right item |
| `style_override=False` | Your own build cost — you're not reinventing a palette from scratch |
| `console.status()` | Waiting-uncertainty cost — does the user know the tool is still alive |
| `checkbox` + `confirm(default=False)` | Decision cost + irreversibility cost — friction only where it earns its keep |

## Do this today

1. Grep one of your own recent internal scripts for a bare `print(some_dict)` or `except Exception as e: print(e)` — those are the spots where a crash is doing your explaining for you.
2. Count every `confirm()` / `input("are you sure?")` in a tool you maintain. If it's more than three, odds are half of them are friction, not protection — try deleting the ones guarding reversible, free actions.
3. Take a script you run more than ten times and add a `console.status()` or equivalent progress indicator. The ten minutes pays for itself by your eleventh run.

*A blade stays sharp for nineteen years not because it's fast, but because it only cuts where there's already room. Your CLI tools are no different — restraint is the highest form of polish.*
