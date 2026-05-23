# Asteroid Lab — Runtime Replay Wiring Plan

Role: Asteroid Lab Runtime Replay Wiring Architect

**문서 상태:** ACTIVE. **제품 replay North Star (2026-05-19):** [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md) — dual-track 폐기; 본 문서 §1·§9의 dual-track 문단은 마이그레이션 전 스냅샷이다. §12 **Sequence 12F·12G·12H**는 구현 완료(2026-05-17). **Sequence 12I**는 §12에 **HUD 어휘 경화(vocabulary hardening)** 초안만 두고, 구현은 별도 PR에서 진행한다. **Sequence 12J**(POST `optimization_replay_attach` 전용 HUD 줄)는 Lab 템플릿·`asteroid_miner_layout_lab.js`·테스트·§12J 문서로 구현 완료(2026-05-17). **Sequence 12K**(POST attach `diagnostic` 스칼라·`evolution_failed` 단계 관측)는 §12K·코드·테스트로 구현 완료(2026-05-17). **Sequence 12L** (optimization 경계에서 raw↔dense 금지·AST)는 2026-05-17 반영. **PR-F (2026-05):** replay/Lab은 island-local `(x,y)` only; `server_coords`·`server_xy_params` **삭제**. 그 외 시퀀스는 설계·경계 고정용이다.  
**범위:** Lab persistence·UI 읽기 경로에 optimization replay를 안전하게 연결하는 방법만 다룬다.  
**금지:** 본 문서만으로는 **솔버·리플레이 이벤트 의미·DTO·테스트 전용 fixture 파서 동작**을 바꾸지 않는다. 실제 배선 구현은 별도 PR·승인 후 진행한다.

> **FIXTURE ENVELOPE SCHEMA ≠ RUNTIME PERSISTENCE SCHEMA**  
> 테스트 골든 봉투(`replay_summary.replay_truncated` + 최상위 `truncation_reason`)와 런타임 persist(프레임 리스트 + 프레임 `metrics` 집계)는 **다른 스키마**이다. 구현 시 `payload["truncation_reason"]` top-level persist **금지** — §6.1 정본.

---

## 1. Purpose (목적)

지금까지 고정된 것은 **출력 계약**이다. 다음 런타임 작업은 기존 optimization replay **출력**을 persistence·UI 읽기 경로로 노출하는 것이며, 그 과정에서 replay가 **솔버 입력**으로 새지 않도록 경계를 고정한다.

본 문서의 목적:

```text
- 무엇을 어디에 저장할지
- UI는 무엇을 어떻게 읽을지
- 무엇이 영원히 output-only인지
- 제품 replay는 단일 replay timeline으로 수렴한다 (Phase 9; dual-track 폐기)
```

를 구현 전에 문서로 고정한다. **제품 replay 정본:** [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md).

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
| Lab / Optimization **dual-track** replay 정책 | **Deprecated** → replay timeline ([`asteroid_lab_09_replay_timeline`](asteroid_lab_09_replay_timeline.md)) |

**중요:** 위 fixture 파서·골든 JSON은 **계약·회귀용**이다. 프로덕션에서 동일 파서/봉투를 솔버 입력 경로에 붙이지 않는다.

### 2.1 런타임에 이미 존재하는 조각 (코드 기준, 2026-05-21)

- **합성·페이로드:** `django_apps.asteroid_lab.services.lab_replay_timeline_payload.build_lab_replay_frames_for_project` — Lab `ReplayTrack` + solver runtime segment → 단일 timeline frames + track `metrics`.
- **RTTP v0.2 (2026-05-23):** RTTP pipeline milestones persist on **`{run_key}:rttp`** (`rttp_optimization_track_key`); `get_latest_lab_replay_track_for_project` **excludes** `rttp-*` / `:rttp` tracks. Until Sequence 3B, **`lab_replay_frames_json` = inspection/reconstruction only** — RTTP milestones are **not** PR-B proof via Lab JSON. See [`2026-05-23-rttp-v0.2-replay-parity-design.md`](../../docs/superpowers/specs/2026-05-23-rttp-v0.2-replay-parity-design.md) § H2.
- **UI:** `django_apps.web.services.asteroid_lab_page_context` + `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` — **`updateReplayTruncationHud`** 가 track `metrics.replay_truncated` / `metrics.truncation_reason` / `diagnostic_reason` 표시(표시 전용).
- **트랙 `metrics`:** `_track_metrics_from_serialized_frames` — `replay_truncated`는 프레임 OR; `truncation_reason`·`dropped_frame_count`는 **마지막 프레임** `metrics`에서 읽음 (§6.1).
- **Deprecated (dual-track):** `build_optimization_replay_track_payload`, `renderOptimizationReplayHud`, `#lab-optimization-replay-status` — 제거·미사용; 신규 코드에서 참조 금지.

