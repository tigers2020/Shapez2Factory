---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: ??
pr: ??PR
related_docs:
  - documents/Algorithm/solver_runtime/README.md
  - documents/Algorithm/asteroid_lab_00_overview.md
  - .cursor/rules/asteroid-lab-invariants.mdc
---

# ?µì‹¬ ?ì¹™ (Â§0)

Solver Runtime ??Phase??ê³µí†µ?¼ë¡œ ?ìš©?œë‹¤.

## 0.1 ?¤ì¹˜?˜ë©´???ìƒ‰?˜ì? ?ŠëŠ”??

**ê¸ˆì?:**

```text
server x/y ?œì„œ?€ë¡??¤ì œ extractor / extension / belt / pipe ?¤ì¹˜
```

**?ˆìš©:**

```text
server x/y ?œì„œ?€ë¡?deterministic candidate enumeration
```

ì¢Œí‘œ ?œì„œ??**?„ë³´ ?ì„± ?œì„œ**??ë¿?**commit ?œì„œê°€ ?„ë‹ˆ??**

**CONFIRMED ?´í›„ ?ˆìš©:** [`phase_k2_placement_materialization.md`](phase_k2_placement_materialization.md) ??commit ?±ê³µ placement + route reservation??`MaterializedLayoutCells`ë¡??¹ê²© (replayÂ·validation ì¶œë ¥). enumerationÂ·probe ?¨ê³„??ì¦‰ì‹œ ?¤ì¹˜?€ êµ¬ë¶„?œë‹¤.

## 0.2 ?¸ê³½ void???¤ì œ ëª©í‘œ belt/pipeë¥?ë¨¼ì? ?¤ì¹˜?˜ì? ?ŠëŠ”??

**ê¸ˆì?:**

```text
void???„ì˜ belt/pipeë¥?ë¨¼ì? ?¤ì¹˜?˜ê³  ê±°ê¸°ë¡?ëª¨ë‘ ?°ê²°
```

**?ˆìš©:**

```text
external void / margin / existing trunkë¥?RouteGoalë¡??ì„±
```

?¤ì œ transport materialization?€ **commit ?´í›„** route network ?´ì„ ?¨ê³„?ì„œ ?˜í–‰?œë‹¤. ([`phase_k_route_materialization.md`](phase_k_route_materialization.md))

## 0.3 Reconstruction map ë¡œë“œ ì§í›„ extension kindë¥?fieldë¡??•ê·œ??

DB reconstruction map?€ miner extension kindë¥??ë³¸ ê·¸ë?ë¡?ë³´ì¡´?????ˆë‹¤. Solver runtime 1ì°?ê³µì •?€ optimization??**field kind**ë¡?ë³€?˜í•œ??

```text
shapeMinerExtension / Layout_ShapeMinerExtension
??asteroid_shape_field

fluidMinerExtension / Layout_FluidMinerExtension
??asteroid_fluid_field
```

- ë³€?˜ì? **DB ?ë³¸???˜ì •?˜ì? ?ŠëŠ”??**
- ê²½ê³„: `LoadedReconstructionSnapshot ??OptimizationInput` **adapter**?ì„œë§??˜í–‰.

Optimizer??ë³€???´í›„ ?¤ìŒ ì§‘í•©???•ë³¸?¼ë¡œ ?¬ìš©?œë‹¤.

```text
OptimizationInput.asteroid_cells
OptimizationInput.mineable_cells
OptimizationInput.rim_cells
OptimizationInput.external_void_cells
OptimizationInput.route_goals
OptimizationInput.route_domain
```

ê·œì¹™:

```text
asteroid_shape_field ??asteroid_cells + mineable_cells
asteroid_fluid_field ??asteroid_cells + mineable_cells
```

extension ?ë³¸ kind??resource/evidence ?©ë„ë¡?**ë³´ì¡´ ê°€??*.

**ê¸ˆì? (optimizer ?´ë?):**

