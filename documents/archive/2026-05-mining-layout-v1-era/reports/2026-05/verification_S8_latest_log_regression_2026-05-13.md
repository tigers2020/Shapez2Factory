# S8 — 최신 로그 회귀 검증 보고서 (E2E / 프록시 픽스처)

**역할**: End-to-End Solver Verification Engineer  
**일자**: 2026-05-13  
**범위**: 검증·보고만 (알고리즘 변경 없음). 정본: `documents/Algorithm/mining_solver_cursor_sessions/README.md` 및 §08·§09·§10·§12·§13·§14·§16 교차 참고.

---

## 1. 증거 한계 (동일 사용자 로그 미보유)

| 항목 | 상태 |
|------|------|
| `var/asteroid_mining_layout_debug/latest.ndjson` | 워크스페이스에 **부재** (또는 비어 있음) — NDJSON 바이트 대조 불가 |
| `var/asteroid_mining_layout_replay/replay_latest.ndjson` | 동일 |
| 사용자 원본 **SHAPEZ2 copy 문자열** / 동일 `BP` | 레포에 포함되지 않음 |

따라서 **“옛 로그와 동일 입력” 바이트 단위 재현은 불가**하다. 대신 아래를 수행했다.

1. **단위 회귀**: `python -m pytest tests/unit/shapez_asteroid -q` — **951 passed**, 3 skipped (2026-05-13 실행).
2. **프록시 E2E**: `build_solver_timeline(decoded)`를 저장소 **공개 픽스처** 3종에 대해 실행. 환경: `SHAPEZ_SOLVER_ALGO_DEBUG=1` (§16 STEP10 트레이스·`replay_frame` 스트라이드 활성), `DJANGO_SETTINGS_MODULE=config.settings`.

**결론 선언**: 사용자가 제시한 **구체 수치(57 extractor, drop 10, no_same_kind_route 10, …)**에 대한 “개선 입증”은 **본 워크스페이스만으로는 주장할 수 없다**. 아래 표는 **옛 로그에서 인용된 목표 수치 vs 프록시 실행 결과**의 대조이며, 동일 시나리오가 아니다.

---

## 2. 옛 로그에서 알려진 목표 수치 (사용자 제공, 증거 파일 없음)

| 지표 | 옛 값 (참고) |
|------|----------------|
| `final_extractor_count` | 57 |
| `preserve_missing_stub_summary.drop_count` | 10 |
| `no_same_kind_route` (preserve 드롭 블로커 누적 등) | 10 |
| 최종 내부 운송 (표기 “final transport”) | 89 |
| `optimization_baseline_internal_transport` (표기 “baseline”) | 50 |
| `replay_frame_count` | 73 |
| `map_timeline_frame_count` | 6 |

---

## 3. 프록시 E2E 결과 (`SHAPEZ_SOLVER_ALGO_DEBUG=1`)

### 3.1 요약 표

| 지표 | fluid_striped_greenfield | striped_greenfield_belt | step4_fluid_pipe_failure_regression |
|------|--------------------------|-------------------------|--------------------------------------|
| 픽스처 경로 | `tests/fixtures/pass12_telemetry_trace_pack/fluid_striped_greenfield_bp.json` | `tests/fixtures/pass12_telemetry_trace_pack/striped_greenfield_bp.json` | `tests/fixtures/asteroid_mining_layout/step4_fluid_pipe_failure_regression_bp.json` |
| `original_extractor_count` | 3 | 3 | 3 |
| `final_extractor_count` | 1 | 2 | 1 |
| `preserve_source_loss_before_step4` | 2 | 0 | 2 |
| `preserve_missing_stub_summary.drop_count` | 2 | 0 | 2 |
| `preserve_drop_blocker_counts` | `blocked_near_stub: 2` | `{}` | `blocked_near_stub: 2` |
| `bootstrap_attempted` / `bootstrap_committed` | False / False | False / False | False / False |
| `external_reachable_transport_after_bootstrap_count` | null | null | null |
| `step4_route_success_on_surviving_placements` | True | True | True |
| `step4_complete_routing_success` | True | True | True |
| `termination.quality_tier` | PARTIAL_SUCCESS_VALID_PRESERVE_LOSS | PARTIAL_SUCCESS_VALID_PRESERVE_LOSS | PARTIAL_SUCCESS_VALID_PRESERVE_LOSS |
| `degradation_causes` | extractor_drop…, preserve_missing_stub_drop | extractor_drop…, internal_transport_above_pass2_baseline | extractor_drop…, preserve_missing_stub_drop |
| `all_transport_protected_trace` hard / soft / candidate | 1 / 16 / 0 | 2 / 19 / 0 | 1 / 16 / 0 |
| `pass3_zero_gain_reason` | no_candidate_route_improved_internal_transport | (동일) | (동일) |
| `pass3_reject_by_reason` (요약) | `no_internal_transport_saving: 3`, `connectivity_break: 1`, 나머지 0 | 동일 패턴 | 동일 패턴 |
| `optimization_baseline_internal_transport` (내부 카운트) | 3 | 4 | 3 |
| `optimization_final_internal_transport_count` | null | null | null |
| `replay_event_count` / `replay_frame_count` | 16 / 1 | 4 / 0 | 16 / 1 |
| `replay_frame_source` (S7 계약) | **replay_trace** | **pass_snapshot_fallback** | **replay_trace** |
| `map_timeline_frame_count` / `decoded_map_timeline_frame_count` | 6 / 6 | 6 / 6 | 6 / 6 |
| `solver_timeline_frame_count` | 6 | 6 | 6 |
| `geometry_valid` / `connectivity_valid` | True / True | True / True | True / True |

