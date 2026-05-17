# Asteroid Lab Optimization — Development Sequence

## 목적

GA + local pattern compiler + route feasibility 기반 optimization layer를 안전한 순서로 구현한다.

**필수:** `candidate 생성 → 즉시 route probe → normal pool` 은 분리된 “나중에 붙이기” 시퀀스로 두지 않는다. Phase 3 문서와 동일하게 Sequence 3 한 블록에서 완료한다.

### 구현·검증 메모 (코드베이스 동기, 2026-05-17)

- **앱 경계:** Lab 리플레이·ORM·디코드는 `django_apps/asteroid_lab/`; 최적화 DTO·GA·probe·validation·replay 직렬화는 `django_apps/shapez_asteroid/optimization/`.
- **테스트:** `python -m pytest tests/unit/shapez_asteroid/ tests/integration/shapez_asteroid/test_optimization_ui_payload.py` → **193 passed** (에이전트 로컬 실행).
- **GitHub #14 (narrow corridor expansion):** `tests/unit/shapez_asteroid/test_corridor_survivability_expansion.py`에 reservation·starvation 리플레이·late commit·evolution→commit 스티칭 회귀를 모은다.
- **대칭 목표 narrow bridge:** `tests/unit/shapez_asteroid/fixtures/narrow_corridor.py`의 `build_symmetric_*` + `tests/unit/shapez_asteroid/test_symmetric_corridor_fixture.py`. 림 우측 단일 goal 편향은 `build_narrow_bridge_optimization_input` 및 기존 비대칭 테스트로 **의도적으로 유지**한다.
- **JSON fixture (narrow corridor v0):** `tests/fixtures/shapez_asteroid/optimization/narrow_corridor_asymmetric_rim_competition.json`, `narrow_corridor_symmetric_rim_competition.json` — `json_safe_replay_value` 스냅샷; 동기 테스트 `tests/unit/shapez_asteroid/test_narrow_corridor_optimization_json_fixtures.py`.
- **JSON 계약 파서 (테스트 전용):** `tests/unit/shapez_asteroid/fixtures/optimization_json.py` — `schema_version == 1`만 허용, 필수 키·상호 배타적 goal export(`primary_route_goal` vs 최상위 `route_goals`)·알 수 없는 최상위 키 거부; `test_optimization_fixture_json_contract.py`에서 디스크 ↔ `json_safe` 빌더 동등성·라운드트립 검증. **프로덕션 솔버 입력·런타임 자동 소비는 범위 밖**이며 전역 진화 JSON 팩·역직렬화 런타임도 여전히 후속.
- **Replay-track JSON 골든(v0, 출력 계약만):** `tests/fixtures/shapez_asteroid/replay/narrow_corridor_{asymmetric,symmetric,starvation}_replay.json` — `build_optimization_replay_track_payload`와 동일 프레임 직렬화; 빌더 `fixtures/replay_track_builders.py`. **테스트 전용 파서** `fixtures/replay_json.py` + `test_replay_fixture_json_contract.py`(`schema_version` 1, 최상위 키 화이트리스트, `replay_event_sequence`↔프레임 정합). **리플레이는 솔버/커밋 입력이 아님**; Lab/런타임 자동 소비 배선은 범위 밖.
- **Long replay stitching JSON(v0, 출력 계약만):** `tests/fixtures/shapez_asteroid/replay_long/narrow_corridor_evolution_commit_replay.json`, `narrow_corridor_truncated_replay.json` — 진화 구간(`optimization.input_loaded`·`genome.*`·`generation.completed`) → `best_genome.selected` → incremental commit(`route.*`) → `commit.survivability_summary` 스티칭을 한 artifact에 고정; truncated 픽스처는 동일 프레임 접두사에서 `replay_summary.replay_truncated=true` 및 최상위 `truncation_reason` 계약을 검증한다. 계약 테스트 `test_long_replay_fixture_contract.py`. **런타임 persistence·역직렬화 자동 소비는 여전히 범위 밖**이며, 픽스처는 알고리즘 입력이 아니다.

---

## Sequence 1A — Domain DTO contracts

DTO·좌표 계약만 먼저 고정해 PR을 작게 유지한다. **hole asteroid fixture·adapter 검증은 1B로 분리**한다.

### 작업

