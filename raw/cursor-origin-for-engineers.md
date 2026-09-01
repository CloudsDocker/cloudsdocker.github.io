# GitHub is still the source of truth. That is the product.

*Cursor Origin looks like a new git host. The interesting move is that it refused to become one.*

The first thing a new forge usually asks a team to do is migrate. Open a ticket. Pick a cutover weekend. Get the CTO to sign a document that says the old remote is no longer canonical.

Cursor Origin, in early beta, asks for a click instead: **Sync from GitHub**.

That is not shyness. It is the design. Origin’s public stance is that it is not a GitHub replacement. A synced repository stays live. You can browse it, search it, and pull it. **Push still goes to GitHub. GitHub remains the source of truth.** Origin grows beside that process rather than ripping it out.

Most of the rest of the product only makes sense after you accept that sentence. This post is the version I would send to engineers who already know git, already have a GitHub org, and are trying to decide whether “one click” is as small as it sounds.

---

## Three names, one layer

Keep these separate or the conversation collapses.

| Name | What it is |
|---|---|
| `origin` remote | A local convention. It can point at GitHub or at Cursor. |
| Cursor Origin | A **git forge**: the service around git — storage, permissions, checks, merge. Hosted at `origin.cursor.com`, rendered at `cursor.com/codebase`. |
| `origin` CLI | A binary for terminal workflows on that forge. Not the Agent CLI (`agent`). Not a new VCS. |

`git` moves bytes. A forge decides who may see them, which checks must pass, and what merge means. GitHub is a forge built as a **process system for humans**. Origin is a forge that expects the writer to be cheap, parallel, and often not human.

---

## The self-downgrade

Truth can only live in one place. A new host that wants to win usually tries to become that place. Origin’s opening move is the opposite: a mirror that updates with GitHub, plus a browse/search/PR surface on the copy.

That looks like a missing feature. It is the feature.

If Origin does not compete for source of truth, the team does not need a decision. No decision means no evaluation committee, no migration budget, no executive signature. A procurement event is downgraded to a click. That is how you enter an enterprise without winning a bake-off.

GitHub keeps the job it already has: the human process — issues, required reviews, Actions, CODEOWNERS, the audit trail. Origin takes the job GitHub was not designed for: sitting next to an agent that can open ten pull requests before lunch.

The cost of that convenience is the rest of this essay. A click that copies bytes is still a copy.

---

## Why a second forge exists

GitHub’s implicit physics: writing code is the bottleneck, and review is the accessory around a human commit stream.

Origin’s physics: writing got cheap. Agents made “produce a diff” a parallel, low-cost operation. The bottleneck flipped to **review and merge throughput** — too many pull requests, each one too large, not enough human hours to finish them.

That is not an aesthetic complaint about GitHub’s UI. Incumbents get moved by quantity changes, not taste changes. Cursor has an observation point other forges do not: it is the editor producing the agent commits, so it sees the curve earlier and more precisely than the host that merely receives them.

The implied answers — not all shipped, not all documented — are the ones you would build if you believed that thesis:

- **Stacked diffs.** A giant change split into a sequence a human can finish. This is Graphite’s core trick. Cursor acquired Graphite in December 2025. Origin does not yet document it.
- **Merge queue.** Ten agents open PRs off stale `main`. You serialize test-then-merge, or the last mile is rebase conflict.
- **Intent-aware conflict resolution.** Judge a conflict by what the change was trying to do, not by which text line won.

If those land, Origin is a review machine that happens to store git. If they do not, it is a convenient mirror with a CLI.

---

## Two buttons, two different products

On a namespace you already claimed, the forge home looks like this:

![cursor.com/codebase for the macquarie-university namespace, showing todd_awesome_repo alongside the + New and Sync from GitHub buttons](codebase-sync-from-github.png)

That screenshot is the whole product in one frame, and almost everyone reads it wrong. **+ New** and **Sync from GitHub** are not two ways to do the same thing:

