---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: M
pr: 7
related_docs:
  - documents/Algorithm/asteroid_lab_09_replay_debug.md
  - documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md
  - documents/Algorithm/solver_runtime/01_entry_point.md
---

# Phase M ??Persist / Replay / UI Payload

## ëª©ì 

solver ê²°ê³¼ë¥?DB?€ UI??ë°˜ì˜?œë‹¤. Lab replay?€ optimization replay??**?”ë¬µ ?™ê¸°?”í•˜ì§€ ?ŠëŠ”??**

> **PR7 = ?¬êµ¬??ê¸ˆì?:** [`asteroid_lab_12_runtime_replay_wiring.md`](../asteroid_lab_12_runtime_replay_wiring.md) ??persist/read/validation/HUD(12F??2L ??ë¥?**?¬ì‘?±í•˜ì§€ ?ŠëŠ”??** Runtime Phase M ?´ë²¤?¸ëŠ” ê¸°ì¡´ writer/reader??**thin adapter**ë¡œë§Œ ?°ê²° ([`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) Â§6).

## ?…ë ¥

```text
ValidationResult
MaterializedLayoutCells
optimization run metrics
replay frames (accumulated)
```

## ?°ì¶œë¬?

```text
SolverRun.config_json (optimization_replay_frames, solver_summary, ??
UI: optimization replay track + layout preview
```

## ?‘ì—…

### Persist (ê¸°ì¡´ ê²½ë¡œ ?¬ì‚¬??

```text
SolverRun.config_json          # ê¸°ì¡´ Lab persist ê³„ì•½
optimization_replay_frames     # ê¸°ì¡´ frame list validatorÂ·truncation ?•ì±… ?¬ì‚¬??
solver_summary
materialized_layout preview
validation_result
```

? ê·œ: Runtime orchestration ??**ê¸°ì¡´** attach/read API ?¸ì¶œ + `OptimizationReplayEventType` (`django_apps/asteroid_lab/optimization/enums.py`) ì¤?Runtime ?„ìˆ˜ subset ê¸°ë¡.

### Replay ?„ìˆ˜ ?´ë²¤??

```text
optimization.input_loaded
capacity.plan_created
route_goal.generated
pattern.generated
candidate.generated
candidate.rejected
route_probe.succeeded
route_probe.failed
candidate_pool.completed
candidate_selection.completed
route.commit_attempted
route.committed
route.rolled_back
route.materialized
validation.completed
```

`OptimizationReplayEventType` enum ??algorithm input ê¸ˆì?.

### UI

```text
Lab replay = map rendering authority
Optimization replay = metadata / overlay observation
No implicit sync
```

## ê¸ˆì?

- replayÂ·NDJSONë¥?solver/GA ?…ë ¥?¼ë¡œ ?¬ìš©
- Lab timelineê³?optimization frame index ?”ë¬µ ?™ê¸°??([`asteroid_lab_09`](../asteroid_lab_09_replay_debug.md) dual-track)

## ?„ë£Œ ì¡°ê±´

- [ ] persist ??`solver_run_id`Â·replay payload ì¡°íšŒ ê°€??
- [ ] ?´ë²¤???œì„œ deterministic
- [ ] UI??optimization track attach (Lab ?˜ì´ë¡œë“œ ë¹„ë???

## ?„ìˆ˜ ?ŒìŠ¤??

```text
test_solver_button_pipeline_persists_result
test_solver_button_pipeline_emits_replay_events
test_solver_button_pipeline_validation_read_only
test_solver_button_pipeline_no_implicit_lab_optimization_sync
```

## ê´€??ì½”ë“œÂ·ë¬¸ì„œ

- [`django_apps/web/views/public_pages.py`](../../../django_apps/web/views/public_pages.py)
- [`asteroid_lab_12_runtime_replay_wiring.md`](../asteroid_lab_12_runtime_replay_wiring.md)
- [`asteroid_lab_13_replay_payload_scalability.md`](../asteroid_lab_13_replay_payload_scalability.md)

## ?¤ìŒ Phase

?†ìŒ (?Œì´?„ë¼??ì¢…ë£Œ). ì§„ì…: [`01_entry_point.md`](01_entry_point.md).
