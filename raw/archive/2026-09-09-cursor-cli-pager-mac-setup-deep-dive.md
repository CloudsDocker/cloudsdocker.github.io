# Cursor CLI pager for Mac: learn the stack, then install it yourself

- **Published:** 2026-09-09 01:22 UTC
- **Audience:** Mac users running Cursor CLI (`agent`) in [Warp](https://www.warp.dev/), stalled on **Run this MCP tool?**
- **Repo name (recommended):** `cursor-cli-pager`
- **What this is not:** auto-approve, a Warp plugin, or Cursor IDE Settings → Notifications


Firstly, all code and configs can be found at https://github.com/CloudsDocker/cursor-cli-pager, welcoemd to fork and star.

You can treat this as a course. Read parts 1–3 to understand *why* the terminal goes silent. Follow part 4 on your Mac. Use part 5 when something is quiet. Part 6 is the interview-level deep dive.

Official references you will hit again:

- Cursor hooks: https://cursor.com/docs/hooks
- Cursor CLI: https://cursor.com/docs/cli/overview
- Cursor MCP: https://cursor.com/docs/mcp
- Warp desktop notifications: https://docs.warp.dev/terminal/more-features/notifications/
- Warp agent notifications: https://docs.warp.dev/agents/capabilities/agent-notifications/

---

## Part 1 — The problem in one screenshot

Cursor CLI in Warp is an interactive agent. When it wants an MCP tool (for example `airflow-snowflake` / `sf_describe` on `ODS.HRIS.EMPLOYEE`), it stops the loop and draws a TUI:

- **Run (once) (y)**
- **Allowlist MCP Tool (tab)**
- **Reject & propose changes (p)**
- **Skip (esc or n)**

That prompt is the product working as designed: a human gate in front of data tools. The failure mode is operational, not security. You switched to Slack. Twenty minutes later the agent is still waiting. Nothing in macOS Notification Center fired.

That is the SLO this tool targets: **page you when the gate appears**, without opening the gate for you.

### Why Warp did not already solve it

Warp has two notification products that look like one setting:

| Warp feature | What it watches | Cursor CLI MCP TUI |
| --- | --- | --- |
| Session / command notifications | Long-running commands; password-like prompts | Usually **misses**. The UI is not `Password:` on stdin. |
| Agent notifications | Warp Agent, Claude Code (plugin), Codex, OpenCode | **Not on the list.** Cursor CLI is unsupported. |

Warp banners also typically fire only when Warp is **in the background**. Another Warp tab still counts as Warp focused. Open issue pattern: https://github.com/warpdotdev/warp/issues/8439

Cursor IDE **Settings → search “notifications”** covers the desktop Agent Chat, not this Warp TUI.

So: you need a signal that is emitted **from the Cursor agent loop**, not from Warp guessing at the screen.

---

## Part 2 — Mental model (three planes)

Three systems can have an opinion. They do **not** share a database.

```text
  ┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
  │  MCP / allowlist    │     │  Cursor hooks        │     │  Terminal + macOS   │
  │  Auto-review, Tab,  │     │  ~/.cursor/hooks.json│     │  Warp OSC, NC,      │
  │  permissions.json   │     │  beforeMCPExecution  │     │  osascript, afplay  │
  └──────────┬──────────┘     └──────────┬───────────┘     └──────────┬──────────┘
             │                           │                            │
             │  shows or skips TUI       │  spawn script, JSON I/O    │  banners
             ▼                           ▼                            ▼
        Run this MCP tool?          notify-approval.py            your eyes/ears
```

1. **Allowlist plane** — decides whether the TUI appears at all.
2. **Hook plane** — Cursor spawns a process before MCP/shell. Today hooks are reliable for **deny**. Returning `{"permission":"allow"}` does **not** skip the MCP prompt. Cursor staff have said the two paths are independent:
   - https://forum.cursor.com/t/hooks-return-allow-but-mcp-tool-still-requires-manual-approval-gets-skipped/155434
   - https://forum.cursor.com/t/the-cursor-hooks-did-not-execute-as-expected/155711
3. **Notification plane** — Warp OSC 9/777, Notification Center, sounds.

**Design rule:** the pager is observe-only. It always returns `allow` so the agent is not blocked by the hook. You still press `y` / Tab / `n`.

There is **no** `approvalPromptShown` event. The closest events are:

- `beforeMCPExecution` — about to call an MCP tool (TUI usually appears if not allowlisted)
- `beforeShellExecution` — about to run a shell command (same idea)
- `stop` — turn ended; that is “maybe finished,” not “blocked on y”

Claude Code is different (`Notification` / `PermissionRequest`). That is why Warp’s Claude plugin can do Request alerts and why multi-agent notifiers often only wire Cursor to `stop`.

**Approximation:** `beforeMCPExecution` also fires for tools that already run without a prompt. Extra banners are possible. Filter in the script if that happens; do not “fix” it by auto-allowlisting production data tools.

---

## Part 3 — What the tool actually does

`hooks/notify-approval.py` is a user-level Cursor hook:

1. Reads one JSON object from **stdin** (Cursor’s payload).
2. Builds a short title/body (`airflow-snowflake: sf_describe`). It does **not** put `tool_input` (table names, SQL, tokens) into the banner.
3. Tries **OSC 777** on `/dev/tty` so Warp can raise a desktop notify if it sees the escape sequence on the PTY.
4. On Darwin: `osascript` `display notification` + `afplay` Glass (sound still works if Warp is focused).
5. Writes **only** this to **stdout**:

```json
{"permission": "allow"}
```

Stdout is a protocol. Debug prints, log lines, or OSC on stdout can break the hook. OSC belongs on the TTY or stderr.

Install layout (user hooks run with cwd `~/.cursor/`):

```text
~/.cursor/hooks.json
~/.cursor/hooks/notify-approval.py
```

`install.sh` copies the script and **merges** the two events into existing `hooks.json` (it will not wipe other hooks).

---

## Part 4 — Setup on your Mac (do this in order)

### 4.1 Prerequisites

- macOS (Notification Center + `osascript` + `afplay`)
- [Cursor CLI](https://cursor.com/docs/cli/overview) — `curl https://cursor.com/install -fsS | bash` then `agent`
- Python 3 (`python3 --version`)
- Warp recommended; the hook still pings Notification Center in Terminal/iTerm

Confirm CLI:

```bash
which agent
agent --version
python3 --version
```

### 4.2 macOS notification permission

1. **System Settings → Notifications → Warp** — Banners or Alerts, sounds on.
2. After the first test, if macOS asks, allow **Script Editor** (or the process attributed to `osascript`).
3. Turn **Focus / Do Not Disturb** off while you validate.

### 4.3 Warp settings (still useful, not sufficient)

1. Warp → Settings → Features → **Session** → desktop notifications on.
2. Settings → Features → **Notifications** → long commands + password/input prompts on.
3. For Warp’s own banners: leave Warp in the **background** (another app focused).

This catches `sleep 30`. It will not reliably catch **Run this MCP tool?**.

### 4.4 Get the files

If you published GitHub as `cursor-cli-pager`:

```bash
cd ~/ws   # or anywhere you keep clones
git clone git@github.com:YOURUSER/cursor-cli-pager.git
cd cursor-cli-pager
```

If you only have this tree locally, `cd` into the directory that contains `install.sh` and `LICENSE`.

### 4.5 Install the hook

```bash
chmod +x install.sh hooks/notify-approval.py
./install.sh
```

You should see `Updated /Users/YOU/.cursor/hooks.json`.

Inspect:

```bash
cat ~/.cursor/hooks.json
ls -l ~/.cursor/hooks/notify-approval.py
```

Expected events:

```json
{
  "version": 1,
  "hooks": {
    "beforeMCPExecution": [
      { "command": "./hooks/notify-approval.py" }
    ],
    "beforeShellExecution": [
      { "command": "./hooks/notify-approval.py" }
    ]
  }
}
```

If you already had other hooks, they should still be listed. The installer appends only if that exact `command` is missing.

**Manual install** (if you do not want `install.sh`):

```bash
mkdir -p ~/.cursor/hooks
cp hooks/notify-approval.py ~/.cursor/hooks/notify-approval.py
chmod +x ~/.cursor/hooks/notify-approval.py
```

Then edit `~/.cursor/hooks.json` to add the two events above. Merge by hand if the file already exists.

### 4.6 Restart Cursor CLI

Quit `agent` fully (not just a new prompt). Start it again in Warp so it reloads `hooks.json`.

Cursor often reloads hooks on save; a restart is the reliable path.

### 4.7 Dry-run (no MCP server required)

```bash
python3 ~/.cursor/hooks/notify-approval.py <<'EOF'
{"hook_event_name":"beforeMCPExecution","mcp_server_name":"airflow-snowflake","tool_name":"sf_describe"}
EOF
```

**Pass criteria:**

- The last line of stdout is exactly `{"permission": "allow"}`
- Glass plays
- Notification Center shows **Cursor MCP approval** / `airflow-snowflake: sf_describe`

If stdout is mixed with `]777;notify;...`, you are on an old script that wrote OSC to the wrong stream. Replace with the current `hooks/notify-approval.py`.

### 4.8 Live-run (the real TUI)

1. In Warp: `agent`
2. Ask for work that needs an MCP tool that is **not** allowlisted.
3. Switch to Safari or Slack **before** the prompt appears if you want a Warp banner as well as `osascript`.
4. When Warp shows **Run this MCP tool?**, you should already have a Mac ping.
5. Return to Warp:
   - `y` — this call only
   - **Tab** — allowlist that tool for the session (fewer future stalls)
   - `n` / esc — skip
   - `p` — reject and propose changes

You still own the click. The tool only bought you latency.

### 4.9 Optional: unit tests in the clone

```bash
python3 -m unittest discover -s tests -v
```

This asserts the process stdout is parseable hook JSON.

---

## Part 5 — Troubleshooting

| What you see | What to check |
| --- | --- |
| Silent stall, no banner, no sound | `~/.cursor/hooks.json` events; script path `./hooks/notify-approval.py`; restart `agent`; Focus mode; osascript permission |
| Sound but no banner | Notification Center attribution (Script Editor vs Warp); banners disabled; Focus |
| Banner on every MCP call | Tools already allowlisted; `beforeMCPExecution` is “about to call,” not “prompt shown.” Filter `mcp_server_name` in the script if needed |
| Agent cannot run tools / hook errors | Extra stdout; `failClosed`; exit code 2 (deny). This script must exit 0 and print only allow JSON |
| Warp banner never, Mac banner yes | OSC did not hit the PTY (hook has no TTY). Expected; osascript is primary |
| Duplicate pings | Also running `cursor-notify`, `agent-notify`, `cursor-attention-beep` |
| `command not found` in hook logs | User hooks cwd is `~/.cursor/`. Do not point `command` at a path that only exists in the git clone |

Uninstall:

```bash
# Remove the two "./hooks/notify-approval.py" entries from ~/.cursor/hooks.json
rm -f ~/.cursor/hooks/notify-approval.py
```

Then restart `agent`.

---

## Part 6 — Deep dive (how to explain this in an interview)

### 6.1 MCP is just tools; the TUI is Cursor policy

[MCP](https://modelcontextprotocol.io/) is JSON-RPC tools a client may call. Cursor’s **client** adds per-call approval after incidents in the MCP/Cursor ecosystem (allowlist, Auto-review, classifier). The pager does not implement MCP. It rides Cursor’s **before-call** hook.

Putting table names in a banner would leak workspace context into Notification Center (lock screen, Apple Watch, screen sharing). The script only shows **server + tool**.

### 6.2 Hook protocol

Cursor:

1. Fork/exec `command` from `hooks.json`
2. Write payload to stdin, close stdin
3. Read stdout as JSON
4. Apply `permission` (deny is real; allow does not override MCP TUI today)
5. Fail-open on crash unless `failClosed: true`

User vs project:

| File | Cwd when command runs | Scope |
| --- | --- | --- |
| `~/.cursor/hooks.json` | `~/.cursor/` | All local agent sessions |
| `.cursor/hooks.json` in a repo | project root | That workspace; cloud agents can pick this up |

Cloud agents do **not** see `~/.cursor/` on your laptop. This pager is for **your Mac CLI**, not a remote VM.

Exit code `2` = deny (Claude-compatible). Never use that for a pager.

### 6.3 Why `/dev/tty` and not stdout for OSC

[Warp documents OSC 9 and OSC 777](https://docs.warp.dev/terminal/more-features/notifications/):

```text
OSC 777:  ESC ] 777 ; notify ; <title> ; <body> BEL
```

The hook is a **child process**. Its stdout is a pipe to Cursor, not Warp’s parser. Writing OSC to stdout corrupts the permission JSON. Writing to `/dev/tty` is an attempt to reach the same PTY Warp is rendering. If Cursor sandboxes the hook without a TTY, OSC is dropped; `osascript` still runs.

`afplay` covers Warp-in-foreground: you hear Glass even when macOS suppresses banners for the focused app.

### 6.4 Why `stop` hooks are the wrong primary signal

`stop` means the agent loop ended a turn. Causes include: finished the task, hit an error, or you interrupted. A process blocked on **Run this MCP tool?** has **not** stopped. Notifiers that only install Cursor `stop` (several popular `agent-notify` builds) will stay quiet during the stall that motivated this tool.

### 6.5 Make vs buy

| If you… | Use |
| --- | --- |
| Run Claude Code in Warp | Warp’s Claude notification plugin, not this |
| Want “agent finished” for many CLIs | https://github.com/collindjohnson/agent-notify |
| Want a beep on turn-end; MCP optional | https://github.com/aRealGem/cursor-attention-beep |
| Want a paid click-to-focus menu bar | https://www.aidonenow.com/cursor-agent-notifications or https://www.agentnotch.app/ |
| Run Cursor CLI in Warp on MCP/shell `y` | This pager |

Feature request that this hacks around: https://forum.cursor.com/t/notification-when-a-cli-agent-needs-input/152166

### 6.6 What not to build

- Scraping the Warp pane for the string `Run this MCP tool?` as the main design (brittle, privacy-hostile).
- Returning hook `ask` and expecting Cursor to honor it today.
- Putting `tool_input` in the notification body.
- Allowlisting `sf_describe` against HRIS tables to “fix” notifications. That is a permission change. Page first; allowlist only tools you would run with your eyes closed.

---

## Part 7 — Copy-paste reference

### Payload Cursor sends (shape)

```json
{
  "hook_event_name": "beforeMCPExecution",
  "mcp_server_name": "airflow-snowflake",
  "tool_name": "sf_describe",
  "tool_input": "{\"table\":\"ODS.HRIS.EMPLOYEE\"}"
}
```

Shell events use `command` and `cwd` instead of MCP fields.

### Keys on the TUI

| Key | Meaning |
| --- | --- |
| `y` | Run once |
| Tab | Allowlist MCP tool (session) |
| `p` | Reject and propose |
| `n` / esc | Skip |

### One-command re-test after macOS updates

```bash
python3 ~/.cursor/hooks/notify-approval.py <<< '{"hook_event_name":"beforeMCPExecution","mcp_server_name":"demo","tool_name":"ping"}'
```

---

## Changelog for this article

| Timestamp (UTC) | Note |
| --- | --- |
| 2026-09-09 01:22 | First public-length guide: learn path + Mac setup + protocol deep dive |

MIT-licensed companion code lives in this repository (`LICENSE`, `hooks/notify-approval.py`, `install.sh`).

