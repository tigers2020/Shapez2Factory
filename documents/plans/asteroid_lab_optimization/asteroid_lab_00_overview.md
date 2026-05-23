# Asteroid Lab Optimization — Overview


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_00_overview.md`](../../Algorithm/asteroid_lab_00_overview.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

## Role

Hybrid Optimization System Architect

## 목적

완성된 asteroid reconstruction 결과 위에서 extractor / extension / belt / pipe 배치를 최적화한다.

이 시스템은 단순 배치기가 아니라:

```text
Asteroid topology
→ Local bundle pattern generation
→ Candidate expansion
→ Route feasibility probe
→ Evolutionary bundle selection
→ Incremental route commit
→ Final validation
→ Replay/debug artifact
```

구조를 가진 optimization layer다.

## 핵심 원칙

```text
Everything is provisional until connected to exterior trunk.
```

즉, extractor / extension bundle은 외부 trunk 연결 가능성이 확인되기 전까지 확정 배치가 아니다.

## 좌표 공간 (정본)

```text
OptimizationInput·TopologyGraph·RouteGoal·candidate·probe·commit·validation·replay의 모든 Coord = island-local (x, y).
Island map grid: integer (x, y) with `grid_contract.neighbors4`. Lab world map has no x==0 column.
```

**Sequence 12L + PR-F:** decode/cleanup/reconstruction 이후 알고리즘은 **island-local** ``(x,y)`` 만. dense server bridge **삭제**; ``CoordFrame.ISLAND_RAW`` 정본. copy JSON ``X==0`` valid; lab world map ``x==0`` column absent.

## 금지 사항

### 1. Replay-driven algorithm 금지

다음 데이터는 알고리즘 입력으로 사용하지 않는다.

```text
NDJSON
ReplayFrame
solver_summary
debug artifact
```

이들은 output/debug 전용이다.

### 1b. 통합 Lab 리플레이 타임라인 (정본)

최적화 단계 리플레이는 **별도 JSON/프론트 트랙이 아니라** 동일 `ReplayTrack`의 `ReplayFrame`에만 append한다. 프론트는 `lab-replay-frames-data`와 **단일** scrub 인덱스만 사용한다. 듀얼 트랙·`optimizationReplayFrameIndex` 등 금지·롤백 기준: `rollback_baseline_lab_replay_timeline.md`.

### 1c. 앱 경계 예외 — output-only adapter

개발 시퀀스의 기본 분할은 다음과 같다.

```text
Lab 리플레이·ORM·디코드 = django_apps/asteroid_lab
최적화 DTO·GA·probe·validation·replay 직렬화 = django_apps/shapez_asteroid/optimization
```

**boundary exception: output-only adapter** — `django_apps/asteroid_lab/services/optimization_replay_to_lab_frames.py` 는 최적화 레코더의 `OptimizationReplayFrame` 등을 Lab `ReplayFrameAppendDTO`로 옮기기 위해 `shapez_asteroid.optimization` DTO·enum을 import한다. **단방향(최적화 → Lab append)** 만 허용되며, Lab → shapez_asteroid 알고리즘 입력으로의 재주입이나 역방향 비즈니스 규칙 전파는 하지 않는다.

### 2. Cell-level GA 금지

잘못된 genome:

```text
gene = cell state
```

권장 genome:

```text
gene = placement bundle candidate
```

### 3. Routing-later pipeline 금지

나쁜 구조:

```text
placement first
routing later
```

권장 구조:

```text
candidate pool 생성
+ immediate route feasibility probe
```

### 4. Outer-rim greedy extractor 설치 금지

다음은 **pass1류 재발**에 해당하므로 금지한다.

```text
for rim_cell in rim_cells:
    if can_place_extractor:
        layout에 extractor 즉시 확정 설치
```

허용되는 것은 **후보만** 생성·probe·풀 적재다. **선택**은 Evolutionary Search가 하고, **확정**은 Incremental Commit이 한다.

```text
Rim cells = extractor 앵커 후보를 둘 위치의 제한(search-space pruning)
Rim cells ≠ 설치 순서·즉시 commit 근거
```

## 최종 아키텍처

```text
OptimizationInput
    ↓
PatternLibrary
    ↓
BundleCandidateGenerator
    ↓
FastRouteProbe
    ↓
GenomeFitnessEvaluator
    ↓
EvolutionarySearch
    ↓
IncrementalRouteCommit
    ↓
Validation
    ↓