```text
[x] RouteGoal / RouteGoalKind
[x] TopologyNode / TopologyEdge / TopologyGraph (무방향 계약)
[x] OptimizationInput DTO (route_goals·topology_graph·existing_transport_cells·trunk·protected)
[x] RouteProbeFailureReason / CandidateRejectReason / ValidationIssueCode / ValidationSeverity
[x] EvolutionConvergenceReason / CommitConflictReason / OptimizationReplayEventType / ReservationState
[x] RouteDomainSnapshotBuilder 시그니처(단일 route_domain 스냅샷 생성 진입점)
[x] RouteDomainCellTransition / RecoveryBudget DTO (Phase 7과 동기)
[x] GenomeDiversityMetrics / EvolutionConfig.forced_distant_mutation_period (Phase 6과 동기)
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_optimization_input.py (DTO·좌표·빈 transport greenfield)
```

### 완료 기준

```text
[x] 관련 DTO·enum import 가능 (순환 없음)
[x] enum 멤버 이름·값이 Phase 문서와 동기화됨
[x] OptimizationInput·그래프·goal의 모든 Coord가 Server X/Y 정본
[x] `neighbors4_server` 밀집 4방 이웃 단위 테스트 (server x=0 포함 케이스)
[x] route_goals가 kind·priority 계약을 만족하는 최소 factory 가능
[x] greenfield = existing_transport_cells 비어 있음 ∧ trunk·protected 공집합 (별도 코드 경로 없음)
```

---

## Sequence 1B — Reconstruction adapter + RouteCellDomain seed builder

입력을 실제 reconstruction 출력과 연결하고, Phase 4가 소비할 domain 초안을 만든다.

### 작업

```text
[x] Reconstruction → OptimizationInput adapter
[x] rim / interior / route_goals 추출
[x] RouteCellDomain 빌더 초안 (**RouteDomainSnapshotBuilder**; existing_transport_cells → transport_mask, trunk·protected·blocked 반영)
[x] topology_graph 이웃이 neighbors4_server와 모순 없음 (그래프 빌더 테스트)
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_optimization_input.py (adapter·builder 구간)
pytest tests/unit/shapez_asteroid/test_route_cell_domain_builder.py (파일명은 구현에 맞게)
```

### 완료 기준

```text
[x] hole asteroid fixture에서 interior fill이 mineable로 유지됨
[x] adapter가 greenfield·비-greenfield 동일 경로로 OptimizationInput을 생산
[x] 빌더 출력이 blocked/hard_blocked와 모순 없음
```

---

## Sequence 2 — Pattern Library

### 작업

```text
[x] BundlePattern DTO (attachments·throughput_factor)
[x] linear 0~3 extension pattern
[x] rotation support
[x] deterministic pattern id
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_pattern_library.py
```

### 완료 기준

```text
[x] ExtensionAttachment·throughput_factor·canonical E (output_dir=E) 계약
[x] extractor + 0~3 extension linear pattern 생성
[x] output_stub가 occupied_cells에 포함되지 않음
```

---

## Sequence 3 — Candidate Generator + Route Probe (통합)

후보가 normal pool에 들어가기 전 **반드시** probe를 통과한다.

### 작업

```text
[x] BundleCandidate DTO (topology_signature·probe 스냅샷; factory만 생성; normal은 rejection 필드 없음)
[x] CandidateGenerationResult (normal vs rejected)
[x] CandidateEquivalenceKey + dedupe (max_candidates 전)
[x] rim-only extractor **후보 생성만** — commit·greedy rim 설치 없음
[x] extension mineable validation
[x] reject reason tracking (enum)
[x] RouteProbeInput / RouteProbeResult (route_domain·RouteGoal·reached_goal·topology_graph·goal_priority_weight)
[x] bounded uniform-cost probe + transport mask
[x] reachable → normal pool / unreachable → diagnostic 또는 폐기
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_bundle_candidate_generator.py
pytest tests/unit/shapez_asteroid/test_route_probe.py
pytest tests/unit/shapez_asteroid/test_candidate_route_probe_integration.py
```

### 완료 기준

```text
[x] valid candidate와 rejected candidate가 deterministic
[x] 연결 불가능 candidate가 normal pool에 들어가지 않음
[x] Candidate Generator가 placement를 확정하지 않음 (풀·probe만)
[x] output_stub에서 RouteGoal 계약에 맞는 도달성 평가
[x] blocked / hard_blocked 통과 금지
[x] budget exceeded failure reason 기록
```

