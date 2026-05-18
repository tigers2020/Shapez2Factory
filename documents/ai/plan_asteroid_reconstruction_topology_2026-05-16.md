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

디코드된 맵에서 **건물(운송·채굴기·익스텐션) 제거 후 빈칸**을 `internal_void`가 아니라, **bbox border 4-neighbor exterior flood + strict bbox interior**로만 판정해 `asteroid_*_field`로 채운다.

## 모듈 경계

- **전처리(cleanup)**: `django_apps/asteroid_lab/cleanup/` — strippable 제거, **`wall_coords`** 산출 (replay/솔버 공통 입력으로 확장 가능)
- **토폴로지 복원**: `django_apps/asteroid_lab/reconstruction/` — `cleaned_cells` + `wall_coords` + `bbox_bounds`만 받아 fill (스냅샷 DTO 비의존)
- **Replay 직렬화**: `django_apps/asteroid_lab/replay/` — `deconstruction_frames` / `reconstruction_frames` + `snapshot_map_replay` orchestration

## `wall_coords` 계약

- `wall_coords`는 “디코드된 소행성 타일만”이 아니라 **flood-fill 기준 topology barrier** 집합이다.
- cleanup에서 제거된 **extractor / extension 좌표**는 `wall_coords`에 포함한다.
- **belt / pipe** 좌표는 제거 목록(`ignored_transport`)에만 남기고 **`wall_coords`에는 넣지 않는다**.
- walkable 빈 칸과 `wall_coords`는 별개: 제거된 채굴기 자리는 맵 row에 없을 수 있어도 플러드에서는 벽으로 취급한다.

## Flood barrier · interior fill

1. `barrier_xy = wall_coords ∪ infer_shell_barrier_coords` (행·열 span closure)
2. **Chebyshev diagonal perimeter closing** (`perimeter_closing.chebyshev_close_barrier`) — 대각 barrier 쌍 사이 코너 1칸을 seal; `_strict_bbox_interior_cells(wall_coords)` 안은 건너뜀 (내부 hole 오판 방지)
3. `walkable = padded_bbox \ barrier_xy`; `external` = border seed 4-neighbor flood on `walkable`
4. `interior_patch = walkable - external`; **strict bbox interior** 컴포넌트는 전부 fill (two-axis evidence guard 없음)
5. topology graph / routing 이웃은 **4-neighbor** (`neighbors4_server`) — closing은 flood 차단 전용

## 데이터 (reconstruction 입력)

- `cleaned_cells` + `wall_coords` + `bbox_bounds` (+ server 좌표 변환용 파라미터)
- **fill 종(shape/fluid)**: MVP에서는 디코드에 남은 `asteroid_*_field` 및 기존 다수결만 사용; 제거된 채굴기 타입으로 fill 결정하지 않음 (`field_vote_hints` 없음)

## 금지

- 최종 `full_map`에 `internal_void`
- filled hole 전용 디버그 overlay
- replay 로그·summary·제거 타입을 fill 판정 입력으로 사용

## 검증

- `tests/unit/asteroid_lab/test_reconstruction_topology.py` 등 단위 + `test_replay_snapshot_contract.py` 갱신