### 2.2 Fixture 봉투 vs 런타임 persist 형상

| 항목 | 골든 long replay (`replay_long/`) | 현재 persist + UI |
|------|-----------------------------------|---------------------|
| `schema_version` | 봉투 최상위 | persist에는 **없음** (프레임 리스트만) |
| `replay_summary` / `replay_event_sequence` | 봉투에 명시 | `build_lab_replay_frames_for_project`가 **재계산** |
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
| `web` (page context) | 읽기 전용 어댑터: 역직렬화 실패 시 빈 트랙 + `metrics.optimization_replay_diagnostic_reason`(12G, 메타데이터만) |
| 테스트 fixture 파서 | 회귀 정본만; 프로덕션 의존 **비권장** |

### 3.3 Sequence 12L — Server 좌표 경계 (optimization 입력)

```text
OptimizationInput 이후(및 동일 좌표를 쓰는 candidate·route·evolution·replay 기록)는 Server X/Y만 사용한다.
raw blueprint X/Y·dense 변환은 decode/import·cleanup/reconstruction 경계에서만 수행한다.
django_apps.shapez_asteroid.optimization 패키지와 asteroid_lab_post_inspection_evolution.py는
`server_coords` 브리지는 **삭제됨** (PR-F). replay/web는 `ReplayProjectionContext` island identity만 사용.
copy JSON `X==0`은 island-local에서 유효; lab world map `x==0` 열 없음 — 프레임 혼동 금지.
```

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
- **집계:** `_track_metrics_from_serialized_frames`(`lab_replay_timeline_payload.py`)가 프레임 `metrics`에서 **`metrics.truncation_reason`**으로 올린다. `replay_truncated == true`일 때 reason·`dropped_frame_count`는 **마지막 프레임** `metrics` 정본(코드 L204–212).
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

### 7.1 진단 reason 코드 (**12G v0 구현값**)

읽기 전용·메타데이터 전용. 상수 키: `django_apps.asteroid_lab.services.optimization_ui_payload.OPTIMIZATION_REPLAY_DIAGNOSTIC_REASON_METRIC_KEY` → 트랙 `metrics` 필드명 **`optimization_replay_diagnostic_reason`**.

```text
missing_optimization_replay          # 어떤 SolverRun.config_json에도 optimization_replay_frames 키가 없음
empty_optimization_replay_frames     # 키는 있으나 리스트가 비어 있음 ([])
invalid_optimization_replay_payload  # 모든 프레임이 알 수 없는 event_type이거나 shape 불일치로 전부 스킵됨
```

> **읽기 경로(lenient)**: `deserialize_optimization_replay_frames_lenient` 사용 — unknown `event_type`인 프레임은 **개별 skip**하고 `omitted_frame_count` 메트릭에 계수한다. 전체 트랙이 빈 경우에만 `invalid_optimization_replay_payload` diagnostic을 설정한다. 엄격(strict) 검증(`validate_optimization_replay_frame_list_payload`)은 **쓰기(persist) 경로**에만 유지된다.

유효 프레임이 일부 스킵된 경우 트랙 `metrics`에 `omitted_frame_count` (int)가 추가된다.

정상 역직렬화 시 이 필드는 **부재**한다. 솔버·리플레이 의미·정렬·집계에는 관여하지 않는다.

### 7.2 UI 노출 (12G / 12H)