---

## Sequence 3B — Replay 최소 골격 (권장, 조기)

candidate/probe 디버깅을 **Sequence 8까지 미루지 않으면** 구현 난이도가 급증한다. UI timeline 전체는 Sequence 8이 담당하고, 여기서는 **기록 파이프라인만** 최소로 연다.

### 작업

```text
[x] OptimizationReplayEventType + OptimizationReplayFrame 직렬화 (Phase 9 상수 MAX_REPLAY_*·replay_truncated 포함)
[x] candidate.generated / candidate.rejected / route_probe.succeeded|failed 이벤트만 우선 기록
[x] replay artifact는 algorithm input 금지 invariant 단위 테스트
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_optimization_replay_skeleton.py (파일명은 구현에 맞게)
```

### 완료 기준

```text
[x] Sequence 3에서 한 번의 run에 대해 replay NDJSON(또는 동등 바이너리)이 쓰이고, 탐색 결과는 replay on/off 동일(Phase 9 invariant)
```

---

## Sequence 4 — Genome / Fitness

### 작업

```text
[x] Gene / Genome DTO (Gene.commit_order)
[x] FitnessBreakdown + FitnessMetrics
[x] overlap penalty
[x] unreachable penalty
[x] route cost penalty
[x] route_fragility_penalty / shared_corridor_pressure_penalty 필드 (v0는 0 허용)
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_genome_fitness.py
```

### 완료 기준

```text
[x] same input + same seed = same fitness
[x] overlap/unreachable penalty가 throughput gain보다 강함
[x] trunk vs margin 등 동일 reachable이라도 route goal 품질이 점수에 반영됨
[x] 좁은 통로 점유 시나리오에서 탐욕적 고처리량 우위가 깨질 수 있는 훅(패널티 필드) 존재
```

---

## Sequence 5 — Evolution Search v0

### 작업

```text
[x] initial population
[x] mutation
[x] repair
[x] elitism
[x] forced_distant_mutation_period (None 허용) + GenomeDiversityMetrics 자리(0 허용)
[x] EvolutionConvergenceReason enum + EvolutionResult
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_evolutionary_search.py
```

### 완료 기준

```text
[x] same seed deterministic (population·mutation·fitness tie-break 포함)
[x] best fitness non-decreasing under elitism
[x] best genome 반환
```

---

## Sequence 6 — Incremental Commit

### 작업

```text
[x] best genome candidate 정렬 (**Gene.commit_order** 정본; candidate 생성·rim 순 기본 금지)
[x] route probe 재실행 (갱신된 route_domain)
[x] RouteReservation (reservation_id·reached_goal·goal_priority·state·domain_cell_transitions)
[x] CommitConflictReason 처리
[x] commit / rollback + route_domain 반영
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_incremental_commit.py
```

### 완료 기준

```text
[x] confirmed candidate는 exterior trunk route를 가진다
[x] commit 실패 candidate는 local rollback된다
[x] commit 순서가 genome `commit_order`와 일치하고 생성 enumeration 순에 묶이지 않는다
```

---

## Sequence 7 — Validation

### 작업

```text
[x] final validation result
[x] confirmed candidate ↔ 정확히 하나의 CONFIRMED RouteReservation 검증
[x] reserved_cells ↔ path 일관성 검증
[x] ValidationIssue (ValidationIssueCode·route_goal_kind·transport_kind·optional route_reservation_id·path_index)
[x] extractor output connectivity check
[x] orphan transport check
[x] overlap check
[x] Coord·`neighbors4_server` 밀집 격자 검증
[x] RouteGoal·transport 일관성 (read-only 검증만)
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_optimization_validation.py
```

### 완료 기준

```text
[x] validation은 read-only
[x] Validation must not invent new routes.
[x] Validation must not mutate placement.
[x] Validation must not fix topology.
```

(정본 서술: `documents/plans/asteroid_lab_optimization/asteroid_lab_08_validation.md` — 계약(금지))

---

## Sequence 8 — Replay Debug (전체 timeline·UI)

Sequence 3B에서 연 **최소 골격**을 확장해 전 이벤트·오버레이·컨트롤러를 완성한다.

### 작업

```text
[x] optimization replay event (OptimizationReplayEventType)
[x] frame serializer
[x] route probe overlay
[x] generation metric frame
[x] validation frame
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_optimization_replay.py
```

### 완료 기준

