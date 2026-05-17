# Phase 9 — Replay and Debug Artifact

## 목적

Optimization 과정을 UI에서 frame-by-frame으로 확인할 수 있게 한다.

## 원칙

Replay/debug artifact는 output 전용이다.

```text
Not algorithm input.
```

## v0 스케일·payload 정책

Overview **「활성 좌표 ≤50 전후」** 전제에서는 프레임당 `visible_cells`·`overlay_cells`를 **full snapshot**으로 유지해도 된다. 이 범위에서 **delta frame 압축·셀 참조 테이블·공유 immutable snapshot**은 **필수 아님**(v1+ 대용량으로 스케일업할 때 검토).

대신 런어웨이 방지를 위해 **문서 상수(구현에서 override 가능하되 기본값 고정)**:

```text
MAX_REPLAY_CELLS_PER_FRAME = 128
MAX_REPLAY_FRAMES = 500
```

`len(visible_cells)+len(overlay_cells) > MAX_REPLAY_CELLS_PER_FRAME`이면 프레임을 잘리거나 요약하고, 누적 프레임이 `MAX_REPLAY_FRAMES`를 넘으면 이후 이벤트 기록을 중단한다. 이 경우 `metrics`에 **`replay_truncated: true`**(및 선택적으로 `replay_omit_reason`)를 넣는다.

## Replay Event 타입

`event_type`은 **자유 문자열 금지**. `OptimizationReplayEventType` enum으로 고정한다.

아래 문자열은 **멤버 값(value)** 또는 멤버 이름과 1:1로 맞춘다 (프로젝트에서 하나만 채택).

```python
class OptimizationReplayEventType(Enum):
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
```

## Frame Payload

```python
@dataclass(frozen=True)
class OptimizationReplayFrame:
    frame_index: int
    event_type: OptimizationReplayEventType
    title: str
    description: str
    visible_cells: tuple[CellDTO, ...]
    overlay_cells: tuple[OverlayCellDTO, ...]
    metrics: dict[str, Any]
```

`metrics`에는 UI·디버그에 필요한 **스칼라 스냅샷**을 넣는다. 권장 키(문서 계약, 구현에서 상수로 고정):

```text
reached_goal_kind (RouteGoalKind value)
goal_priority (int | null)
route_probe_failure_reason (RouteProbeFailureReason value | null)
candidate_reject_reason (CandidateRejectReason value | null)
fitness_total (float)
fitness_breakdown (FitnessBreakdown 직렬화 또는 요약 dict)
commit_conflict_reason (CommitConflictReason value | null)
evolution_convergence_reason (EvolutionConvergenceReason value | null)
route_reservation_id (str | null, Phase 7 reservation_id와 동일)
reservation_state (ReservationState value | null)
replay_truncated (bool, 상수 초과 시 true)
replay_omit_reason (str | null, 선택)
```

알고리즘 입력으로 쓰이지 않도록 **metrics는 표시·로그 전용**이며, 탐색 루프는 이 값을 읽지 않는다.

## UI 표시 목표

```text
candidate pool count
rejected candidate count
route probe success/failure (+ failure_reason / reached_goal_kind / goal_priority)
current generation
best fitness (+ fitness_breakdown 요약)
selected bundle count
committed route count (+ reservation_id / reservation_state when applicable)
validation issue count (+ issue_code)
```

## Invariant

```text
[ ] replay frame is serializable
[ ] replay frame does not affect algorithm result
[ ] frame index is monotonic
[ ] event_type is OptimizationReplayEventType (자유 문자열 금지)
[ ] v0 상수 MAX_REPLAY_* 및 replay_truncated 동작
[ ] 동일 입력·동일 seed에서 replay 기록 on/off에 관계없이 best genome·best fitness가 동일하다 (부작용 없음)
```

## Frontend Dual-track Replay Policy

프론트엔드에서 **Lab replay**와 **Optimization replay**는 **이중 트랙(dual-track)**으로 취급한다. 오버레이·좌표 투영을 구현하기 전에 아래 정책을 정본으로 고정한다.