- **12G:** 빈 트랙으로 떨어질 때에만 §7.1 문자열을 `metrics.optimization_replay_diagnostic_reason`에 둔다. **리플레이 시맨틱·프레임 순서에는 관여하지 않는다.**
- **12H:** Lab 템플릿·`asteroid_miner_layout_lab.js`가 `replay_truncated` / `truncation_reason` / `optimization_replay_diagnostic_reason`을 **표시 전용 HUD**로 노출한다(`#lab-optimization-replay-status` 등). 동기화·재시도·페이로드 변조 없음; Run Solver JSON 갱신 시에는 클라이언트 `replaceOptimizationReplayPayload`가 HUD를 다시 그린다.

---

## 8. Truncation contract (절단 계약)

- **Fixture:** `replay_json` — `replay_summary.replay_truncated` + 최상위 `truncation_reason`.
- **런타임 트랙:** §6.1의 `track.metrics` 짝.
- **의미 변경 금지:** HUD는 관측만; commit/route/evolution 시맨틱은 변경하지 않는다.

---

## 9. Dual-track UI policy (듀얼 트랙) — **Deprecated historical**

> **구현·리뷰·테스트 설계에 적용하지 않는다.** 제품 정본: [`asteroid_lab_09_replay_timeline.md`](asteroid_lab_09_replay_timeline.md).

<details>
<summary>Deprecated historical: Dual-track UI policy (펼치기)</summary>

```text
Lab replay owns map rendering.
Optimization replay owns optimization metadata/overlay observation.
No implicit index sync.
No implicit event-order sync.
Optimization replay controls must not mutate Lab currentFrameIndex
unless an explicit sync mode is introduced later (out of scope for v0).
```

</details>

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
- 12F-v0에서 schema envelope / schema sibling / byte-size cap 미도입(12H에서 **절단·진단 HUD**만 추가; 시맨틱·동기화 비변경)
```

---

## 12. Implementation sequence (구현 순서)

### Sequence 12F — Persist frame-list guard v0

**구현 상태 (v0, 2026-05-17): 완료**

- **가드·역직렬화:** `django_apps.shapez_asteroid.optimization.optimization_ui_payload`에 `validate_optimization_replay_frame_list_payload` 및 `deserialize_optimization_replay_frames_from_json` 내 프레임 `metrics` 절단 짝 검증(`replay_truncated == true` → 동일 `metrics`에 non-empty `truncation_reason`).
- **트랙 집계:** `build_optimization_replay_track_payload`가 `replay_truncated == true`일 때만 `metrics.truncation_reason`을 넣으며, 값은 프레임 순서 기준 **첫** non-empty reason(없으면 in-memory 비정합 시 `"unknown"` — persist 경로는 역직렬화에서 걸러짐).
- **쓰기:** `persist_optimization_replay_frames_to_solver_run`는 직렬화 후 가드 실패 시 저장 생략. `attach_optimization_replay_frames_after_successful_replay_build`는 `invalid_replay_payload` reason으로 스킵.
- **Recorder:** `OptimizationReplayRecorder`가 셀·프레임 상한 절단 시 `truncation_reason`을 함께 기록(`max_replay_cells_per_frame`, `max_replay_frames`).
- **범위 유지:** `optimization_replay_schema_version` / `optimization_replay_truncated` / `optimization_replay_truncation_reason` **sibling 미도입**, 봉투·byte cap·migration **미도입**; **12H**에서 표시 전용 HUD만 추가(§11·§12와 정합).
- **12G 예고:** 읽기 실패 시 `optimization_replay_diagnostic_reason` 등 단일 진단 문자열은 12G; 12F는 shape·절단 짝·트랙 reason 집계만.

**테스트 (추가·갱신):** `tests/unit/shapez_asteroid/test_optimization_ui_payload.py`(가드·집계·역직렬화), `tests/unit/shapez_asteroid/test_solver_optimization_replay_import_boundary.py`(솔버 패키지 문자열 비참조), `tests/unit/asteroid_lab/test_optimization_replay_persist.py`(persist/attach/page 빈 트랙), Recorder 단언 보강 `test_optimization_replay.py`·`test_optimization_replay_skeleton.py`.

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
- DB migration
- payload byte-size cap
- dict 전역 키 화이트리스트의 과도한 확장(필요 시 후속 PR)
```

(표시 전용 **절단·진단 HUD**는 **12H**에서 `asteroid_miner_layout_solver.html` / `asteroid_miner_layout_lab.js`로 도입; 리플레이 시맨틱·Lab 동기화 없음.)

