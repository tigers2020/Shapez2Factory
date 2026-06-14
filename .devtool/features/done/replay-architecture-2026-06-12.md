---
id: "replay-architecture-2026-06-12"
status: "done"
priority: "medium"
assignee: null
epic: null
dueDate: null
created: "2026-06-12T18:00:00.000Z"
modified: "2026-06-12T19:00:00.000Z"
labels: ["asteroid-lab", "replay", "architecture"]
order: "a3"
---
# Replay system architecture review

## Scope

Holistic `/improve-codebase-architecture` pass on Asteroid Lab replay. **Implemented:** Option A height-layer JS mirror + paint index enrich. Detail: `documents/architecture/replay-architecture/spec.md`.

## Acceptance

- [x] Architecture map documented (write → wire → read → paint → UI)
- [x] Remaining complexity symptoms with evidence
- [x] Deep module candidate + two design options
- [x] Minimal change plan with validation commands
- [x] `spec.md` locked (Option A approved)
- [x] Height layer mirror implemented (`lab_replay_height_layer.js`)
- [x] Paint index + Z filter wired to module
- [x] Overlay harvest registry → JS manifest (`lab_replay_overlay_bucket_registry.js`)

## Artifacts

| Kind | Path | Updated |
|------|------|---------|
| report | documents/architecture/replay-architecture/report.md | 2026-06-12 |
| spec | documents/architecture/replay-architecture/spec.md | 2026-06-12 |
| plan | documents/architecture/replay-architecture/plan.md | 2026-06-12 |

## Progress

- 2026-06-12 — **align → slice** — Review-only architecture report; GRAPH_STALE graph.
- 2026-06-12 — **implement** — Option A approved: `lab_replay_height_layer.js`, template load order, paint plan enrich, lab shell delegate, Python paint mirror, parity tests + node script.
- 2026-06-12 — **verify** — `pytest` 68 passed: height layer slice.
- 2026-06-12 — **implement** — overlay registry JS mirror + paint/lab wiring; pytest 55+ registry/paint/golden.
- 2026-06-12 — **done** — all Acceptance met.
