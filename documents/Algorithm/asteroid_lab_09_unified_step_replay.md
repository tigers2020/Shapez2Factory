# Phase 9 — Unified Step Replay Timeline

**상태:** `ACTIVE` (제품 replay 정본)  
**이전 정본:** [`asteroid_lab_09_replay_debug.md`](asteroid_lab_09_replay_debug.md) — dual-track 정책 **폐기(deprecated)**  
**페이로드 스케일:** [`asteroid_lab_13_replay_payload_scalability.md`](asteroid_lab_13_replay_payload_scalability.md)  
**런타임 배선:** [`asteroid_lab_12_runtime_replay_wiring.md`](asteroid_lab_12_runtime_replay_wiring.md)

---

## Purpose

Blueprint import부터 final validation까지 **solver lifecycle 전체**를 **하나의 2D map replay timeline**으로 재생한다.

```text
Blueprint Import
→ Decode
→ Reconstruction
→ Optimization Input
→ Candidate Generation
→ Route Probe
→ Genome / Fitness
→ Evolution
→ Incremental Commit / Rollback
→ Final Validation
→ Final Layout
```

위 모든 단계는 **동일한 global `frame_index`** 아래 등록되며, **모든 프레임은 2D map에서 직접 렌더**되어야 한다.

---

## North Star

```text
There is exactly one product replay timeline.
Every solver lifecycle step that changes or observes the map must emit a 2D-renderable frame.
The replay timeline shows the complete story from blueprint decode to final validated layout.
```

한국어:

```text
제품 replay timeline은 하나만 존재한다.
맵을 변경하거나 관측하는 모든 solver lifecycle step은 2D 렌더 가능한 frame을 emit해야 한다.
replay timeline은 blueprint decode부터 최종 validation layout까지 전체 과정을 보여준다.
```

---

## Deprecated (이전 dual-track 정책)

아래 문장·정책은 **더 이상 제품 목표가 아니다.** 구현·리뷰·테스트 설계 시 **적용하지 않는다.**

```text
Deprecated:
The previous dual-track Lab replay / Optimization replay policy is obsolete.
The product replay model is now a single unified step timeline.
Optimization events must be projected into 2D map frames, not displayed as HUD-only metadata.
```

**폐기된 구체 정책:**

| 폐기 항목 | 이유 |
|-----------|------|
| Lab replay authoritative / Optimization replay metadata only | 단일 timeline; optimization 이벤트도 map frame으로 승격 |
| Run Solver가 Lab timeline을 바꾸지 않음 | 전 lifecycle이 **같은** timeline에 append |
| Lab `frame_index` ↔ Optimization `frame_index` 연결 금지 | **하나의** monotonic global index |
| 별도 optimization play/scrubber/인덱스 | UI controller **하나**만 |
| 11A/11B를 optional overlay | **핵심** map projection·렌더 파이프라인(Sequence 9C–9E) |

역사적 dual-track·13A·13B 계측 상세: [`asteroid_lab_09_replay_debug.md`](asteroid_lab_09_replay_debug.md) (보관·링크 유지용).

---

## Core Contract

| 불변 | 설명 |
|------|------|
| **One timeline** | 제품 UI는 replay controller **하나**만 소유 |
| **2D-renderable frames** | 모든 프레임은 `map_view`를 가짐 (metadata-only frame 금지) |
| **Phase, not track** | decode / route_probe / commit 등은 **별도 트랙이 아니라** `phase` 마커 |
| **Global monotonic index** | `frame_index`는 전 lifecycle에서 단조 증가 |
| **Output-only** | solver·GA·commit·validation은 replay payload를 **읽지 않음** |
| **Inspector secondary** | HUD/inspector는 **선택 프레임 설명**만; map이 1차 |

```text
Replay is output-only.
The unified replay timeline is an output-only artifact.
The solver must never read replay to decide the next step.
```

**유지:** replay on/off·기록 여부가 **동일 입력·동일 seed**에서 best genome·best fitness·final layout에 영향을 주면 안 됨.

---

## DTO (정본)

