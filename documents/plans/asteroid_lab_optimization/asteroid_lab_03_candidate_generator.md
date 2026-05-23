# Phase 3 — Bundle Candidate Generator


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_03_candidate_generator.md`](../../Algorithm/asteroid_lab_03_candidate_generator.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

## 목적

PatternLibrary를 실제 asteroid topology 위에 배치해 가능한 bundle candidate를 생성한다.

## 구현 철학 (필수)

문서 Phase 번호와 무관하게 **구현 시퀀스에서는** 다음이 한 덩어리다.

```text
candidate 생성
→ local geometry validation
→ 즉시 route feasibility probe
→ reachable 만 normal pool
```

“일단 candidate만 생성하고 나중에 probe”는 금지에 가깝게 취급한다. 상세는 `asteroid_lab_10_development_sequence.md` Sequence 3.

## Greedy rim 설치 금지 (필수)

Candidate Generator는 **extractor / extension을 layout에 확정 설치하지 않는다.** (belt·pipe 실체도 마찬가지.)

이 단계는 오직 다음까지만 수행한다.

```text
BundleCandidate 생성
local geometry 검증
저비용 route feasibility probe
normal pool / rejected 분리
```

**선택**은 Phase 6 Evolutionary Search가 하고, **확정**은 Phase 7 Incremental Commit이 한다.

`ExtractorPlacementPolicy.RIM_ONLY` 및 문서의 **rim-only** 표현은 **후보 생성 제약**(extractor 앵커 coord ∈ `rim_cells`)이지, **rim을 순회하며 가능한 자리에 순서대로 설치하는 greedy pass**가 아니다.

```text
search-space pruning ≠ greedy installation
```

## 입력

```python
OptimizationInput
tuple[BundlePattern, ...]
CandidateGenerationConfig
```

### `CandidateGenerationConfig`

```python
class ExtractorPlacementPolicy(Enum):
    RIM_ONLY = "rim_only"

@dataclass(frozen=True)
class CandidateGenerationConfig:
    extractor_policy: ExtractorPlacementPolicy
    allow_diagnostic_unreachable: bool
    max_candidates: int | None
    route_probe_max_expansions: int
    transport_kinds: frozenset[TransportKind]
    route_probe_goal_priority_weight: int
```

`ExtractorPlacementPolicy`는 **후보 풀을 어떻게 열어둘지**만 정한다. v0 기본값 `RIM_ONLY`는 **extractor 앵커를 `rim_cells`로 제한**해 조합 폭을 줄인다 (mineable 전체에 두지 않음). **설치 순서·즉시 commit과 무관**하다.

`route_probe_goal_priority_weight`는 Phase 4 `RouteProbeInput.goal_priority_weight`에 전달된다.

`max_candidates`가 `None`이 아니면, **normal pool(`normal_candidates`)이 확정된 뒤** 후보 수가 상한을 넘으면 잘라낸다. `rejected_candidates`는 상한에 포함하지 않는다. 잘라내기 전 **정렬 키(v0 정본, 결정성):**

```text
1) base_score 내림차순
2) route_probe_result.cost 오름차순
3) candidate_id 오름차순
```

그다음 앞에서부터 `max_candidates`개만 남긴다.

`allow_diagnostic_unreachable=True`이면 unreachable 후보를 **normal pool에는 넣지 않고** `rejected_candidates` 또는 별도 diagnostic 목록에 남길 수 있다.

## Candidate equivalence / dedupe (조합 폭발 완화)

`rim_cell × pattern × rotation × transport_kind × goal 매칭` 등으로 후보 수가 커질 수 있다. **evolution에 넘기기 전**에 동치 후보를 한 건으로 줄인다.

### `CandidateEquivalenceKey`

동일한 **점유 기하·출력 stub·처리량 계약·topology_signature**이면 탐색·fitness 관점에서 중복에 가깝다. v0 정본 키(필드명은 구현에서 조정 가능, **의미는 유지**):

```python
@dataclass(frozen=True)
class CandidateEquivalenceKey:
    occupied_cells: frozenset[Coord]
    output_stub: Coord
    output_dir: Direction
    transport_kind: TransportKind
    base_throughput: int
    topology_signature: str
