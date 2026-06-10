```
Status changed
```

# Linear Todo Plan Writing Automation

Trigger: Run when a Linear issue card enters **Todo**.

Goal: Convert the **trigger issue** spec into local implementation plan files (by priority), then move that issue to **In-progress**.

**Do not drain the Todo queue in one run.** One automation invocation processes exactly one issue.

---

## Hard concurrency rules (non-negotiable)

1. **One run = one issue** — process only the trigger issue (`issue_id` from the webhook payload). **No loop.** Do not search for the oldest Todo card.
2. **Global mutex** — before work, list Shapez2Factory issues with label `auto:todo-plan-running`. If any were updated within the last **45 minutes**, exit immediately. Report `Status: blocked`, reason `concurrent-run`.
3. **Per-issue lock** — immediately add labels `reviewing` and `auto:todo-plan-running` to the trigger issue (keep all existing labels).
4. **`finally` cleanup** — always remove `reviewing` and `auto:todo-plan-running` from the trigger issue when the run ends (success, skip, or failure). Never leave them stuck.
5. **Idempotency** — if any of these are true, skip plan creation, do not change status, remove lock labels, exit:
   - `plans/**/<LINEAR-KEY>-*.md` already exists in the repo
   - a Linear comment on this issue already contains `Processed by Todo Plan Automation`

## Trigger pairing

Use **either**:

- Cursor built-in Linear status trigger, **or**
- `scripts/linear_cursor_webhook_bridge.py` → Cursor webhook

**Not both.** Dual triggers caused duplicate parallel runs (e.g. SHA-30 processed four times). The bridge applies per-issue and global Todo cooldowns when enabled.

Cursor Automations: set **concurrency = 1** for this automation if the UI exposes it.

---

## Runaway PR guard (non-negotiable)

Dirty root is an **automation stop gate** — not a trigger to open a PR.

If the repo root worktree is dirty before this run:

1. **Stop immediately.**
2. Do **not** create a branch or Pull Request.
3. Do **not** run `/clean-root auto` unless the operator explicitly requested it.
4. Do **not** run `git clean -fdX` or delete `var/plan-run/**`, `.worktrees/**`, `plans/**`.
5. Report `BLOCKED: dirty root worktree` with exact dirty file paths.

**Forbidden loop:** `dirty root → clean-root → commit → branch → PR`

**Automation-safety PR** (operator-only): title must contain `automation-safety`; skills/prompts only; at most one open. Not a substitute for operator cleaning dirty root.

Skill reference: `.cursor/skills/todo-plan-automation/SKILL.md`, `.cursor/skills/clean-root/SKILL.md`.

---

## Workflow (single issue)

1. Resolve trigger `issue_id`. If missing → `Status: blocked`.
2. Global mutex gate (see above).
3. `get_issue` — must be **Todo**. Skip if status is already In Progress / Done / Canceled unless idempotency says plans are missing.
4. Add lock labels (`reviewing`, `auto:todo-plan-running`) immediately.
5. Read the full issue:
   - title
   - description / spec
   - priority breakdown
   - labels
   - comments
   - linked issues / docs
6. Confirm the issue has a usable spec.
7. If missing clear **Problem**, **Scope**, **Proposed Approach**, or **Acceptance Criteria**:
   - keep issue in **Todo**
   - remove lock labels
   - add label `blocked` or `question`
   - comment with the missing information
   - exit (do not process other issues)
8. If spec is usable, run `/writing-plans` for priority sections in the spec only.
9. Write plan files (see below).
10. Comment on Linear with plan paths.
11. Move issue to **In-progress**.
12. Remove lock labels.

---

## Plan file creation

Create local plan files according to the issue priority breakdown.

Folder structure:

```text
plans/
  high/
  mid/
  low/
```

If the project already has a canonical plan directory, use that instead, but preserve the priority folders.

For each priority section in the issue spec:

- `High` items → `plans/high/`
- `Mid` items → `plans/mid/`
- `Low` items → `plans/low/`

If an issue has multiple priority sections, create **separate** plan files per priority.

Recommended filename format:

```text
YYYY-MM-DD-LINEARKEY-short-slug.md
```

Examples:

```text
plans/high/2026-06-09-SHA-123-fix-resolve-preview-typecheck.md
plans/mid/2026-06-09-SHA-123-add-regression-tests.md
plans/low/2026-06-09-SHA-123-docs-cleanup.md
```

---

## Required plan file format

Each generated plan file must use this structure:

```md
---
linear_issue: LINEAR-KEY
title: Issue title
priority: High | Mid | Low
labels:
  - bug
  - ui
status: planned
created_by: todo-plan-automation
---

# Plan: Issue title

## Source Issue

- Linear: LINEAR-KEY
- Status at planning time: Todo
- Priority: High | Mid | Low

## Problem

Restate the confirmed problem from the issue spec.

## Scope

What this plan will change.

## Non-goals

What this plan must not change.

## Implementation Plan

1. Step one.
2. Step two.
3. Step three.

## Files / Areas Likely Affected

- path/or/module, if known
- unknown areas should be marked as `TBD`, not invented

## Validation Plan

- lint:
- typecheck:
- tests:
- build:
- manual verification:

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- List risks or questions.
```

Frontmatter contract also aligns with `.cursor/skills/plan-run/SKILL.md`.

---

## Priority rules

- **High** — blockers, broken core behavior, failing validation, correctness, data loss, security, severe user impact.
- **Mid** — maintainability, missing tests, incomplete UX, partial spec mismatch, important non-blocking behavior.
- **Low** — cleanup, docs polish, naming, minor UI polish, optional refactor, non-blocking improvement.
- Do not invent priority items. Use the issue spec. If unclear, create one `plans/mid/` plan and note uncertainty under Risks / Open Questions.

---

## Linking back to Linear

After writing plan files:

1. Add a comment to the Linear issue with links/paths to every generated plan file.
2. Use this comment format:

```md
Processed by Todo Plan Automation.

Generated plan files:

- High: `plans/high/...md` (or _(none)_)
- Mid: `plans/mid/...md`
- Low: `plans/low/...md`

Next status: In-progress.
```

3. If the environment supports clickable repository links, include full repo links.
4. If only local paths are available, include relative paths.

---

## Finalization

After successful plan creation:

1. Move the Linear issue from **Todo** to **In-progress**.
2. Remove labels `reviewing` and `auto:todo-plan-running`.
3. Leave all existing topic labels intact.
4. Do not remove `blocked` or `question` unless the issue is clearly resolved enough to proceed.

---

## Safety rules

- Do not implement product code in this automation.
- Do not modify product files except plan files under `plans/`.
- Do not create duplicate plan files for the same issue and priority tier.
- If plan files already exist for this issue, update only when they clearly correspond to the same Linear issue and priority; prefer skip via idempotency gate.
- Do not move an issue to In-progress if plan creation failed.
- Do not keep `reviewing` or `auto:todo-plan-running` on a finished or failed card.
- If filesystem or Linear API/tooling fails:
  - keep the issue in Todo (unless already moved)
  - remove lock labels if possible
  - add a failure comment with the reason
  - exit (do not pick up other Todo cards)

---

## Stop condition

Stop after the **single trigger issue** is processed, skipped, or blocked.

Do **not** loop until the Todo column is empty. Additional Todo cards are handled by their own automation triggers.

---

## Final run report

At the end of the automation run, report:

```text
Status: complete | partial | blocked

Trigger issue: LINEAR-KEY

Plan files created:
- High: N
- Mid: N
- Low: N

Moved to In-progress:
- LINEAR-KEY | none

Blocked / skipped:
- LINEAR-KEY: reason

Failures:
- ...
```