### `UnifiedReplayFrame`

```python
@dataclass(frozen=True)
class UnifiedReplayFrame:
    frame_index: int
    phase: ReplayPhase
    event_type: ReplayEventType
    title: str
    description: str
    map_view: ReplayMapView
    inspector: Mapping[str, Any]
    metrics: Mapping[str, Any]
```

- `inspector`: 후보 id, 비용, reject reason, fitness 요약 등 **UI 설명** (algorithm input 금지).
- `metrics`: 스칼라 스냅샷·truncation 플래그 (표시·로그 전용).

### `ReplayMapView`

모든 프레임은 아래 중 **최소 하나**로 map을 표현해야 한다.

```text
base_ref (snapshot keyframe 참조)
full_cells (전체 스냅샷)
cell_delta (자재화된 셀 변경)
overlay_cells (probe path, candidate bundle, highlight 등)
annotations (라벨·실패 이유·goal marker)
bbox (camera / clip)
```

```python
@dataclass(frozen=True)
class ReplayMapView:
    base_ref: str | None
    full_cells: tuple[ReplayCell, ...]
    cell_delta: tuple[ReplayCellDelta, ...]
    overlay_cells: tuple[ReplayOverlayCell, ...]
    annotations: tuple[ReplayAnnotation, ...]
    bbox: BBox
```

**부족한 예 (제품 frame 아님 — HUD 이벤트로만 허용, timeline에 단독 등록 금지):**

```json
{
  "event_type": "genome.evaluated",
  "metrics": {"fitness_total": 12.5}
}
```

**정본 frame 예:**

```json
{
  "frame_index": 42,
  "phase": "route_probe",
  "event_type": "route_probe.succeeded",
  "title": "Route probe succeeded",
  "description": "Candidate cand_017 reached external margin.",
  "map_view": {
    "base_ref": "reconstruction_complete",
    "full_cells": [],
    "cell_delta": [],
    "overlay_cells": [
      {"x": 12, "y": 5, "kind": "route_probe_path", "transport": "shape_belt"},
      {"x": 13, "y": 5, "kind": "route_probe_path", "transport": "shape_belt"}
    ],
    "annotations": [
      {"x": 12, "y": 5, "label": "stub"},
      {"x": 20, "y": 5, "label": "external goal"}
    ],
    "bbox": {"min_x": 10, "min_y": 4, "max_x": 22, "max_y": 7}
  },
  "inspector": {
    "candidate_id": "cand_017",
    "cost": 8,
    "reached_goal_kind": "external_margin"
  },
  "metrics": {
    "reached_goal_kind": "external_margin",
    "goal_priority": 2
  }
}
```

### `ReplayPhase`

```python
class ReplayPhase(StrEnum):
    DECODE = "decode"
    RECONSTRUCTION = "reconstruction"
    OPTIMIZATION_INPUT = "optimization_input"
    PATTERN_GENERATION = "pattern_generation"
    CANDIDATE_GENERATION = "candidate_generation"
    ROUTE_PROBE = "route_probe"
    GENOME_FITNESS = "genome_fitness"
    EVOLUTION = "evolution"
    INCREMENTAL_COMMIT = "incremental_commit"
    ROLLBACK = "rollback"
    VALIDATION = "validation"
    RESULT = "result"
```

### `ReplayEventType`

`event_type`은 **자유 문자열 금지**. enum·const와 테스트를 동시 갱신한다.

**Lifecycle (decode ~ reconstruction):**

```text
decode.started | decode.completed
reconstruction.started | reconstruction.completed
optimization.input_loaded
```

**Optimization (기존 optimization replay 이벤트 — map frame으로 승격):**

