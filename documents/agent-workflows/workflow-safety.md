# Workflow Safety — Delivery Modes

Router: `.cursor/rules/workflow-safety.mdc`. Canon: `AGENTS.md` § Delivery safety.

## Core rule

```text
The agent must not treat dirty root as a problem to "fix" automatically.
Dirty root is user state. Report it, protect it, and stop unless the requested edit scope is explicitly safe.
```

## Problem pattern (avoid)

```text
AI creates branch per small change
→ documents/plans left in root
→ AI "fixes" dirty root via clean-root / stash / checkout / git clean
→ protected workflow state or docs deleted
→ active.md / plans / docs corrupt
→ dirty root blocks next task
```

Incident: `clean-root auto → git clean -fdX → var/plan-run/active.md` deleted.

## Default policy

| Default | Rule |
|---------|------|
| PR | forbidden unless explicit "open PR" |
| New branch | forbidden unless explicit "create branch" |
| `git clean` (all variants) | forbidden — includes `-fd`, `-fdX`, `-fxd`, `-fd .` |
| `git reset --hard` | forbidden unless explicit approval |
| Untracked delete | forbidden |
| Auto stash apply | forbidden |
| `git checkout` / `git switch` | forbidden Mode 0–1 unless explicit branch movement |
| Dirty files outside scope | **STOP** before editing |

**`git clean` exception:** only targeted deletion of explicitly approved cache paths, after preview and user approval. Never wholesale clean.

Allowed without escalation: review-only, patch proposal, edit scoped files on current branch when scope is safe.

## Dirty root handling

Dirty root is user state, not cleanup debt.

If `git status --short` shows files outside the explicit task scope:

- **STOP** before editing.
- Do not stash them.
- Do not restore them.
- Do not clean them.
- Do not switch branches.
- Report the dirty files and continue only if the user explicitly approves.

**Allowed exception:** all dirty files are inside the explicit task scope → Mode 1 may proceed on the current branch.

## Mode 0 — Review only

- Purpose: design review, findings, patch plan
- Forbidden: file edits, `git checkout` / `git switch`, any `git clean`, stash, commit, branch
- Output: chat answer or draft markdown (user saves if needed)

## Mode 1 — Local patch only

- Conditions: 1–3 files; docs or tests bias; user will commit; dirty ⊆ scope
- Forbidden: any `git clean`, auto stash apply, branch delete, PR create, `checkout` / `switch`
- Current branch only

## Mode 2 — Single working branch

- One `work/<topic>` branch; multiple commits OK
- Create/switch **only** to that single approved branch
- PR only when user says "open PR"
- Preferred for multi-step features (e.g. replay cell semantics Steps 1–3)

## Mode 3 — Real PR

All required:

- Scope clear, tests pass, dirty root resolved within scope
- User documents/workflow files protected
- User explicitly requests PR

## Protected paths

Never auto-delete or plain `git clean` target:

```text
plans/**
documents/**
documents/**
var/plan-run/**
.worktrees/**
.devtool/**
```

Also: `.env`, `.env.*` (secrets).

### graphify-out/ (hybrid)

```text
graphify-out/**
- Never delete wholesale.
- Tracked core files may be updated only when task explicitly involves graph refresh.
- Ignored cache/obsidian outputs may be cleaned only by explicit user command.
```

Detail: `ops-recovery-routine.md`, `clean-root` skill, `graphify.mdc`.

## Agent checklist (before edits)

1. `git status --short`
2. Report dirty files
3. Dirty outside scope → **STOP**; ask user (continue / narrow / review-only)
4. Edit only explicit scope
5. Never any `git clean` variant without explicit approval + preview
6. Never delete untracked files
7. Never `git reset --hard` without approval
8. Never auto-apply stash
9. Mode 0–1: never `checkout` / `switch` without explicit branch-move request

## Slice naming vs GitHub PRs

| Term | Meaning |
|------|---------|
| Step 1 / Step 2 / … | Implementation sequence on one branch |
| PR1 / PR2 (legacy) | Slice size only — not "must open GitHub PR" |

Example (replay cell semantics): Step 1 resolver move → Step 2 semantics extraction → Step 3 flat shim migration → optional Step 4 canonical compare.

## replay-cell-semantics flow

```text
1. Review-only — design locked
2. Single branch — Step 1 patch (or current branch)
3. Tests pass
4. User review
5. PR decision deferred until explicit command
```
