# Path A 이후 진단·품질 감사 요약 (2026-05-13)

## 결론 분류

**A. 진단 전용 품질 이슈가 남는다.**  
최신 NDJSON에서 관측된 `SUCCESS` + `PARTIAL_SUCCESS_VALID_PRESERVE_LOSS` + `EXPECTED_UNRECOVERABLE_PRESERVE_LOSS_ONLY` 조합은, 이번 패치로 **원인 축을 텔레메트리에 더 잘 투영**할 수 있게 되었으나, 솔버의 물리적 배치·STEP4 라우팅 계약 자체를 바꾸지는 않았다.

## NDJSON / `solver_summary` 해석 (변경 전 → 후)

| 영역 | 이전 | 이후 |
|------|------|------|
| Preserve 드롭 | `NO_MATCHING_STUB`만으로는 `occupied_neighbor_ring` / `stub_local_geometry_sealed` / 목표·경계 실패가 한 줄에 섞여 보일 수 있음 | `preserve_drop_blocker`·`preserve_drop_detail` 보강, 요약에 `preserve_drop_blocker_counts`, `preserve_drop_rejected_subtype_counts`, `preserve_drop_unrecoverable_reason_counts` |
| 외부 마진 0 | `margin_generation_reason_if_zero`만 존재 | 동일 키 유지 + `pass2_external_margin_diagnostic.exterior_margin_status` (`predicate_shell_padding_suppressed` / `generation_bug_suspected` / `no_margin_by_design`) |
| Trunk seed 0 | `trunk_seed_candidate_count`만 있음 | Pass2: `trunk_seed_candidate_zero_reason`, STEP4: `step4_trunk_seed_candidate_zero_reason` + `diagnose_trunk_seed_pool_empty` / `diagnose_trunk_seed_candidate_zero_for_kind` |
| Pass3 0 절감 | `pass3_internal_transport_saved` 등 산술만 | `pass3_zero_gain_reason`, `pass3_zero_gain_context`(before/after 내부·전체 운송·STEP4 라우트 수) |
| P4 `all_transport_protected` | `p4_reclaim_*` 카운터가 흩어져 있음 | 동일 사유일 때 `all_transport_protected_trace`에 hard/soft/candidate·mineable 전후·final_route 길이 묶음 |
| `run_end` | `run_id`, `elapsed_s`만 | `emit_solver_summary_once` 이후 **경량** `solver_summary` 스냅샷(글로서리·replay 카운터·Pass3 zero 등) 포함 가능 |
| 카운터 글로서리 | `replay_frame_count` 설명만 | `replay_frame_source` 항목 추가 (`trace_frame_counter_glossary`) |

## 정책·버그 여부

- **STEP0.5 기존 운송 → hard 직접 승격**: 이번 변경은 **관측·요약**만 추가했으며, `reclaim_corridor_contracts` 등 기존 “힌트는 soft/candidate 쪽” 서술과 충돌하는 코드 변경은 하지 않았다. 별도 감사는 `documents/Algorithm/mining_solver_cursor_sessions/12_protected_corridor.md`와 대조할 것.
- **물리적 불가 보존 손실(B)**: `preserve_drop_unrecoverable_reason_counts`·`no_legal_same_kind_route_under_bounds`가 여전히 설계상 기대 손실을 뒷받침하는 경우 B로 남긴다.
- **코드 버그(C)**: `exterior_margin_status == generation_bug_suspected`가 **반복**되면 `is_external`/마진 샘플링 경로를 별도 이슈로 분리한다(이번 패치는 `is_external`·마진 기하 변경 없음).

## 검증

- `python -m pytest tests/unit/shapez_asteroid/` (907 passed, 3 skipped)
- 변경 파일 대상 `ruff check`, `black`(finalize·일부 테스트 자동 정리), 변경 앱 모듈 `mypy` 성공

## 이후 진행

- 실제 `latest.ndjson` 한 건에 대해 `run_end.solver_summary.trace_frame_counter_glossary`·`pass3_zero_gain_reason`이 기대와 일치하는지 **오프라인** 대조.
- 보호 회랑 STEP4 이전 hard 승격 여부는 전용 회귀(라우팅 상태 타임라인)로 확장 가능.