```text
[x] optimization 과정을 timeline으로 확인 가능
[x] replay artifact는 algorithm input으로 사용되지 않음
```

---

## Sequence 9 — UI Integration

### 작업

```text
[x] replay controller에 optimization track 추가
[x] candidate overlay
[x] route probe overlay
[x] best genome overlay
[x] validation issue overlay
```

### 테스트

```text
pytest tests/integration/shapez_asteroid/test_optimization_ui_payload.py
```

### 완료 기준

```text
[x] UI에서 candidate/probe/commit/validation frame 확인 가능
```

---

## Sequence 10 — Regression Fixtures

> **상태:** Sequence **10A** 완료 · Regression Fixtures 하위 **Sequence 10B-v0**(metrics contract + minimal survivability 비교) **완료** · narrow corridor **#14 회귀 팩 + 대칭 goal 변형**은 테스트/픽스처로 반영됨 · **narrow corridor JSON 골든(v0)** 은 `tests/fixtures/shapez_asteroid/optimization/`에 반영됨 · **full narrow-map evolutionary JSON·역직렬화·결정론 팩** 등은 여전히 후속. Lab UI 시퀀스 표의 “10A–10F”와 **번호 계층이 다름**.

### 작업

```text
[x] simple asteroid fixture
[x] hole asteroid fixture
[x] narrow corridor asteroid fixture — test helper 기반 narrow bridge
[x] shape/fluid mixed fixture
[x] unreachable output fixture
[x] existing trunk / protected corridor 스텁 fixture
```

### 10A 완료 내용

```text
[x] 3-cell narrow bridge OptimizationInput builder
[x] dual-goal symmetric narrow bridge builder (`build_symmetric_narrow_bridge_optimization_input`)
[x] rim competition candidate pool
[x] candidate probe reachable → commit-time reprobe failure regression
[x] shared bridge rollback regression
[x] shape/fluid transport conflict regression
[x] protected ∩ existing trunk seed-domain precedence regression
[x] replay event order deterministic regression
[x] targeted pytest / ruff / mypy green
```

### 남은 범위

```text
[x] JSON fixture under tests/fixtures/shapez_asteroid/optimization/ (narrow corridor asymmetric + symmetric rim competition v0)
[ ] same seed → same best genome on full narrow evolution run
```

### Sequence 10B — Commit Survivability Metrics v0 (Regression Fixtures 하위; Lab UI 10B 아님)

> **상태:** **10B-v0 완료** (metrics contract + minimal survivability 비교). penalty 튜닝이 아니라 **계약·관측·penalty off/on 비교** 고정이 목적. **10B fixture expansion**(reservation·starvation·late-unreachable 등)은 별도 미완료.

**완료 (v0):**

- `PenaltyMode.OFF` / `PenaltyMode.CONSERVATIVE`
- `CommitSurvivabilityMetrics` 계약 및 `summarize_incremental_commit`
- JSON-safe replay metrics adapter
- `COMMIT_SURVIVABILITY_SUMMARY` 리플레이 프레임
- 보수 모드에서 `route_fragility` / `shared_corridor_pressure` 최소 휴리스틱(`route_domain` 유무에 따른 이중 경로 포함)
- narrow bridge 기준 penalty off/on 비교·타깃 pytest / ruff / scoped mypy green

**남은 범위 (expansion):**

- reservation accumulation fixture
- corridor starvation replay fixture
- late-generation unreachable fixture
- evolution fitness 스냅샷과 commit summary 프레임의 penalty 스티칭
- 전역 quality gates (`## Sequence 11` 참고)

#### 메트릭 계약

- **Post-commit(관측 전용):** `CommitSurvivabilityMetrics` — `commit_attempt_count`, `commit_confirmed_count`, `commit_rolled_back_count`, `commit_success_ratio`, `rollback_reason_counts`(enum 값 키), `route_probe_failed_count`, `transport_kind_conflict_count`. 진화 탐색 입력 **금지**.
- **Pre-commit(fitness):** `PenaltyMode.OFF` / `PenaltyMode.CONSERVATIVE`. 보수 모드는 `route_fragility_penalty`·`shared_corridor_pressure_penalty`에만 결정적 휴리스틱을 부여; 나머지 breakdown 슬롯은 v0와 동일하게 0 유지 가능.
- **CONSERVATIVE:** 결정적 **국소** 휴리스틱이며 **전역 commit 성공 예측기가 아님**.

