---
id: "replay-canvas-mapz-filter-2026-06-12"
status: "done"
priority: "medium"
assignee: null
epic: null
dueDate: null
created: "2026-06-12T20:00:00.000Z"
modified: "2026-06-12T20:00:00.000Z"
labels: ["asteroid-lab", "replay", "ui"]
order: "a4"
---
# Replay canvas Map Z filter

## Scope

Apply Height layer (L) picker filter to canvas sprite paint path (`buildLabPaintPlanFromFrame`). Terrain/DOM already filtered; sprite canvas showed L=0 floor field sprites on L=1/L=2 selection.

## Acceptance

- [x] `selectedMapZLayer` passed from lab shell to paint plan
- [x] `buildLabPaintPlanFromFrame` skips wires outside selected plane
- [x] Python parity helper + unit tests
- [x] Contract tests on JS paint plan + buildCanvasPaintPlan

## Progress

- 2026-06-12 — **implement** — `effectiveWirePassesMapZFilter` in paint plan; lab.js passes `labMapZSelectedLayer`.
- 2026-06-12 — **verify** — pytest 53+ pass; enriched-row coord universe fix.
- 2026-06-12 — **done**
