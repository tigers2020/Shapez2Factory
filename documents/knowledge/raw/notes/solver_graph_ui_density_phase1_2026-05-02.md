# Solver Graph Visibility & Density — Phase 1 Implementation Log

## Status

Phase 1 implemented per user request (plan: Solver graph visibility & density improvements).

## Chosen values

| Item | Value | Notes |
|------|-----|------|
| `NODE_HEIGHT` | 260 | Shape card height; aligned via smaller markup preview & padding |
| `ROW_GAP` | 276 | `NODE_HEIGHT + 16` (prevents vertical overlap) |
| `MULTI_INPUT_SPREAD_GAP` | `round(ROW_GAP * 0.65)` | Eases vertical spread for multi-input predecessor nodes only |
| `COLUMN_STAGGER` | `min(26, floor(COLUMN_GAP * 0.05))` | COLUMN_GAP=270 → 13px; softens horizontal stepping within same rank |
| Edge colors | input: amber family, output: cyan family | Default remains cyan |

## Out of scope (Phase 2)

Operation-node–specific compact layout boxes require heterogeneous sizing in the layout engine and are excluded from this document’s scope.
