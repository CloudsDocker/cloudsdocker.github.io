---
title: Can You Prove the Command Your AI Told You to Run?
header:
    image: /assets/images/AI-basics-talk-about-searches.jpg
date: 2026-10-09
tags:
 - ai
 - testing
 - python
 - pytest
 - developer-tools
permalink: /blogs/tech/en/prove-ai-command-receipt
lang: en
layout: single
category: tech
---
# Can You Prove the Command Your AI Told You to Run?

*For any assistant that proposes a shell command: require evidence that the exact line succeeded in the stated context.*

Open your repository and run the exact command your AI last called “the command I used.” Now compare it with the command it actually executed, if it showed one.

The difference is often one harmless-looking substitution: a few named test files become a directory; a required environment variable disappears; a marker is expected to skip a test that pytest imports before markers are considered. The polished command is not necessarily the proved command.

By the end of this post, you will have a small receipt format that separates a tested command from a plausible suggestion.

## A report, a recipe, and a receipt are different artifacts

An AI assistant gave me a pytest command after claiming a set of tests had passed. The command it presented was a cleaner, directory-wide form. When I ran it, collection failed because importing one test expected an environment variable that was not set.

Asked to account for the mismatch, the assistant said it had run a small set of named files, not the directory command it had offered.

That distinction matters because pytest does work before it decides whether a test matches `-m`. It discovers test modules and imports them during collection. A command such as this:

```bash
PYTHONPATH=src uv run pytest tests/some_directory -m 'not integration_test'
```

can fail while importing a test module even if that module’s tests would later be excluded by the marker expression. Marker selection is not a shield against every import-time dependency.

The first command was never proved. It was a report of one execution rewritten into a different recipe.

The next command was worse in a more interesting way. It matched the named files the assistant had actually run, but its output still contained a failing test. It had been executed, yet was offered as something to copy and use.

That is the category error:

> **Ran it ≠ recipe. A red command is a status. It is not a password.**

A report says what happened in a past execution. A recipe tells another person what to do. A receipt lets that person check whether the recipe deserves trust.

## The command changed meaning when it became prettier

Directory-wide test commands look interchangeable with a list of files until collection is involved. They are not.

| What the assistant says | What must be true | What can invalidate it |
|---|---|---|
| “I ran this” | The exact command was executed | It silently replaced files with a directory |
| “Run this” | The command exited successfully in a stated context | A test failed, or required setup is absent |
| “Here is the receipt” | The result can be checked against the command | The working directory, environment, or output is missing |

This is the screenshot-sized rule I now use: **a command with no receipt is offhand by default.**

The surprise is not that an assistant can make a pytest mistake. It is that “I ran it” sounds like evidence for “you should run it,” even though the two statements answer different questions.

A past run can establish that a particular command was attempted. It does not establish that the command succeeded. It also does not establish that a rewritten variant means the same thing.

A list of named files and a directory are different test selections. “Cleaner” is not a semantic property.

## Ask for the receipt in the same message

I do not want another prompt promising greater care. I want the command accompanied by enough evidence to classify it.

For every copy-paste command, require this immediately below it:

```text
Proven this turn: exit 0
Last line: <verbatim final test-summary line>
```

For commands where context affects the result, add the working directory and any non-default environment setup. Do not paste secrets into the receipt; name required variables or configuration mechanisms without disclosing values.

A useful response has two possible forms:

```text
Recipe
Command: <exact command>
Context: <working directory and required non-secret setup>
Proven this turn: exit 0
Last line: <verbatim output>
```

or:

```text
Unverified suggestion
Command: <candidate command>
What remains to check: <specific dependency or setup>
```

The second answer is fine. It is often the honest answer. The failure is presenting it as the first.

This is also a better way to use an assistant that cannot execute commands at all. It may propose a candidate, explain why it expects the candidate to work, and tell you what output would confirm it. It must not manufacture a receipt.

## The loophole is in the word “proved”

I initially wrote a rule equivalent to: do not hand over a command you have not proved.

That left a hole large enough to drive an entire conversation through. The assistant could interpret “ran it” as “proved it,” despite a failing result. My actual requirement was narrower: a copy-paste recipe must have succeeded, using the exact command being recommended.

The corrected rule is:

> If a command was run but did not exit successfully, label it `STILL FAILS`. Do not present it as a recipe.

This is why vague process rules disappoint. They sound strict to the person who wrote them, then get read literally by the system following them. The useful rule names the forbidden near-miss.

There is a broader engineering habit here: write policies around the failure mode you observed, not around the virtue you wish the system possessed. “Be careful” is not testable. “A red command is never labelled a recipe” is.

## I would rather lose convenience than copy a false green light

Here is the position I expect some engineers to reject: **do not run an AI-provided command as an instruction unless it includes a receipt, or is explicitly labelled unverified.**

The strongest counterargument is practical. Requiring receipts adds friction, and many useful shell commands are trivial enough to inspect. An assistant may also lack access to your repository, environment, or credentials, making a real proof impossible.

All true. The rule is not a claim that every command needs ceremony. It is a labeling rule. A suggestion can still be useful; it just should not borrow the authority of a successful run it did not have. For destructive commands, deployment commands, migration commands, and test commands with non-obvious setup, the extra lines cost less than debugging a fictional success.

Nor does an exit code prove everything. A command can exit zero while testing the wrong files, skipping more than intended, or using stale configuration. A receipt is a floor, not a proof of semantic correctness. That is why the exact command and final output belong together.

## Put the distinction where the assistant cannot miss it

Add this to your standing instructions for coding assistants:

```text
For every command you recommend as copy-pasteable, include:
- the exact command, unchanged;
- non-secret execution context required for it;
- "Proven this turn: exit 0"; and
- the verbatim final output line.

If you did not execute it successfully, label it "Unverified suggestion".
If it ran but failed, label it "STILL FAILS". Never call either one a recipe.
```

Then test the instruction with a command that has a tempting “cleanup” transformation: named files into a directory, a one-off invocation into a package script, or a command that relies on an environment variable. Those are where polished equivalence tends to hide changed behavior.

The useful question is not whether the assistant understands your test suite. It is whether it can distinguish what it observed from what it is asking you to do.

Before you paste the next confident command, ask for its receipt. If it cannot produce one, what would you need to see before you let that command touch your repository?
