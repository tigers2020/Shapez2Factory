# 0-extension 채굴기 배치 억제 (구현 정본, 2026-05-09)

## 목표

긴 파이프를 Pass3에서 줄이기 전에, **trunk에서 멀리 떨어진 단독(0-extension) 번들**을 placement 단계에서 걸러낸다.

## 컨텍스트별 `min_extensions`

| 컨텍스트 | 값 | 비고 |
|----------|---:|------|
| pass2_spine | 1 | `_place_pass2_spine_phase` |
| pass2_scan | 2 | `_place_scan_pass("pass2")` |
| pass3_scan | 2 | `_place_scan_pass("pass3")` |
| recovery (rail_reloc 등) | 0 | 좁은 공간 생존 |
| `_build_opportunity_score` | 0 (기본) | 슬롯 추정 왜곡 방지 — 호출부 변경 금지 |

상수: `solver_service.MIN_EXTENSIONS_PASS2_SPINE`, `MIN_EXTENSIONS_PASS2_SCAN`, `MIN_EXTENSIONS_PASS3_SCAN`, `MIN_EXTENSIONS_RECOVERY`.

## 0-extension 예외

`placement.stub_outlet_on_or_adjacent_to_transport(out_pos, transport_cell_keys)` — 아울렛이 기존 transport 칸 위이거나 4-인접.

호출부는 `solver_service._transport_touch_predicate(transport_cells)` 로 콜백 조립.

## 랭킹

- `_place_scan_pass`: `rank_key = (-n_ext, ma, -ext_on_boundary, dir_rank[d], ti)`
- `select_best_extension_tree_for_pass2`: `inner = (-n_extensions, ma, -ext_on_boundary, ti)`
- trace: `select_best_extension_tree_for_pass2` exit에 `ranking: extension_count_first`

## Trace 키 (relaxed selector)

- `below_min_extensions`
- `zero_extension_rejected_not_trunk_adjacent`
- 성공 시 옵션: `zero_extension_gate` = `zero_extension_trunk_adjacent_allowed`

## P1 — marginal route · ROI (placement 게이트)

아울렛에서 **anchor 또는 기존 transport**까지 맨해튼 하한(`shapez_manhattan`)을 marginal로 두고, extension 수별 상한과 coarse ROI로 추가 거른다.

| 상수 | 의미 |
|------|------|
| `MAX_MARGINAL_ROUTE_MANHATTAN_BY_EXT` | 0→1, 1→3, 2→6, 3→12 |
| `PRODUCTION_SCORE_PER_SLOT_BLOCK` | 슬롯 블록당 100 (`1+n_extensions` 블록) |
| `ROUTE_COST_PER_MANHATTAN_UNIT` | marginal당 8 |
| `MIN_PLACEMENT_ROI_SCORE_BY_PASS` | pass2→80, pass3→160 |

함수: `_marginal_route_manhattan_to_trunk`, `_bundle_placement_roi_score`, `_placement_p1_roi_gate_ok`.

적용 위치:

- `_place_scan_pass` 트리 번들 루프: 방향별 `chosen_tree` 확정 후 `rank_key` 전 (`roi_pass_key=pass_name`).
- `_place_pass2_spine_phase` 후보 배치 직전 (`roi_pass_key="pass2"`, trace `placement_p1_rejected`, `context: pass2_spine`).

튜닝 시 위 상수와 함께 단위 테스트·실맵 회귀를 다시 본다.

## P2 (선택, 미구현)

routing 전 low-ROI 번들 prune — 별도 플랜.