### Sequence 12G — UI payload read adapter

**구현 상태 (v0, 2026-05-17): 완료**

- page context가 persist된 프레임을 읽는다(12F에서 shape·절단 짝은 `deserialize`/`validate`로 이미 고정).
- 실패 시 empty payload + §7.2 진단 문자열(`optimization_replay_diagnostic_reason` 등 — **12G 구현 범위**).
- `metrics.truncation_reason` 노출은 §6.1에 따른다(12F에서 트랙 집계 완료).

### Sequence 12H — Truncation / diagnostic metadata HUD

**구현 상태 (PR8 unified, 2026-05-19): 부분**

- **통합 타임라인:** 제품 replay는 `lab_replay_frames_json` 단일 트랙. dual-track `lab-optimization-replay-data` / `replaceOptimizationReplayPayload` / `renderOptimizationReplayHud` **미사용**.
- **템플릿 SSR:** `lab-replay-truncation-hud`(절단·`diagnostic_reason`·`optimization_replay_diagnostic_reason`), `lab-optimization-replay-attach`(12J, POST attach 전용).
- **클라이언트:** `updateReplayTruncationHud` · `renderOptimizationReplayAttachHud` · `replaceLabReplayPayload`가 metrics/attach를 갱신.
- **금지(유지):** Lab ↔ optimization 암묵적 프레임 동기화, 메타데이터 상호작용(재시도·수리), 솔버·리플레이 의미 변경 없음.

### Sequence 12I — Optimization replay HUD vocabulary hardening (초안)

**목표:** optimization replay HUD에 오르는 **표시용 문자열·코드**를 `status` / `reason` / `diagnostic` **3축**으로 분리해, SSR·클라이언트 재주입(`replaceOptimizationReplayPayload`)·Python 진단 계약이 서로 섞이지 않도록 어휘를 고정한다. **구현은 본 시퀀스 범위에 포함하지 않는다** — 이 절은 문서 정본만 확정한다.

**비목표(12I에서 금지):** Lab map 리플레이와 optimization 오버레이의 **동기화 모드 도입**, `renderOptimizationReplayHud`·오버레이 파이프라인의 **렌더/소유권(ownership) 변경**, 관측용 오버레이를 “완전 표시”하기 위한 **프레임 인덱스·이벤트 순서 강결합**. 오버레이 **완전성(completeness)** 은 구현 후 **관측·메트릭·수동 QA**로만 기록하고, 본 시퀀스는 그 결과를 **문서·테스트 기대값**에 반영하지 않는다(동기화/렌더 책임 변경 없음).

#### 12I.1 3축 정의 (status / reason / diagnostic)

| 축 | 의미(표시·계약) | 소스(개략) | 비고 |
|----|------------------|------------|------|
| **status** | “지금 트랙이 정상 로드됐는지 / 비어 있는지 / 잘렸는지” 등 **사용자 대면 요약** | 트랙 `metrics`의 `frame_count`, `replay_truncated`, empty vs non-empty payload 등에서 **파생** | **솔버·리플레이 시맨틱과 1:1 대응하지 않는다.** HUD 라벨 전용. |
| **reason** | 잘림·절단의 **도메인 이유** (예: `truncation_reason`, recorder 상한) | 프레임 `metrics` → 트랙 `metrics` 집계(§6.1) | §6.1 짝 계약 위반 시 **읽기 경로는 empty + diagnostic** (§7). |
| **diagnostic** | 역직렬화·형상·지원 외 `event_type` 등 **읽기 어댑터 실패 코드** | `metrics.optimization_replay_diagnostic_reason` 및 **쓰기 스킵** 시 attach reason (아래 12I.3) | **메타데이터 전용**; 프레임 순서·이벤트 해석에 관여하지 않음(§7.1·12G와 정합). |

세 축은 **서로 대체 불가**. UI는 한 축의 문자열을 다른 축 라벨에 재사용하지 않도록 **명명 규칙**을 JS·SSR·Python에서 동일하게 맞춘다.

#### 12I.2 JS `enum`/const 매핑 (초안)

