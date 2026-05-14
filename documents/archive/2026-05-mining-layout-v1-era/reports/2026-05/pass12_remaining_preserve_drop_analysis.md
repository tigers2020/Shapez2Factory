# Pass12 남은 preserve stub 드롭 분석 (2026-05)

## 범위

- **관측**: Tier D 복구가 유효한 운영 케이스에서도 `extractor_drop_count`가 남고, `solver_quality_tier`는 API 호환을 위해 `PARTIAL_SUCCESS_VALID_PRESERVE_LOSS`로 유지되는 흐름을 정리한다.
- **증거**: 본 문서의 **원문 JSON 붙여넣기**는 `var/asteroid_mining_layout_debug/latest.ndjson`(run `ceaa1731e164`, `pass12_completed` 이벤트)에서 추출했다. 이 파일의 `preserve_missing_stub_summary.drop_count`는 **10**이며, 아래 **「인용 생산 스냅샷」** 의 `drop_count=2`, `tier_d` 9/8과 **동일 런이 아니다**. 생산 2건의 `miner_cell` 등은 **해당 생산 NDJSON**으로 대조해야 한다.

## 인용 생산 스냅샷 (이슈 입력, 레포 외부)

| 필드 | 값 |
|------|---|
| `original_extractor_count` | 67 |
| `final_extractor_count` | 65 |
| `extractor_drop_count` | 2 |
| `preserve_missing_stub_summary.drop_count` | 2 |
| `preserve_missing_stub_summary.bounded_recovery.tier_d_attempted_count` | 9 |
| `preserve_missing_stub_summary.bounded_recovery.tier_d_success_count` | 8 |
| `preserve_missing_stub_summary.unrecoverable_drop_count` | 2 |
| `preserve_missing_stub_summary.expected_unrecoverable_drop_count` | 2 |
| `preserve_missing_stub_summary.recoverable_unresolved_drop_count` | 0 |
| `preserve_missing_stub_summary.unrecoverable_reason_counts.no_legal_same_kind_route_under_bounds` | 2 |
| `solver_quality_tier` | `PARTIAL_SUCCESS_VALID_PRESERVE_LOSS` |
| `solver_quality_subtier` | `EXPECTED_UNRECOVERABLE_PRESERVE_LOSS_ONLY` |
| `degradation_causes` (요지) | `preserve_missing_stub_drop`, `internal_transport_above_pass2_baseline` |

**검증·주장 한계**: 위 생산 수치는 **새 생산 NDJSON**으로만 재검증한다. 레포에 보관된 `latest.ndjson`만으로는 `drop_count=2` 런을 복원할 수 없다.

## 남은 2건 — 열 계약 표 (`report_pass12_preserved_missing_stub_drop_details`)

아래 2행은 **증거 `latest.ndjson`의 `pass12_preserved_missing_stub_drop_details[0]`, `[1]`** 을 `report_pass12_preserved_missing_stub_drop_details`로 평탄화한 값이다. 스키마·Tier D·repack 필드 확인용이며, **생산 2드롭 좌표와 동일함을 주장하지 않는다.**

| # | `miner_cell` | `transport_kind` | `preserve_drop_reason` | `recoverability_class` | `rejected_reason_subtype` | `nearest_same_kind_transport_hops` | `tier_d_attempted` | `tier_d_success` | `tier_d_skip_reason` | `tier_d_failure_reason` | `output_repack_candidate_count` | `output_repack_selected_rotation` | `unrecoverable_reason` (`pass12_unrecoverable_contract_reason_code`) |
|---:|---|---|---|---|---|---:|---|---|---|---|---:|---|---|
| 1 | `[-2, -7]` | `fluid_pipe` | `NO_MATCHING_STUB` | `NEAR_TRANSPORT` | `occupied_neighbor_ring` | 5 | `true` | `false` |  | `tier_d_failed_no_same_kind_route` | 26 |  | `no_legal_same_kind_route_under_bounds` |
| 2 | `[-3, -3]` | `fluid_pipe` | `NO_MATCHING_STUB` | `NEAR_TRANSPORT` | `occupied_neighbor_ring` | 5 | `true` | `false` |  | `tier_d_failed_no_same_kind_route` | 49 |  | `no_legal_same_kind_route_under_bounds` |

**생산 2건과의 정합(요약만)**: 인용 생산에서 `unrecoverable_drop_count=2`이고 `unrecoverable_reason_counts['no_legal_same_kind_route_under_bounds']=2`이면, 위 표의 **마지막 열**이 생산 각 행에서도 동일 버킷이어야 한다. 행별 `tier_d_*` 합이 `bounded_recovery`의 9/8과 어떻게 맞는지는 **생산 `preserve_stub_recovery` 원문**으로만 확정한다.

### 원문 행 붙여넣기 (`pass12_preserved_missing_stub_drop_details` 요소)

증거 파일 `latest.ndjson` — **요소 0** (10-drop 런). 생산 2-drop 런과 동일하지 않을 수 있다.