```python
class ReplayEventType(StrEnum):
    OPTIMIZATION_INPUT_LOADED = "optimization.input_loaded"
    PATTERN_GENERATED = "pattern.generated"
    CANDIDATE_GENERATED = "candidate.generated"
    CANDIDATE_REJECTED = "candidate.rejected"
    ROUTE_PROBE_SUCCEEDED = "route_probe.succeeded"
    ROUTE_PROBE_FAILED = "route_probe.failed"
    GENOME_GENERATED = "genome.generated"
    GENOME_EVALUATED = "genome.evaluated"
    GENERATION_COMPLETED = "generation.completed"
    BEST_GENOME_SELECTED = "best_genome.selected"
    ROUTE_COMMIT_ATTEMPTED = "route.commit_attempted"
    ROUTE_COMMITTED = "route.committed"
    ROUTE_ROLLED_BACK = "route.rolled_back"
    VALIDATION_COMPLETED = "validation.completed"
    VALIDATION_FAILED = "validation.failed"
    RESULT_LAYOUT = "result.layout"
```

**하위 호환:** 구현 전환 기간 `OptimizationReplayEventType` 값 문자열은 위와 **동일 value**를 유지할 수 있다. 제품 DTO 이름은 `ReplayEventType` / `UnifiedReplayFrame`으로 통일한다.

---

## Frame Types

| 유형 | `map_view` 패턴 | 용도 |
|------|-----------------|------|
| **snapshot** | `full_cells` 또는 `base_ref` + 빈 delta | decode/reconstruction 완료, commit 후 materialized state |
| **delta** | `cell_delta` | transport 셀 자재화, rollback 제거 |
| **overlay** | `base_ref` + `overlay_cells` | probe path, candidate bundle, genome highlight |
| **annotation** | overlay + `annotations` | reject reason, goal, validation issue |
| **synthetic checkpoint** | named `base_ref` only | 대형 맵에서 키프레임; 이후 delta/overlay가 참조 |

---

## Solver Event → 2D Frame (승격 계약)

optimization·solver 내부 이벤트는 **관측용 로그가 아니라** `UnifiedReplayFrame`으로 기록한다.

| `event_type` | `phase` | `map_view` 요구 |
|--------------|---------|-----------------|
| `candidate.generated` | `candidate_generation` | bundle occupied cells + output stub overlay |
| `candidate.rejected` | `candidate_generation` | 실패 위치 + `candidate_reject_reason` annotation |
| `route_probe.succeeded` | `route_probe` | probe path + reached goal marker |
| `route_probe.failed` | `route_probe` | expanded frontier / blocked area + failure annotation |
| `genome.evaluated` | `genome_fitness` | selected candidate set overlay + fitness는 inspector/metrics |
| `best_genome.selected` | `genome_fitness` | best bundle set highlight |
| `route.commit_attempted` | `incremental_commit` | candidate + planned route preview overlay |
| `route.committed` | `incremental_commit` | `cell_delta`로 transport cells materialize |
| `route.rolled_back` | `rollback` | rollback 대상 path 제거 또는 red-flash overlay |
| `validation.completed` | `validation` | final issues / passed markers |
| `validation.failed` | `validation` | issue cells + `issue_code` annotations |
| `result.layout` | `result` | final validated layout snapshot |

**좌표:** Server X/Y dense → Lab world 투영은 **Sequence 9C** adapter에서만 수행. 알고리즘 계층은 replay를 읽지 않는다.

---

## UI Contract

**단일 controller (Lab 페이지):**

```text
#lab-timeline-play
#lab-timeline-slider
#lab-timeline-current-frame
```

| MUST | 설명 |
|------|------|
| One play / pause | 전 lifecycle 재생 |
| One scrubber | global `frame_index`만 이동 |
| One current frame label | `frame_index` + `phase` (+ 선택 `event_type`) |
| Map updates every frame | 2D grid는 **항상** `map_view`에서 derive |
| Inspector / HUD | 현재 프레임의 `inspector`·`metrics`만 표시 |
| No second optimization timeline | `optimizationReplayFrameIndex` 등 **독립 인덱스 제거** (마이그레이션 목표) |

**Phase UI:** 타임라인을 쪼개지 않고, 스크러버 위 **phase marker** 또는 프레임 메타로 구간 표시.

---

## v0 스케일·payload 정책

