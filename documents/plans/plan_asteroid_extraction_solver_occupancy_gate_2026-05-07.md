# 소행성 솔버 occupancy 결정 게이트 (2026-05-07)

## 승안

플랜의 **결정 게이트 2번(MVP)** 을 채택한다.

- 디코드에 “순수 암석” 전용 레이어가 없을 수 있음([research](../research/research_shapez2_asteroid_extraction_2026-05-07.md)).
- **`mineable_placement_cells`**: 채굴 분류 좌표(추출관련 건물 점유) ∪ 형태학 패치 내부(`compute_patch_interior_cells(shell)`) 에서 **`PlotStyle.belt` / `pipe` 좌표를 제외** 한 집합.
- **`blueprint_occupied_cells`**: `BP`의 `Entries` 등에서 **`X ≠ 0` 인 모든 블루프린트 점유**(바운딩·스타일 분류·패치 계산에 사용). **라우팅 hard block이 아니다** — rebuild 모드에서는 전부 삭제 대상이다.
- **`legacy_transport_cells`**: 디코드된 벨트/파이프 좌표의 합집합. **메타·마스킹용**이며, rebuild 라우팅 기본값에서는 경로 장애물로 넣지 않는다.
- **`transport_hard_block_cells`**: rebuild 라우팅에서 실제 벽으로 취급할 명시적 좌표 집합. MVP 기본값은 빈 집합이며, 라우팅 중에는 새로 배치한 코어/익스텐션 footprint만 동적으로 hard block에 더한다.
- **`routed_transport_cells`**: 이미 만든 벨트/파이프 경로는 hard block이 아니라 soft trunk 후보이다. 벨트는 같은 방향 재사용을 선호하고, 역방향 edge만 충돌로 막는다.

“전 구조물 제거 후 암석만” 모델(게이트 1)은 블루프린트 `T` 신뢰가 확보되면 후속 단계에서 전환 검토한다.

## 구현 정본 코드

[`django_apps/shapez_asteroid/services/asteroid_reconstruction.py`](../../django_apps/shapez_asteroid/services/asteroid_reconstruction.py)의 `reconstruct_from_decoded` 결과 DTO가 위 정의를 구현한다.

**후속(추출 파이프라인, 마스크 정의 불변)**: 빔 `BEAM_HARD_CAP`/커버리지 점수, `route_extractor_outputs` 벨트·파이프 분기, `solve_pipeline` 파이프 연결 검증, fluid 시 `cheap_transport_escape_exists(..., transport_kind="pipe")`.
