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
