# Architecture review artifacts

Durable outputs from `/improve-codebase-architecture` and related implementation threads.

Skill: `.cursor/skills/improve-codebase-architecture/SKILL.md`  
Kanban: one feature-thread card in `.devtool/features/` with an **Artifacts** table linking here.

## Layout

```text
docs/architecture/<thread-slug>/
  report.md   # Architecture Improvement Report (review)
  spec.md     # Contract: scope, decisions, invariants
  plan.md     # Implementation steps, stop conditions, validation
```

**Slug:** kebab-case (e.g. `replay-cell-semantics`). One directory per thread — not per chat or sub-step.

## Authority

| Kind | Role |
|------|------|
| `report.md` | Evidence and design analysis at review time |
| `spec.md` | What is allowed/forbidden for the thread (process + domain contract) |
| `plan.md` | Ordered slices for implementation agents |

Domain canon still wins over older reports. When code drifts, update artifacts or note drift in kanban **Progress**.

## Kanban link (required)

Each thread card must include:

```markdown
## Artifacts

| Kind | Path | Updated |
|------|------|---------|
| report | docs/architecture/<slug>/report.md | YYYY-MM-DD |
| spec | docs/architecture/<slug>/spec.md | YYYY-MM-DD |
| plan | docs/architecture/<slug>/plan.md | YYYY-MM-DD |
```

Card = WIP + Acceptance + links. Long-form content stays in artifact files.
