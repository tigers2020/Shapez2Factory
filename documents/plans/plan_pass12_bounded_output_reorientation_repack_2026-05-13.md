# Pass12 Tier D: bounded_output_reorientation_repack (2026-05-13)

## 목적

- 기존 Tier A/B/C([bounded 1칸 rollback](plan_pass12_bounded_extension_rollback_2026-05-13.md))가 모두 실패한 뒤, **출력 회전 변경 + 로컬 extension 번들 재배치(4이웃만)** 로 동일 kind stub-route probe가 성공할 수 있는지 **한 번에 한 miner·해당 번들만** 시도한다.
- 성공 시에만 커밋 데이터 반영; 실패 시 기존 drop·trace 유지.

## 이름·식별

- `bounded_output_reorientation_repack` (**Tier D**)

## 범위

- preserve stub recovery 대상 **단일 miner** + 호출부가 넘긴 `extensions` 집합(해당 miner 클레임 번들)만 변경 후보.
- **4-neighbor(cardinal)** 만으로 (1) miner–extension 연결성 검증, (2) 재배치 후보 생성. `extension_topology.enumerate_extension_topologies` 재사용.
- **대각 인접만으로 miner에 연결된 extension 집합**은 `tier_d_skipped_diagonal_only_extension_topology` 로 조기 종료.
- 출력 회전 후보는 기존 `_rotation_order` 와 동일.
- stub이 **무관 extractor / 잘못된 kind transport / `scratch_blocked_cells`(보호 코리도 등)** 에 의해 막히면 해당 회전 스킵.
- 맵은 **딥카피**에서 strip·repack·probe; STEP4 merge 라우팅 본함수는 변경하지 않는다.

## 비범위

- orphan transport goal 승격, 전역 reroute, 무관 번들 제거, 보호 코리도 변경, STEP4 라우팅 권한 우회.

## per-row `preserve_stub_recovery` 텔레메트리

| 필드 | 의미 |
|------|------|
| `tier_d_attempted` | Tier D 로직 진입(연결성 검사 통과 후 시도) |
| `tier_d_success` | Tier D로 `accepted` |
| `tier_d_skip_reason` | 조기 스킵 시 사유 문자열 |
| `tier_d_failure_reason` | 시도 후 최종 실패 라벨 |
| `output_repack_candidate_count` | (회전, topology) 시도 수 상한 내 카운트 |
| `output_repack_candidate_sample` | 소량 샘플(회전·셀 시그니처) |
| `output_repack_selected_rotation` | 성공 시 선택 `r` |
| `output_repack_removed_extension_cells` | strip된 원래 extension 좌표 |
| `output_repack_replaced_extension_cells` | 성공 시 새 extension 좌표 |
| `output_repack_preserved_extension_count` | 성공 시 extension 타일 수(원본과 동일) |
| `output_repack_route_len_edges` | 성공 BFS `route_len_edges` |

## `preserve_missing_stub_summary.bounded_recovery` 집계

- `tier_d_attempted_count`, `tier_d_success_count`
- `tier_d_skip_reason_counts`, `tier_d_failure_reason_counts`

## 기존 키와의 관계

- `_empty_psr`의 `output_reorientation_attempted` / `output_reorientation_success`는 Tier A 회전 스캔과 연동된 레거시 의미를 유지한다. Tier D 전용은 `tier_d_*` 및 `output_repack_*` 로 구분한다.

## 검증

- [`test_pass12_preserve_stub_route_recovery.py`](../../tests/unit/shapez_asteroid/test_pass12_preserve_stub_route_recovery.py)
- [`test_pass12_merged_layout_seed_preserve.py`](../../tests/unit/shapez_asteroid/test_pass12_merged_layout_seed_preserve.py)

## 승인

- 본 문서 합의 후 Tier D 구현·머지한다.
