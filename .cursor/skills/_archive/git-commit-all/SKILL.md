---
name: git-commit-all
description: >-
  Guides safe git add, conventional commit, pull --rebase sync, and push:
  inspect branch and status, review diffs, stage intended paths, avoid secrets
  and force-push. Use when the user runs /git-commit-all, @git-commit-all, or
  asks to commit and push all current changes with a structured workflow.
disable-model-invocation: true
---

# Git Commit & Push Workflow

When asked to commit and push changes, follow this exact workflow.

## Step 1 — Inspect Repository State

Run:

```bash
git status
git branch --show-current
git remote -v
```

Then summarize:

* current branch
* modified files
* newly added files
* deleted files

Do NOT continue if:

* merge conflicts exist
* rebase is in progress
* detached HEAD state detected

---

## Step 2 — Review Changes

Run:

```bash
git diff --stat
git diff
```

Provide a concise technical summary of:

* major code changes
* refactors
* new features
* removed logic
* generated files
* risky changes

If unrelated or accidental files are detected:

* warn before staging

---

## Step 3 — Stage Changes

Stage all intended changes:

```bash
git add .
```

Then verify:

```bash
git status
```

---

## Step 4 — Generate Commit Message

Generate a clean conventional-style commit message.

Preferred format:

```text
type(scope): short summary
```

Examples:

* feat(router): add trunk congestion weighting
* fix(pass3): prevent disconnected transport outlets
* refactor(replay): split corridor overlay readers
* docs(plan): add recovery diagnostics notes

Add bullet details if needed.

---

## Step 5 — Commit

Run:

```bash
git commit -m "generated commit message"
```

If commit fails:

* explain exact reason
* resolve simple formatting/staging issues if possible
* retry once

---

## Step 6 — Sync Before Push

Run:

```bash
git pull --rebase
```

If conflicts occur:

* stop
* summarize conflicting files
* do NOT auto-resolve complex conflicts

---

## Step 7 — Push

Push current branch:

```bash
git push
```

Then report:

* pushed branch
* latest commit hash
* commit summary

---

## Rules

* Never use `git push --force` unless explicitly requested.
* Never commit secrets, `.env`, API keys, tokens, or large cache/build directories.
* Warn before committing generated binaries or massive assets.
* Prefer small atomic commits over giant mixed commits.
* Preserve existing branch strategy.
* Do not rewrite history unless explicitly instructed.