```python
# candidate_geometry / route_probe ?´ë??ì„œ ì§ì ‘ kind ?ì • ê¸ˆì?
cell.kind == "shapeMinerExtension"
cell.kind == "fluidMinerExtension"
cell.kind == "asteroid_fluid_field"
cell.kind == "asteroid_shape_field"
```

kind ?ì •?€ adapter 1ì°??•ê·œ??ì±…ì„?´ë©°, optimizer ?´ë???`asteroid_cells` / `mineable_cells` ì§‘í•©ë§?ë³¸ë‹¤.

## 0.4 ëª¨ë“  candidate??route probeë¥??µê³¼?´ì•¼ normal pool???¤ì–´ê°„ë‹¤

```text
projected gene
??geometry validation
??route probe
??reachable=True only normal_candidates
```

unreachable candidate??diagnostic / rejected candidateë¡œë§Œ ?¨ê¸´??

## 0.5 Candidate phase reachable?€ commit successê°€ ?„ë‹ˆ??

commit ?œì ?ëŠ” ??ƒ **ìµœì‹  route domain**?¼ë¡œ ?¤ì‹œ probe?œë‹¤.

```text
candidate probe success ??final commit success
```

?ì„¸: [`phase_j_incremental_commit.md`](phase_j_incremental_commit.md).

## 0.6 ì¢Œí‘œ ?©ì–´ (Runtime ?•ë³¸, alias ê¸ˆì?)

| ?´ë¦„ | ?˜ë? |
|------|------|
| `fixed_output_transport` | extractor ì§í›„ **ì²?belt/pipe** ?€ (canonical E?ì„œ offset `(1,0)`) |
| `route_probe_start` | route search **?œì‘** ?€ (offset `(2,0)`; `occupied_offsets`??**?¬í•¨ ê¸ˆì?**) |
| `output_stub` | **?ˆê±°??* ??? ê·œ DTOÂ·?¨ìˆ˜Â·ë¬¸ì„œ ?„ë“œëª…ìœ¼ë¡?**?¬ìš© ê¸ˆì?** |

`CandidateRejectReason.output_stub_*` enum ë©¤ë²„ ?´ë¦„?€ **ê¸°ì¡´ enum ?¸í™˜??*?´ë©° ?˜ë???`route_probe_start`?´ë‹¤.

## 0.7 ? ê·œ ?ŒìŠ¤?¸Â·ë¬¸??ëª…ëª… (reject / geometry)

| ë²”ìœ„ | ê·œì¹™ |
|------|------|
| **? ê·œ pytest ?¨ìˆ˜ëª?* | `route_probe_start_*` Â· `fixed_output_transport_*` ??`output_stub_*` **?¬ìš© ê¸ˆì?** |
| **? ê·œ ë¬¸ì„œ ë³¸ë¬¸Â·ì£¼ì„** | `route_probe_start` ?•ë³¸ ([Â§0.6](#06-ì¢Œí‘œ-?©ì–´-runtime-?•ë³¸-alias-ê¸ˆì?)) |
| **ê¸°ì¡´ enum ê°?* | `output_stub_inside_occupied` ??**rename ê¸ˆì?** (?˜ìœ„ ?¸í™˜); assert??enum ê°’Â·ì˜ë¯?ë§¤í•‘?¼ë¡œ ê²€ì¦?|

?? `test_geometry_rejects_route_probe_start_inside_occupied` (O) Â· `test_geometry_rejects_output_stub_inside_occupied` (? ê·œ ì¶”ê? X).

?ì„¸: [`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) Â§4 Â· [`open_decisions.md`](open_decisions.md) OD-1.

## ì¢Œí‘œÂ·replay (êµì°¨ ì°¸ì¡°)

- OptimizationInput ?´í›„ ëª¨ë“  `Coord` = **Server X/Y** only. raw?”server ?¬ë??˜ì? optimization ?´ë? ê¸ˆì?.
- ReplayÂ·NDJSONÂ·metrics??**algorithm input ê¸ˆì?**.

[`asteroid_lab_00_overview.md`](../asteroid_lab_00_overview.md) Â· [`.cursor/rules/asteroid-lab-invariants.mdc`](../../../.cursor/rules/asteroid-lab-invariants.mdc)
