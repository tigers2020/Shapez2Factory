---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: A
pr: 1B
related_docs:
  - documents/Algorithm/solver_runtime/phase_b_optimization_input.md
  - documents/Algorithm/solver_runtime/00_core_principles.md
---

# Phase A ??Load Reconstruction Map

## ëª©ì 

DB???€?¥ëœ reconstruction ê²°ê³¼ë¥?solver ?…ë ¥?¼ë¡œ ë¡œë“œ?œë‹¤.

## ?…ë ¥

```text
Reconstruction map full_map
cell rows
bbox
existing layout metadata
resource kind metadata
```

## ?°ì¶œë¬?

```text
LoadedReconstructionSnapshot
```

## ?‘ì—…

1. project??ìµœì‹  reconstruction map ì¡°íšŒ
2. `full_map` / `bbox` / cell kind ë¡œë“œ
3. ê¸°ì¡´ extractor / extension / belt / pipe ì¢Œí‘œ ë¶„ë¦¬
4. raw blueprint ì¢Œí‘œê°€ ?¨ì•„ ?ˆìœ¼ë©?**adapter boundary?ì„œë§?* server coordë¡??•ê·œ??

## ê¸ˆì?

- optimization ?´ë??ì„œ raw X/Y ë³€???¸ì¶œ
- DB ?ë³¸ cell kind ì§ì ‘ ?˜ì •
- server x/y ?œì„œ?€ë¡??¤ì œ ?¤ë¹„ ?¤ì¹˜ ([`00_core_principles.md`](00_core_principles.md) Â§0.1)

## ?„ë£Œ ì¡°ê±´

- [ ] `LoadedReconstructionSnapshot`??bboxÂ·?€ ?‰Â·ë©”?€?°ì´?°ë? ë³´ì¡´
- [ ] extractor/extension/transport ì¢Œí‘œê°€ adapterë¡??˜ê¸¸ ???ˆê²Œ ë¶„ë¦¬??
- [ ] raw?’server ë³€?˜ì´ adapter ë°–ì—??ë°œìƒ?˜ì? ?ŠìŒ

## ?„ìˆ˜ ?ŒìŠ¤??

PR1B ??adapterÂ·OptimizationInput ?µí•© ?ŒìŠ¤?¸ëŠ” [`implementation_sequence.md`](implementation_sequence.md) Â§ PR1B ë°?[`phase_b_optimization_input.md`](phase_b_optimization_input.md) ì°¸ì¡°.

## ê´€??ì½”ë“œÂ·ë¬¸ì„œ

- `django_apps/asteroid_lab/adapters/` (decode/reconstruction adapter)
- [`asteroid_lab_01_optimization_input.md`](../asteroid_lab_01_optimization_input.md) ??Sequence 1B

## ?¤ìŒ Phase

??[`phase_b_optimization_input.md`](phase_b_optimization_input.md)