- **원칙:** `asteroid_miner_layout_lab.js`(및 Lab 전용 번들)에 **표시용 상수 테이블**을 둔다. 문자열 리터럴을 템플릿·HUD 분기 곳곳에 흩뿌리지 않는다.
- **최소 구성:** (1) **diagnostic 코드** — §7.1과 동일 문자열 집합을 `OPTIMIZATION_REPLAY_DIAGNOSTIC_*` 또는 단일 객체 맵으로 고정. (2) **truncation / status 배지** — `replay_truncated`·`truncation_reason` 표시용 라벨·툴팁 키를 const로 묶는다.
- **i18n:** v0는 한국어/영문 고정 문자열이어도 되나, 키는 **코드 값(diagnostic)** 과 **표시 문자열**을 분리해 후속 i18n PR이 맵만 갈아끼우게 한다.
- **금지:** diagnostic 문자열을 Lab 리플레이 인덱스나 map 스텝과 연동하는 분기(암묵 동기, §9·12H 비목표와 충돌).

#### 12I.3 `optimization_replay_attach.reason` 매핑 (초안)

- **범위:** `attach_optimization_replay_frames_after_successful_replay_build` 등 **persist/attach 쓰기 경로**에서 가드 실패·스킵 시 남기는 **내부 이유 코드**(문서·로그·선택적 메타)와, **페이지에 노출되는** `optimization_replay_diagnostic_reason`을 **표로 대응**시킨다.
- **원칙:** attach reason은 **운영·디버그·회귀 테스트** 우선이며, 반드시 HUD에 그대로 노출할 필요는 없다. 노출 시에는 §7.1에 이미 있는 코드만 사용하거나, **신규 코드는 §7.1 표에 먼저 추가**한 뒤 JS const와 함께 고정한다(문자열 표류 방지).
- **문서 산출물(구현 PR 전):** “attach reason → (optional) diagnostic → HUD 표시 여부” **매핑 표**를 본 절 하위에 두는 것을 권장한다(구현 시 복붙 가능한 한 표).

#### 12I.4 Malformed payload matrix (초안)

아래는 **읽기 경로** 기준 행렬이다. 열: 입력 조건 / 기대 트랙 / `optimization_replay_diagnostic_reason` / `replay_truncated`·`truncation_reason` / 페이지 비파괴. 구현 PR은 각 행에 **단위 테스트 이름**을 한 줄씩 붙인다.

| # | 입력 조건 (config_json `optimization_replay_frames`) | 기대 트랙 | diagnostic (있을 때) | truncation 축 | 비고 |
|---|--------------------------------------------------------|-----------|------------------------|-----------------|------|
| M1 | 키 없음 | empty | `missing_optimization_replay` | 짝 §6.1에 맞는 기본 false/부재 | §7.1 |
| M2 | `[]` | empty | `empty_optimization_replay_frames` | 동상 | |
| M3 | 리스트가 아님·프레임 dict 깨짐·`frame_index` 불연속 등 | empty | `invalid_optimization_replay_payload` | 동상 | |
| M4 | `replay_truncated`와 `truncation_reason` 짝 깨짐 | empty | `invalid_truncation_contract` | 집계 전에 차단 | |
| M5 | 알 수 없는 `event_type` | empty | `unsupported_or_unknown_event_type` | 동상 | |
| M6 | (후속) 봉투·`optimization_replay_schema_version` 불일치 | empty | 별도 코드(§10) | 별도 PR에서 §7.1 확장 | 12I는 **행만 예약**; 코드 문자열은 봉투 PR과 동시 고정 |
| M7 | (후속) 바이트 상한 초과 | empty 또는 정책 택일 | 후속 | 후속 | §14 open decision과 연계 |

**주의:** M1–M5 코드 문자열은 **§7.1 구현값과 동일**해야 한다. 행렬은 **계약 표**이며, 구현 변경 시 §7·§12I·테스트 세 곳을 한 번에 갱신한다.

#### 12I.5 검증 체인: persist → deserialize → `replaceOptimizationReplayPayload` → HUD 보존 (초안)

