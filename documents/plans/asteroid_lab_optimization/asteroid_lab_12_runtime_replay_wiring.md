# Asteroid Lab — Runtime Replay Wiring Plan

Role: Asteroid Lab Runtime Replay Wiring Architect

**문서 상태:** ACTIVE (설계 전용). 본 문서는 **구현 승인 전 단계**의 경계·순서·검증을 고정한다.  
**범위:** Lab persistence·UI 읽기 경로에 optimization replay를 안전하게 연결하는 방법만 다룬다.  
**금지:** 본 문서만으로는 **솔버·리플레이 이벤트 의미·DTO·테스트 전용 fixture 파서 동작**을 바꾸지 않는다. 실제 배선 구현은 별도 PR·승인 후 진행한다.

---

## 1. Purpose (목적)

지금까지 고정된 것은 **출력 계약**이다. 다음 런타임 작업은 기존 optimization replay **출력**을 persistence·UI 읽기 경로로 노출하는 것이며, 그 과정에서 replay가 **솔버 입력**으로 새지 않도록 경계를 고정한다.

본 문서의 목적:

```text
- 무엇을 어디에 저장할지
- UI는 무엇을 어떻게 읽을지
- 무엇이 영원히 output-only인지
- Lab replay 트랙과 Optimization replay 트랙을 암묵적으로 합치지 않을지
```

를 구현 전에 문서로 고정한다.

---

## 2. Current contracts (현재 계약)

다음은 **이미 구현·테스트로 고정된** 계약이다.

| 계약 | 위치·수단 (요약) |
|------|------------------|
| Optimization JSON golden v0 | `tests/fixtures/shapez_asteroid/optimization/` |
| Optimization fixture JSON parser | `tests/unit/shapez_asteroid/fixtures/optimization_json.py` |
| Replay-track JSON golden v0 | `tests/fixtures/shapez_asteroid/replay/` |
| Replay JSON parser (fixture 봉투) | `tests/unit/shapez_asteroid/fixtures/replay_json.py` |
| Long replay stitching JSON v0 | `tests/fixtures/shapez_asteroid/replay_long/` |
| `replay_truncated` / `truncation_reason` (fixture 봉투 짝) | 골든 + `replay_json` 계약 |
| `commit.survivability_summary` 리플레이 프레임 | 도메인 이벤트·회귀 테스트와 정합 |
| Lab / Optimization **dual-track** replay 정책 | Lab map 트랙 vs optimization 관측 트랙 분리 |

**중요:** 위 fixture 파서·골든 JSON은 **계약·회귀용**이다. 프로덕션에서 동일 파서/봉투를 솔버 입력 경로에 붙이지 않는다.

### 2.1 런타임에 이미 존재하는 조각 (코드 기준)

- **저장:** `django_apps.asteroid_lab.services.optimization_replay_persist` — `SolverRun.config_json`에 `SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY` (`"optimization_replay_frames"`)로 **프레임 리스트만** 병합 저장. 다른 `config_json` 키는 보존.
- **직렬화:** `optimization_replay_frames_to_json_list` — 프레임 단위 dict 리스트.
- **UI:** `django_apps.web.services.asteroid_lab_page_context` — 최신 `SolverRun`에서 위 키를 읽고 `deserialize_optimization_replay_frames_from_json` 성공 시에만 `build_optimization_replay_track_payload`로 `OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY` (`"optimization_replay"`) 트랙을 채운다. 실패·없음이면 `empty_optimization_replay_track_payload()`.
- **트랙 `metrics`:** `build_optimization_replay_track_payload`가 `frame_count`, `event_type_counts`, `replay_truncated`를 채운다. `replay_truncated`는 프레임 `metrics` 집계 (`_aggregate_replay_truncated`).

### 2.2 Fixture 봉투 vs 런타임 persist 형상

| 항목 | 골든 long replay (`replay_long/`) | 현재 persist + UI |
|------|-----------------------------------|---------------------|
| `schema_version` | 봉투 최상위 | persist에는 **없음** (프레임 리스트만) |
| `replay_summary` / `replay_event_sequence` | 봉투에 명시 | UI에서 `build_optimization_replay_track_payload`가 **재계산** |
| `truncation_reason` | 봉투 최상위 (짝 계약) | **12F v0 이후:** 프레임 `metrics` → 트랙 `metrics.truncation_reason` 집계 (아래 §6.1) |