Overview **「활성 좌표 ≤50 전후」**에서는 프레임당 full snapshot을 허용한다. 대용량은 [`asteroid_lab_13`](asteroid_lab_13_replay_payload_scalability.md) 로드맵을 따른다.

**코드 상수 (트랙별, 정본: `django_apps/asteroid_lab/replay/replay_limits.py`):**

| 상수 | 값 | 적용 |
|------|-----|------|
| `MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME` | 128 | optimization in-memory recorder (`visible_cells` + `overlay_cells`) |
| `MAX_OPTIMIZATION_REPLAY_FRAMES` | 500 | optimization recorder 프레임 수 |
| `MAX_UNIFIED_LAB_REPLAY_CELLS_PER_FRAME` | 2000 | Lab / unified adapter·composer (9B는 truncate 미적용) |
| `MAX_UNIFIED_LAB_REPLAY_FRAMES` | 500 | 통합 timeline 목표 상한 (9D composer) |

`optimization/replay_frame.py`의 `MAX_REPLAY_*`는 **optimization 트랙 별칭**(deprecated 이름)이다.

초과 시 프레임 요약·기록 중단; `metrics.replay_truncated = true`, 선택 `replay_omit_reason`.

**통합 timeline (9D+):** composer가 Lab·Optimization 프레임을 합칠 때 위 상한을 **트랙별로** 적용한다. dual-track별 상한 폐기.

---

## Development Sequence (Phase 9)

기존 Sequence 11A/11B(optional overlay)는 **핵심 파이프라인**으로 재번호한다.

| ID | 목표 | 산출 |
|----|------|------|
| **9A** | `UnifiedReplayFrame` DTO + enum + JSON 직렬화 + 계약 단위 테스트 | `django_apps/asteroid_lab/replay/unified_*.py` |
| **9B** | Lab `ReplayFrame` / snapshot 이벤트 → `UnifiedReplayFrame` adapter | `phase=decode` / `reconstruction`; 9D baseline |
| **9C** | Optimization 이벤트 → 2D `map_view` adapter | **완료** — `optimization_unified_adapter.py` |
| **9D** | Timeline composer | **완료** — `unified_timeline_composer.py` |
| **9E** | Single controller UI | 하나의 play/scrubber; phase markers |
| **9F** | Commit frame materialization | `route.committed` → `cell_delta` |
| **9G** | Validation/result keyframes | `validation.*`, `result.layout` snapshots |
| **9H** | Payload scale strategy | 13 시리즈와 정렬; lazy-load·delta는 **의미 동일** 하에 |

### 9A 착수 조건 / 금지

**범위 (9A만):**

```text
UnifiedReplayFrame, ReplayMapView, ReplayCell, ReplayCellDelta,
ReplayOverlayCell, ReplayAnnotation, ReplayPhase, ReplayEventType
+ JSON-safe serialization + invariant unit tests
```

**금지 (9A):**

```text
- JS controller 변경 (asteroid_miner_layout_lab.js)
- ReplayFrame ORM / migration 변경
- Solver algorithm 변경
- optimization_replay_persist 구조 변경
- payload lazy-load 변경
- timeline composer (9D)
- replay를 algorithm 입력으로 사용
- dual-track runtime 제거 (legacy 코드는 유지)
```

**금지 (9A–9H 공통):**

```text
replay를 solver / GA / commit / validation 입력으로 사용
metadata-only frame을 timeline에 단독 등록
두 번째 optimization timeline controller 유지 (목표 상태)
암묵적 Lab↔Optimization index sync (deprecated 정책 재도입)
```

### 9B — Lab adapter (구현 완료)

**산출:** `django_apps/asteroid_lab/replay/lab_unified_adapter.py`, `unified_event_coverage.py`, `replay_limits.py`

**체크리스트:**

