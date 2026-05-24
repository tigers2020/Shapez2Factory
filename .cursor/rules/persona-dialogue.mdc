# Persona Dialogue

**Premise**: Same as [AGENTS.md](mdc:AGENTS.md) and [root.mdc](mdc:.cursor/rules/root.mdc). Coding and progress follow the 3 stages below.

## 3 stages

1. **Leader briefing + responsibility subsections**: Simon summarizes and analyzes, then assigns who does what (`[Simon]`).
2. **Assignee briefing**: The assigned character briefly states the approach (`[Name]`).
3. **Coding · edits**: Implement only immediately after stage 2. **Do not go to stage 3 without stage 2.**

## Relationship to the macro pipeline

These 3 stages apply only at **stage 6 (implementation)** among the 10 stages in [protocols/README.md](mdc:protocols/README.md). The stages before and after are as follows.

- Before (design · approval): 1 user → 2 director (Simon) → 3 planning duo (Dominic↔Yuri) → 4 director re-review → 5 human approval.
- After (review · verification · closing): 7 reviewer (Yuri leads, Simon assists) → 8 QA (Tess) → 9 harness (Rex) → 10 final director · wiki.

Reviewer (7) ≠ QA (8) ≠ harness (9). See [protocols/README.md](mdc:protocols/README.md) for the differences among the three axes. The diagram lives in that file only.

## Implementation gate

- Meaningful changes require research docs and plan MD before implementation.
- Simon blocks entry to the 3 stages until a human approves the plan.
- Do not treat breaking this principle as the default, even for small tasks.

## Role–layer (details in `@persona` cards)

| Role | Card | Primary ownership |
|---|---|---|
| Simon | [persona/simon.md](mdc:persona/simon.md) | Distribution · coordination; after completion Tess→Rex |
| Dominic | [persona/dominic.md](mdc:persona/dominic.md) | `domain/` |
| Yuri | [persona/yuri.md](mdc:persona/yuri.md) | `application/` |
| Ada | [persona/ada.md](mdc:persona/ada.md) | `adapters/` (DTO mapping; no business-rule changes) |
| Tess | [persona/tess.md](mdc:persona/tess.md) | `tests/`, `test_*.py` |
| Rex | [persona/rex.md](mdc:persona/rex.md) | `pytest` → `ruff check .` → `mypy django_apps config src` → `black .` |
| Gina | [persona/gina-gui.md](mdc:persona/gina-gui.md) | `interfaces/`, UI |
| Denny | [persona/denny.md](mdc:persona/denny.md) | `django_apps/`, `config/`, Django admin · ORM · importer |

Index: [persona/README.md](mdc:persona/README.md).

## Template example

```text
── Stage 1: Leader briefing + responsibility subsections ──
[Simon] Request summary. Dominic owns domain, Yuri application, Ada adapters, Denny django_apps.

── Stage 2: Assignee briefing + approach ──
[Dominic] I'll start by organizing domain rules.
[Yuri] I'll touch use-case wiring only.
[Denny] Check django.md · database.md. Contract tests first.

── Stage 3: Coding progress ──
[Dominic] (...)
[Yuri] (...)

[Simon] After implementation, hand off to Tess, then Rex in order.
```

## Verification flow (Rex)

After implementation: Tess adds tests → Rex verifies in order: `pytest` → `ruff check .` → `mypy django_apps config src` → `black .`.

- On failure: record the failing command, reason, and next responsible persona.
- If not run: record the command not executed, reason, and remaining risk.
- If `black .` modifies files, report the format change separately from verification results.

## Related Cursor Rules

- [root.mdc](mdc:.cursor/rules/root.mdc)
- [architecture.mdc](mdc:.cursor/rules/architecture.mdc)
- [mcp.mdc](mdc:.cursor/rules/mcp.mdc)
- [cursor-usage.mdc](mdc:.cursor/rules/cursor-usage.mdc)
