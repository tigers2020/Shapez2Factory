---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
related_docs:
  - documents/Algorithm/solver_runtime/README.md
  - documents/Algorithm/asteroid_lab_10_development_sequence.md
  - documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md
---

# Architecture Reconciliation — Runtime vs 레거시 문서

**역할:** Solver Runtime Architecture Reviewer  
**목적:** Runtime 시리즈와 `asteroid_lab_*`·삭제된 `shapez_asteroid` 인용 간 충돌을 한곳에서 해소한다.

## 1. 본 시리즈의 정체 (충돌 #1)

### 판정

Runtime 문서는 **「Solver 버튼 E2E 파이프라인 v0」의 계약·PR 체크리스트**이다.  
**「저장소 전체 optimization이 미착수」** 뜻이 **아니다.**

### 두 축을 분리한다

| 축 | 의미 | 정본 |
|----|------|------|
| **Runtime execution order** | 버튼 1회 클릭 시 A→M **실행 순서** | Phase 문서·README 파이프라인 |
| **Implementation order (PR)** | 개발·리뷰·merge **단위** | [`implementation_sequence.md`](implementation_sequence.md) |
| **Code inventory** | 이미 `django_apps/asteroid_lab/optimization/` 에 있는 모듈 | 아래 §5 표 |
| **Legacy narrative** | GA·`BundlePattern`·`shapez_asteroid` pytest 경로 | [`asteroid_lab_*`](../) — **역사·설계 참고**, Runtime PR 완료 증명 아님 |

### `asteroid_lab_10` 과의 관계

- [`asteroid_lab_10_development_sequence.md`](../asteroid_lab_10_development_sequence.md) 상단 베이스라인(2026-05-18): optimization 체크리스트를 **`[ ]` 미착수로 재설정**한 것은 **문서 추적용**이며, 코드 삭제를 뜻하지 않는다.
- [`asteroid_lab_12_runtime_replay_wiring.md`](../asteroid_lab_12_runtime_replay_wiring.md) 의 12F–12L 등 **「구현 완료」** 는 **Lab replay persist/read/HUD 경계**에 한정된다. Solver Runtime Phase C–K와 **동일 PR이 아니다.**

**Runtime PR 표의 「미착수」** = **해당 PR의 Solver-button 계약·테스트가 아직 green이 아님** (또는 orchestration 미연결).  
**≠** 레거시 문서에 적힌 개념이 코드에 없음.

---

## 2. 패키지 경계 (충돌 #2)

### 판정 (저장소 2026-05-19)

```text
django_apps/shapez_asteroid/  — 저장소에서 제거됨 (git 기록만)
django_apps/asteroid_lab/optimization/  — 유일한 optimization 구현 패키지
```

### 정본

| 역할 | 경로 |
|------|------|
| **신규 Runtime PR (PR1–7)** | `django_apps/asteroid_lab/optimization/` |
| **Lab ORM·decode·reconstruction·Lab replay** | `django_apps/asteroid_lab/` (optimization 밖) |
| **레거시 인용** | `tests/unit/shapez_asteroid/`, `django_apps.shapez_asteroid` — **금지·역사**; 새 import 추가 금지 |

**금지:** Runtime 문서·코드에 `shapez_asteroid.optimization` 을 “현재 패키지”로 서술하거나 import.

---

## 3. v0 선택기: greedy vs GA (충돌 #3)

### 판정

**Solver Button v0 정본 = A: capacity-aware greedy selector only** ([`phase_i_candidate_selection.md`](phase_i_candidate_selection.md), [OD-4](open_decisions.md)).

| 항목 | Runtime v0 | 레거시 (`asteroid_lab_05`/`06`, `asteroid_lab_10` Seq 4–5) |
|------|------------|--------------------------------------------------------------|
| 선택 | PR4 greedy | Evolution Search v0·`Genome`·`Gene.commit_order` |
| 용도 | **참고·향후 v1** | Solver 버튼 v0 **필수 경로 아님** |

DTO에 `EvolutionConfig`·`EvolutionConvergenceReason` 등이 있어도 **Solver orchestration v0는 GA를 호출하지 않는다** (필드는 schema 자리).

---

## 4. 좌표 용어 (충돌 #4)

### 정본 (alias 금지)

| 이름 | 의미 |
|------|------|
| `fixed_output_transport` | extractor 출력 직후 **첫 belt/pipe 예약 셀** (offset `(1,0)` from extractor, canonical E) |
| `route_probe_start` | route search **시작 셀** (offset `(2,0)`; **occupied 아님**) |
| `output_stub` | **레거시** — Runtime·신규 코드·DTO 필드명 **사용 금지** |