이 표로 **테스트 봉투 ≠ 런타임 persist**를 분리해, fixture 파서를 production parser처럼 가져오는 실수를 방지한다.

---

## 3. Runtime boundary (런타임 경계)

다음을 **명시적으로** 고정한다.

```text
Optimization replay is output-only.
Persisted replay must never be used by solver, candidate generation, route probe,
evolutionary search, incremental commit, or validation.
```

### 3.1 단방향 데이터 흐름

```text
Optimization 실행 / post-inspection
  → (메모리) OptimizationReplayFrame 시퀀스
  → (저장) SolverRun.config_json["optimization_replay_frames"]  # 출력만
  → (읽기) deserialize → build track → Lab context["optimization_replay"]
  → (표시) 메타데이터·오버레이 관측용 UI
```

### 3.2 레이어 책임

| 레이어 | 책임 |
|--------|------|
| `shapez_asteroid.optimization` | 이벤트·프레임 DTO·직렬화 dict (비즈니스 규칙) |
| `asteroid_lab` | `SolverRun`에 출력 병합 저장, import 경계 |
| `web` (page context) | 읽기 전용 어댑터: malformed이면 빈 트랙 + (선택) 진단 문자열 |
| 테스트 fixture 파서 | 회귀 정본만; 프로덕션 의존 **비권장** |

---

## 4. Persistence target (저장 대상)

### 4.1 키 이름 (코드 정본과 일치)

**현재 구현이 사용하는 키(이름 변경 없음):**

```text
SolverRun.config_json["optimization_replay_frames"]
```

상수: `django_apps.shapez_asteroid.optimization.optimization_ui_payload.SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY` (`"optimization_replay_frames"`).

**12F v0에서 추가하지 않는 것:** 별도 봉투를 도입하지 않는 한, 아래 sibling 키는 **추가하지 않는다** (구현자가 임의로 넣지 않음).

```text
optimization_replay_schema_version   # v0에서 도입 안 함
optimization_replay_truncated       # v0에서 sibling으로 도입 안 함
optimization_replay_truncation_reason # v0에서 sibling으로 도입 안 함
```

절단·스키마는 §6·§7의 **프레임 리스트 + 트랙 metrics** 모델로만 다룬다. 봉투·schema sibling·추가 키는 **별도 migration / compatibility PR**에서만 검토한다.

### 4.2 **12F v0 결정 (schema_version)**

별도 봉투를 도입하지 않는 한 `optimization_replay_schema_version` sibling key는 **추가하지 않는다.** v0 runtime guard는 기존 `optimization_replay_frames` 리스트를 `deserialize_optimization_replay_frames_from_json`으로 검증하는 방식이다. 봉투 또는 schema sibling 도입은 **별도 migration/compatibility PR**에서만 다룬다.

---

## 5. Write path (쓰기 경로)

```text
Run / Lab inspection 흐름
→ inspection·Lab replay 성공 (기존 파이프라인)
→ bounded optimization 실행
→ optimization replay frames 생산 (메모리)
→ JSON-safe 직렬화·12F v0 가드 통과 시에만
→ config_json["optimization_replay_frames"]에 출력 페이로드만 attach
```

리플레이 데이터는 **솔버 쪽으로 되돌아가지 않는다.**

---

## 6. Read path (읽기 경로)

```text
page context / UI payload builder
→ config_json에서 optimization_replay_frames 읽기
→ deserialize + (12F 이후) 추가 shape/짝 검증
→ optimization_replay 트랙을 템플릿·json_script에 노출
→ UI는 dual-track 정책에 따라 metadata/overlay만 표시
```

### 6.1 `replay_truncated` 및 `truncation_reason` (**12F v0 결정**)

**`truncation_reason`은 `SolverRun.config_json` sibling으로 저장하지 않는다.**

- **발행:** 잘림을 나타내는 프레임의 `metrics`에 `replay_truncated: true`와 `truncation_reason: <non-empty string>`을 **함께** 둔다.
- **집계:** `build_optimization_replay_track_payload`가 프레임 `metrics`에서 `truncation_reason`을 읽어 **`metrics.truncation_reason`**으로 올린다. 여러 프레임에 reason이 있으면 **첫 번째** reason을 정본으로 사용한다.
- **v1 대안:** `config_json` sibling은 설계상 보류이며, 필요 시 별도 문서/PR에서만 재검토한다.