- **+ New** creates an **Origin-hosted** repository. Origin is the source of truth. Nothing is mirrored anywhere.
- **Sync from GitHub** creates a **mirror**. GitHub is the source of truth. Origin follows it.

`todd_awesome_repo` in that list came from **+ New**. It is a disposable spike, not a mirror. Every reassuring thing you have read about "GitHub is still SoT" applies to the other button.

- Forge home: [cursor.com/codebase](https://cursor.com/codebase)
- Example tree: [cursor.com/codebase/macquarie-university/todd_awesome_repo/tree/main](https://cursor.com/codebase/macquarie-university/todd_awesome_repo/tree/main)

Clone is two tastes, one effect:

```bash
# taste 1 — Origin CLI
origin clone macquarie-university/todd_awesome_repo
origin repo clone macquarie-university/todd_awesome_repo

# taste 2 — ordinary git
git clone https://origin.cursor.com/macquarie-university/todd_awesome_repo.git
```

Daily work after authentication is still `git push` and `git pull`. The CLI is not a new transport. It is the forge API in a shell: sign in, create a repo, open or merge a PR, finish the loop when there is no browser.

Push a local project that does **not** already live on GitHub:

```bash
git init -b 'main'
git remote add origin 'https://origin.cursor.com/macquarie-university/todd_awesome_repo'
git add .
git commit -m "Initial commit"
git push -u origin 'main'
```

If GitHub is already `origin`, do not run that block. Sync the GitHub repo. Do not invent a second source of truth by accident.

`origin auth login` opens the Cursor account you already have and installs a credential helper for `origin.cursor.com`. Headless sessions print a URL. Nobody should paste a token into chat. The installer drops a binary at `~/.local/bin/origin`. Native Windows is not supported; WSL is.

---

## Adding a remote is not mirroring

This is the question every engineer asks about ten seconds after the SoT sentence: *if GitHub stays source of truth, do I just point a remote at Origin?*

No. This line does **not** create a mirror:

```bash
git remote add origin 'https://origin.cursor.com/macquarie-university/todd_awesome_repo'
```

That points your local repo at an **Origin-hosted** repository. If the code also exists on GitHub, you now have two independent remotes and two candidate sources of truth. Nothing syncs. Nothing passes through. You built a fork with good intentions.

| | Add an Origin remote | Sync from GitHub |
|---|---|---|
| What it is | Local push to an Origin-hosted repo | GitHub copied into Origin and kept updated |
| GitHub is SoT? | **No** | **Yes** — Settings shows Origin = mirror, GitHub = source |
| Auto-sync | Never | History, branches, tags; PRs both directions |
| `git push` to the Origin remote | Stops at Origin | **Passes through to GitHub** |

### The real mirror path

Prerequisites, in the order they bite:

1. A paid plan with Origin access.
2. A claimed codebase name — ours is `macquarie-university`.
3. The Cursor GitHub App connected to the GitHub org that owns the repo.
4. **GitHub admin on the repository you want to sync.** This is the one that stops most people. Write access is not enough.

Then, in the UI:

1. Open [cursor.com/codebase](https://cursor.com/codebase)
2. Click **Sync from GitHub** — not **+ New**
3. Pick the GitHub organization and repository
4. Confirm

Verify it afterwards in the repository's **Settings → General**: a synced repo reports Origin as the mirror and GitHub as the source. If it does not say that, you did not make a mirror.

The CLI equivalent takes the **GitHub** `org/repo`, not an `origin.cursor.com` URL:

```bash
origin repo create-mirrored macquarie-university/some-real-service
origin repo create-mirrored acme/checkout --namespace macquarie-university
```

Once the mirror exists, clone from the green **Code** button — or keep your GitHub checkout and add a second remote under an honest name:

```bash
git remote add cursor https://origin.cursor.com/macquarie-university/<mirrored-repo>.git
```

Do not overwrite an existing `origin` that points at GitHub. The name is already taken by the thing that is actually canonical.

What does not come along: GitHub Issues, and Actions workflows and secrets. Those stay on GitHub, which is where they should be while GitHub is source of truth.

---

## The CLI’s real user is the agent

The docs describe the CLI as “terminal workflows.” Read that from the agent’s point of view.

You already have `git` and a browser. An agent in a cloud box has neither a GUI nor a habit of clicking **Code**. The binary exists so it can walk a headless path: authenticate, create the repository, set the remote, push, open the pull request. Cursor’s own docs say agents can create Origin repos. That sentence is the reason the CLI exists.

Forge-layer work, not git-layer work:

- credential helper
- create / list / delete repositories
- open and merge pull requests
- give a non-human a complete loop

The agent inherits the signed-in user’s permissions. There is no hidden superuser. That is reassuring and slightly sharp: an Internal repo plus a chatty agent is visible to anyone with codebase access, and a “save this project” prompt will stage whatever git would stage.

---

## Two merges hiding under one verb

A sentence you will hear: *reviews assigned on GitHub can be reviewed and merged in Cursor.*

That sentence does not say which system executed merge. Two implementations hide under it.

**System A — Cursor as a GitHub client.** Cursor calls GitHub’s merge API. The bytes never left GitHub. Source of truth did not move. This is the path that matches “GitHub is still SoT.”

**System B — an Origin pull request.** On a mirrored repo, Origin PRs can sync back to GitHub. On a native Origin repo, the PR stays on Origin and is not mirrored anywhere.

If you only wanted comments on GitHub PRs, you did not need Origin. Cursor Review and Bugbot already do that without moving storage. Origin is for when the forge, the review UI, and the agent I/O are supposed to be one system.

---

## There are no Actions. That is the hole they borrowed.

Origin does not have GitHub Actions. Actions is the layer GitHub locked deepest. Cursor will not rebuild it this quarter, so the beta ships three apps that already do the jobs Actions used to monopolize:

- **Vercel** — preview deployments from a pull request.
- **Depot** and **Buildkite** — CI on **Origin-hosted** repositories.

They were not chosen because they are the most popular. They were chosen because their existence is an argument: GitHub’s CI can be replaced without becoming GitHub.

On a **mirror**, that argument is deferred. Actions, secrets, and the existing required checks stay on GitHub. Depot and Buildkite do not attach to mirrored repos. While GitHub is source of truth, that is the correct default.

Rules and Protections exist. The UI is being redesigned. Do not tell a platform team you have CODEOWNERS parity until you have clicked the page.

---

## What “GitHub’s terms still apply” actually means

This is the sentence that will get said in a design review, and it is the sentence that is wrong.

GitHub’s terms govern **GitHub’s copy**. They follow GitHub’s service, not the bytes. Once a repository is copied into Origin, the physical holder of that second copy is Cursor. GitHub’s contract does not travel with it.

The accurate rebuttal is one line:

> GitHub’s terms continue to govern the GitHub copy. They say nothing about the copy in Cursor’s hands.

A few facts sit under that line, as of this investigation:

- Origin-hosted and mirrored copies do not come with a published data-retention term, subprocessor list, or training-use policy specific to that copy.
- Cursor’s parent is now SpaceX. The data-use page lists SpaceXAI alongside OpenAI and Anthropic as providers.
- Origin follows the **namespace owner’s** Privacy Mode — the person or team who claimed the codebase name — not the GitHub repository’s own settings, and not GitHub’s ToS.

For a regulated industry, “GitHub already approved this vendor path” is not a risk transfer. It is a category error. This is not legal advice. It is the refusal to treat a second physical copy as covered by the first copy’s contract.

---

## Disconnect is not un-copy

The other sentence that will get said: *we can turn it off whenever we want.*

Detach stops the **stream**. It does not undo the copy, the cache, or the index that already happened. The reversibility story covers flow. It does not cover stock.

Two more organizational facts make that sharper:

- During beta, the codebase name cannot be renamed. Any team member can claim it. You can stop a sync. You cannot un-claim an org slug or un-index what was already ingested.
- Teams on legacy privacy mode must switch to Privacy Mode *before* Origin turns on. A “trial” whose first step is changing enterprise privacy settings is not a pilot. It is an org-wide config change sold as curiosity.

There is also the operational footgun, which is narrower and more common: **Detach from GitHub** on a repo people still ship from. GitHub is untouched, but Origin becomes standalone, the next push to the Origin remote no longer flows to GitHub, and CI can go green on the wrong host. Do not click it to see what happens.

---

## A sane evaluation, given that the click is the strategy

The useful question is not “should we leave GitHub?” Origin already answered that: no.

The useful question is “what is allowed to be copied, by whom, under which privacy switch, and what do we believe happens to the copy if we disconnect?”

A sequence that does not create a mess:

1. Repeat the SoT sentence until the room can say it without you.
2. Treat the codebase name as permanent. Claim it as if you cannot change it, because in beta you cannot.
3. Use a throwaway native repo — `todd_awesome_repo` is the right size — to learn `origin clone` vs `git clone`.
4. If you sync anything from GitHub, sync a **named sandbox**, not a service that ships.
5. Do not rewrite a production `origin` remote. Do not detach. Do not let an agent `repo delete`.
6. Send legal the two-sentence version of the terms argument *before* anyone calls the click zero-risk.
7. Write kill criteria down. The click is designed so you skip this step. Do not skip it.

Kill criteria I would put on an internal doc:

- Someone treats a mirror as harmless *because* GitHub’s terms exist.
- Legal cannot get retention, subprocessor, or training terms for the Cursor-held copy.
- Enabling Origin requires an org-wide Privacy Mode change the org is not ready to make.
- A disconnect is used as proof the copy is gone.
- A production remote is rewritten, or Detach is clicked on a real service.

Stay criteria are simpler: GitHub remains SoT on everything we still ship; only a throwaway or a named sandbox is on Origin; admins know who claimed the namespace; nobody had to change enterprise privacy settings “just to look.”

---

## What I would tell a staff engineer in one paragraph

Origin is Cursor’s git forge, not a new `git`. It speaks ordinary HTTPS, authenticates through a CLI-installed credential helper, and exists so an agent can create a repo and open a pull request without a GUI. It is not a GitHub replacement. **GitHub is still the source of truth.** That refusal is how Origin skips a migration decision and arrives as a click. The click still copies bytes. GitHub’s terms do not follow those bytes. Disconnect stops the stream and does not un-copy the stock. Evaluate on a spike or a sandbox mirror. If the review-and-merge bottleneck is real, the interesting work is stacked diffs, merge queues, and intent-aware conflicts — most of which are not a demo you can give today.

---

## Commands worth keeping

```bash
# install + auth
curl -fsSL https://downloads.cursor.com/origin/install.sh | sh
origin auth login

# two tastes, same clone
origin clone macquarie-university/todd_awesome_repo
git clone https://origin.cursor.com/macquarie-university/todd_awesome_repo.git

# mirror an existing GitHub repo — GitHub stays SoT
# (UI: cursor.com/codebase -> Sync from GitHub)
origin repo create-mirrored <github-org>/<github-repo> --namespace macquarie-university

# native spike only — do not do this to a GitHub SoT
git init -b 'main'
git remote add origin 'https://origin.cursor.com/macquarie-university/todd_awesome_repo'
git add .
git commit -m "Initial commit"
git push -u origin 'main'
```

Docs: [cursor.com/docs/origin](https://cursor.com/docs/origin) · Codebase: [cursor.com/codebase](https://cursor.com/codebase)

*Origin is early beta. Commands, protection UIs, and the API can change. The SoT sentence should not.*