- **의도:** 저장 직후 한 번 읽어도, **Run Solver JSON 갱신**으로 클라이언트가 `replaceOptimizationReplayPayload`를 탈 때도, **동일 diagnostic·truncation·status 표시**가 유지되는지 회귀한다.
- **권장 테스트 계층:**
  1. **Python:** persist fixture 또는 `SolverRun.config_json` 주입 → `deserialize_optimization_replay_frames_from_json` + `build_optimization_replay_track_payload` → 기대 `metrics` 스냅샷.
  2. **Django page context:** 기존 `test_page_context_malformed_optimization_replay_does_not_crash` 계열 확장 — HTML에 **진단·절단 placeholder**가 기대 문자열을 포함하는지(SSR).
  3. **JS(선택·최소):** `replaceOptimizationReplayPayload` 호출 후 DOM에 HUD 노드가 사라지지 않고, 동일 normalize 경로를 타는지 — **프론트 빌드 정책**에 맞춰 단위 또는 통합 한 건.
- **보존 정의:** “보존”은 **표시 문자열·가시성**이며, **프레임 수·이벤트 내용**이 JSON 갱신으로 바뀌는 것과 혼동하지 않는다. optimization 트랙이 **의도적으로 비워지면** HUD는 empty 상태로 맞추는 것이 정상이다.

#### 12I.6 오버레이 완전성·동기화 (관측만)

- **완전성:** “모든 셀/모든 이벤트가 오버레이에 그려졌는가”는 **관측 지표**(로그, 스크린샷, 수동 체크리스트)로만 기록한다. 12I는 이를 **PASS/FAIL 게이트**로 문서화하지 않는다.
- **금지 재확인:** 프레임 인덱스 동기화, Lab `currentFrameIndex`와 optimization 스텝 맞추기, 오버레이 레이어 소유권 이동, `renderOptimizationReplayHud` 책임 확대 — **전부 비범위**. 문제가 보이면 **버그 리포트·별도 시퀀스**로 분리한다.

**구현 시 스코프 요약:** 3축 어휘·JS const·attach↔diagnostic 매핑 표·M1–M7 행렬·체인 테스트를 **한 PR 또는 12I 전용 소PR 연속**으로 묶되, 각 PR은 §3 output-only·§11 비목표를 위반하지 않는다. (§9 dual-track는 historical — replay timeline 정본 참조.)

### Sequence 12J — Optimization replay attach HUD (POST write channel, 별도 줄)

**구현 상태 (2026-05-17): 완료**

- **목표:** `Accept: application/json` POST 응답의 `optimization_replay_attach` `{ attached, reason }`를 **읽기 진단(`metrics.optimization_replay_diagnostic_reason`)과 섞지 않고**, Optimization Replay 패널에 **`#lab-optimization-replay-attach`** 한 줄로만 노출한다.
- **표시 규칙 (클라이언트):** `formatOptimizationReplayAttachHudLine` — `attached === true` 이고 `reason === "attached"` 이면 `Attach: attached`; `attached === false` 이면 `Attach: skipped (<reason>)` (`reason` 없으면 `unknown`); 메타 없음·비객체·`attached` 비불리언이면 `Attach: —`.
- **렌더:** `renderOptimizationReplayHud(track)`가 status / truncation / diagnostic을 **기존과 동일**으로 갱신한 뒤, 캐시된 POST 값(`optimizationReplayAttachHudRaw`)으로 attach 줄을 갱신한다. `replaceOptimizationReplayPayload`만 호출될 때는 attach 캐시를 바꾸지 않으므로 **마지막 POST의 attach 표시가 유지**된다(읽기 트랙 교체와 쓰기 관측 축 분리).
- **`renderOptimizationReplayAttachHud(raw)`:** POST 처리 경로에서만 호출; 캐시를 갱신한 뒤 `renderOptimizationReplayHud(optimizationReplayTrack)`로 HUD 전체를 다시 그린다.
- **비범위(유지):** 솔버·GA·`optimization_replay_persist` 동작 변경 없음; read diagnostic 의미 변경 없음; `optimization_replay_diagnostic_reason`에 attach reason을 **합치지 않음**; 페이로드 압축·Lab/Optimization 암묵 동기·오버레이 수명 변경 없음.
- **12I.6과의 관계:** 12I.6의 “`renderOptimizationReplayHud` 책임 확대” 비범위는 **오버레이·Lab 인덱스 동기·렌더 소유권 이동**을 가리킨다. 12J는 **POST attach 메타 한 줄(쓰기 관측)** 만 추가한다.

### Sequence 12K — POST attach scalar diagnostics (`evolution_failed` stage)

