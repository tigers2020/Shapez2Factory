---
id: "replay-overlay-display-b2-2026-06-12"
status: "done"
priority: "medium"
assignee: null
epic: null
dueDate: null
created: "2026-06-12T18:00:00.000Z"
modified: "2026-06-12T18:00:00.000Z"
completedAt: null
labels: ["asteroid-lab", "replay", "ui"]
order: "a3"
---
# Replay overlay cells — B2 display fix

## Scope

`candidate_route_path` / other overlay semantic kinds must not render as **Machine** in cell detail (e.g. `(17,9,L2)` SpaceBelt route preview). Align `wireCellKind` empty-string handling with Python.

## Acceptance

- [x] `candidate_route_path` with belt tile → Overlay + Transport (not Machine)
- [x] `candidate_miner` / `candidate_transport_stub` → Overlay path (not Machine)
- [x] `shape_miner_extension` still → Machine
- [x] JS contract tests updated

## Progress

- 2026-06-12: User screenshot `(17,9,L2)` map_view_client_only — Machine mislabel; implement display + wireCellKind parity.
- 2026-06-12: Diagnostics panel (sprites, wire kind, provenance); removed redundant Source wires dump.
