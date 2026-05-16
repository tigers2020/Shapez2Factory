# Refactor Execution Order

## Phase 0 — Freeze the Truth Surface

### 목표

canonical 문서와 live `asteroid_lab`가 같은 시스템이 아니라는 점을 공식화한다.

### 작업

| Order | Scope | Why now | Touch policy |
|---|---|---|---|
| 0.1 | canonical/live mapping 문서화 | 잘못된 리팩터링 방지 | `freeze` |
| 0.2 | `asteroid_lab`를 inspection/replay shell인지 solver runtime인지 결정 | 이후 모든 이름/모델 정리의 기준 | `freeze` |
| 0.3 | dangerous orchestrator 목록 확정 | 큰 파일 분해 전에 blast radius 파악 | `freeze` |

## Phase 1 — Separate Replay Output from Runtime Calculation

### 대상

- `django_apps/asteroid_lab/replay/snapshot_map_replay.py`
- `django_apps/asteroid_lab/services/cell_snapshot_service.py`
- `django_apps/asteroid_lab/services/existing_layout_service.py`

### 목적

replay 계층에서 `run_reconstruction(...)` 호출과 phase synthesis를 제거하고 projection-only adapter로 축소한다.

### 이유

이 결합을 먼저 풀지 않으면 이후 DTO split, UI contract 정리, validation migration이 모두 왜곡된다.

## Phase 2 — Break Orchestration Monolith

### 대상

- `django_apps/asteroid_lab/services/replay_pipeline_service.py`
- `django_apps/web/views/public_pages.py`

### 목적

decode / normalize / persist / run scaffolding / replay build / retry policy를 분리한다.

### 주의

- `"force=True"` 문자열 분기는 typed result로 교체 전까지 temporary adapter로만 남긴다.
- web view가 rebuild policy를 직접 해석하지 않게 만든다.

## Phase 3 — Split DTO and Serializer Seams

### 대상

- `django_apps/asteroid_lab/services/dto.py`
- `django_apps/web/services/asteroid_lab_page_context.py`

### 목적

DTO monolith와 UI serializer fallback rule을 정리해 contract authority를 한 곳으로 모은다.

## Phase 4 — Deprecate Shadow Solver Models

### 대상

- `django_apps/asteroid_lab/models.py`의 `CandidateBundle`, `RoutingProbe`, `SolverMetricSnapshot`
- 필요 시 `PatternTemplate`, `PatternVariant`

### 목적

실제 solver runtime 없이 존재하는 speculative schema를 격리한다.

### 조건

- 먼저 admin/tests/live usage inventory 작성
- 즉시 삭제보다 `deprecate` 라벨과 migration note 우선

## Phase 5 — Define Missing Canonical Systems Explicitly

### 대상

- validation
- recovery
- protected corridor
- cycle streaming replay

### 목적

현재 tree에 없는 canonical 시스템을 "미구현"으로 명시하고, 억지로 `asteroid_lab` inspection layer에 녹여 넣지 않는다.

## Phase 6 — Strengthen Structural Tests

### 추가해야 할 테스트

| Test | Purpose |
|---|---|
| import graph allowed-edge test | layer 방향 고정 |
| no-SCC test | hidden cycle 조기 탐지 |
| replay no-runtime-import test | output-only 규칙 고정 |
| canonical/live inventory test | namespace drift 조기 탐지 |
| serializer contract test | UI fallback drift 차단 |

## Early No-Touch List

- `django_apps/asteroid_lab/reconstruction/pipeline.py`
- `django_apps/asteroid_lab/reconstruction/fill.py`
- `django_apps/asteroid_lab/snapshots/transport_components.py`
- `django_apps/asteroid_lab/snapshots/server_coords.py`
- `tests/unit/asteroid_lab/test_reconstruction_topology.py`

## Final Outcome Definition

이번 감사 기준에서 "안정화"는 다음을 뜻한다.

1. canonical/live mapping이 문서화되어 있다.
2. replay/output이 runtime calculation을 호출하지 않는다.
3. orchestration이 단계별 service로 분리된다.
4. unused shadow model이 deprecate 또는 isolate 상태다.
5. validation/recovery/protected corridor는 부재인지 구현인지 경계가 분명하다.
