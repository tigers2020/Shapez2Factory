# Algorithm 문서

알고리즘·Lab 계약 메모를 모아 둔다. **구현 정본**은 코드·[`documents/index/document_inventory.md`](../index/document_inventory.md)의 `CANON`·[`documents/ai/START_HERE.md`](../ai/START_HERE.md)를 우선한다.

## 구현 베이스라인 (2026-05-22)

| 레이어 | 상태 | 코드 |
|--------|------|------|
| **Reconstruction** | **ACTIVE** | `django_apps/asteroid_lab/reconstruction/`, `cleanup/`, Lab persist·replay |
| **Optimization / Solver runtime** | **REMOVED** | `django_apps/asteroid_lab/optimization/` 삭제; `solver_runtime_entry`는 `SOLVER_NOT_AVAILABLE` 스텁만 |
| **Genetic sample (admin)** | **ACTIVE** | `django_apps/asteroid_lab/genetic_sample/` |
| **Game data snapshot** | **ACTIVE** | `django_apps/asteroid_lab/contracts/game_data_snapshot.py` |

**Surgery spec:** [`docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md`](../../docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md)

## Solver Runtime (ARCHIVED)

**상태:** 2026-05-22 제거. Phase C–M·PR3–7 계약은 역사 보관.

- **인덱스:** [`solver_runtime/README.md`](solver_runtime/README.md) (`status: ARCHIVED`)
- **충돌 해소 (역사):** [`solver_runtime/ARCHITECTURE_RECONCILIATION.md`](solver_runtime/ARCHITECTURE_RECONCILIATION.md)
- **HTTP 진입 (스텁):** [`solver_runtime/01_entry_point.md`](solver_runtime/01_entry_point.md) → `run_solver_runtime_for_project` → `SOLVER_NOT_AVAILABLE`

## 읽기 순서 (reconstruction-first)

1. [`asteroid_lab_00_overview.md`](asteroid_lab_00_overview.md) — 개요·좌표·금지 사항  
2. Reconstruction·cleanup·topology — `reconstruction/` 코드 + [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md) (Lab replay **ACTIVE**)  
3. **Legacy optimization 시리즈** `asteroid_lab_01`–`08` — `RESEARCH` / 역사 참고만 (구현 삭제됨)  
4. [`asteroid_lab_10_development_sequence.md`](asteroid_lab_10_development_sequence.md) — 시퀀스 체크리스트 (미갱신 항목 다수)  
5. **삭제된 solver 버튼:** `solver_runtime/phase_*` — 모두 `ARCHIVED`

## 파일 목록

| 파일 | 상태 | 설명 |
|------|------|------|
| `asteroid_lab_00_overview.md` | `RESEARCH` | Lab·좌표 원칙 |
| `asteroid_lab_01`–`08` | `ARCHIVED` | Optimization layer (코드 없음) |
| `asteroid_lab_09_replay_timeline.md` | `ACTIVE` | Lab Step Replay Timeline |
| `asteroid_lab_09_replay_debug.md` | `ARCHIVED` | dual-track 역사 |
| `asteroid_lab_10`–`13` | `RESEARCH` | 로드맵·배선 |
| [`solver_runtime/`](solver_runtime/) | `ARCHIVED` | Solver 버튼 Phase A–M (2026-05-22 제거) |
| [`plans/asteroid_lab_optimization/`](plans/asteroid_lab_optimization/README.md) | `ARCHIVED` | 2026-05 이전 optimization 플랜 복사본 |

## 경로·패키지 주의

- **`django_apps/shapez_asteroid`** · **`asteroid_lab/optimization/`** — 저장소에서 제거됨. 문서 인용은 역사적.
- Gene template·coord: **`genetic_sample/`** · grid: **`snapshots/grid_contract.py`**
- 교차 확인: [`documents/refactor_audit/00_global_summary.md`](../refactor_audit/00_global_summary.md)

새 알고리즘 정본은 `documents/ai/` 플랜·`document_inventory.md` 갱신 후 추가한다.
