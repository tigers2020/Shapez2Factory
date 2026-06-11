# Ops / Recovery Routine

Router: `.cursor/rules/ops-recovery.mdc`. Canon: `AGENTS.md` § Task routing.

## When to use

| Trigger | Examples |
|---------|----------|
| Dirty root blocks automation | plan-run cannot start; mixed WIP |
| Workflow state loss risk | `git clean` preview; accidental delete |
| PR / CI | red checks, merge conflicts, stale branch |
| Plan-run | `var/plan-run/active.md` missing or corrupt |
| Handoff | stash recover; worktree orphan cleanup |

Classify as ops/recovery **before** treating as implementation. Ops mode allows dirty inventory; implementation mode does not.

## Protected paths

Never auto-delete or plain `git clean` target:

```text
var/plan-run/**
.worktrees/**
plans/**
```

Incident context: plain `git clean -fdX` deleted `var/plan-run/active.md` — excluded paths are mandatory for any ignored cleanup.

## Safe recovery order

1. `git status --short`, `git worktree list`, `git stash list`
2. Report dirty paths; identify protected paths in scope
3. Choose skill: `/clean-root status` → `plan` → operator-invoked `auto` / `recover` / `clear-ignored`
4. Verify: root clean enough for stated goal OR `BLOCKED:` with exact next command
5. `STOPPED_AT_APPROVED_SCOPE` — no product slice unless recovery contract named it

## Forbidden

- dirty root → auto clean-root → commit → branch → PR (runaway loop)
- `/clean-root` opening GitHub PRs
- `git clean -fd` (tracked + untracked wipe)
- `git clean -fdX` without protected `-e` excludes
- product code edits while "just cleaning up"

## CI / PR triage

Read-only first: `gh pr checks`, logs, failing job name. Separate infra flake from code regression before any edit. Code fix → reclassify as regression or implementation.

## Linear / plan-run

Stale claim: read queue + `var/plan-run/active.md`; do not delete active state. Recover via `/plan-run recover` when documented in skill.