#### 리플레이

- `OptimizationReplayEventType.COMMIT_SURVIVABILITY_SUMMARY` — 스칼라·JSON-safe `rollback_reason_counts`; **solver/GA 입력 금지**.
- **commit-only** summary 프레임에서 `route_fragility_penalty` / `shared_corridor_pressure_penalty`는 **0.0 플레이스홀더** — “패널티가 없다”가 아니라 **이 프레임이 fitness breakdown을 소유하지 않는다**는 뜻이다. 값은 evolution+commit 스티치 시에만 채워질 여지가 있다.

#### 테스트

- `tests/unit/shapez_asteroid/test_commit_survivability_metrics.py` — narrow bridge fixture 기준 survivability 요약·rollback 이유·penalty off vs conservative·랭킹·리플레이 프레임.
- 진화 루프 **리플레이 기록 on/off 동일 결과**는 `tests/unit/shapez_asteroid/test_optimization_replay.py`의 `test_replay_same_seed_on_off_identical_best_genome`·`test_replay_events_do_not_affect_algorithm_result` 등(Sequence 3B replay artifact = algorithm input 금지 계열)으로 이미 고정. `CommitSurvivabilityMetrics`는 post-commit 관측이므로 GA 입력과 분리된 채로 동일 패밀리 불변식을 따른다.

---

## Sequence 11 — Quality Gates

### 작업

```text
[x] ruff check .
[x] black --check .
[x] mypy .
[x] targeted pytest
[x] integration pytest
```

### 완료 기준

```text
[x] all gates pass (2026-05-17 로컬: `ruff check .` · `black --check .` · `mypy .` · `python -m pytest` → 792 passed)
```

> **참고 (2026-05-17):** `tests/unit/shapez_asteroid/` + `tests/integration/shapez_asteroid/test_optimization_ui_payload.py` 구간 **193 passed** (기존). 동일 날짜 **전 저장소** `python -m ruff check .` · `python -m black --check .` · `python -m mypy .` · `python -m pytest` 를 추가로 실행해 **전부 green** 확인(코드 변경 없음).

> **참고 (12E 이후):** Run Solver copy POST 경로는 `tests/unit/asteroid_lab/test_optimization_replay_persist.py`·`tests/integration/web/test_asteroid_miner_layout_solver.py` 등 **타깃 구간 green**. 전 저장소 게이트는 아래 `### 알려진 부채 (전역 게이트)`와 같이 **기존 부채**로 남긴다.

---

## Asteroid Lab — Run Solver POST · optimization replay 영속 (시퀀스 12C–12F)

Lab **검사(디코드) 리플레이**가 성공한 뒤 같은 요청 안에서 **POST 동기** bounded GA를 돌리고, optimization replay 프레임을 `SolverRun.config_json`에 합친다. Lab 응답 JSON에 inspection 번들을 넣기 **전**에 attach를 실행해야 동일 응답에 optimization 트랙이 포함된다 (`django_apps/web/views/public_pages.py`, `django_apps/web/services/asteroid_lab_post_inspection_evolution.py`). `replay_pipeline_service`는 `shapez_asteroid`를 import하지 않는 경계를 유지한다.

### 진행 표 (12C–12F)

| 시퀀스 | 상태 | 요약 |
|--------|------|------|
| 12C | 완료 | `optimization_replay_persist` — 성공한 inspection replay 빌드 이후에만 `SolverRun.config_json`에 프레임 기록 (output-only) |
| 12D | 완료 | 검사 replay `ok` 직후 post-inspection evolution + attach로 UI optimization 트랙 동기 반영 |
| 12E | 완료 | POST 전용 하드캡(`max_candidates`, `route_probe_max_expansions`, `time_budget_ms`, `population_size` 등), `empty_candidate_pool` / `evolution_failed` 분리, JSON `optimization_replay_attach` `{attached, reason}`, `_finalize_attach` INFO 로그, `event_type`·접두사 스모크 및 attach 계약 통합 테스트 |
| 12F | 완료 | persist 프레임 리스트 가드: `validate_optimization_replay_frame_list_payload` + 역직렬화 시 절단 짝·연속 `frame_index`·알려진 `event_type`; malformed 시 읽기 빈 트랙·쓰기 스킵(`invalid_replay_payload`); `build_optimization_replay_track_payload`가 잘림 시 첫 `truncation_reason` 집계; schema/truncation **sibling·봉투·HUD·cap·migration** 비범위 유지(정본: `asteroid_lab_12_runtime_replay_wiring.md`) |

