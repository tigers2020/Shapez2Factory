# Plan Lifecycle

Canon: `AGENTS.md` § Authority split. Related: `workflow-phases.md`, `plan-run` skill.

## Authority stack

```text
user > canon/spec/ADR > active plan (in execution) > code/tests > closed plan > agent memory
```

| State | Role for agents |
|-------|-----------------|
| **Active plan** (`planned` / `in_progress` in `plans/{high,mid,low}/`) | Execution authority when user or plan-run invoked it |
| **Closed plan** (`plans/done/`, `status: done` / `skipped`) | Audit trail only — not behavior authority |
| **Canon / spec / ADR** | Durable domain truth |
| **Code + tests** | Implementation evidence |
| **Agent memory** | Never authority |

## Doc rot risk

Stale PRDs and plans in-repo can mislead agents when names, files, and requirements have drifted. On merge:

1. Move or mark plan `status: done` per plan-run lifecycle
2. Do not treat closed plan text as current spec
3. Promote durable decisions to canon/spec/ADR or wiki — not left only in closed plan

## When agents may read closed plans

- Incident/debug context (historical)
- After explicit user `@` reference

Default search for "how should X behave": **canon → code/tests → wiki**, not `plans/done/`.

## Wiki vs plan

| Kind | Location | Authority |
|------|----------|-----------|
| Working research | `documents/knowledge/wiki/` | research — promote via `doc-update` |
| Execution queue | `plans/` | active only while queued/running |
| Governance | `AGENTS.md`, `.cursor/rules/` | process |

Maintenance: `dream-sequence.md` for wiki; plan-run metadata commit for queue state.
