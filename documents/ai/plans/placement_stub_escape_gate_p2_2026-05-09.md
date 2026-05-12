# placement stub escape gate P2 (2026-05-09)

## 범위

1. **`count_stub_escape_neighbors_after_placement`**  
   `outlet_stub_has_escape_neighbor`와 동일하게, `frozen_outlet_stubs`에만 있고 `reserved_transport`에 없는 이웃은 탈출 degree에 포함하지 않는다.

2. **공용 헬퍼** (`placement.py`)

   - `extension_tree_stub_escape_degree` — 배치 footprint 기준은 `place_tree_bundle`의 `occupied` 인자와 동일(`occupied_for_stub_degree`). 맵 검증용 `scan_occ`과 혼동하지 않는다.
   - `substitute_extension_tree_for_stub_escape` — 기존 `place_tree_bundle` 내부 retree 루프와 동일한 탐색·선호(확장 수 최대).

3. **`_place_scan_pass` (tree 분기)**  
   `substitute_extension_tree_for_stub_escape` 적용 후에도 degree가 0이면 `place_tree_bundle` 호출 전 `continue` + 선택적 trace `placement_stub_escape_reject`.  
   `can_place_extractor_and_outlet`에 `frozen_outlet_stubs=frozenset(outlets_order)`를 넘겨 스캔 단계와 `can_place_tree_bundle` 정책을 맞춘다.

4. **pass2 spine 등**  
   `pass2_spine.py`에는 `place_tree_bundle` 호출이 없다. `solver_service` 내 spine/복구 경로는 기존처럼 `can_place_tree_bundle` 또는 `place_tree_bundle` 내부 substitute에 의존한다.

## 검증

- 단위: `count_stub_escape_neighbors_after_placement` frozen 이웃 제외·reserved 시 포함.
- `pytest` / `ruff` / `black` 변경 파일.

## 관련 문서

- [mining_layout_stub_recovery_2026-05-09.md](mining_layout_stub_recovery_2026-05-09.md)
- [research_merge_repair_not_found_2026-05-09.md](../research/research_merge_repair_not_found_2026-05-09.md) — P2 상류 게이트 한 줄