**트랙 `metrics` 짝 계약 (UI·가드의 공통 기준):**

```text
track.metrics.replay_truncated == false  →  track.metrics.truncation_reason 부재
track.metrics.replay_truncated == true   →  track.metrics.truncation_reason 은 non-empty string
```

UI는 잘림 배지에 `replay_truncated`, 상세·툴팁에 `truncation_reason`만 사용하고 **리플레이 이벤트 의미를 바꾸지 않는다.**

### 6.2 Fixture 봉투 짝과의 관계

- **테스트 골든:** `replay_summary.replay_truncated` + 최상위 `truncation_reason` (회귀).
- **런타임:** persist는 프레임 리스트만; 짝은 **프레임 `metrics` → 트랙 `metrics`**로 맞춘다.

---

## 7. Malformed payload policy (깨진 페이로드 정책)

필수 동작:

```text
Malformed optimization replay payload must not crash Lab page.
Malformed payload must be dropped or replaced by empty replay payload.
A diagnostic reason should be exposed for UI/debug.
Solver result must remain unchanged.
```

### 7.1 권장 진단 reason 코드 (예시)

```text
missing_schema_version          # 봉투 도입 후에만 적용; v0에서는 미사용 가능
unsupported_schema_version
invalid_frame_shape
invalid_event_type
invalid_truncation_contract
payload_too_large               # 12F-v0 범위 밖; 후속 시퀀스
```

v0에서는 주로 `deserialize` 실패·shape 위반에 대응하는 코드를 쓴다.

### 7.2 UI에 노출할 진단 문자열 (12G)

읽기 경로가 빈 트랙으로 떨어질 때, 트랙 `metrics`에 **`optimization_replay_diagnostic_reason`** 같은 **단일 문자열**을 둘 수 있다. 이 값은 **표시·디버그 전용**이며 솔버 입력이 아니다. (구현은 Sequence **12G**에서 정리한다.)

---

## 8. Truncation contract (절단 계약)

- **Fixture:** `replay_json` — `replay_summary.replay_truncated` + 최상위 `truncation_reason`.
- **런타임 트랙:** §6.1의 `track.metrics` 짝.
- **의미 변경 금지:** HUD는 관측만; commit/route/evolution 시맨틱은 변경하지 않는다.

---

## 9. Dual-track UI policy (듀얼 트랙)

```text
Lab replay owns map rendering.
Optimization replay owns optimization metadata/overlay observation.
No implicit index sync.
No implicit event-order sync.
Optimization replay controls must not mutate Lab currentFrameIndex
unless an explicit sync mode is introduced later (out of scope for v0).
```

---

## 10. Schema policy (스키마 정책)

**문서상 v0 (persist):**

```text
별도 optimization_replay_schema_version 키 없음.
deserialize_optimization_replay_frames_from_json + 12F v0 shape/truncation 가드가 구조 검증의 중심.
```

**향후 봉투 도입 시(별도 PR):**

```text
optimization_replay_schema_version = 1  # 예시
unknown version → empty payload + diagnostic; silent coercion 금지
```

---

## 11. Explicit non-goals (명시적 비목표)

```text
- No production solver input from replay
- No replay-driven optimization
- No implicit Lab/Optimization frame sync
- No UI sync mode (v0)
- No database migration unless existing config_json is insufficient
- No JSON fixture parser reuse as production parser unless explicitly reviewed
- No route/commit/evolution algorithm changes
- 12F-v0에서 schema envelope / schema sibling / byte-size cap / HUD 미도입
```

---

## 12. Implementation sequence (구현 순서)

### Sequence 12F — Persist frame-list guard v0

**Scope:**

- `optimization_replay_frames`만 optimization replay persist 키로 유지한다.
- attach/read 전 **리스트 형태** 검증.
- 깨진 프레임 dict 거부.
- `frame_index` **연속**(0..n-1) 요구.
- `event_type`은 알려진 `OptimizationReplayEventType` 값만 허용.
- **프레임 `metrics` 절단 짝:** `metrics.replay_truncated == true`인 프레임은 **같은 프레임**의 `metrics`에 non-empty `truncation_reason`이 있어야 한다. 집계 후 `track.metrics`가 §6.1 짝을 만족하지 않으면 **persist 거부** 또는 **읽기 시 empty 트랙** 중 하나로 고정한다(구현 PR에서 택일·테스트로 박는다).
- 읽기 경로에서 malformed이면 **empty optimization replay payload**로 노출.