```json
{"miner_cell":[-2,-7],"reason":"NO_MATCHING_STUB","preserve_drop_reason":"NO_MATCHING_STUB","transport_kind":"fluid_pipe","expected_stub_role":"pipe","pass12_merged_seed_miner_count":67,"nearest_same_kind_transport_hops":5,"nearest_same_kind_transport_cell":[-3,-11],"recoverability_class":"NEAR_TRANSPORT","preserve_stub_recovery":{"tier_d_attempted":true,"tier_d_success":false,"tier_d_skip_reason":null,"tier_d_failure_reason":"tier_d_failed_no_same_kind_route","output_repack_candidate_count":26,"output_repack_selected_rotation":null,"rejected_reason_subtype":"occupied_neighbor_ring","rejected_reason":"no_same_kind_route"}}
```

증거 파일 `latest.ndjson` — **요소 1** (10-drop 런).

```json
{"miner_cell":[-3,-3],"reason":"NO_MATCHING_STUB","preserve_drop_reason":"NO_MATCHING_STUB","transport_kind":"fluid_pipe","expected_stub_role":"pipe","pass12_merged_seed_miner_count":67,"nearest_same_kind_transport_hops":5,"nearest_same_kind_transport_cell":[-8,-3],"recoverability_class":"NEAR_TRANSPORT","preserve_stub_recovery":{"tier_d_attempted":true,"tier_d_success":false,"tier_d_skip_reason":null,"tier_d_failure_reason":"tier_d_failed_no_same_kind_route","output_repack_candidate_count":49,"output_repack_selected_rotation":null,"rejected_reason_subtype":"occupied_neighbor_ring","rejected_reason":"no_same_kind_route"}}
```

(전체 원문은 NDJSON `pass12_completed` → `data.pass12_stats.pass12_preserved_missing_stub_drop_details` 배열 요소와 동일하다. 위는 가독성을 위해 축약한 코어 필드만 남긴 사본이다.)

## 도구 (알고리즘 입력 아님)

- `django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_merged_layout_seed.report_pass12_preserved_missing_stub_drop_details`
  - 인자: `pass12_preserved_missing_stub_drop_details` 리스트(또는 동일 스키마의 dict 시퀀스).
  - 각 행에 대해: `miner_cell`, `transport_kind`, `nearest_same_kind_transport_hops`, `nearest_same_kind_transport_cell`, `recoverability_class`, `preserve_drop_reason`, `rejected_reason_subtype`, `adjacent_cardinal_cells`, `rotation_probe_summary`, `preserve_stub_recovery.*` Tier D·repack 필드, `stub_route_probe_last.blocked_frontier_reason_counts`, `pass12_remaining_drop_classification`, `pass12_unrecoverable_contract_reason_code`를 평탄화해 반환한다.
- `classify_pass12_remaining_preserve_drop_row` / `_unrecoverable_contract_reason_code`: 상세 필드만으로 3분류·비복구 사유 버킷을 채운다 (NDJSON 역주입 없음).

## 합성 예시 (단위 테스트 픽스처)

- **대각 전용 extension**: `tier_d_skip_reason == tier_d_skipped_diagonal_only_extension_topology` → `pass12_unrecoverable_contract_reason_code = diagonal_only_extension_topology`, 분류 `unrecoverable_by_design` ([`plan_pass12_bounded_output_reorientation_repack_2026-05-13.md`](../../plans/plan_pass12_bounded_output_reorientation_repack_2026-05-13.md) §4-neighbor).
- **Tier D 시도 후 BFS 한계**: `tier_d_failure_reason`에 `tier_d_failed_no_same_kind_route` 등 → `no_legal_same_kind_route_under_bounds`, 분류 `unrecoverable_by_design`.

## 요약 계약 (`preserve_missing_stub_summary`)

- `unrecoverable_drop_count`, `unrecoverable_reason_counts`: `_preserve_missing_stub_summary_from_details`에서 위 버킷 규칙으로 집계된다.
- `expected_unrecoverable_drop_count`: `unrecoverable_drop_count`와 동일한 **안정 별칭**(대시보드·NDJSON 비교용).
- `recoverable_unresolved_drop_count`: `max(0, drop_count - unrecoverable_drop_count)` — 계약 비복구로 잡히지 않았으나 여전히 드롭으로 남은 건수.
- `solver_quality_subtier == EXPECTED_UNRECOVERABLE_PRESERVE_LOSS_ONLY`: `drop_count > 0` 이고 `unrecoverable_drop_count == drop_count`일 때만 설정된다. **`solver_quality_tier`는 변경하지 않는다.**

## Pass2 / `final_goal_count == 0`

- 장비 셸·margin 0·orphan 미승격 등 **문서화된 기하**이면 `final_goal_count == 0`은 유효할 수 있다 ([`plan_pass2_first_route_external_goal_alignment_2026-05-13.md`](../../plans/plan_pass2_first_route_external_goal_alignment_2026-05-13.md) §감사 판정, `test_external_predicate_equipment_shell_alignment.py` 보강).
