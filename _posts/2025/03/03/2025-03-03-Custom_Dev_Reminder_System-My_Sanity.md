---
header:
    image: /assets/images/GoogleMap_missing_JPN.jpg
title:  Custom Dev Reminder System My Sanity
date: 2025-03-03
tags:
    - tech
permalink: /blogs/tech/en/Custom-Dev-Reminder-System-My-Sanity
layout: single
category: tech
---
> If you tell the truth, you don't have to remember anything. - Mark Twain

# Taming the Chaos: How I Created a Custom Dev Reminder System That Saved My Sanity

We've all been there: deep in a coding flow state when suddenly you remember that PR you were supposed to check two hours ago. Your heart sinks as you realize you've completely forgotten to review those critical changes that are blocking your team.

After this happened to me one too many times, I decided to create a simple yet effective reminder system that has revolutionized my workflow. Today, I want to share this little productivity hack that combines terminal commands and macOS scripting to create a dual-notification system that's nearly impossible to ignore.

## The Problem with Existing Solutions

Before diving into my solution, let's talk about why existing reminder apps weren't cutting it for me. Calendar notifications are great for meetings, but too heavy for quick development tasks. Slack reminders get lost in the noise of other messages. And browser notifications? Those are the first things I instinctively dismiss when I'm in the zone.

I needed something that would:
1. Break through my focus tunnel without requiring context switching
2. Create both auditory and visual interruptions
3. Be dead simple to set up on the fly
4. Not require installing yet another app

## The Solution: A Bash One-Liner

Here's the elegant little command that has saved me countless hours of context-switching and follow-up headaches:

```bash
(sleep 2 && say "Reminder to check build status of PR 4285") &
(sleep 2 && osascript -e 'display dialog "Reminder to check build status of PR 4285" buttons {"OK"} default button "OK" with title "PR Reminder"') &
```

Let's break down why this works so beautifully:

### The Dual-Sensory Approach

The command creates two parallel processes (note the `&` at the end of each line):

1. An audio reminder using macOS's text-to-speech engine
2. A visual pop-up dialog that stays on screen until dismissed

This dual-sensory approach makes it nearly impossible to miss the reminder, even when I'm deeply focused or have stepped away from my desk momentarily.

### Technical Breakdown

The first part uses the `sleep` command to wait 2 seconds before triggering the `say` command, which uses macOS's built-in text-to-speech:

```bash
(sleep 2 && say "Reminder to check build status of PR 4285") &
```

The second part also waits 2 seconds, then uses `osascript` to execute an AppleScript snippet that creates a dialog box:

```bash
(sleep 2 && osascript -e 'display dialog "Reminder to check build status of PR 4285" buttons {"OK"} default button "OK" with title "PR Reminder"') &
```

The `&` at the end of each line makes these processes run in the background, allowing you to continue using your terminal.

## Taking It To The Next Level

After using this basic version for a while, I created some enhancements that have made it even more powerful:

### Creating A Simple Function

I added this function to my `.zshrc` file (works with `.bashrc` too):

```bash
remind() {
  local delay=${1:-2}
  local message="${@:2}"
  (sleep $delay && say "$message") &
  (sleep $delay && osascript -e "display dialog \"$message\" buttons {\"OK\"} default button \"OK\" with title \"Reminder\"") &
  echo "Reminder set for: $message (in $delay seconds)"
}
```

Now I can simply type `remind 60 "Check PR 4285 build status"` to get a reminder in one minute.

### Making It Smarter with Context

I eventually extended this to pull in context from our issue tracker using a simple API call:

```bash
prremind() {
  local pr_number=$1
  local delay=${2:-300}
  
  # Get PR title from GitHub API (requires gh CLI tool to be authenticated)
  local pr_title=$(gh pr view $pr_number --json title -q .title)
  
  # Create the reminder message
  local message="Check PR #$pr_number: $pr_title"
  
  # Set the reminder
  (sleep $delay && say "$message") &
  (sleep $delay && osascript -e "display dialog \"$message\" buttons {\"OK\"} default button \"OK\" with title \"PR Reminder\"") &
  
  echo "Reminder set for PR #$pr_number in $(($delay / 60)) minutes"
}
```

## The Impact on My Workflow

Since implementing this system, I've noticed several significant improvements:

1. **Fewer dropped balls**: Critical checks don't slip through the cracks anymore
2. **Reduced anxiety**: I don't have that constant nagging feeling that I'm forgetting something
3. **Better focus**: I can fully immerse myself in deep work, knowing my reminder system has my back
4. **Improved team trust**: My colleagues know that when I say "I'll check that PR in an hour," I actually will

## Why This Matters

In our interrupt-driven development culture, tools that help us manage our attention are invaluable. This simple script has become a critical part of my attention management system.

What I love most about this approach is that it uses built-in system tools rather than requiring yet another app or service. It's lightweight, reliable, and surprisingly effective.

## Try It Yourself

The beauty of this solution is its simplicity. Copy the commands, adapt them to your needs, and see if they make a difference in your workflow. If you're not on macOS, similar approaches can be implemented on Linux using `notify-send` or on Windows with PowerShell's `New-BurntToastNotification`.

What simple productivity hacks have you created that made a significant difference in your workflow? I'd love to hear about them in the comments.

Happy coding (and reminding)!

--HTH--