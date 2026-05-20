---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-20
phase: K2
pr: —
related_docs:
  - documents/Algorithm/solver_runtime/phase_k_route_materialization.md
  - documents/Algorithm/asteroid_lab_07_incremental_commit.md
---

# Phase K2 — Confirmed Placement Materialization

## 목적

Incremental Commit이 **CONFIRMED** 한 extractor·extension 점유를 Phase K transport materialization과 **동일한** `MaterializedLayoutCells` 산출물에 승격한다.

## 입력

```text
IncrementalCommitResult.confirmed
Mapping[candidate_id, GeneCandidate]
Mapping[gene_id, GeneTemplate]  # extension_attachments for R
```

## 산출물

`MaterializedLayoutCells.equipment_cells` — `shape_miner` / `fluid_miner` / `*_extension` + `tile_type` (`Layout_*`).

## 파이프라인 순서

```text
materialize_route_network
→ materialize_confirmed_placements
→ merge_materialized_layout  # rejects equipment∩transport coord overlap
```

## 금지

- candidate generation / route probe 단계 layout commit ([§0.1](00_core_principles.md) — enumeration 중 설치)
- `fixed_output_transport` 셀에 miner 배치 (occupied_offsets에 transport 없음)

## 완료 조건

- [x] CONFIRMED마다 extractor + extensions가 equipment_cells에 포함
- [x] extension R은 `GeneTemplate.extension_attachments` + server 4-neighbor ports
- [x] replay `cell_delta`에 equipment + transport 동시 기록
- [x] `validate_final_layout` — `placement_not_materialized` issue

## 관련 코드

- `placement_network_materializer.py`
- `solver_runtime_pipeline.py`
- `replay_recording_cells.materialized_cells_to_cell_delta`
