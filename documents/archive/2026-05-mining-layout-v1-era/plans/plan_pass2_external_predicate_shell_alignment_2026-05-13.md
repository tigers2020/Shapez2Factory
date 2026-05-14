# Pass2 외부 판정 셸 정렬 (승인 대기)

**상태**: ACTIVE (정책·알고리즘 변경은 사람 승인 후 구현)  
**배경**: `pass2_external_margin_diagnostic`가 §15 `is_external` 확장 mineable bbox 셸과 샘플 이웃을 분해해 보여준다. 샘플 이웃이 전부 셸 안·`x==0`이면 `is_external_true_neighbor_sample_count=0`은 **구현 버그가 아니라 기하**일 수 있다.

## 관측 요약 (코드 계약)

- `is_external`: [`external_predicate_for_mining_map`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/validation/final_validation.py) — timeline[1] mineable bbox ± 동적 margin, `x==0`은 항상 비외부.
- Pass2 pack에 동일 bbox·margin을 실어 진단 셸 분해와 정렬 ([`Pass2RouteProbePack`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/placement/pass12_route_probe.py)).

## 승인 후 선택지 (배타)

| ID | 내용 | STEP4·STEP9 정합 | 위험 |
|----|------|------------------|------|
| A | goal/margin 전용 bbox를 probe universe hull 등으로 좁힘 | 불일치 시 별도 문서·이중 predicate 논의 필요 | 높음 |
| B | 동적 margin 상·하한 조정 (Pass 전역 또는 국소) | §15 문서·검증 전면 | 중~높음 |
| C | 관측·리포트만 유지, 배치 품질은 별 트랙 | 없음 | 낮음 |

**금지(합의)**: orphan transport를 goal로 승격하는 fallback — [`build_pass2_step4_aligned_routing_goals`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/placement/pass12_route_probe.py) 주석 계약과 충돌.

## 다음 액션

1. 실제 실패 NDJSON에서 `sampled_neighbor_shell_breakdown`·`is_external_predicate_mineable_bbox` 확인.
2. A/B/C 중 하나를 승인 문서에 명시한 뒤에만 구현 PR 분리.

## 관련 플랜

- Replay·`cycle_frames` 검증은 debug NDJSON이 아닌 replay 스트림으로 한다 — [`plan_step10_cycle_replay_streams_2026-05-13.md`](plan_step10_cycle_replay_streams_2026-05-13.md).