### 12E 구현 요약

- **응답 지연:** POST 인라인 GA에 동기 상한을 둔다 (v0는 응답 안정성 우선).
- **관측성:** 스킵·실패 시에도 `optimization_replay_attach.reason`으로 UI·테스트·로그가 동일 어휘를 공유한다. (의미상 `empty_candidate_pool`은 orchestration 결과에 가깝고 `empty_frames`는 attach 결과에 가깝다; v1에서 타입 분리 여지는 있으나 12E 범위에서는 단일 `OptimizationReplayAttachReason`에 포함해 둔다.)
- **검증:** 위 타깃 pytest 구간 통과.

### 알려진 부채 (전역 게이트)

과거 병합 구간에서는 **전 저장소** `ruff check .` / `mypy .` / `black --check .` 가 환경·드리프트로 실패한 적이 있어 merge PR에 **known debt**로 남긴 바 있다. **2026-05-17 로컬 gate sweep** 기준으로는 위 명령 + `python -m pytest` 가 green이었다. CI·다른 OS·다른 Python 마이너에서 재현 실패가 나오면 이 절을 다시 열어 이슈로 추적한다.

---

## Asteroid Lab — Optimization replay UI (시퀀스 10A–10F)

**번호 주의:** 아래 `10A–10F`는 Lab 페이지 **optimization 리플레이 UI** 전용 진행 번호이다. 위젯·스크립트(`asteroid_miner_layout_lab.js` 등)와 `asteroid_lab_09_replay_debug.md`의 **Frontend Dual-track Replay Policy**와 정렬한다. 본 문서 상단의 `## Sequence 10 — Regression Fixtures`(회귀 fixture)와 **같은 “10” 계층이 아니다.**

### 진행 표 (10A–10F)

| 시퀀스 | 상태 | 요약 |
|--------|------|------|
| 10A | 완료 | parse-only — optimization 리플레이 JSON 파싱만 |
| 10B | 완료 | metadata summary — 요약 메타데이터 표시 |
| 10C | 완료 | summary panel — 요약 패널 UI |
| 10D | 완료 | selected frame metadata — 선택 프레임 메타데이터 |
| 10E | 완료 | independent metadata navigation — `optimizationReplayFrameIndex`만 clamp·갱신, Lab replay 타임라인 비침해 |
| 10F | 완료 | dual-track sync policy document — `asteroid_lab_09_replay_debug.md`에 이중 트랙·비동기화 계약 문서화 |

### 향후 (오버레이·동기화)

| 시퀀스 | 상태 | 요약 |
|--------|------|------|
| 11A | 완료 | readonly overlay projection — `projectOptimizationReplayFrameToLabOverlay(frame)` → `{ cells, diagnostics }`; Lab/optimization 인덱스·Lab 페이로드 미변경; bbox는 `metrics`에서만 |
| 11B | 완료 | overlay rendering — `ENABLE_LAB_OPTIMIZATION_OVERLAY` 뒤에서만; 11A projection + 별도 `#lab-optimization-overlay-layer`; Lab 셀 DOM·페이로드 비변형·인덱스 비동기화 유지 |
| 11C | 미착수 | frame sync policy — **필요할 때만** 명시적 동기화 정책 검토 (기본은 비동기화, `09` 정본 참조) |

#### 11B 완료 기준 (요약)

```text
[x] asteroid_lab_09에 Sequence 11B 정책(플래그·별도 레이어·금지) 문서화
[x] 템플릿에 lab-optimization-overlay-layer / lab-optimization-overlay-diagnostics
[x] asteroid_miner_layout_lab.js: 플래그, clear/render, Lab 그리드와 동기 grid 스타일, 패널·applyFrame·줌 훅
[x] test_asteroid_lab_page_context.py 11B 정적 계약 테스트
```

#### 11A 완료 기준 (요약)

```text
[x] asteroid_lab_09에 Sequence 11A 계약(입출력·금지·bbox·drop) 문서화
[x] asteroid_miner_layout_lab.js에 projectOptimizationReplayFrameToLabOverlay 구현 (렌더/DOM/인덱스 sync 없음)
[x] test_asteroid_lab_page_context.py에 11A 정적 계약 테스트
```