### 3.2 S7 `replay_frame_source` 기대와의 정합

- §14 / `enrich_solver_summary_replay_frame_contract` 규칙: `replay_frame_count > 0`이면 `replay_trace`.
- fluid_striped·fluid 회귀 픽스처: `replay_frame_count == 1`, `map_timeline_frame_count == 6` → **`replay_frame_source == replay_trace`** — **PASS** (UI가 6칸 map 타임라인만 고르지 않도록 하는 계약과 일치).
- belt striped: `replay_frame_count == 0`, 마일스톤 6프레임 → **`pass_snapshot_fallback`** — **PASS**.

---

## 4. 체크리스트 (사용자 원 시나리오 대비)

| 검증 항목 | 프록시에서의 결과 | 사용자 원 로그 대비 |
|-----------|-------------------|---------------------|
| Orphan 외부 transport bootstrap | 세 픽스처 모두 **부트스트랩 미시도** (`bootstrap_attempted=False`) | **미검증** — 원 맵(orphan-only fluid 등)에서만 의미 있음 |
| preserve 드롭 `no_same_kind_route` 감소 | 본 픽스처는 **`blocked_near_stub`** 중심 (2건), `same_kind_goal_unreachable` 0 | 옛 로그의 **10× no_same_kind_route** 패턴과 **불일치** → 동일 실패 모드 아님 |
| STEP4 성공 vs preserve 손실 분리 | `step4_route_success_on_surviving_placements` True + `preserve_source_loss_before_step4` 2 (fluid 계열) | 계약 필드 존재·동시 True 가능 — **부분 PASS** (의미는 정본 §08·finalize 요약과 정합) |
| Protected corridor 증명 | `all_transport_protected_trace`에 hard/soft 수치 존재; 정본 §12 “hard는 증명 후만”과 구현 MVP 간 **이미 알려진 tension** (S0 감사 참고) | **부분** — 수치는 있으나 문서상 증명 체인과 1:1 아님 |
| Pass3 zero gain 분해 | `pass3_reject_by_reason` + `pass3_zero_gain_reason` 채워짐 | **PASS** (텔레메트리 존재) |
| Replay frame source | 위 §3.2 | **PASS** (조건부) |
| Final geometry/connectivity | 모두 True | **PASS** |

---

## 5. 남은 블로커 (사실 기준)

1. **입력 재현 불가**: 동일 `BP`/copy 없이는 “57→?, 10→?” 개선을 **주장할 수 없음**.
2. **프록시 스케일**: 픽스처는 extractor 3대 수준 — orphan-only 대규모 맵에서의 bootstrap·goal 0·`no_same_kind_route` 연쇄를 **대표하지 않음**.
3. **`optimization_final_internal_transport_count`**: 프록시 실행에서 `null` — 최종 vs baseline 비교 UI는 별도 경로/조건 확인 필요 (회귀 범위 밖이면 이슈로 분리).

---

## 6. 권장 다음 시퀀스 (해결 미입증 시)

1. **증거 확보**: 문제 재현 copy를 `*_decoded.json` 또는 암호화 copy 파일로 레포 외부 저장소에 두고, `scripts/debug/pass12_preserve_recovery_ab.py --ndjson` 또는 동등 파이프라인으로 **동일 `run_id`** NDJSON을 다시 생성.
2. **bootstrap 전용 검증**: `orphan_island_external_bootstrap`이 실제로 호출되는 맵(단위: `test_orphan_island_external_bootstrap.py` 참고)으로 E2E 한 건을 문서화.
3. **대규모 회귀**: 사용자 원 맵을 **fixture로 승인**한 뒤, CI에서 `solver_summary` 스냅샷 golden 비교(민감 필드 제외).

---

## 7. 검증 명령 (실행 로그)

```text
python -m pytest tests/unit/shapez_asteroid -q
# → 951 passed, 3 skipped

python -m ruff check django_apps/shapez_asteroid tests/unit/shapez_asteroid
# → All checks passed! (test 함수명 길이 E501 3건 수정 후)

python -m black --check django_apps/shapez_asteroid tests/unit/shapez_asteroid
# → 260 files would be left unchanged
```

**참고 (코드 변경)**: S8 검증 중 `ruff` E501로 실패하던 테스트 3개의 **함수명만** 짧게 바꿨다 (`test_runtime_authority_leakage_regression.py`). 알고리즘·계약 변경 없음.

---

## 8. 정본 문서와의 관계 (요약)

- **README / §02**: decode → pass → finalize 흐름; 본 보고서 E2E는 `build_solver_timeline` 단일 진입점으로 정합.
- **§08 STEP4**: 생존 placement 기준 route 성공은 `step4_route_success_on_surviving_placements`로 관측 가능(프록시 True).
- **§09 Pass3**: `pass3_zero_gain_reason` + `pass3_reject_by_reason`으로 무이득 거절 분해 가능 — 프록시 **충족**.
- **§12 Protected corridor**: `all_transport_protected_trace` 수치 제공; hard 승격과 “증명” 문구 간 갭은 기존 감사와 동일.
- **§13 / §15**: `geometry_valid` / `connectivity_valid` True.
- **§16 Replay UI**: `replay_frame_source`가 cycle 프레임 존재 시 `replay_trace` — S7 계약과 **일치** (증거: §3.2).

**종합**: 단위 테스트·프록시 E2E·S7 replay 계약은 **통과**. 사용자 원 **대규모 preserve / orphan** 시나리오의 **실질 개선(S1–S7 효과)**은 **동일 로그·동일 입력 없이는 입증하지 않았다.**