**구현 상태 (2026-05-17): 완료**

- **목표:** `optimization_replay_attach.reason`은 **기존 어휘를 유지**한 채(특히 `evolution_failed`·`empty_candidate_pool` 등), 실패 원인을 **스칼라 `optimization_replay_attach.diagnostic`** 으로만 구분한다. **읽기 축** `metrics.optimization_replay_diagnostic_reason`(persist 스캔·역직렬화)과 **쓰기 축** attach 진단은 **계속 분리**한다(12J 불변).
- **필드:** `stage`, 후보·리코더 카운트,`best_genome_present`, `evolution_convergence_reason`, (예약) commit/validation 스칼라, `error_type` / 짧은 `error_message` — **프레임 배열·경로·전체 traceback·대형 맵 없음**. 허용 `stage` 값은 코드 상수 `OPTIMIZATION_REPLAY_ATTACH_DIAGNOSTIC_STAGES`로 고정.
- **경로:** `django_apps/web/services/asteroid_lab_post_inspection_evolution.py`에서 단계 변수로 예외 매핑; `optimization_replay_persist.attach_optimization_replay_frames_after_successful_replay_build`는 attach 실패 시 `replay_serialization` / `attach_persist` 등 단계를 병합. `public_pages` JSON·INFO 로그에 `diagnostic.stage`를 노출(추가 HUD 줄 **비목표**).
- **비범위(유지):** 솔버·GA·후보 생성·incremental commit·검증 **의미 변경 없음**; Lab/optimization 리플레이 동기·오버레이·페이로드 압축 없음.
- **테스트(회귀):** `tests/unit/asteroid_lab/test_optimization_replay_persist.py`의 12K 전용 케이스(`evolution_search` 예외는 후보 풀을 테스트 헬퍼로 고정), `tests/integration/web/test_asteroid_miner_layout_solver.py`의 `test_post_json_attach_diagnostic_does_not_overwrite_read_diagnostic` 등.

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

- `test_ui_payload_preserves_dual_track_no_sync` (historical 이름 — unified 마이그레이션 시 단일 timeline·output-only 경계 테스트로 대체 예정)
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
| Dual-track | **Deprecated** → replay timeline ([`asteroid_lab_09_replay_timeline`](asteroid_lab_09_replay_timeline.md)) |
| 12F-v0 | 프레임 리스트 가드만; 봉투·HUD·cap·migration **제외** |
| 12I (초안, 미구현) | §12I: HUD **status / reason / diagnostic** 3축·JS const·`optimization_replay_attach.reason`↔diagnostic 매핑·malformed 행렬(M1–M7)·persist→deserialize→`replaceOptimizationReplayPayload`→HUD **표시 보존** 테스트; 오버레이 완전성·동기화/렌더 ownership 변경 **비범위(관측만)** |
| 12J (구현 완료) | §12J: POST **`optimization_replay_attach` 전용 HUD 줄** (`Attach: …`); read **`optimization_replay_diagnostic_reason` 불변**; 솔버/attach/persist **비변경** |
| 12K (구현 완료) | §12K: attach **`reason` 어휘 유지** + **`diagnostic` 스칼라**(`stage`·카운트·짧은 오류); read 진단과 분리; 솔버 의미·동기화 **비변경** |
## Sequence 12L 좌표 경계 보강 (2026-05-17)

- Critical invariant: decode/import normalization이 Server X/Y를 만든 뒤에는 알고리즘 코드에서 raw 좌표가 불법이다.
- optimization replay write path는 solver output 관측 계층이며, 입력 구성은 Server X/Y만 사용한다.
- post-inspection evolution은 `build_optimization_input` 이후 raw 좌표 변환기를 호출하지 않는다.
- Island-local `x`/`y`만 replay `map_view`·Lab HUD에 노출; `server_*` 필드는 레거시 JSON read-compat에서도 UI·wire **금지**.
- **Hardening:** `test_coordinate_frame_ast_gate`, `test_import_boundaries`, POST `test_post_json_optimization_input_does_not_raw_convert_server_coords`.
- 12L에서 UI/overlay projection 변경은 범위 밖이다. projection boundary 문제가 발견되면 별도 UI/export boundary 작업으로 분리한다.
