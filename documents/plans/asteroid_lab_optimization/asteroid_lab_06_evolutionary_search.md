# Phase 6 — Evolutionary Search v0

## 목적

Bundle candidate 조합을 evolutionary search로 최적화한다.

## v0 전략

초기 버전은 복잡한 crossover보다 mutation + repair + elitism 위주로 간다.

```text
initial population
→ evaluate
→ select elites
→ mutate
→ repair
→ evaluate
→ repeat
```

## 입력

```python
CandidatePool
FitnessEvaluator
EvolutionConfig
```

### `EvolutionConfig`

```python
@dataclass(frozen=True)
class EvolutionConfig:
    seed: int
    population_size: int
    elite_count: int
    mutation_rate: float
    tournament_size: int
    max_generation: int
    max_stall_generation: int
    time_budget_ms: int | None
    forced_distant_mutation_period: int | None
```

`forced_distant_mutation_period`가 `N`이면 **매 N세대마다** 최소 한 번은 `replace_with_nearby_candidate`가 아닌 **원거리 후보 치환**(예: rim 극단 간 swap, 랜덤 후보 주입)을 **결정적 규칙**으로 강제한다. `None`이면 비활성(v0 최소 구현 허용). 국소 최적에만 갇히는 붕괴 완화용이다.

`population_size`·`elite_count`·`tournament_size`는 `population_size > 0`, `0 <= elite_count < population_size` 등 **빌더에서 검증**한다.

`mutation_rate`는 **`0.0 <= mutation_rate <= 1.0`** 을 만족해야 한다.

## 탐색 대상 (책임 경계)

Evolutionary Search는 **이미 geometry·1차 probe를 통과한 candidate pool**을 입력으로 받는다.

```text
조합(bundle id 집합) 선택만 담당
셀 단위 직접 배치 금지
벨트·파이프 경로 직접 생성 금지
rim 순회 순서·candidate 생성 순서를 설치 순서로 상속하지 않는다
```

배치 확정·경로 예약은 Phase 7 Incremental Commit이 `Gene.commit_order` 등 genome 계약에 따라 수행한다.

## 출력

```python
class EvolutionConvergenceReason(Enum):
    MAX_GENERATION = "max_generation"
    MAX_STALL_GENERATION = "max_stall_generation"
    TIME_BUDGET_MS = "time_budget_ms"
    NO_IMPROVEMENT = "no_improvement"
    CANDIDATE_POOL_EXHAUSTED = "candidate_pool_exhausted"
```

```python
@dataclass(frozen=True)
class EvolutionResult:
    best_genome: Genome
    best_fitness: FitnessBreakdown
    generation_count: int
    evaluated_genome_count: int
    convergence_reason: EvolutionConvergenceReason
```

`convergence_reason`은 **자유 문자열 금지**. 위 enum만 사용한다.

## Mutation 종류

```text
add_candidate
remove_candidate
swap_candidate
replace_with_nearby_candidate
toggle_candidate
commit_order_shuffle
```

(`Gene`의 `commit_order` 필드와 정렬; 예전 `priority_shuffle` 명칭 폐기.)

## Repair 종류

```text
remove_overlap_low_score
remove_unreachable
remove_corridor_blocker
dedupe_candidate
limit_bundle_count
```

## Selection

v0 추천:

```text
elitism + tournament selection
```

## Population diversity (로그·replay metrics)

탐색이 동일 `topology_signature`·비슷한 rim 위치에 수렴하는지 관측하기 위해 **세대 요약**을 남길 수 있다. 알고리즘 입력으로 쓰이지 않는다.

```python
@dataclass(frozen=True)
class GenomeDiversityMetrics:
    distinct_topology_signatures: int
    rim_cell_entropy_bits: float
    transport_kind_mix_score: float
```

`EvolutionResult`에 필수 필드로 둘지, replay `metrics`에만 넣을지는 구현 선택이다. v0는 **계산 생략·0 채움**을 허용하되, **DTO 자리**는 문서에 고정한다.

## 종료 조건

종료 조건은 **`EvolutionConvergenceReason`** 과 1:1로 매핑한다.

```text
max_generation -> MAX_GENERATION
max_stall_generation -> MAX_STALL_GENERATION
time_budget_ms -> TIME_BUDGET_MS
no_improvement -> NO_IMPROVEMENT
candidate_pool_exhausted -> CANDIDATE_POOL_EXHAUSTED
```

## 동점·결정성 (필수)

`same seed produces same result` 외에, **동일 fitness**에서의 순위를 고정한다.

```text
fitness tie-break (우선순위, 동일 total일 때):
1) FitnessBreakdown.total 내림차순 (높을수록 우선)
2) FitnessMetrics.selected_candidate_count 내림차순 (높을수록 우선; throughput 기회 보존)
3) genome_id 문자열 오름차순
```

구현은 위 키를 **단일 `sort_key` 튜플**로 고정해 `sorted(...)` / `heapq`에 사용한다.

## Invariant

```text
[x] same seed produces same result (population 초기화·mutation·tie-break 포함)
[x] best fitness is non-decreasing under elitism (total 기준)
[x] repair never creates unknown candidate id
[x] mutation never generates cell-level genes
[x] result includes convergence_reason (EvolutionConvergenceReason enum)
[x] fitness 동점 시 tie-break 키가 문서와 구현에서 동일하다
[x] commit_order는 genome 필드로 유지되며 rim·candidate 풀 enumeration 순을 그대로 commit 정본으로 쓰지 않는다 (Phase 7)
```

## 테스트

```text
test_evolution_same_seed_deterministic
test_evolution_best_fitness_non_decreasing_with_elitism
test_evolution_repair_removes_overlap
test_evolution_mutation_keeps_valid_candidate_ids
test_evolution_result_has_convergence_reason_enum
test_evolution_fitness_tie_break_deterministic
```

## 완료 조건

```text
[x] EvolutionConfig DTO 구현
[x] random initial population 구현
[x] mutation-only search 구현
[x] repair 구현
[x] EvolutionConvergenceReason enum + EvolutionResult 반영
[x] deterministic seed·tie-break 테스트 통과
[x] best genome 반환
```
