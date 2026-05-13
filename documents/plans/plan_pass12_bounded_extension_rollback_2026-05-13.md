# Pass12 preserve: 확장 1칸 bounded rollback (2026-05-13)

## 목적

- `NO_MATCHING_STUB` + `occupied_neighbor_ring` / `extension_carve_disabled`에 가까운 상황에서, **무제한 철거 없이** 출력 스텁 좌표에 깔린 **동일 번들 `extensions` 내 확장 1셀만** 제거한 맵 사본으로 stub-route recovery BFS를 **최대 1회** 재시도한다.
- orphan transport를 goal로 승격하거나 `transport_cells_before` 전체 fallback은 **하지 않는다** (정본 유지).

## 상한·안전

- 제거 후보: `shape_miner_output_cell(miner, r)`가 `extensions`에 속하고 `layout_kind`가 `EXTENSIONS`인 셀만.
- 회전 순서 `_rotation_order`대로 **첫 유효 후보만** 적용(루프당 최대 1셀 carve 시도).
- BFS·신규 transport·경로 길이 기존 상수(`MAX_PASS12_STUB_ROUTE_RECOVERY_*`) 동일.
- 실패 시 기존과 동일하게 drop·trace 유지.

## trace 계약

- 성공: `preserve_stub_recovery.extension_carve_applied` = true, `carved_extension_cell` = `[x,y]`.
- `StubRouteRecoveryResult.carved_extension_cells`: 성공 시에만 비어 있지 않음; 호출부가 `cells`에서 동일 좌표 제거.

## 비범위

- 다중 확장 연쇄 제거, 비인접 확장, Pass2 goal 재정의, STEP4 라우팅 본경로 변경.

## 검증

- `tests/unit/shapez_asteroid/test_pass12_preserve_stub_route_recovery.py`에 carve 성공/무시 케이스.
- 기존 `extension_carve_disabled` 회귀 유지.

## 승인

- 본 문서 합의 후 구현·머지한다.
