# Protocols — Spec-first workflow stages

Single reference for [`AGENTS.md`](../AGENTS.md) and [`.cursor/rules/workflow.mdc`](../.cursor/rules/workflow.mdc). Do not duplicate this pipeline elsewhere.

## Workflow stages

| Stage | Name | Owner | Output |
|---|---|---|---|
| 1 | Problem | Human | One-line problem + non-goals |
| 2 | Contract | Human (+ agent draft) | [`contract-brief.md`](../documents/ai/templates/contract-brief.md) or spec amendment |
| 3 | PR plan | Human (+ agent draft) | [`pr-plan.md`](../documents/ai/templates/pr-plan.md) — **one purpose per PR** |
| 4 | Approval | **Human** | Scope locked — no production edits before this for non-trivial contract changes |
| 5 | Audit | Agent (read-only) | Current behavior vs contract — optional when spec is clear |
| 6 | Failing tests | Agent | New tests fail on current HEAD when behavior must change |
| 7 | Implementation | Agent (scoped) | Minimal production diff for **this PR only** |
| 8 | Gate | Agent + CI | Focused pytest → ruff; PR: full gate |
| 9 | Review | Human | Contract impact · rollback · next PR |
| 10 | Merge + observe | Human | Merge; update ACTIVE plan; retrospective if needed |
| 11 | Doc sync | Agent (when asked) | CANON spec / ADR / runbook when public contract changed |

Small, obvious fixes may collapse stages 1–4 into the task prompt. **Contract changes never skip stage 2 or 6.**

## Review · QA · harness (three lenses)

Same work, different questions — not three mandatory chat personas.

| Lens | Question |
|---|---|
| **Review** | Does the diff match the contract? Scope creep? Invariant violations? |
| **QA (tests)** | Failing test existed first? Golden/invariant coverage? Regression guarded? |
| **Harness (tools)** | pytest · ruff · mypy · black green? |

Position cards map habits: [tess.md](../persona/tess.md) (tests), [rex.md](../persona/rex.md) (harness). No scripted dialogue required.

## Implementation gate

Agent **BLOCKED** when:

- No contract brief for behavior change
- No failing test before production fix (regression / contract change)
- PR scope > one contract change or one refactor goal
- Superseded doc used as authority

Human approval (stage 4) required for non-trivial contract changes before production edits.

## PR sequencing example

```text
PR-1: audit (read-only)
PR-2: contract docs
PR-3: failing tests only
PR-4: implementation
PR-5: cleanup
```

## Related files

- [AGENTS.md](../AGENTS.md)
- [workflow.mdc](../.cursor/rules/workflow.mdc)
- [shapez2-core.mdc](../.cursor/rules/shapez2-core.mdc)
- [Position index](../persona/README.md)
- Plan examples: [`docs/superpowers/plans/`](../docs/superpowers/plans/)
