# Replay / Runtime Coupling

## canonical baseline

- `14_step10_replay_ui.md` §16: replay is trace/output/UI layer
- `13_step9_validation.md`: validation is assertion gate
- `03_data_schema_dto.md` §E: existing layout analysis is read-only context

## Current coupling evidence

| File | Coupling evidence | Root cause | Risk severity | Confidence | Action |
|---|---|---|---|---|---|
| `django_apps/asteroid_lab/replay/snapshot_map_replay.py` | replay module calls `run_reconstruction(...)` | algorithm projection pushed into replay utility | `P1` | High | `split` |
| `django_apps/asteroid_lab/services/cell_snapshot_service.py` | decode frame recording depends on `build_cleanup_and_reconstruction_rows(...)` | decode frame emission coupled to replay projection | `P1` | High | `split` |
| `django_apps/asteroid_lab/services/existing_layout_service.py` | inspection replay recording performs snapshot rebuild + reconstruction overlay + issue filtering | inspection read-model mixed with replay emitter | `P1` | High | `split` |
| `django_apps/web/services/asteroid_lab_page_context.py` | serializer rewrites UI contract by combining fallback/full_map/diff/summary | no canonical trace serializer | `P1` | High | `isolate` |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | UI independently interprets `full_map`, `cell_overlay_json`, `diff`, issue overlays | rendering concern absorbs payload semantics | `P1` | High | `split` |

## Core problem

Replay is not “runtime output” but a middle layer that pulls runtime computation and shapes it for display. In this structure:

- replay changes entangle with reconstruction behavior
- UI fallback masks backend contract drift
- hard to move to canonical `trace_event` / `computation_cycle` / streaming rules

## Early-phase prohibitions

Do not touch these before replay coupling separation:

- `django_apps/asteroid_lab/reconstruction/pipeline.py`
- `django_apps/asteroid_lab/reconstruction/fill.py`
- `tests/unit/asteroid_lab/test_reconstruction_topology.py`

## Recommended separation direction

1. pure runtime
   - `reconstruction/*`
   - `snapshots/existing_layout_inspection.py`
2. projection adapter
   - snapshot DTO → replay frame rows
3. persistence adapter
   - replay row append / snapshot row save
4. UI serializer
   - persisted row → canonical API payload

## Related test gaps

- no test that replay module does not import runtime
- no `trace_event` schema alignment test
- no `computation_cycle` / streaming cadence test
