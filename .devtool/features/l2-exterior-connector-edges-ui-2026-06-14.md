---
status: verify
modified: 2026-06-14
---

# L2 exterior connector edge picker + rim contiguous placement

## Scope

User request: Lab UI cardinal direction (N/E/S/W) picker; L2 places connectors on selected map edges at rim (depth-1 void), side-by-side in one-cell contiguous rows.

## Acceptance

- [x] UI sidebar N/E/S/W toggles; POST `exterior_connector_edges`
- [x] Config wired Django → CLI → run_stack → L2
- [x] L2 uses exterior lane slots (bbox +12 offset, spacing 2) on allowed edges only — not rim-adjacent
- [x] Unit tests for edges filter + contiguous placement + CLI arg
- [x] Targeted pytest green (82 passed)

## Progress

- 2026-06-14 — implement rim slots, contiguous placement, UI + wire chain
- 2026-06-14 — verify — `pytest tests/unit/asteroid_lab/layers/test_layer_02_*` + subprocess + UI strings: 82 passed
