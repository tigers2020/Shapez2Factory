# Import Boundary Violations

## Criteria

- canonical refs: `02_pipeline_control_flow.md`, `03_data_schema_dto.md`, `14_step10_replay_ui.md`
- structural scan result: no multi-file SCC inside `django_apps/asteroid_lab`
- existing guard: `tests/unit/asteroid_lab/test_service_import_boundaries.py` only forbids old solver namespace strings

## Major violations

| File | Boundary violation | Root cause | Canonical refs | Severity | Confidence | Action |
|---|---|---|---|---|---|---|
| `django_apps/asteroid_lab/replay/snapshot_map_replay.py` | replay module imports `run_reconstruction(...)` | replay used as transformation host, not output adapter | `14_step10_replay_ui.md` §16, `13_step9_validation.md` | `P1` | High | `split` |
| `django_apps/asteroid_lab/services/cell_snapshot_service.py` | decode frame service indirectly depends on reconstruction via replay helper | decode/replay/reconstruction boundaries not separated | `02_pipeline_control_flow.md`, `14_step10_replay_ui.md` | `P1` | High | `split` |
| `django_apps/asteroid_lab/services/existing_layout_service.py` | inspection service owns replay helper + replay recorder + snapshot reload + reconstruction frame | read-only inspection and replay emission mixed in one service | `03_data_schema_dto.md` §E, `14_step10_replay_ui.md` | `P1` | High | `split` |
| `django_apps/web/services/asteroid_lab_page_context.py` | web adapter effectively defines replay payload fallback rules as canon | serializer seam tuned to UI convenience over solver trace schema | `14_step10_replay_ui.md` §16.3 | `P1` | High | `isolate` |
| `django_apps/web/views/public_pages.py` | web view directly decides replay rebuild policy | application-service boundary too thin | `02_pipeline_control_flow.md` | `P1` | High | `split` |

## Important observations (not violations)

| Observation | Evidence | Meaning |
|---|---|---|
| no old solver namespace runtime import seen | `tests/unit/asteroid_lab/test_service_import_boundaries.py` | no v1/v2 import leakage at string level |
| however canonical/live namespace mismatch is large | live tree is `asteroid_lab`, canonical docs use `shapez_asteroid` / `asteroid_mining_layout_v2` | boundary test does not block largest drift |

## Recommended actions

1. Demote `replay/snapshot_map_replay.py` to `output_projection` layer and remove reconstruction computation calls.
2. Shrink `cell_snapshot_service.py` and `existing_layout_service.py` to emitters that accept pure DTO input only.
3. Web layer calls one `trace payload serializer`; move fallback/merge rules into core serializer.
4. Upgrade import boundary test from string prohibition to AST graph + allowed-edge list verification.
