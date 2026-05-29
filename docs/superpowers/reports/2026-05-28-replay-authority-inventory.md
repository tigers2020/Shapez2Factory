# Replay Authority Inventory — Central Solver Runtime Assembler

**Date:** 2026-05-28  
**Branch:** (fill at PR open) `feat/central-solver-runtime-replay-assembler`  
**Spec:** [`2026-05-28-central-solver-runtime-replay-assembler-design.md`](../specs/2026-05-28-central-solver-runtime-replay-assembler-design.md)

## Classification legend

| Label | Meaning |
|-------|---------|
| `canonical_owner` | Stays authoritative after reunification |
| `segment_projection` | Logic moves under `replay/layer*_segment.py` |
| `deprecated_wrapper` | Thin delegate or empty stub until removal |
| `forbidden_split_authority` | Must migrate or delete in this work |

## Inventory table

| Path / symbol | Classification | Disposition |
|---------------|----------------|-------------|
| `django_apps/asteroid_lab/replay/event_types.py` | `canonical_owner` | Add L3 event types; sole allowlist |
| `django_apps/asteroid_lab/replay/replay_enums.py` | `canonical_owner` | Add `ReplayEventType` L3 members |
| `django_apps/asteroid_lab/replay/replay_limits.py` | `canonical_owner` | Add `LAYER03_REPLAY_TOP_N`, `MAX_LAYER04_REPLAY_SELECTED` |
| `django_apps/asteroid_lab/replay/timeline_dtos.py` | `canonical_owner` | Wire schema unchanged |
| `django_apps/asteroid_lab/replay/timeline_serialization.py` | `canonical_owner` | JSON round-trip |
| `django_apps/asteroid_lab/replay/lab_timeline_adapter.py` | `canonical_owner` | Host `find_reconstruction_complete_source_frame` |
| `django_apps/asteroid_lab/replay/timeline_composer.py` | `canonical_owner` | Compose Lab + runtime |
| `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py` | `canonical_owner` | Composition entry only |
| `django_apps/asteroid_lab/services/solver_run_config_keys.py` | `canonical_owner` | `solver_runtime_replay_frames` key |
| `django_apps/asteroid_lab/replay/solver_runtime_assembler.py` | `canonical_owner` | **Create** — single runtime assembler |
| `django_apps/asteroid_lab/replay/layer02_segment.py` | `segment_projection` | **Create** — migrate from `lab_layer02_timeline` |
| `django_apps/asteroid_lab/replay/layer03_segment.py` | `segment_projection` | **Create** |
| `django_apps/asteroid_lab/replay/layer04_segment.py` | `segment_projection` | **Create** — migrate from layer `replay.py` |
| `django_apps/asteroid_lab/services/lab_layer02_timeline.py` | `deprecated_wrapper` | Delegate to `layer02_segment` + assembler |
| `django_apps/asteroid_lab/services/lab_layer02_timeline.py::build_layer02_runtime_replay_frames` | `deprecated_wrapper` | Delegate to `build_solver_runtime_replay_frames` |
| `django_apps/asteroid_lab/services/solver_runtime_layer02.py` | `canonical_owner` (caller) | Single write via assembler |
| `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/replay.py` | `forbidden_split_authority` | **Delete** after `layer04_segment` |
| `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/run.py` | `deprecated_wrapper` | `replay_frames=()` only |
| `django_apps/asteroid_lab/layers/contracts/rim_placement.py::replay_frames` | `deprecated_wrapper` | v1 empty tuple; v1.1 remove field |
| `django_apps/asteroid_lab/services/dto.py::ReplayFrameAppendDTO` | `canonical_owner` (Lab ORM) | Not runtime wire owner |
| `django_apps/asteroid_lab/services/replay_recorder.py` | `canonical_owner` (Lab ORM) | ORM append only |
| `django_apps/asteroid_lab/services/replay_service.py` | `canonical_owner` (Lab ORM) | ORM append only |
| `web/*`, `solver_runtime_entry.py` | `canonical_owner` (consumer) | Read composed timeline only |

## Post-migration invariant

```text
Exactly one module orders runtime replay frames: replay/solver_runtime_assembler.py
Segment modules never read prior frame lists; they receive base_map_view from the assembler only.
```