```

동일 키가 여러 번 나오면 **하나만 남긴다**. 대표 선택 tie-break(v0 정본): `candidate_id` 오름차순으로 첫 번째.

dedupe는 **`max_candidates` 잘라내기 전**에 적용해, 잘림이 무작위가 아니라 **동치 축소 후** score 정렬 기반임을 보장한다.

### `CandidateSpatialHash` (선택)

좌표 기반 버킷팅은 **선택 최적화**다. 결정성·동치 키의 정본은 `CandidateEquivalenceKey`이다.

## 출력

성공 후보와 거절 후보를 **타입으로 분리**해 “normal pool = 성공만”을 컴파일 타임에 가깝게 고정한다.

```python
@dataclass(frozen=True)
class BundleCandidate:
    candidate_id: str
    pattern_id: str
    topology_signature: str
    extractor: Coord
    extensions: tuple[Coord, ...]
    occupied_cells: frozenset[Coord]
    output_stub: Coord
    output_dir: Direction
    transport_kind: TransportKind
    base_throughput: int
    base_score: float
    route_probe_result: RouteProbeResult
```

경로 비용은 **`route_probe_result.cost`** 만 사용한다 (`route_cost` 중복 필드 없음).

`BundleCandidate`는 **직접 생성하지 않고** factory/builder로만 만들어 `route_probe_result.reachable`·`reached_goal` 등 성공 계약을 한 곳에서 assert한다.

목표 종류는 **`route_probe_result.reached_goal.goal_kind`** 만 사용한다 (`matched_goal_kind` 같은 별칭 필드는 두지 않는다).

```python
@dataclass(frozen=True)
class RejectedBundleCandidate:
    attempted_pattern_id: str
    extractor: Coord | None
    rejection_reason: CandidateRejectReason
    route_probe_result: RouteProbeResult | None
```

geometry 단계에서 막힌 경우 `route_probe_result`는 `None`일 수 있다.

```python
@dataclass(frozen=True)
class CandidateGenerationResult:
    normal_candidates: tuple[BundleCandidate, ...]
    rejected_candidates: tuple[RejectedBundleCandidate, ...]
```

### Probe 결과 스냅샷

`route_probe_result`는 **candidate phase**에서의 1차 probe 결과다.

- fitness·diagnostic·pool 재평가에서 재사용한다.
- **incremental commit** 단계에서는 반드시 probe를 다시 수행한다 (문서 Phase 5·7).

### topology_signature

후보 granularity가 `extractor + extensions + stub` 하나로만 묶이면, 이후 mutation에서 **extension topology만** 바꾸고 싶을 때 genome이 비대해진다.

v0에서는 `topology_signature`로 **기하·부착·stub 방향·처리량·운송 종류**를 **결정적 문자열**(또는 정수 해시를 16진 문자열로 고정)로 식별한다. v1에서 `PlacementGene` / `TopologyGene` / `RoutingPreferenceGene` 분리를 검토할 때도 **문자열 의미가 갈리지 않게** 필드 세트를 확장한다.

**포함 권장(결정적 순서로 직렬화):**

```text
pattern_id
linear_extension_count (0~3)
회전·대칭 정본 id (pattern library의 canonical rotation id)
extractor 방향 / extension chain 방향 요약 (프로젝트에서 하나의 enum 순서로 고정)
output_stub·output_dir
transport_kind
base_throughput (또는 base_throughput bucket)
occupied_cells의 정렬된 나열 또는 결정적 해시(좌표 lex order)
```

`lin_e_len3_outE` 수준의 짧은 약어 전용 문자열만 쓰면 패턴 라이브러리가 늘 때 **signature drift**가 난다. 위 항목을 **빠지지 않게** 직렬화 규칙에 넣는다.

## v0 정책

```text
extractor 앵커 ∈ rim_cells (후보 생성 제약; 즉시 설치 아님)
extension ∈ mineable asteroid cells
output_stub = non-occupied route start
```

위 루프는 **풀을 채우는 enumeration**일 뿐, `rim_cell` 순서는 **commit 순서·greedy 설치 순서로 쓰지 않는다.**

```text
for rim_cell in rim_cells:
    for pattern in pattern_library:
        project pattern onto rim_cell
        validate occupied cells
        validate extension cells
        validate output stub
        build RouteProbeInput (route_domain + route_goals from OptimizationInput)
        run route feasibility probe
        append BundleCandidate to normal_candidates OR RejectedBundleCandidate to rejected_candidates
