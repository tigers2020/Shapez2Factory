# `documents/archive/`

완료·폐기·대체·보관 문서를 모아 둔다. 현재 구현 판단은 archive가 아니라 [`documents/index/document_inventory.md`](../index/document_inventory.md)와 `CANON` 문서를 우선한다.

## Archive buckets

| 하위 경로 | 상태 | 설명 |
|------|------|------|
| [`2026-05-mining-layout-v1-era/`](2026-05-mining-layout-v1-era/README.md) | `ARCHIVED` | v1 `asteroid_mining_layout` 시대의 계획, refactory, Algorithm root 메모, 일부 report/research/ai plan 묶음. 현재 구현 권위는 v2 경로와 canonical session specs다. |
| [`2026-05-completed/`](2026-05-completed/README.md) | `COMPLETED` | 2026-05에 완료 처리된 Python 정리·Recipe Graph Editor 계열 문서 묶음. |
| [`completed-implementation/`](completed-implementation/README.md) | `COMPLETED` | 구현 반영이 끝난 `plan_*`/`research_*` 1:1 pair를 stem별로 보관한다. |
| [`obsolete-src-shapez2-solver-plans-2026-05-01/`](obsolete-src-shapez2-solver-plans-2026-05-01/) | `ARCHIVED` | Django-first 전환 전 `src/shapez2_solver` 기준의 오래된 계획 초안. |

## 2026-05-15 archive 판정

- 새 파일 이동은 하지 않았다. 최근 v2 작업(`documents/ai/plans/mining_solver_v2_mvp_execution_2026-05-13.md`, `documents/ai/ACTIVE_v2_dto_slice_reconstruction.md`, `documents/Algorithm/mining_solver_cursor_sessions/`, `documents/reports/2026-05/`)은 아직 현재 작업 판단에 필요하므로 `ACTIVE`, `CANON`, `REPORT`로 남긴다.
- v1-era 묶음은 계속 `ARCHIVED`다. 참조가 필요하면 [`2026-05-mining-layout-v1-era/README.md`](2026-05-mining-layout-v1-era/README.md)를 통해 읽고, 현재 구현 계약으로 승격하지 않는다.
- 구현 완료 여부가 명확하지 않은 `documents/plans/` 문서는 active/backlog로 유지한다. archive 이동은 검증 결과나 완료 보고가 있는 stem만 대상으로 한다.

상위 지도는 [`../README.md`](../README.md)를 우선한다.
