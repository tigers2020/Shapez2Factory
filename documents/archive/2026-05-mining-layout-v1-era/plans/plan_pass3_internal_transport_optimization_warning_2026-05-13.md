# Pass3 내부 수송 최적화 경고 분석·후속 최적화 플랜 (2026-05-13)

## 목적

- `degradation_causes` / `optimization_warnings`에 포함될 수 있는 **`internal_transport_above_pass2_baseline`** 를, Pass3·P4·카운터팩트 지표와 함께 **관측·보고 전용**으로 정리한다.
- **구현 변경 없음** (라우팅 권한·preserve 복구 범위 확대·goal 승격 등 금지). 다음 최적화 단계의 입력으로 쓸 **필드 사전**과 질문 목록만 남긴다.

## 관측 예시 (증거: `var/asteroid_mining_layout_debug/latest.ndjson`, run `ceaa1731e164`)

`solver_summary` 액션에서 읽은 값이다. **생산 2-drop 케이스와 동일 런이 아님** (`extractor_drop_count=10`). 수치는 **스키마·필드 존재 확인**용이다.

| 필드 | 값 |
|------|---|
| `optimization_warnings` | `["internal_transport_above_pass2_baseline"]` |
| `optimization_baseline_internal_transport` | 50 |
| `optimization_baseline_internal_transport_post_step4` | 89 |
| `after_internal_transport_count` (= `optimization_final_internal_transport_count`에 대응) | 82 |
| `internal_transport_delta_vs_baseline` | 39 |
| `optimization_internal_transport_quality_ratio` | 0.946809 |
| `pass3_final_committed` | `true` |
| `pass3_gain` | 0 |
| `pass3_committed` | `false` |
| `pass3_skipped` | `false` |
| `p4_reclaim_candidate_count` | 0 |
| `p4_reclaim_accepted_count` | `null` |
| `p4_reclaim_rollback_reason` | `null` |

### 해석 메모 (플랜 단계, 정책 아님)

- **baseline vs post_step4**: Pass2 직후 기준선(50)과 STEP4 이후 스냅샷(89)이 분리되어 있다. `internal_transport_delta_vs_baseline`(39)은 **최종 내부 수송(82) − Pass2 baseline(50)** 으로, STEP4 이후 증가분과는 다른 축일 수 있다. 다음 단계에서는 **어느 baseline과의 차이를 “경고”로 쓸지** 문서·UI 문구를 통일할지 검토한다.
- **`optimization_internal_transport_quality_ratio`**: 카운터팩트 시퀀셜 v1 대비 최종/비율. 1에 가까울수록 “카운터팩트 대비 여유가 작다”는 **품질 경고**(`optimization_warnings`의 다른 토큰)와 결합될 수 있다. 본 증거 런에서는 위 표와 같이 **baseline 초과만** 활성화되어 있다.
- **Pass3 / P4**: `pass3_final_committed`와 `pass3_committed` 불일치, `pass3_gain=0`, P4 후보 0 등은 **리플레이·타임라인 계약**과 함께 읽어야 한다 ([`documents/14_step10_replay_ui.md`](../14_step10_replay_ui.md), [`documents/02_pipeline_control_flow.md`](../02_pipeline_control_flow.md)). 최적화 플랜에서는 “내부 수송 증가가 Pass3 커밋·P4 리클레임과 어떤 순서로 관측되는지”를 STEP10 NDJSON으로만 추적한다.

## 비범위 (합의)

- STEP4 라우팅 권한 변경, preserve Tier 확대, 대각 extension, orphan transport goal 승격, `transport_cells_before` 전역 goal화, 무관 번들 제거, 보호 회랑 셀 제거.

## 다음 최적화 단계에서 할 일 (구현 전)

1. **한 런 내** `optimization_baseline_internal_transport` → `optimization_baseline_internal_transport_post_step4` → `after_internal_transport_count` 타임라인을 STEP10 프레임과 맞춰 시각화한다.
2. `internal_transport_above_pass2_baseline`이 켜질 때 `pass3_gain`·`p4_reclaim_accepted_count`가 0인 비율을 **관측**한다 (알고리즘 입력으로 NDJSON을 쓰지 않는다는 전제 유지).
3. `optimization_internal_transport_quality_ratio`가 `OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_QUALITY_RATIO_HIGH`와 동시에 뜨는지 여부로, “baseline 초과”와 “카운터팩트 대비 효율” 경고를 분리할지 결정한다.

## 검증

- 본 문서는 리서치·플랜 전용. 코드 변경은 동일 날짜의 품질 계약·테스트·copy-preview 보강 PR과 독립이다.

## 승인

- 내용 합의 후, 별도 구현 PR에서 Pass3/P4 최적화를 다룬다.