레거시 [`asteroid_lab_04`](../asteroid_lab_04_route_probe.md) 의 `output_stub` 는 읽을 때 **`route_probe_start`로 mentally 치환**한다.

`CandidateRejectReason.output_stub_*` enum 값은 **레거시 이름 유지** 가능하나, 의미는 `route_probe_start` ([`phase_f_geometry_validation.md`](phase_f_geometry_validation.md)).

Materialization: [OD-1](open_decisions.md) — reservation path **앞에** `fixed_output_transport` prepend 권장.

---

## 5. 코드 인벤토리 vs Runtime PR (상태 분리)

**코드에 존재** ≠ **Runtime PR 완료** (통합 테스트·§0.3·orchestration·이벤트 계약 포함).

| 모듈·계약 | 코드 | Runtime PR | 비고 |
|-----------|------|------------|------|
| DTO·enum·`RouteDomainSnapshotBuilder` | 있음 | 1A (레거시 Seq) | PR 표에는 PR1B와 함께 소비 |
| `optimization_input_from_reconstruction` | 있음 | **PR1B 완료** | `LoadedReconstructionSnapshot`·`mineable_field_kind` (§0.3 adapter) |
| `GeneTemplate`·projection | 있음 | **PR1 완료** | |
| `candidate_geometry`·`route_probe` | 있음 | **PR2 완료** | `provisional_blocked_cells` |
| capacity·route goal planner | 있음 | **PR2.5 완료** | |
| candidate pool (`GeneCandidate`, dedupe, truncate) | 있음 | **PR3 완료** | |
| candidate selection (score, greedy, `SelectedCandidatePlan`) | 있음 | **PR4 완료** | materializer는 PR6 |
| incremental commit (`commit_selected_candidates`, reservation overlay) | 있음 | **PR5 완료** | PR6 materializer·PR7 orchestration |
| Solver A→M orchestration | 없음 | PR7 미착수 | |
| Lab optimization replay persist/read (12F–12L) | Lab/web 측 **별도** | PR7 **재사용** | 아래 §6 |

---

## 6. Replay persist (충돌 #6)

### 판정

PR7 Phase M은 **새 persist 스택을 처음부터 만들지 않는다.**

### 정본

```text
기존: SolverRun.config_json · optimization replay frame list · read validation · HUD diagnostic
      (asteroid_lab_12, web Lab JS, replay pipeline — 구현·테스트 이미 존재할 수 있음)
신규: Solver Runtime이보내는 event_type 집합을 기존 writer/reader에 thin adapter로 연결
금지: 12F–12L semantics 재구현, Lab↔Optimization 암묵 동기화
```

상세: [`phase_m_persist_replay_ui.md`](phase_m_persist_replay_ui.md).

---

## 7. 권장 구현 순서 (PR) vs 실행 순서 (Phase)

### Runtime execution order (버튼 1회)

```text
A → B → C → D → E → F → G → H → I → J → K → L → M
```

### Implementation order (merge 단위)

```text
PR1 (완료) → PR1B (부분) → PR2.5 → PR2 → PR3 → PR4 → PR5 → PR6 → PR7
```

PR1이 Phase D를 먼저 끝낸 것은 **유전자 계약 고정** 목적이며, 런타임 실행 시에는 D는 C 이후·E 이전에 호출된다.

---

## 8. 리뷰 결론 체크리스트

- [x] 정본 패키지: `django_apps/asteroid_lab/optimization/`
- [x] v0 선택기: greedy only; GA = legacy reference
- [x] 용어: `route_probe_start` / `fixed_output_transport`; `output_stub` legacy
- [x] PR 표 vs 코드 인벤토리 분리
- [x] PR7 replay: thin adapter·기존 wiring 재사용

변경 시 본 문서와 [`README.md`](README.md) PR 표를 **함께** 갱신한다.

---

## 9. 구현자 오해 방지 (2차 리뷰, 2026-05-19)

| 항목 | 정본 |
|------|------|
| **PR2.5 선행** | PR1B → **PR2.5** → PR2. `route_probe`는 planned `RouteGoal` 필요. README PR 표 하단 1줄 참고. |
| **`route_goals`** | Phase B: seed/empty only. Phase C: planned 정본. |
| **Candidate route domain** | `provisional_blocked_cells=` 권장; `committed_occupied_cells=`는 과도기·commit과 혼동 금지 ([`phase_g_route_probe.md`](phase_g_route_probe.md)). |
| **신규 테스트명** | `route_probe_start_*`; enum `output_stub_*` 값은 유지·rename 금지 ([`00_core_principles.md`](00_core_principles.md) §0.7). |