**Out of scope (12F-v0에서 하지 않음):**

```text
- schema envelope
- optimization_replay_schema_version sibling
- config_json truncation sibling keys
- UI HUD
- DB migration
- payload byte-size cap
- dict 전역 키 화이트리스트의 과도한 확장(필요 시 후속 PR)
```

### Sequence 12G — UI payload read adapter

- page context가 persist된 프레임을 읽고 스키마·shape·절단 짝을 검증한다.
- 실패 시 empty payload + §7.2 진단 문자열.
- `metrics.truncation_reason` 노출은 §6.1에 따른다.

### Sequence 12H — Truncation HUD / metadata display

- `replay_truncated` / `truncation_reason` 표시; 리플레이 시맨틱 변경 없음.

### Sequence 12I — Runtime malformed payload tests

- unsupported schema(봉투 도입 후)·invalid event type·invalid truncation contract·oversized(후속)·empty fallback 등.

---

## 13. Test plan (테스트 계획) — 12F 구현 PR 수용 기준

아래 이름은 **구현 PR에서 추가·이름 맞출 것**을 권장한다.

**Persist / schema (봉투 도입 시 확장):**

- `test_persisted_optimization_replay_schema_version_required` (봉투 PR 시)
- `test_persisted_optimization_replay_rejects_unsupported_schema`

**Shape / read:**

- `test_persisted_optimization_replay_invalid_shape_falls_back_empty`
- `test_persisted_optimization_replay_truncation_contract` (프레임 metrics + 트랙 metrics 짝)

**Page context:**

- `test_page_context_reads_persisted_optimization_replay`
- `test_page_context_malformed_optimization_replay_does_not_crash`

**경계:**

- `test_ui_payload_preserves_dual_track_no_sync`
- `test_solver_does_not_read_persisted_replay` (정적 검색 또는 아키텍처 테스트로 “역방향 import/호출 없음” 고정)

**회귀:** `test_optimization_replay_persist.py`, `test_replay_fixture_json_contract.py`, `test_long_replay_fixture_contract.py` 유지.

---

## 14. Remaining open decisions (남은 결정)

1. **Payload byte-size cap:** 12F-v0 **범위 밖**; 도입 시점·상한 값은 후속.
2. **다중 SolverRun:** “최신만 표시” 외 UI에서 이전 run 선택 필요 여부.
3. **봉투·`optimization_replay_schema_version`:** 별도 migration/compatibility PR에서만.

~~`truncation_reason` sibling vs metrics~~ → **v0는 metrics 집계로 확정(§6.1).**

---

## 15. Acceptance criteria (문서 자체)

- 본 문서가 존재하고 §3 경계·§11 비목표가 명시된다.
- 12F-v0 범위·비범위가 §12에 고정된다.
- output-only 불변식이 §3·§11에서 반복된다.
- **코드 동작 변경은 본 문서 작업에 포함하지 않는다.**
- 이후 구현은 **작은 PR**로 12F→12G→12H→12I 순 진행 가능해야 한다.

---

## 16. 검증 (본 문서 작업)

- Markdown만 변경한다.
- 문서 전용 lint 스크립트는 별도로 두지 않은 것으로 보아 **실행하지 않음**.

---

## 17. 교차 참조

- `asteroid_lab_10_development_sequence.md`
- `asteroid_lab_11_future_execution_plan_post_sequence.md`
- `asteroid_lab_09_replay_debug.md`
- 코드: `optimization_ui_payload.py`, `optimization_replay_persist.py`, `asteroid_lab_page_context.py`

---

## 18. 요약

| 항목 | 결론 |
|------|------|
| Persist | `config_json["optimization_replay_frames"]`만 (키 이름 유지) |
| schema_version | v0 sibling **미도입**; deserialize + 12F shape 가드 |
| truncation_reason | **프레임 metrics → `build` → track.metrics**; 첫 reason 정본; sibling **없음** |
| Malformed | 빈 트랙 + 진단 문자열(12G); Lab 페이지 비파괴 |
| Dual-track | Lab map 권한 vs optimization 관측; 암묵 동기 없음 |
| 12F-v0 | 프레임 리스트 가드만; 봉투·HUD·cap·migration **제외** |