```text
[x] lab frame adapter (`lab_snapshot_event_to_unified`, `lab_replay_row_to_unified`)
[x] Lab frame_index → unified frame_index 보존 (9D 전 composer 이전)
[x] phase 매핑: decode → DECODE; reconstruction·layout_cleanup → RECONSTRUCTION
[x] event_type 고정 매핑표 (`LAB_EVENT_TYPE_TO_UNIFIED`)
[x] full_map → ReplayCell; bbox min_x/min_y/max_x/max_y
[x] inspector/metrics output-only passthrough (`lab_event_type` 등 보존)
[x] malformed / 미지원 Lab frame → LabUnifiedAdapterError
[x] source mutate 금지 (단위 테스트)
[x] deterministic JSON round-trip
[x] ReplayEventType coverage matrix (9B / 9C / post-9B partition)
```

**금지 (9B):** optimization projection, delta 압축, lazy-load, JS, ORM, persist, solver 변경.

#### 9B Lab `event_type` → unified `ReplayEventType` (출력)

| Lab `event_type` | Unified |
|------------------|---------|
| `decode.raw_loaded` | `decode.started` |
| `decode.normalized` | `decode.completed` |
| `reconstruction.begin` … `reconstruction.mineable_finalized` | `reconstruction.started` |
| `reconstruction.map_complete` | `reconstruction.completed` |
| `replay.snapshot.cleanup_*` / `replay.snapshot.reconstruction` | `reconstruction.started` (`layout_cleanup` phase 포함) |

**9B 거부:** `candidate.*`, `routing.*`, `ga.*`, `existing_layout.*`

**테스트:** `tests/unit/asteroid_lab/test_unified_replay_lab_adapter.py`, `test_unified_replay_event_coverage_matrix.py`, `test_replay_limits.py`

### 9C — Optimization adapter (구현 완료)

**산출:** `django_apps/asteroid_lab/replay/optimization_unified_adapter.py`, `projection_context.py`, `replay_recording_cells.py`, `unified_event_coverage.SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER`

**체크리스트:**

```text
[x] optimization frame adapter (`optimization_replay_frame_to_unified`)
[x] Server dense → Lab raw (x,y) projection (`ReplayProjectionContext.server_xy_params`)
[x] `visible_cells` → `map_view.full_cells`; `overlay_cells` → `overlay_cells`
[x] `REPLAY_EVENT_TYPE_TO_PHASE` (21 optimization event types)
[x] inspector `optimization_event_type` / `source_frame_index` 보존
[x] metrics annotation keys (`candidate_reject_reason`, `route_probe_failure_reason`, `reached_goal_kind` + 좌표)
[x] `fallback_full_cells` / `base_ref`로 renderable 보수적 wrapping
[x] non-renderable → `OptimizationUnifiedAdapterError`
[x] source mutate 금지 (단위 테스트)
[x] Runtime recorder: `visible_cell_dicts_from_loaded` / materialization overlay (output-only)
[x] coverage matrix: `SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER` (21)
```

**금지 (9C):** timeline composer(9D), JS, ORM, `optimization_replay_persist` 키 변경, solver·GA·commit·validation 입력에 replay 사용.

#### 9C `ReplayEventType` → `ReplayPhase` (요약)

| 그룹 | `ReplayPhase` |
|------|----------------|
| `optimization.input_loaded`, `capacity.plan_created`, `route_goal.generated` | `optimization_input` |
| `pattern.generated` | `pattern_generation` |
| `candidate.*`, `candidate_pool.completed`, `candidate_selection.completed` | `candidate_generation` |
| `route_probe.*` | `route_probe` |
| `genome.*`, `best_genome.selected` | `genome_fitness` |
| `generation.completed` | `evolution` |
| `route.commit_*`, `route.materialized` | `incremental_commit` |
| `route.rolled_back` | `rollback` |
| `validation.*` | `validation` |
| `result.layout` | `result` |

**테스트:** `test_unified_replay_optimization_adapter.py`, `test_server_to_lab_projection.py`, `test_solver_runtime_pipeline.py` (visible_cells)

**import:** `optimization_unified_adapter`는 `replay/__init__.py`에서 re-export하지 않음 (`optimization.replay_frame` ↔ circular import 방지). 호출부는 submodule 직접 import.

### 9D — Timeline composer (구현 완료)

**산출:** `django_apps/asteroid_lab/replay/unified_timeline_composer.py` — `compose_unified_timeline`

