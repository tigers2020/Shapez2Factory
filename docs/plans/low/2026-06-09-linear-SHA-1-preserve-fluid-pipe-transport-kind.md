# Plan: SHA-1 - Preserve fluid_pipe transport_kind (Low: integration verification)

## Source

- Linear issue: https://linear.app/zkaufman/issue/SHA-1
- Priority: Low
- Labels: bug, solver, spec
- Status at planning time: Todo

## Problem

After unit-level fixes, solver integration on mixed shape/fluid fixtures should be verified to ensure transport tags survive the full L3 run stack.

## Scope

- Run solver smoke on a mixed-shape-fluid fixture and confirm transport tags in output artifacts.

## Non-goals

- New solver features or L5 work.

## Implementation Plan

1. Identify or add a mixed-shape-fluid slug/fixture suitable for L3 smoke.
2. Run `python manage.py run_solver --slug <slug>` and inspect provisional overlay / replay output for correct `transport_kind` per placement.
3. Document fixture slug and expected transport tags in test or runbook note if none exists.

## Files / Areas Likely Affected

- Solver fixture data under `tests/` or `fixtures/`
- Optional smoke documentation in `docs/runbooks/`

## Tests / Validation

- `python manage.py run_solver --slug <mixed-transport-slug>`

## Acceptance Criteria

- [ ] Solver integration confirms fluid placements retain `FLUID_PIPE` through full L3 run

## Risks

- Fixture availability; may need minimal fixture addition if none exists.

## Human Review Required

- no
- reason: Verification-only follow-up after core fix lands.

## Automation Notes

Generated from Linear Todo issue by planning automation.

Depends on Mid-priority DTO/replay work completing first.
