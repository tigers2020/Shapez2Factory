---
name: todo-plan-automation
description: >-
  Linear Todo → local plan files → In Progress. Use for Cursor Automation
  "Todo Plan Writing" or when processing Shapez2Factory issues in Todo status.
  Canon prompt: documents/prompt/03 Linear Todo Plan Writing Automation.md
---

# Todo Plan Writing Automation

**Authority:** `documents/prompt/03 Linear Todo Plan Writing Automation.md` — follow that prompt in full for Cursor Automations and agent runs.

Quick reminders (not a substitute for the canon prompt):

- One trigger = one issue; no Todo queue loop.
- Mutex: `auto:todo-plan-running` + `reviewing`; remove in `finally`.
- Idempotency: existing `plans/**/<KEY>-*.md` or prior automation comment → skip.
- Trigger: built-in Linear **or** webhook bridge, not both.
- Plan execution: `.cursor/skills/plan-run/SKILL.md`

---

## Runaway PR guard

Todo Plan Automation must **never** create a GitHub PR to fix dirty root, clean-root failures, or workflow-state drift.

If repo root is dirty before this automation runs:

1. **Stop** — no plan files commit on root unless this run's scoped metadata (see canon prompt).
2. Do **not** invoke `/clean-root auto` automatically.
3. Do **not** create branch or PR.
4. Do **not** run `git clean -fdX` or delete `var/plan-run/**`, `.worktrees/**`, `plans/**`.
5. Linear comment (Korean ok): 보류 — root dirty; operator 정리 필요.

```text
BLOCKED: dirty root worktree
Dirty files:
- ...
Next:
- operator must commit, stash, or discard manually
```

**Forbidden loop:**

```text
dirty root → clean-root → commit → branch → PR
```

**Automation-safety PR:** operator-only; title `automation-safety`; skills/prompts; ≤1 open. See [plan-run Runaway PR guard](../plan-run/SKILL.md#runaway-pr-guard).
