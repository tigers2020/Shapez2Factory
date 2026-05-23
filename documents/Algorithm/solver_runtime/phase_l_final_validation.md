---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: L
pr: 7
related_docs:
  - documents/Algorithm/asteroid_lab_08_validation.md
  - documents/adr/ADR-003-final-validation-assertion-gate.md
---

# Phase L ??Final Validation

## ëª©ì 

ìµœì¢… layout??solver contractë¥?ë§Œì¡±?˜ëŠ”ì§€ **read-only**ë¡?ê²€ì¦í•œ??

## ?…ë ¥

```text
MaterializedLayoutCells
confirmed placements
RouteReservation(s)
OptimizationInput (final)
```

## ?°ì¶œë¬?

```python
ValidationResult(
    passed=True/False,
    issues=...,
)
```

## ?‘ì—…

ê²€ì¦???ª©:

```text
all extractor outputs connected
all route reservations reach valid RouteGoal
no orphan transport
no invalid overlap
transport kind consistency
reserved_cells match path
confirmed candidate has exactly one confirmed reservation
capacity violation ?†ìŒ
```

`ValidationIssueCode` ??**enum**ë§??¬ìš© ???ìœ  ë¬¸ì??ê¸ˆì?.

## ê¸ˆì?

Validation?€ ?¤ìŒ???˜ì? ?ŠëŠ”??

```text
new route ?ì„±
placement ?˜ì •
topology ?˜ì •
```

## ?„ë£Œ ì¡°ê±´

- [x] `passed=False` ??`issues`??êµ¬ì¡°?”ëœ ì½”ë“œë§?
- [x] validation??layout/route/topologyë¥?ë³€ê²½í•˜ì§€ ?ŠìŒ
- [x] confirmed ???¨ì¼ CONFIRMED reservation ?¼ì¹˜

## ?„ìˆ˜ ?ŒìŠ¤??

PR7 ??`test_solver_button_pipeline_validation_read_only` ([`implementation_sequence.md`](implementation_sequence.md)).

## ê´€??ì½”ë“œÂ·ë¬¸ì„œ

- [`asteroid_lab_08_validation.md`](../asteroid_lab_08_validation.md)
- ADR-003 (validation gate)

## ?¤ìŒ Phase

??[`phase_m_persist_replay_ui.md`](phase_m_persist_replay_ui.md)