**체크리스트:**

```text
[x] Lab unified frames → optimization unified frames 순서로 concat
[x] global `frame_index` 0..n-1 재부여
[x] `inspector.source_frame_index`에 트랙별 원본 index 보존
[x] `MAX_UNIFIED_LAB_REPLAY_FRAMES` 초과 시 head truncate + 마지막 프레임 `replay_truncated` / `truncation_reason`
[x] per-frame cell 재-truncate 없음 (adapter 책임)
```

**금지 (9D):** page context, JS, persist, dual-track 제거(9E), algorithm 입력.

**테스트:** `test_unified_timeline_composer.py`

---

## Metrics (inspector 보조)

`metrics` 권장 키 (표시·로그 전용; 탐색 루프 미참조):

```text
reached_goal_kind
goal_priority
route_probe_failure_reason
candidate_reject_reason
fitness_total
fitness_breakdown
commit_conflict_reason
evolution_convergence_reason
route_reservation_id
reservation_state
replay_truncated
replay_omit_reason
```

---

## Invariants (체크리스트)

```text
[ ] UnifiedReplayFrame 직렬화 가능
[ ] 모든 프레임에 renderable map_view (full_cells | cell_delta | overlay_cells 중 ≥1 또는 base_ref 키프레임)
[ ] frame_index 전 lifecycle 단조 증가
[ ] event_type ∈ ReplayEventType (자유 문자열 금지)
[ ] phase ∈ ReplayPhase
[ ] replay 기록 on/off 동일 seed → 동일 best genome·fitness·final layout
[ ] scrubber가 unified timeline만 제어 (두 번째 optimization controller 없음)
[ ] HUD/inspector가 map 렌더를 대체하지 않음
[ ] v0 MAX_REPLAY_* 및 replay_truncated 동작
```

---

## Test Plan

| 테스트 | 검증 |
|--------|------|
| `test_unified_replay_frame_serializable` | DTO round-trip |
| `test_unified_replay_frame_indices_monotonic` | global index |
| `test_every_frame_has_renderable_map_view` | map_view 비어 있지 않음 (계약 helper) |
| `test_replay_events_do_not_affect_algorithm_result` | output-only |
| `test_replay_same_seed_on_off_identical_best_genome` | 부작용 없음 |
| `test_unified_timeline_single_controller` | DOM/JS: optimization 전용 scrubber 부재 (목표) |
| `test_replay_large_payload_truncation` | MAX_REPLAY_* |
| `test_replay_event_type_is_enum` | 자유 문자열 거부 |

기존 회귀: `test_manual_snapshot_replay_not_used_as_algorithm_input_doc`, `test_lab_js_replay_wiring_smoke` — **unified timeline** 기준으로 갱신 예정.

---

## Related Documents

| 문서 | 관계 |
|------|------|
| [`asteroid_lab_13_replay_payload_scalability.md`](asteroid_lab_13_replay_payload_scalability.md) | POST 크기·lazy-load·delta (timeline **의미** 유지) |
| [`asteroid_lab_10_development_sequence.md`](asteroid_lab_10_development_sequence.md) | 구현 순서표 — 9A–9H 반영 필요 |
| [`asteroid_lab_12_runtime_replay_wiring.md`](asteroid_lab_12_runtime_replay_wiring.md) | attach·diagnostic·런타임 배선 |
| [`asteroid_lab_09_replay_debug.md`](asteroid_lab_09_replay_debug.md) | **Deprecated** dual-track·13A·13B 역사 |

---

## 완료 조건 (제품)

```text
[ ] UnifiedReplayFrame + ReplayMapView + ReplayPhase + ReplayEventType
[ ] Timeline composer가 decode → result까지 단일 frames[] emit
[ ] 모든 optimization 이벤트가 2D map_view를 가짐
[ ] UI 단일 play/scrubber/current-frame
[ ] output-only invariant 테스트 통과
[ ] asteroid_lab_09_replay_debug dual-track 정책 코드·문서에서 제거 또는 feature-flag off
```