**핵심 계약(암묵적 동기화 금지):** Lab replay frame index와 Optimization replay frame index 사이에는 **암묵적 동기화가 없다.**  
`no implicit index sync` — 프레임 번호 일치·이벤트 순서·양방향 모두에서 암묵 연동 금지.  
(영문 대응: *There is no implicit synchronization between Lab replay frame index and Optimization replay frame index.*)

### Lab replay 트랙 (권위)

- **소스:** `lab_replay_frames_json`(Lab 리플레이 프레임 JSON; 페이지 컨텍스트·템플릿 계약).
- **역할:** 격자·맵 렌더링을 **이 트랙이 단독으로 주도**한다.
- **소유:** Lab 타임라인의 play / pause / scrubber / **현재 Lab 프레임 인덱스**는 Lab replay 상태가 소유한다.

### Optimization replay 트랙 (관측용 보조)

- **소스:** `optimization_replay`를 `json_script` 등으로 전달한 optimization 리플레이 페이로드(`optimization_replay.py`·`optimization_ui_payload.py` 계약과 정렬).
- **Sequence 10E까지:** **메타데이터 전용** — 선택 프레임의 `event_type` / `title` / `description` / `metrics` 등 표시만 허용.
- **소유:** `optimizationReplayFrameIndex` 등 **독립적인 optimization 전용 인덱스**가 소유한다. Lab의 `currentFrameIndex`와 **별도**로 clamp·prev/next만 적용한다.
- **금지(투영 정책 전):** optimization 트랙이 **격자 렌더링을 주도**해서는 안 된다. `visible_cells` / `overlay_cells`를 Lab 격자에 그리려면 **별도 투영 정책·어댑터(Sequence 11A)**가 선행되어야 한다.

### 비동기화 규칙 (양방향)

- `currentFrameIndex`(또는 동등한 Lab 현재 프레임) → optimization 프레임 인덱스로의 **암묵적 매핑 없음**.
- optimization 프레임 인덱스 → Lab `currentFrameIndex`로의 **암묵적 매핑 없음**.
- **프레임 번호 숫자만 같다**는 이유로 두 인덱스를 맞추지 않는다(**no implicit index sync by numeric frame number**).
- **이벤트 도착 순서**만으로 두 트랙을 맞추지 않는다(**no implicit sync by event order**).
- Optimization prev/next는 **Lab replay 상태·프레임 인덱스·스크러버·재생 루프를 변경하지 않는다.**
- Lab replay 컨트롤은 **명시적인 동기화 정책이 추가되기 전까지** optimization 리플레이 인덱스를 변경하지 않는다.

### 알고리즘·솔버 경계

- Optimization replay는 **관측·디버그·UI 출력 전용**이며, **솔버/알고리즘 입력으로 사용되면 안 된다**(상위 원칙 `Not algorithm input.`과 동일).
- Lab replay 트랙이 맵 렌더링에 대한 **권위(authoritative)**를 유지한다. Optimization replay는 **이차적 관측 트랙**이다.

### 기하·좌표

- **기하(셀) 렌더링**에는 Lab 시각화와 별도의 **투영(projection) 정책**이 필요하다.
- 서버 밀집(dense) optimization 좌표는 **기존 Lab 시각 좌표 헬퍼만으로 해석하지 않는다.** 명시적 어댑터 없이 Lab 보조 함수에 넣지 않는다.

### 향후 오버레이 게이트 (Sequence 11A 이후)

- **오버레이 렌더링**은 **Sequence 11A — readonly overlay projection adapter**가 있어야 시작한다.
- 어댑터는 `OptimizationReplayFrame`의 cells를 **Lab 오버레이 셀 표현**으로 **명시적으로 변환**해야 한다.
- 어댑터는 **기본 Lab replay 프레임 페이로드를 변형(mutate)하지 않는다**(읽기 전용 오버레이 합성).

## 테스트

```text
test_replay_frame_serializable
test_replay_frame_indices_monotonic
test_replay_events_do_not_affect_algorithm_result
test_replay_same_seed_on_off_identical_best_genome
test_replay_large_payload_truncation
test_replay_event_type_is_enum
```

## 완료 조건

```text
[ ] OptimizationReplayEventType enum + OptimizationReplayFrame 구현
[ ] optimization events 기록
[ ] UI에서 timeline 재생 가능
[ ] artifact/debug only invariant 테스트 통과
```
