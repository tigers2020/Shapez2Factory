# Phase 9 — Replay and Debug Artifact


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_09_replay_debug.md`](../../Algorithm/asteroid_lab_09_replay_debug.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

> **Superseded narrative (dual-track):** 본 문서의 UI·런타임 관점에서 **Lab 리플레이와 Optimization 리플레이를 별도 트랙·독립 `optimizationReplayFrameIndex`로 취급**하는 서술이 있었다면, 구현 정본은 **Unified Lab Replay Timeline**이다. 최적화 이벤트는 동일 `ReplayTrack`의 `ReplayFrame`에 append되고, 프론트는 `lab-replay-frames-data`와 단일 scrub 인덱스만 사용한다. 상세·금지 심볼 목록: `rollback_baseline_lab_replay_timeline.md`.

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

## Sequence 13A — POST JSON payload 계측·스케일 연구 (replay scalability research)

**상태:** 계측 헬퍼·회귀 테스트·본 절 기록 완료. **즉시 delta 압축 구현 단계는 아님.**

### 현장 증거 (브라우저 / HAR)

```text
POST /asteroid-miner-layout/projects/ (Accept: application/json)
응답 JSON 본문 약 22.6MB (Content-Length, HAR)
Chrome DevTools Response 탭: "Request content was evicted from inspector cache"
```

UI 라이프사이클(11D)·HUD(12I)는 정상이었고, **문제의 중심은 관측 가능한 단일 JSON 응답 크기**와 DevTools 캐시 한계다.

### 계측 (코드)

- 테스트 전용: ``tests/support/measure_json_sections.py`` 의 ``measure_json_sections`` — 최상위 키별 UTF-8 바이트(값만 ``json.dumps``), ``lab_replay_frames_json`` / ``optimization_replay.frames`` 프레임 수·프레임당 바이트·``full_map`` 길이 합·optimization ``visible_cells``+``overlay_cells`` 상한 등.
- 통합: ``test_post_projects_json_size_attribution_and_optimization_replay_hard_caps`` — Django test client로 POST 응답 dict를 직접 분석 (DevTools 캐시에 의존하지 않음).

### 하드 캡 검증 vs 갭

| 정책 | 적용 위치 | POST 응답에서 기대 |
|------|-------------|---------------------|
| ``MAX_REPLAY_FRAMES`` = 500, ``MAX_REPLAY_CELLS_PER_FRAME`` = 128 | ``OptimizationReplayRecorder`` (optimization 트랙 기록) | ``optimization_replay.frames`` — 회귀 테스트로 프레임 수·셀 합 상한 검증 |
| 동일 상수 | Lab inspection ``ReplayFrame`` 직렬화 경로 | **미적용**. ``serialize_replay_frame`` / ``full_map`` 은 inspection 파이프라인 산출물이며 v0 optimization 캡과 별개 |

즉 **22MB급 bulk의 1차 후보는 ``lab_replay_frames_json``(프레임당 큰 ``full_map`` 등)** 과, 동일 POST에 실린 **``optimization_replay``** 의 합이다. Optimization 쪽은 레코더 상한이 있으나 Lab 쪽은 **별도 truncation 정책이 없으면** 대형 맵에서 선형 증가한다.

### 축소 전략 후보 (우선순위·의미 리스크)

1. **Lab replay frame truncation / sampling / summary mode** — 시맨틱: full snapshot equivalence가 약화될 수 있음. 테스트: 기존 inspection 단계별 계약 + UI 타임라인 최소 셋.
2. **반복 full snapshot dedupe** — 키프레임만 전량·중간은 diff만 등. 시맨틱: 클라이언트 재구성 규칙 명문화 필요. 테스트: 직렬화·역직렬화 라운드트립.
3. **visible_cells / overlay_cells delta frame (optimization 쪽 프로토타입)** — Lab과 별도 트랙 유지. 시맨틱: dual-track·no implicit sync 유지 하에 optimization만 축소. 테스트: cap·truncation 메타데이터.
4. **gzip/Brotli 전송** — 본문 의미 불변; 인프라·클라이언트 협상 확인. 테스트: Accept-Encoding + 디코드 후 기존 JSON 계약.
5. **디버그 전용 replay 다운로드 엔드포인트 분리** — POST 본문 경량화; 시맨틱: PRG/폼 경로와 권한 분리. 테스트: 라우트·CSRF·용량.

### 금지 (13A 범위)

```text
delta replay 즉시 구현
binary replay 포맷
solver / GA / commit / validation 동작 변경
Lab vs optimization 암묵 동기화
replay 지표를 알고리즘 입력으로 사용
```

## Sequence 13B — Lab replay payload attribution / reduction design (구현 아님)

**상태:** 계측 확장·중복 프로파일·캡 갭 문서화·13C 후보 순위·회귀 키 존재 검증까지. **런타임 POST 페이로드 축소나 시맨틱 변경은 하지 않는다.**

### 계측 확장 (테스트 전용)

``tests/support/measure_json_sections.py`` 의 ``measure_json_sections`` 가 Lab 전용으로 아래를 추가한다 (모두 JSON ``sort_keys=True, separators=(",", ":")`` 기준으로 결정적).

- **크기:** ``lab_total_bytes`` = 최상위 키 ``lab_replay_frames_json`` 값만 직렬화한 UTF-8 바이트 수(``top_level_key_bytes["lab_replay_frames_json"]`` 와 동일). 프레임별 합 ``sum_frame_bytes`` 와는 구분(괄호·콤마 오버헤드 포함 여부).
- **셀 수:** ``lab_full_map_cell_count_{sum,max,avg}`` — 프레임별 ``len(full_map)`` 집계.
- **상위 프레임:** ``largest_lab_frames`` — 프레임 전체 dict 직렬화 바이트 기준 내림차순 상위 N(기본 8); ``list_index``, ``frame_index``, ``frame_key``, ``bytes``.
- **중복 추정 (``redundancy``):**
  - ``adjacent_identical_full_map_count`` — 인접 프레임의 ``full_map`` 정렬·정규 직렬화 지문 동일 쌍 수.
  - ``cell_row_duplicate_instance_estimate`` — 모든 프레임의 ``full_map`` 행 인스턴스 수 − 전역 고유 행 지문 수(동일 행 페이로드가 프레임 간 반복될 때 상승).
  - ``coordinate_slots_with_multiple_instances`` — (x, y, layer) 슬롯이 둘 이상의 인스턴스를 가진 슬롯 개수.
  - ``sum_full_map_json_bytes`` / ``sum_diff_body_json_bytes`` / ``sum_diff_added_len`` / ``sum_diff_removed_len`` — 프레임별 ``full_map``·``diff``(최상위 또는 ``frame_payload.diff``) 대비 크기·길이 합(관측용).

### Optimization 하드 캡 vs Lab 미캡 (갭 재확인)

| 정책 | Optimization 트랙 | Lab ``lab_replay_frames_json`` |
|------|-------------------|-------------------------------|
| ``MAX_REPLAY_*`` | 레코더·직렬화 경로에서 적용 | **비적용** (inspection / ``serialize_replay_frame`` 경로) |
| POST 압력 | 프레임·셀 상한으로 상한 존재 | 맵·프레임 수에 따라 **선형 증가 가능** |

현장 관측(13A): 단일 POST JSON 약 22.6MB, DevTools response body eviction — 본 13B 계측으로 **Lab vs optimization 기여 분해**를 테스트에서 반복 가능하게 한다 (대형 골든 파일 불필요).

### 13C 구현 후보 (의미 리스크·테스트 힌트, 우선순위 제안)

1. **디버그 전용 full replay 다운로드 / POST는 요약+현재 프레임** — POST 경량화; 권한·CSRF·PRG 분리 테스트. 시맨틱: UI가 어느 경로를 “권위 소스”로 삼는지 명문화 필요.
2. **Lab 프레임 truncation·샘플링 + 명시 metrics** — 시맨틱 약화 위험; inspection 단계 계약·타임라인 최소 셋 회귀.
3. **Delta 프레임(재구성 규칙 문서화)** — 클라이언트 복원 불변; 프레임 N full snapshot 동등성 테스트.
4. **셀 행 intern / dictionary** — 직렬화만 변경 시 UI 동일성·역직렬화 라운드트립 테스트.
5. **HTTP 압축(Accept-Encoding)** — 본문 의미 동일; 협상·디코드 후 기존 JSON 계약 테스트.

### 13C(예정) 시맨틱 동등성 테스트 설계(체크리스트)

추후 delta/압축 구현 시 고정할 검증(알고리즘 입력 금지 원칙 유지):

```text
- reconstruct frame N == 현행 full snapshot 직렬화 결과(또는 동일 DOM 입력 해시)
- frame_index / event 메타데이터 순서 불변
- 셀 상세 조회·Lab 타임라인 스크럽 동작 회귀
- optimization 입력 경로가 압축 리플레이를 읽지 않음
```

### 금지 (13B 범위)

```text
페이로드 실제 축소(캡 버그 미증명 시)
binary 포맷
solver / optimization 동작 변경
Lab vs optimization 암묵 동기화
replay를 알고리즘 입력으로 전환
대형 골든 JSON 커밋
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
