---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: A
pr: 1B
related_docs:
  - documents/Algorithm/solver_runtime/phase_b_optimization_input.md
  - documents/Algorithm/solver_runtime/00_core_principles.md
---

# Phase A ? Load Reconstruction Map

## Purpose

Load the reconstruction result stored in the DB as solver input.

## Input

```text
Reconstruction map full_map
cell rows
bbox
existing layout metadata
resource kind metadata
```

## Output

```text
LoadedReconstructionSnapshot
```

## Tasks

1. Query the project's latest reconstruction map
2. Load `full_map` / `bbox` / cell kind
3. Separate existing extractor / extension / belt / pipe coordinates
4. If raw blueprint coordinates are missing, normalize to server coord **only at adapter boundary**

## Forbidden

- raw X/Y conversion inside optimization interior
- Direct modification of DB original cell kind
- Installing actual equipment using server x/y coordinates ([`00_core_principles.md`](00_core_principles.md) §0.1)

## Completion criteria

- [ ] `LoadedReconstructionSnapshot` preserves bbox·width·height·metadata
- [ ] extractor/extension/transport coordinates separated so they do not pass through adapter incorrectly
- [ ] raw?server conversion does not occur outside adapter

## Prerequisite phase

PR1B adapter·OptimizationInput integration phase ? see [`implementation_sequence.md`](implementation_sequence.md) § PR1B and [`phase_b_optimization_input.md`](phase_b_optimization_input.md).

## Related code·documents

- `django_apps/asteroid_lab/adapters/` (decode/reconstruction adapter)
- [`asteroid_lab_01_optimization_input.md`](../asteroid_lab_01_optimization_input.md) ? Sequence 1B

## Next Phase

? [`phase_b_optimization_input.md`](phase_b_optimization_input.md)
