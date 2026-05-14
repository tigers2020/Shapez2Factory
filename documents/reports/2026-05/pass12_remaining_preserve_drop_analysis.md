# Pass12 남은 preserve stub 드롭 분석 (2026-05)

## 범위

- **관측**: 최신 운영 NDJSON에서 Tier D 복구가 유효함(시도 9 / 성공 8)에도 불구하고 `extractor_drop_count == 2`가 남고, `solver_quality_tier`는 API 호환을 위해 `PARTIAL_SUCCESS_VALID_PRESERVE_LOSS`로 유지되는 케이스를 다룬다.
- **본 워크스페이스**: 해당 운영 NDJSON 파일 본문은 **저장소에 포함되어 있지 않다.** 아래 **운영 스냅샷 수치**와 **분류 확정 필드**는 에이전트 작업 시점에 제공된 최신 생산 요약에서 가져온 것이다. `miner_cell`·`nearest_same_kind_transport_cell` 등 **좌표·맵 기준 필드 전체**는 로컬에 보관된 동일 NDJSON의 `solver_summary.pass12_preserved_missing_stub_drop_details[0]`, `[1]` 원문과 반드시 대조한다.

## 운영 NDJSON 스냅샷 (최신, 레포 외부 원본과 대조)

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

**검증·주장 한계**: `extractor_drop_count` 개선이나 추가 드롭 감소는 **새 생산 NDJSON**으로만 확인한다. 본 문서·코드 변경만으로 생산 지표가 좋아졌다고 주장하지 않는다.

## 남은 2건 — `report_pass12_preserved_missing_stub_drop_details` 관점

운영에서 두 드롭 모두 계약상 비복구로 집계되었다. `report_pass12_preserved_missing_stub_drop_details(details)` 출력에서 **확정된** 열은 아래와 같다(좌표·트랜스포트 세부는 원본 NDJSON 행을 따른다).

| # | `miner_cell` | `pass12_unrecoverable_contract_reason_code` | `pass12_remaining_drop_classification` | 비고 |
|---|--------------|-----------------------------------------------|------------------------------------------|------|
| 1 | **운영 NDJSON `details[0].miner_cell`과 동일** | `no_legal_same_kind_route_under_bounds` | `unrecoverable_by_design` | Tier D 시도 후 BFS/한계 계열 사유로 집계됨 |
| 2 | **운영 NDJSON `details[1].miner_cell`과 동일** | `no_legal_same_kind_route_under_bounds` | `unrecoverable_by_design` | 동일 |

### 원문 행 붙여넣기용 (NDJSON `pass12_preserved_missing_stub_drop_details` 요소)

레포에 파일이 없어 **전체 원문 JSON은 비워 두지 않고**, 운영 NDJSON에서 각 배열 요소를 **그대로** 아래 블록에 교체한다.

```json
<PASTE_PRODUCTION_drop_details[0]_AS_SINGLE_JSON_OBJECT>
```

```json
<PASTE_PRODUCTION_drop_details[1]_AS_SINGLE_JSON_OBJECT>
```

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
