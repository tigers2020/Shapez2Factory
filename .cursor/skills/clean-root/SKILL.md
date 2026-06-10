---
name: clean-root
description: >-
  Auto-clean the repository root before plan-run or other agent workflows.
  Classifies dirty files, commits safe agent/governance changes, stashes
  product-code or unknown changes, removes ignored junk, and reports a clean
  handoff state. Invoke via /clean-root status | plan | auto | stash |
  commit-agent | recover | clear-ignored | undo. Designed to make /plan-run
  run/auto safe.
disable-model-invocation: true
---

# /clean-root — safe root cleanup

Prepare the main worktree for `/plan-run`, PR worktree creation, or other agent workflows.

Goal:

```text
dirty root
→ classify changes
→ preserve all user work
→ commit safe agent/governance changes
→ stash risky/unknown changes
→ preview ignored junk (delete only via clear-ignored)
→ report clean root
```

Default branch: `master`.

Never silently discard tracked work.

---

## Runaway PR guard

**`/clean-root` never opens a GitHub PR.** Dirty root is operator intervention state — not self-healing via branch/PR.

If root is dirty when any automation (plan-run, todo-plan, clean-root chain) would start:

1. **Stop** — do not create branch or PR.
2. Do **not** auto-run `/clean-root auto` from another automation (operator must invoke explicitly).
3. Do **not** run plain `git clean -fdX` — deletes workflow state without excludes.
4. Report `BLOCKED: dirty root worktree` with exact dirty file list.

Protected workflow state — **never** `git clean` target:

```text
var/plan-run/**
.worktrees/**
plans/**
```

**Automation-safety PR** (operator-only, ≤1 open): title contains `automation-safety`; skills/prompts only. Not a substitute for cleaning dirty root.

**Forbidden loop:**

```text
dirty root → clean-root auto → commit → branch → PR
```

---

## Commands

| Command | Purpose |
|---------|---------|
| `/clean-root status` | Read-only report of root dirty state |
| `/clean-root plan` | Read-only cleanup proposal |
| `/clean-root auto` | Auto-clean using safe defaults |
| `/clean-root commit-agent` | Commit only agent/governance changes |
| `/clean-root stash` | Stash risky or unknown dirty files |
| `/clean-root clear-ignored` | Remove ignored junk only |
| `/clean-root recover` | Inspect latest clean-root stash/commit |
| `/clean-root undo` | Revert latest clean-root auto action when possible |

If `/clean-root` alone, run **`status`**.

---

## Safety model

`/clean-root auto` is consent for:

- committing safe agent/governance changes
- stashing product-code or unknown changes
- **previewing** ignored junk (report only — no delete)
- reporting next recommended command

It is **not** consent for:

- deleting ignored files (use `/clean-root clear-ignored` explicitly)
- `git reset --hard`
- `git clean -fd` without `-X`
- force push
- modifying Linear/GitHub
- merging
- editing files

---

## Classification

Run:

```bash
git status --short
git status --ignored --short
git branch --show-current
git rev-parse --short HEAD
```

Classify each dirty path.

### Class A — agent/governance safe-to-commit

Allowed paths:

```text
.cursor/skills/**
.cursor/rules/**
AGENTS.md
scripts/check_governance.ps1
docs/agent-workflows/**
docs/agent-skills/**
```

These may be auto-committed by `/clean-root auto`.

### Class B — plan queue metadata

Paths:

```text
plans/high/**
plans/mid/**
plans/low/**
plans/done/**
var/plan-run/active.md
```

Rules:

- Do not auto-commit plan queue changes unless command is `/plan-run`-owned [metadata commit](plan-run/SKILL.md#metadata-commit).
- At claim, plan-run writes `var/plan-run/**` only — frontmatter may stay `planned` until ship/merge/skip.
- `/clean-root auto` may stash `plans/**` if they block root clean and are not part of an in-flight plan-run metadata commit.
- If `var/plan-run/active.md` exists, report it but do not delete it.

### Class C — product code / tests / config

Examples:

```text
django_apps/**
src/**
tests/**
config/**
documents/game_data/**
scripts/**
```

Rules:

- Never auto-commit.
- Never auto-restore.
- Stash with a named stash.
- Report exact paths.

### Class D — ignored junk

Examples:

```text
__pycache__/**
.pytest_cache/**
.mypy_cache/**
.ruff_cache/**
node_modules/**
dist/**
build/**
coverage/**
htmlcov/**
graphify-out/**
graphify_out/**
```

**Not junk — never delete via clean (even if under ignored `var/`):**

```text
var/plan-run/**
.worktrees/**
plans/**
```

Rules:

- May delete only when ignored by git **and** not under [protected paths](#protected-ignored-paths).
- Use protected clean via [`/clean-root clear-ignored`](#clean-root-clear-ignored) only — never plain `git clean -fdX`.
- Never use `git clean -fd`.

### Protected ignored paths

Never delete these paths, even if ignored:

```text
.env
.env.debug
.env.webhook.local
var/plan-run/**
.worktrees/**
plans/**
```

- `.env` / `.env.debug` / `.env.webhook.local` — local secrets and runtime overrides; never `git clean` target.
- `var/plan-run/active.md` — plan-run session handoff state, not disposable cache.
- `.worktrees/**` — may contain active implementation worktrees.
- `plans/**` — queue metadata or in-progress frontmatter (tracked or dirty); never `git clean` target.

### Class E — unknown untracked

Examples:

```text
?? random_file.py
?? notes.md
?? temp.patch
```

Rules:

- Never delete.
- Stash with `git stash push -u`.
- If stash fails, leave untouched and BLOCKED.

---

## `/clean-root status`

Read-only.

Report:

```text
Summary
- Branch: <branch> @ <sha>
- Dirty: yes|no
- Active plan-run: none | <issue/phase>
- Safe agent changes: N
- Product/risky changes: N
- Unknown untracked: N
- Ignored junk: N

Next
- /clean-root auto
- /plan-run run SHA-XX
```

Do not edit files.

---

## `/clean-root plan`

Read-only cleanup proposal.

Output:

```text
Cleanup Plan
1. Commit agent/governance changes:
   - <paths>

2. Stash risky/unknown changes:
   - <paths>

3. Remove ignored junk (preview only in auto):
   - <paths from protected preview, excluding protected>

Will not:
- delete ignored files in auto (use clear-ignored)
- delete protected workflow state (.env, var/plan-run, .worktrees, plans)
```

Do not edit files.

---

## `/clean-root auto`

Run the full safe cleanup pipeline.

### Step 0 — preflight

Run:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
```

If not in repo root:

```text
BLOCKED: not repo root · next: cd <repo-root>
```

If merge/rebase/cherry-pick in progress:

```bash
git status
test -d .git/rebase-merge
test -d .git/rebase-apply
test -f .git/MERGE_HEAD
test -f .git/CHERRY_PICK_HEAD
```

Then:

```text
BLOCKED: git operation in progress · next: resolve or abort manually
```

### Step 1 — detect plan-run state

If `var/plan-run/active.md` exists:

- read it
- report `status`, `phase`, `linear_issue`, `worktree`, `branch`
- do not modify it

If active run exists and dirty root includes plan files:

```text
BLOCKED: active plan-run plus plan-file dirty state · next: /plan-run recover
```

### Step 2 — preview ignored junk (no delete)

**Do not run `git clean -fdX` in `/clean-root auto`.** Deleting ignored files is **`/clean-root clear-ignored` only**.

Preview safe-to-delete ignored paths:

```bash
git clean -ndX \
  -e .env \
  -e .env.debug \
  -e .env.webhook.local \
  -e var/plan-run/ \
  -e var/plan-run/** \
  -e .worktrees/ \
  -e .worktrees/** \
  -e plans/ \
  -e plans/**
```

Report preview paths in output. Set `Ignored junk removed: no (preview only)`.

If preview would touch protected paths despite excludes:

```text
BLOCKED: ignored clean would delete protected workflow state · next: /clean-root plan
```

Never run plain:

```bash
git clean -fdX
```

Never run:

```bash
git clean -fd
```

### Step 3 — commit agent/governance changes

If Class A changes exist:

1. Show paths.
2. Ensure no Class C files are staged.
3. Stage only Class A paths:

```bash
git add .cursor/skills .cursor/rules AGENTS.md scripts/check_governance.ps1 docs/agent-workflows docs/agent-skills
```

4. Verify staged set:

```bash
git diff --cached --name-only
```

Abort if staged file outside Class A.

5. Commit.

Commit message selection:

| Paths | Message |
|-------|---------|
| `.cursor/skills/clean-root/**` | `chore(agent): add clean-root skill` |
| `.cursor/skills/plan-run/**` | `chore(agent): add plan-run skill` |
| multiple `.cursor/skills/**` | `chore(agent): update workflow skills` |
| `.cursor/rules/**` or `AGENTS.md` | `chore(agent): update agent governance` |
| mixed agent/governance | `chore(agent): update workflow automation` |

Run:

```bash
git commit -m "<message>"
```

Record commit SHA:

```bash
git rev-parse --short HEAD
```

### Step 4 — stash risky/unknown changes

If any Class B/C/E changes remain:

Create stash name:

```text
clean-root/<timestamp>-pre-plan-run
```

Run:

```bash
git stash push -u -m "clean-root: pre-plan-run <timestamp>"
```

Then verify:

```bash
git status --short
git stash list -n 3
```

If stash fails:

```text
BLOCKED: stash failed · next: inspect git status manually
```

Do not restore or delete those files.

### Step 5 — final verification

Run:

```bash
git status --short
```

If clean:

```text
CLEAN
```

If dirty remains:

```text
BLOCKED: root still dirty
```

Report remaining paths and class.

### Output

```text
Summary
- Branch: <branch> @ <sha>
- Agent commit: <sha or none>
- Stash: <stash@{n} or none>
- Ignored junk removed: no (auto previews only; use clear-ignored)
- Root clean: yes|no

Next
- /plan-run run SHA-XX
- /plan-run auto SHA-XX
```

---

## `/clean-root commit-agent`

Commit only Class A changes.

Rules:

- Do not stash.
- Do not clean ignored files.
- Abort if product-code changes are staged.
- Abort if staged paths are outside Class A.

Commands:

```bash
git status --short
git add .cursor/skills .cursor/rules AGENTS.md scripts/check_governance.ps1 docs/agent-workflows docs/agent-skills
git diff --cached --name-only
git commit -m "<agent commit message>"
```

If no Class A changes:

```text
NOOP: no agent/governance changes
```

---

## `/clean-root stash`

Stash Class B/C/E changes.

Rules:

- Prefer named stash.
- Include untracked files.
- Do not stash ignored files unless needed.
- Do not commit.

Command:

```bash
git stash push -u -m "clean-root: manual stash <timestamp>"
```

Output:

```text
Stashed
- stash: stash@{0}
- message: clean-root: manual stash <timestamp>
```

---

## `/clean-root clear-ignored`

Remove ignored junk only — **explicit command**; never part of `/clean-root auto`.

### Protected excludes (required)

Never delete:

```text
.env
.env.debug
.env.webhook.local
var/plan-run/**
.worktrees/**
plans/**
```

### Precheck

```bash
git clean -ndX \
  -e .env \
  -e .env.debug \
  -e .env.webhook.local \
  -e var/plan-run/ \
  -e var/plan-run/** \
  -e .worktrees/ \
  -e .worktrees/** \
  -e plans/ \
  -e plans/**
```

If output lists anything under `.env*`, `var/plan-run/`, `.worktrees/`, or `plans/`:

```text
BLOCKED: ignored clean would delete protected workflow state
```

### Delete

```bash
git clean -fdX \
  -e .env \
  -e .env.debug \
  -e .env.webhook.local \
  -e var/plan-run/ \
  -e var/plan-run/** \
  -e .worktrees/ \
  -e .worktrees/** \
  -e plans/ \
  -e plans/**
```

Never use plain `git clean -fdX` without excludes. Never use `git clean -fd`.

Output deleted ignored paths when possible.

---

## `/clean-root recover`

Inspect recent clean-root actions.

Run:

```bash
git log --oneline -5
git stash list -n 10
git status --short
```

Report:

```text
Recovery
- Latest clean-root commit: <sha or none>
- Latest clean-root stash: <stash@{n} or none>
- Root dirty: yes|no

Options
- apply stash: git stash apply <stash>
- drop stash: git stash drop <stash>
- revert commit: git revert <sha>
```

Do not apply, drop, or revert automatically.

---

## `/clean-root undo`

Undo only the latest clean-root auto action when unambiguous.

Allowed:

- If latest commit message starts with `chore(agent):` and only Class A files changed: run `git revert <sha>`
- If latest stash message starts with `clean-root:`: run `git stash apply <stash>`

Not allowed:

- dropping stash automatically
- reverting product-code commits
- reset hard
- force cleaning unknown files

If both commit and stash exist:

```text
BLOCKED: both commit and stash exist · run /clean-root recover and choose manually
```

---

## Integration with `/plan-run`

Per [plan-run root mutation policy](../plan-run/SKILL.md#root-mutation-policy):

- **`/plan-run run`** — writes `var/plan-run/**` only; not blocked by unrelated root dirty unless skill patches block you.
- **`/plan-run auto` (fresh)**, **`/plan-run skip`** — blocked when unrelated tracked edits remain.
- **Plan metadata** (`plans/**` frontmatter) — changed only at ship/merge/skip with immediate metadata commit; never left dirty mid-phase.

When `/plan-run` blocks on dirty root:

- Report BLOCKED with file list — **do not** auto-chain `/clean-root auto`.
- Operator may run `/clean-root plan` (read-only) then `/clean-root auto` **explicitly**, then retry plan-run.

Recommended flow for stale Linear claim:

```text
/plan-run run SHA-XX
```

(clean root only when operator explicitly chooses — not automatic)

Recommended flow for fresh auto (operator-driven):

```text
# operator clears dirty root first (commit | stash | /clean-root auto)
/plan-run auto SHA-XX
```

---

## Failure report

Always use:

```text
BLOCKED: <what> · tried: <commands> · next: <one recovery command>
```

Never hide dirty files. Never silently discard user work.

---

## Acceptance: protected ignored state

Given:

- `var/plan-run/active.md` exists
- `.worktrees/auto-SHA-*` exists
- `plans/high/*.md` has local metadata changes

When:

- `/clean-root auto` runs

Then:

- it must **not** run plain `git clean -fdX`
- it must **not** delete `.env`, `.env.debug`, or `.env.webhook.local`
- it must **not** delete `var/plan-run/active.md`
- it must **not** delete `.worktrees/**`
- it must **not** delete or restore `plans/**`
- ignored junk cleanup is **preview-only** (use `/clean-root clear-ignored` to delete)
