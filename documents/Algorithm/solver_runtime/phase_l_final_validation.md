---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: L
pr: 7
related_docs:
  - documents/Algorithm/asteroid_lab_08_validation.md
  - documents/adr/ADR-003-final-validation-assertion-gate.md
---

# Phase L ? Final Validation

## Purpose

**Read-only** verification that final layout satisfies solver contract.

## Input

```text
MaterializedLayoutCells
confirmed placements
RouteReservation(s)
OptimizationInput (final)
```

## Output

```python
ValidationResult(
    passed=True/False,
    issues=...,
)
```

## Tasks

Validation scope:

```text
all extractor outputs connected
all route reservations reach valid RouteGoal
no orphan transport
no invalid overlap
transport kind consistency
reserved_cells match path
confirmed candidate has exactly one confirmed reservation
no capacity violation
```

`ValidationIssueCode` ? **enum only**; free-form strings forbidden.

## Forbidden

Validation must not:

```text
create new route
modify placement
modify topology
```

## Completion criteria

- [x] `passed=False` ? `issues` has structured codes only
- [x] validation does not change layout/route/topology
- [x] each confirmed has exactly one CONFIRMED reservation match

## Prerequisite phase

PR7 ? `test_solver_button_pipeline_validation_read_only` ([`implementation_sequence.md`](implementation_sequence.md)).

## Related code?documents

- [`asteroid_lab_08_validation.md`](../asteroid_lab_08_validation.md)
- ADR-003 (validation gate)

## Next Phase

? [`phase_m_persist_replay_ui.md`](phase_m_persist_replay_ui.md)
