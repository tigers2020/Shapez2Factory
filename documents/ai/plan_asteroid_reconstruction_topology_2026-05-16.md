---
status: ACTIVE
owner: asteroid-lab
last_reviewed: 2026-05-16
supersedes: []
superseded_by: []
related_epics: []
---

# Asteroid Lab: topology-only reconstruction (정본)

## 목적

디코드된 맵에서 **건물(운송·채굴기·익스텐션) 제거 후 빈칸**을 `internal_void`가 아니라, **외부 void와의 연결 여부 + 보수적 enclosure 가드**로만 판정해 `asteroid_*_field`로 채운다.

## 모듈 경계

- **전처리(cleanup)**: `django_apps/asteroid_lab/cleanup/` — strippable 제거, **`wall_coords`** 산출 (replay/솔버 공통 입력으로 확장 가능)
- **토폴로지 복원**: `django_apps/asteroid_lab/reconstruction/` — `cleaned_cells` + `wall_coords` + `bbox_bounds`만 받아 fill (스냅샷 DTO 비의존)
- **Replay 직렬화**: `django_apps/asteroid_lab/replay/` — `deconstruction_frames` / `reconstruction_frames` + `snapshot_map_replay` orchestration

## `wall_coords` 계약

- `wall_coords`는 “디코드된 소행성 타일만”이 아니라 **flood-fill 기준 topology barrier** 집합이다.
- cleanup에서 제거된 **extractor / extension 좌표**는 `wall_coords`에 포함한다.
- **belt / pipe** 좌표는 제거 목록(`ignored_transport`)에만 남기고 **`wall_coords`에는 넣지 않는다**.
- walkable 빈 칸과 `wall_coords`는 별개: 제거된 채굴기 자리는 맵 row에 없을 수 있어도 플러드에서는 벽으로 취급한다.

## 데이터 (reconstruction 입력)

- `cleaned_cells` + `wall_coords` + `bbox_bounds` (+ server 좌표·핑거프린트는 [`../research/research_asteroid_server_coords_layout_fingerprint_2026-05-16.md`](../research/research_asteroid_server_coords_layout_fingerprint_2026-05-16.md) 참고)
- **fill 종(shape/fluid)**: MVP에서는 디코드에 남은 `asteroid_*_field` 및 기존 다수결만 사용; 제거된 채굴기 타입으로 fill 결정하지 않음 (`field_vote_hints` 없음)

## Reconstruction 단계 (flood 전·후)

1. `close_diagonal_leaks(wall_coords)` — Chebyshev(L∞) pinhole만: **evidence walls 입력만**; strict wall-bbox **내부** 셀은 봉인하지 않음 (내부 hole 유지)
2. `barrier = wall_coords ∪ diagonal_closed`
3. `external_reachable` — **4-neighbor** flood from padded bbox border
4. `interior = walkable - external` → component fill — 가드는 **`passes_bbox_interior`만**
5. `stamp_islands_uniform` — 최종 `asteroid_*_field`

- bbox margin flood에 닿는 1칸 void(좁은 외부 통로·분리선 포함)는 **external** — fill 하지 않음
- flood 미도달 void만 **interior_patch** 후보

- topology graph / routing adjacency: **4-neighbor** (`neighbors4_server`) — closing morphology와 분리

## 금지

- 최종 `full_map`에 `internal_void`
- filled hole 전용 디버그 overlay
- replay 로그·summary·제거 타입을 fill 판정 입력으로 사용
- **orthogonal 1-cell slit sealing** 전역 적용 (`close_orthogonal_one_cell_slits`를 pipeline에서 호출)
- **inferred shell / sealed slit / diagonal close** 결과를 fill 후보로 재주입 (morphology → interior union)
- **추론 shell·봉인 결과**를 다음 morphology pass의 opposing solid로 재사용 (recursive closure)

## 검증

- `tests/unit/asteroid_lab/test_reconstruction_topology.py`
- `tests/unit/asteroid_lab/test_reconstruction_regression_overclose.py` (fixture `regression_narrow_external_channels.txt`)
- `tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py` — `reconstruction_required_.txt` ↔ `reconstruction_complete_solved.txt` **라인별** Server X/Y topology (solved는 decode-only)
- `test_replay_snapshot_contract.py`

## Confidence / acceptance (실전)

- `django_apps/asteroid_lab/reconstruction/confidence.py` — `confirmed_cells`, `ambiguous_cells`, `confidence_score`, `quality_tier`
- 실전 통과: `ambiguous_ratio ≤ 0.05`, `confidence_score ≥ 0.95`, `reconstruction_acceptance_ok(result)` (`CONFIDENT_RECONSTRUCTION`)
- solved fixture는 **정답률**이 아니라 calibration(overlap 리포트)용만 — `test_reconstruction_canon_line_confidence_calibration`
