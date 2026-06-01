---
name: shapez2-workflow
description: >-
  Spec-first · Small PR · Test-gated workflow checklist for shapez2 Factory Planner.
  Contract brief, PR plan, scoped agent tasks, dual gate. Invoke via /shapez2-workflow or @shapez2-workflow.
disable-model-invocation: true
---

# shapez2 Workflow (integrated harness)

Canonical: [`AGENTS.md`](../../../AGENTS.md) · [`.cursor/rules/workflow.mdc`](../../rules/workflow.mdc) · [`protocols/README.md`](../../../protocols/README.md)

Templates: [`contract-brief.md`](../../../documents/ai/templates/contract-brief.md) · [`pr-plan.md`](../../../documents/ai/templates/pr-plan.md)

## Before start

- [ ] Work type: `django` · `solver` · `asteroid_lab` · `frontend` · `tests` · `refactor` · `database`
- [ ] Open matching manual only ([`AGENTS.md` domain routing](../../../AGENTS.md))
- [ ] Link **CANON spec** or fill contract brief
- [ ] Declare **Position · Authority · Acceptance · Stop conditions**
- [ ] Minimize `@` scope; new thread per PR purpose

## Contract gate

- [ ] Problem · Goal · Non-goals · Contract · Acceptance written
- [ ] Human approval for non-trivial contract changes
- [ ] Superseded docs **not** used as authority

## PR scope

- [ ] **One purpose** (audit · contract docs · acceptance tests · implement · cleanup)
- [ ] Acceptance tests from spec on HEAD before production (contract/regression)

## Implementation order

```text
audit (optional) → acceptance tests from spec → minimal fix → regression/golden → gates → doc sync
```

## Verification (dual gate)

**Iteration:**
```bash
python -m pytest <narrow path>   # no -q / --quiet / --tb=no
python -m ruff check <paths>
```

**PR full gate:**
```bash
powershell -File scripts/test_full.ps1
ruff check .
mypy django_apps config src
black --check .
```

Close: caveman six sections ([`shapez2-core.mdc`](../../rules/shapez2-core.mdc)).

## Skills by PR phase

| Phase | Skill |
|-------|--------|
| Pre-spec · branching design | `grill-me-shapez2` (optional; read-only) |
| PR-3 tests only | `write-tests` |
| CLI touch | `cli-boundary` |
| Pre-merge review | `quality-check` |
| Public contract changed | `doc-update` |

## References

- [`testing.md`](../../../documents/ai/manuals/testing.md)
- [`cursor_usage.md`](../../../documents/ai/manuals/cursor_usage.md)
- [`asteroid-lab-invariants.mdc`](../../rules/asteroid-lab-invariants.mdc)
- Position lenses: [`persona/README.md`](../../../persona/README.md)