```

이중 `for rim_cell`·`for pattern` 순서는 **결정적 enumeration**용이다. **layout 확정·commit_order의 정본이 되면 안 된다** (commit_order는 genome `Gene.commit_order`, Phase 7).

## Reject 이유

문서 나열 값은 **`CandidateRejectReason` enum** 멤버와 1:1로 맞춘다 (자유 문자열 금지).

```text
extractor_not_rim
extension_not_mineable
occupied_outside_asteroid
output_stub_inside_occupied
output_stub_invalid_coord
pattern_overlap_self
route_probe_unreachable
```

## Route Probe와의 관계

1차 route feasibility probe는 **후보 한 건이 채택되기 직전**에 수행한다.

unreachable candidate는 normal pool에 넣지 않는다. diagnostic은 `allow_diagnostic_unreachable` 정책에 따른다.

## Invariant

```text
[ ] Candidate Generator가 placement를 확정(commit)하지 않는다
[ ] rim 순회 순서가 commit 순서로 새지 않는다 (commit_order는 genome)
[ ] topology_signature deterministic (pattern·회전·연장·stub·처리량·transport·occupied 기하 요약)
[ ] CandidateEquivalenceKey 기반 dedupe가 max_candidates truncation보다 먼저 적용된다
[ ] occupied_cells contains extractor and extensions only
[ ] output_stub not in occupied_cells
[ ] extractor in rim_cells
[ ] extensions in mineable_cells
[ ] topology_graph·occupied가 island map grid·`grid_contract.neighbors4`와 모순 없음 (copy JSON X==0 허용)
[ ] 모든 절대 Coord·셀 집합이 island-local (x, y) (Phase 1 좌표 규칙과 동일)
[ ] normal_candidates의 각 원소: route_probe_result.reachable is True
[ ] normal_candidates: route_probe_result.reached_goal is not None (v0 성공 계약)
[ ] rejected_candidates: rejection_reason은 항상 CandidateRejectReason
[ ] normal pool 등록 전 probe 통과 여부가 타입으로 구분된다
```

## 테스트

```text
test_candidate_generator_rim_only_extractors
test_candidate_generator_extensions_must_be_mineable
test_candidate_generator_output_stub_not_occupied
test_candidate_generator_island_coord_contract
test_candidate_generator_deterministic_ids
test_candidate_generator_topology_signature_deterministic
test_candidate_generator_records_rejection_reason_enum
test_candidate_generator_stores_probe_snapshot_on_success
test_candidate_generator_immediate_probe_excludes_unreachable_from_normal_pool
test_candidate_generator_equivalence_dedupe_deterministic
```

## 완료 조건

```text
[ ] rim-only extractor **후보 생성만** (commit·greedy rim 설치 없음)
[ ] linear extension 후보 생성
[ ] reject reason 기록
[ ] CandidateRejectReason·RouteProbeFailureReason·ValidationIssueCode 정의
[ ] CandidateEquivalenceKey + dedupe (max_candidates 전)
[ ] topology_signature 필드 (직렬화 구성요소 문서와 일치)
[ ] CandidateGenerationConfig DTO 정의
[ ] route_probe를 동일 시퀀스에서 호출 (normal pool 게이트)
[ ] 성공 후보에 route_probe_result 기록 (별칭 matched_goal_kind·route_cost 없음)
[ ] BundleCandidate factory/builder로만 생성
[ ] CandidateGenerationResult (normal vs rejected 타입 분리)
```