ReplayDebugArtifact
```

## v0 범위

v0는 다음만 처리한다.

```text
rim-only extractor candidate generation (앵커 ∈ rim_cells; 즉시 설치·greedy pass 없음)
linear extension pattern
shape/fluid transport kind separation
bounded uniform-cost route probe (Dijkstra-lite; traversal_cost=1 fixture에서는 BFS와 동일)
bundle-level genome
mutation-only evolutionary search
best genome replay
```

**한 줄:** Rim은 후보 앵커 필터일 뿐, 설치 순서가 아니다.

## v0에서 제외

```text
complex extension topology
full optimal routing
CP-SAT
MILP
advanced corridor replacement
multi-objective Pareto search
global trunk balancing
```

## v0 필드 정책

v0에서 corridor / trunk / future expansion 관련 동작은 **고급 치환·전역 밸런싱을 하지 않는다** (위 「v0에서 제외」와 동일).

다만 DTO·artifact·fitness breakdown에는 해당 필드를 **미리 둔다**. 값은 대부분 `0`·빈 집합·**보수적 휴리스틱**으로 채운다.

즉, v0는 advanced corridor replacement를 수행하지 않지만, **그 기능이 들어올 자리와 schema는 먼저 고정**한다. 구현자가 「필드는 있는데 왜 안 쓰지?」로 drift하지 않도록, 본 문서·Phase 1·5·7이 동일 정책을 전제한다.

## 계약 보강 (리뷰 반영, v0~v1 경계)

장기적으로 solver급 안정성을 위해 입력·라우팅 계층에 다음을 **문서·DTO 수준에서 선행**한다 (Phase 1·4·5·10 참조).

```text
RouteGoal (goal_kind·priority·existing_trunk·transport)
RouteCellDomain + route_domain (allowed/preferred/blocked drift 방지)
TopologyGraph (reconstruction 시 1회 생성, 중복 neighbor 탐색 방지; 무방향 계약)
existing transport (coord + TransportKind) / trunk coords / protected corridor
incremental commit 후 route_domain·예약(reservation) 반영 (Phase 7, candidate probe와 drift 방지)
fitness: corridor·narrow passage·future expansion·trunk sharing·route goal quality 필드
```

**Greenfield 계약:** greenfield는 `existing_transport_cells`가 비어 있고 `existing_trunk_cells`·`protected_corridor_cells`도 공집합인 **특수 케이스**로만 취급한다. optimizer는 greenfield 전용 입력 경로·별도 DTO를 두지 않는다.

동일 `OptimizationInput`·동일 빌더 체인을 타야 **나중에 레이아웃 통합 시 DTO를 다시 뜯는 일**을 막는다.

## 구현 생존성·아키텍처 리뷰 요약

아키텍처 방향(placement+routing 동시 평가, bundle-level genome, provisional→commit FSM, **replay·NDJSON은 output only**)은 기존 v1/v2류 drift 원인을 상당 부분 제거한다. 다만 **구현 단계**에서 아래를 문서·DTO로 고정하지 않으면 topology graph / `route_domain` / reservation / probe 간 **소유권·누적 상태 drift**와 후보 조합 폭발로 생존성이 떨어진다.

**v0에서 문서·DTO로 선행할 보강(우선순위):**

```text
1) candidate canonical dedupe — CandidateEquivalenceKey 등 동치 키로 동일 기하·stub·처리량·topology_signature 후보 축소 (Phase 3)
2) route_domain 단일 소유 — RouteDomainSnapshotBuilder만 스냅샷 생성; reservation·commit 반영은 전면 재빌드, 제자리 in-place mutation 금지 (Phase 1·4·7)
3) probe 낙관성 대응 — predictive fragility/corridor penalties (`PenaltyMode.CONSERVATIVE`; Phase 4·5)
4) Recovery budget — max_removed_candidates·max_carve_cells·max_reroute_attempts 등 thrashing 상한 (Phase 7)
5) evolution diversity — forced distant mutation(**seed-stable hash**; Phase 6)
8) observed survivability — solver/GA 입력 금지 (Phase 10B)
6) domain 전이 기록 — 예약으로 domain이 바뀔 때 coord별 before/after route_class 등 최소 전이 DTO (Phase 7; frozenset[Coord]만으로는 디버그 복구 불충분)
7) validation 확장 — corridor 잔여·trunk 중복·격리 위험은 v0 최소 검증 유지, 심화는 v1+ (Phase 8)
```

### v0 스케일·Replay 정책

**전제:** asteroid / mining 관련 **활성 좌표(셀) 수가 대략 50 이하**인 v0에서는 프레임당 **full cell 스냅샷** replay로 충분하다. 이 전제에서 **delta frame 압축·셀 참조 테이블·불변 스냅샷 공유**는 **필수 아님**(v1+ 스케일업 시 선택).

대신 artifact·메모리 폭주를 막기 위해 **하드 캡**만 둔다 (Phase 9).

```text
MAX_REPLAY_CELLS_PER_FRAME = 128
MAX_REPLAY_FRAMES = 500
```

초과 시 이후 프레임 생략 또는 트렁케이트 후 `metrics`에 `replay_truncated: true` 등을 기록한다.

## Trunk vs existing transport (정본)

`existing_transport_cells`(coord + `TransportKind`)와 `existing_trunk_cells`(coord 집합)를 **함께** 둔다. **trunk 멤버십의 정본은 `existing_trunk_cells`** 이다. `ExistingTransportCell`에는 trunk 플래그를 두지 않는다 (중복 표현 제거). adapter는 `existing_trunk_cells ⊆ coords(existing_transport_cells)` invariant를 강제한다.
## Sequence 12L 좌표 경계 보강 (2026-05-17)

- Critical invariant: after decode/normalize to island grid, 알고리즘 코드에서 raw 좌표가 불법이다.
- `OptimizationInput` 이후 canonical coords are island-local (PR-F).
- copy JSON `X==0`은 유효 좌표이며, optimization input/candidate/route/evolution/validation/replay 경로에서 실패 조건이 아니다.
- copy JSON ↔ map grid 재변환은 decode/import 또는 UI/export 경계에서만 허용(알고리즘 내부 금지).
- `build_optimization_input` 및 post-inspection evolution 경로는 island `Coord` only; raw 좌표를 다시 변환하지 않는다.
- **12L-hardening:** `test_import_boundaries`, `test_coordinate_frame_ast_gate`; POST `test_post_json_optimization_input_does_not_raw_convert_server_coords` (legacy test name; copy `X==0` boundary).
- 12L에서 UI/overlay projection 변경은 범위 밖이다. projection boundary 문제가 발견되면 별도 UI/export boundary 작업으로 분리한다.
