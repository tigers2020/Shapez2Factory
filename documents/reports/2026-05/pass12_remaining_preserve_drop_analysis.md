# Pass12 남은 preserve stub 드롭 분석 (2026-05)

## 범위

- **관측**: 운영 NDJSON에서 `extractor_drop_count == 2`, Tier D가 8건 성공했으나 `quality_tier`는 여전히 `PARTIAL_SUCCESS_VALID_PRESERVE_LOSS`인 상황을 전제로 한다.
- **본 문서**: 이 워크스페이스에는 **해당 2건의 `pass12_preserved_missing_stub_drop_details` 원문 행이 첨부되어 있지 않다.** 따라서 생산 좌표·셀 단위 분류 표는 **비워 두고**, 분류에 쓸 **필드 계약·도구·합성 예시**만 기록한다.
- **추측 금지**: 아래 “생산 2건” 표는 NDJSON 행을 붙인 뒤 `report_pass12_preserved_missing_stub_drop_details` 출력으로 채운다.

## 도구 (알고리즘 입력 아님)

- `django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_merged_layout_seed.report_pass12_preserved_missing_stub_drop_details`
  - 인자: `pass12_preserved_missing_stub_drop_details` 리스트(또는 동일 스키마의 dict 시퀀스).
  - 각 행에 대해: `miner_cell`, `transport_kind`, `nearest_same_kind_transport_hops`, `nearest_same_kind_transport_cell`, `recoverability_class`, `preserve_drop_reason`, `rejected_reason_subtype`, `adjacent_cardinal_cells`, `rotation_probe_summary`, `preserve_stub_recovery.*` Tier D·repack 필드, `stub_route_probe_last.blocked_frontier_reason_counts`, `pass12_remaining_drop_classification`, `pass12_unrecoverable_contract_reason_code`를 평탄화해 반환한다.
- `classify_pass12_remaining_preserve_drop_row` / `_unrecoverable_contract_reason_code`: 상세 필드만으로 3분류·비복구 사유 버킷을 채운다 (NDJSON 역주입 없음).

## 생산 2건 분류 표 (NDJSON 붙인 후 작성)

| # | miner_cell | pass12_unrecoverable_contract_reason_code | pass12_remaining_drop_classification | 비고 |
|---|------------|-------------------------------------------|--------------------------------------|------|
| 1 | *(미기입)* | *(미기입)* | *(미기입)* | `report_pass12_preserved_missing_stub_drop_details` 한 행을 그대로 붙여 채운다. |
| 2 | *(미기입)* | *(미기입)* | *(미기입)* | 동일. |

## 합성 예시 (단위 테스트 픽스처)

- **대각 전용 extension**: `tier_d_skip_reason == tier_d_skipped_diagonal_only_extension_topology` → `pass12_unrecoverable_contract_reason_code = diagonal_only_extension_topology`, 분류 `unrecoverable_by_design` ([`plan_pass12_bounded_output_reorientation_repack_2026-05-13.md`](../../plans/plan_pass12_bounded_output_reorientation_repack_2026-05-13.md) §4-neighbor).
- **Tier D 시도 후 BFS 한계**: `tier_d_failure_reason`에 `tier_d_failed_no_same_kind_route` 등 → `no_legal_same_kind_route_under_bounds`, 분류 `unrecoverable_by_design`.

## 최소 수정(Phase 2) 적용 여부

- 생산 NDJSON의 두 행이 없어 **코드 경로의 추가 최소 수정은 적용하지 않았다.** `recoverable_with_small_fix`는 필드 불일치·누락 텔레메트리 등 **증거가 있는 경우에만** 해당한다.

## 기대 손실 요약(`preserve_missing_stub_summary`)

- `unrecoverable_drop_count`, `unrecoverable_reason_counts`는 `_preserve_missing_stub_summary_from_details`에서 위 버킷 규칙으로 집계된다. 운영에서 두 드롭이 모두 설계 비복구로 분류되면 `unrecoverable_drop_count == 2`와 사유별 카운트가 맞아야 한다.

## Pass2 / `final_goal_count == 0`

- 장비 셸·margin 0·orphan 미승격 등 **문서화된 기하**이면 `final_goal_count == 0`은 유효할 수 있다 ([`plan_pass2_first_route_external_goal_alignment_2026-05-13.md`](../../plans/plan_pass2_first_route_external_goal_alignment_2026-05-13.md) §감사 판정, `test_external_predicate_equipment_shell_alignment.py` 보강).

## 검증

- NDJSON로 **드롭 수가 줄었음을 주장하지 않는다.** 변경 후에도 `extractor_drop_count`는 **새 생산 NDJSON**으로만 확인한다.
