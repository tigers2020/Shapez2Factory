# Pass12 보존 손실 수락 보고서 (2026-05-13)

## 1. 판정(Decision)

- 현재 상태는 **수락 가능한 기대·복구 불가 보존 손실(expected / unrecoverable preserve loss)** 로 분류한다.
- `termination.tier == SUCCESS`이며 최종 검증이 통과하므로, 본 케이스를 **하드 솔버 실패(hard solver failure)** 로 보지 않는다.
- 게이트 관점 품질 등급은 기존과 같이 **B(물리·경계 조건으로 설명 가능한 보존 손실 / 기대적 비복구)** 를 유지한다. C급(코드·정책 버그)으로 증명된 항목은 없다.

## 2. 근거(Evidence)

오프라인으로 확보된 최신 NDJSON·진단 요약·단위 테스트 결과만 인용한다. NDJSON은 솔버 입력으로 사용하지 않았다.

### 2.1 종료·품질 티어

- `termination.tier`: **SUCCESS**
- `solver_quality_tier`: **PARTIAL_SUCCESS_VALID_PRESERVE_LOSS**
- `solver_quality_subtier`: **EXPECTED_UNRECOVERABLE_PRESERVE_LOSS_ONLY**

### 2.2 추출기·보존 드롭

- `original_extractor_count`: **67**
- `final_extractor_count`: **57**
- `extractor_drop_count`: **10**
- `preserve_missing_stub_summary`: **NO_MATCHING_STUB** × **10**

### 2.3 Preserve 드롭 블로커·비복구 사유

- `preserve_drop_blocker_counts`: `occupied_neighbor_ring` **9**, `stub_local_geometry_sealed` **1**
- `preserve_drop_unrecoverable_reason_counts`: `no_legal_same_kind_route_under_bounds` **10**

### 2.4 외곽 마진·트렁크 시드

- `exterior_margin_status`: **predicate_shell_padding_suppressed** (`generation_bug_suspected` 아님)
- `trunk_seed_candidate_zero_reason`(문맥상 Pass2/STEP4 진단 키): **exterior_margin_empty_and_no_seed**

### 2.5 Pass3·Reclaim 0 절감

- `pass3_zero_gain_reason`: **no_candidate_route_improved_internal_transport**
- `all_transport_protected_trace`: 사용 가능하나, **STEP4 커밋 이전 hard 승격을 증명하지는 않음**(구조적 의심만 해소되지 않았던 시점의 관측 한계).

### 2.6 보호 회랑 hard 승격 타이밍(회귀)

- 전용 회귀: [`tests/unit/shapez_asteroid/test_protected_corridor_hard_promotion_timing.py`](../../../tests/unit/shapez_asteroid/test_protected_corridor_hard_promotion_timing.py)에서 **STEP0.5·ELA 기반 기존 운송이 STEP4 커밋 전 `hard_extras` / reclaim 권한 hard 풀로 승격되지 않음**을 단위 테스트로 고정함.
- `routing_state`의 hard 풀은 `source == "step4_committed_routes"` 및 stub·경로 끝 규칙과 정합함을 동일 파일에서 검증.

### 2.7 Path A 진단 전달·최종 검증

- Path A 진단이 **전체 `solver_summary`**, **`run_end` 경량 스냅샷**, **copy-preview** 간에 정렬된 상태(이전 감사에서 지적된 전달 갭 해소).
- **최종 검증(final validation)**: 성공(사용자 제공 사실·기존 게이트와 일치).

## 3. 기각된 가설(Rejected hypotheses)

| 가설 | 기각 근거 |
|------|-----------|
| 최종 검증 버그 | 최종 검증 성공, `SUCCESS` 종료 |
| 리플레이 프레임 버그 | Path A 전달 계약 정리 및 관련 단위 테스트로 회귀 방지; 본 보고서 범위에서 역추적 불일치 없음 |
| 외곽 마진 생성 버그 | `exterior_margin_status`가 `predicate_shell_padding_suppressed`이며 `generation_bug_suspected` 아님 |
| 트렁크 시드 정책 단독 버그 | `exterior_margin_empty_and_no_seed` 등 관측이 마진·시드 풀 빈 조건과 정합; C급 단정 증거 없음 |
| 보호 회랑 hard 조기 승격 | 전용 회귀가 STEP4 커밋 전 hard 승격 경로를 부정; reclaim은 STEP4 `routing_state`만 권한 |
| NDJSON 입력 오염 | NDJSON은 오프라인 증거로만 사용; 솔버 입력으로 사용하지 않음 |

## 4. 남는 품질 한계(Remaining quality limitations)

- **보존 대상 추출기 10기**가 드롭됨(`extractor_drop_count == 10`).
- **최종 운송 수**는 여전히 Pass2 베이스라인 위일 수 있음(절감 여지는 Pass3/Reclaim에서 0 절감 사유와 함께 설명됨).
- **Path B 외곽 마진 기하**는 미구현(정책·기하 변경 없음).
- **라우트 예산 A/B 실험**은 수행되지 않음.

## 5. 이후 선택 작업(Future optional work)

- Path B: `exterior_margin_status == predicate_shell_padding_suppressed`인 케이스에서 외부 마진 기하를 바꿀지 **설계서** 수준에서 결정.
- 라우트 예산·경계 A/B 실험(오프라인 스크립트·실험 JSON은 솔버 입력 계약 밖에서 유지).
- `mypy .` 시 `scripts/debug` 이중 모듈명 중복(기존 이슈) 정리.
- preserve-loss 관련 **UI 문구** 다듬기(표현만, 솔버 동작 변경 없음).

## 6. 검증(Validation)

- 단위 테스트: `tests/unit/shapez_asteroid/` — **911 passed, 3 skipped**(사용자 제공·오프라인 증거).
- 변경 파일 기준: **ruff / black / mypy** 통과(사용자 제공).
- `mypy .`: `scripts/debug/t7_step4_ndjson_contracts.py` 등 **기존 중복 모듈명 이슈**로 전체 프로젝트 타입체크는 여전히 실패할 수 있음(본 수락 범위 밖).

---

## 산출물·범위 요약

| 항목 | 내용 |
|------|------|
| 생성·변경 파일 | 본 문서 `documents/reports/2026-05/pass12_expected_preserve_loss_acceptance_2026-05-13.md` **신규 작성** |
| 솔버 동작 | **변경 없음**(라우팅·외곽 마진·복구·Pass3/Reclaim·보호 회랑 정책·검증 미수정) |
| 최종 분류 | **B** 유지(기대·비복구 보존 손실로 물리적으로 설명 가능) |
