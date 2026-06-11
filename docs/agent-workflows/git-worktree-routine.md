# Git / Worktree Routine

Router: `.cursor/rules/git-worktree.mdc`. Canon: `AGENTS.md`.

## When to check

- Session start, before first production edit
- After switching branch or worktree
- Before claiming a slice is ready for commit/PR

## Commands

```powershell
git status --short
git branch --show-current
git worktree list
```

Optional: `git diff --stat` to see whether dirty files match the assigned task.

## If dirty

Do not edit until the surface is clean or the user scoped the dirty files.

| Situation | Action |
|-----------|--------|
| Own WIP, wrong task | Stash or commit on a WIP branch; start clean |
| Another agent/session mix | Stop; list files; ask user which branch owns them |
| Large/risky change | `git worktree add` + new branch; work there |
| User named files in prompt | Proceed only on those paths; do not touch other dirty paths |
| Ops / recovery (plan-run, clean-root, PR/CI) | Route `ops-recovery.mdc`; dirty inventory OK; whitelist edits only |
| Dirty root blocks automation | `/clean-root status` — never plain `git clean -fdX` on protected paths |

## Clean enough

- `git status --short` empty, or
- Only paths explicitly assigned in the current user prompt/plan

## Not clean

- Untracked `__pycache__`, `.pyc`, local caches in the diff scope — add to `.gitignore` or clean before edits when they obscure review
- Locale/binary churn unrelated to the task
- Multiple unrelated modified areas without user approval
