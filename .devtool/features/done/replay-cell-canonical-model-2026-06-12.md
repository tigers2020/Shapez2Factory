---
id: "replay-cell-canonical-model-2026-06-12"
status: "done"
priority: "medium"
assignee: null
epic: null
dueDate: null
created: "2026-06-12T00:00:00.000Z"
modified: "2026-06-12T12:00:00.000Z"
completedAt: null
labels: ["asteroid-lab", "replay", "architecture", "ui"]
order: "a2"
---
# Replay cell canonical model (EffectiveCellView v2)

## Scope

Close the gap between **raw map_view wire rows** and **one canonical cell read-model** for Lab detail UI and paint. Evolve existing `EffectiveCellView` merge (do not fork a parallel authority). Formalize raw evidence bag; add `overlay_role` + output requirement semantics; UI shows canonical only; raw in collapsed debug.

**Epic relation:** Builds on `replay-cell-semantics` (done) and `replay-sprite-visibility` (paint path). Does not reopen sanitizer / harvest delete scope.

## Acceptance

- [x] Merge captures overlay semantic kinds (`inner_field_block`, etc.) as `overlay_role`; `output_transport_kind` on non-occupant overlays → `output_requirement`
- [x] Frame 38 / inner_field_block fixture: canonical view matches architect example (terrain + overlay + output requirement; no spurious rotation/simulation)
- [x] Detail panel: canonical sections only; raw `map_view_*` keys in collapsed Sources
- [x] `effectiveCellViewDisplaySections` hides empty/default placeholders from primary panel
- [x] Paint index stops reading `overlay_role` from `sources` hack (`overlayRoleFromWireSources`) — role lives on merged view
- [x] Python + JS merge parity tests updated

## Artifacts

| Kind | Path |
|------|------|
| design (chat) | user contract 2026-06-12 |
| canon (evolve) | `effective_cell_view.py`, `lab_effective_cell_view.js` |
| spec (pending) | `documents/architecture/replay-cell-canonical-model/spec.md` |

- [x] Slice C: `buildDomPlanForCell` → `applyDomPlanToCell`; v2 render path canonical-only

## Progress

- 2026-06-12 — **done** — Slices A–C: merge authority, canonical detail UI, DOM plan render path
