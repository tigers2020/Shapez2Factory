# Hermes Skill Suggestion Workflow

Canon: `AGENTS.md` § Cursor ↔ Hermes. Routers: `.cursor/rules/00-hermes-skill-suggestion.mdc`, `.cursor/rules/01-hermes-handoff-format.mdc`.

## Canonical Shapez2 agent pipeline

```text
Problem
→ Authority / contract check
→ Cursor Plan Mode
→ grill-me-shapez2 (only when domain/contract ambiguity exists)
→ PLAN_TO_SKILL_REQUEST
→ Hermes research + SKILL_SUGGESTION
→ Cursor implementation (approved skill only)
→ SKILL_APPLICATION_SUMMARY
→ optional SKILL_IMPROVEMENT_REQUEST
```

Use `/grill-me-shapez2` only when:

- Shapez2 domain contract is ambiguous
- solver or factory behavior changes
- algorithmic route, throughput, or validation changes
- user explicitly asks for adversarial review

Skip grill for: approved CANON-only work, clear regression with reproducer, rename/lint/format, tasks under ~5 minutes.

If grill and Hermes disagree: **surface the conflict to the user** — do not silently pick one.

User may explicitly skip Hermes; user explicit instruction wins over this workflow.

## Role split

**Cursor:** codebase analysis, plans, code, tests, summaries.

**Hermes:** research standards/libraries/algorithms; check project skills; suggest implementation skill; draft `SKILL.md`; surface better approaches. **Not** a plan APPROVE/BLOCK gate.

## Non-trivial workflow

1. Cursor Plan Mode first.
2. Do not implement immediately.
3. Produce `PLAN_TO_SKILL_REQUEST` (template: `hermes-handoff.md`).
4. Wait for Hermes `SKILL_SUGGESTION`.
5. Apply **human-reviewed approved** skill during implementation (`skill-trust-boundary.md`).
6. Send `SKILL_APPLICATION_SUMMARY`; `SKILL_IMPROVEMENT_REQUEST` if needed.

## Cursor must not

- treat Hermes as implementer or write production code via Hermes
- ask Hermes only for APPROVE/BLOCK
- skip research for new algorithms, libraries, standards, or complex design
- install dependencies without justification
- modify unrelated files
- treat unreviewed Hermes output as operational skill

## Trivial exception

Skip only for typo-only markdown or local scratch notes.

Never skip for: Python, Django, models/views/forms/serializers/services/tasks, tests, migrations, settings, dependencies, algorithms, performance-sensitive or security-sensitive code.

## Validation

Use commands from `AGENTS.md` § Validation only. Do not invent generic commands (`pytest`, `mypy .`, etc.) unless listed there.
