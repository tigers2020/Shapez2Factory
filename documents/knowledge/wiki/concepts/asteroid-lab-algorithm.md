---
title: Asteroid Lab Solver Layers (L2–L5)
created: 2026-06-11
updated: 2026-06-11
type: concept
tags: [solver, asteroid-lab, routing, optimization]
sources: [documents/ai/manuals/solver.md, raw/docs-superpowers/specs/2026-06-10-solver-runtime-wires-replay-projection-design.md]
confidence: medium
---

# Asteroid Lab Solver Layers

## Layer stack (source)

| Layer | Role |
|-------|------|
| L2 | Mixed resource plan — what to mine / pump per island |
| L3 | Rim greedy placement — corridor sharing, transport profile |
| L4 | Interior routing — A* / greedy fill, merge groups |
| L5 | Transport routing — space belt/pipe paths, prerequisites |

Solver core lives in `src/shapez2_factory/application/asteroid_lab/layers/`. Django replay/UI projects solver output; **runtime wire is forbidden as algorithm input**.

## Replay projection boundary

- Semantic: frozen dataclasses in `timeline_dtos.py`, `effective_cell_view.py`
- Wire: named `TypedDict` + converters only (`timeline_serialization.py`, `overlay_wire_contract.py`)
- See [[asteroid-lab-wire-typing]] for typing authority map

## Cross-References

- [[transport-system]]: SpaceBelt/SpacePipe layout IDs and capacity bottlenecks
- [[building-definitions]]: miners, pumps, corridors, connectors
- [[asteroid-lab-wire-typing]]: replay wire contracts and mypy rollout
- [[game-data-manifest]]: dump integrity for game-data inputs

## Open (unverified)

- `building-variants`, `island-mechanics`, `transport-capacity` wiki pages not yet synthesized — referenced from raw analysis only.
