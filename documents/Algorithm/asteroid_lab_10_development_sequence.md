# Asteroid Lab Optimization — Development Sequence

> **문서 베이스라인 (2026-05-18):** 코드 기준 **Decode → Reconstruction** 완료 이후 optimization 시퀀스는 문서상 **미착수**다. 아래 `[ ]` 체크리스트는 재설정된 상태이며, pytest·통과 수·fixture 목록은 **갱신하지 않음**(역사 인용 보관). Lab 앱: `django_apps/asteroid_lab/` · 상위 [`README.md`](README.md).
>
> **Solver 버튼 v0:** merge·실행 계약·PR 상태는 [`solver_runtime/`](solver_runtime/) 이 정본이다. 본 문서 체크박스와 **상태가 다를 수 있음** — [`solver_runtime/ARCHITECTURE_RECONCILIATION.md`](solver_runtime/ARCHITECTURE_RECONCILIATION.md).

## 목적

GA + local pattern compiler + route feasibility 기반 optimization layer를 안전한 순서로 구현한다.

**필수:** `candidate 생성 → 즉시 route probe → normal pool` 은 분리된 “나중에 붙이기” 시퀀스로 두지 않는다. Phase 3 문서와 동일하게 Sequence 3 한 블록에서 완료한다.

### 구현·검증 메모 (보관)

- **앱 경계(의도):** Lab 디코드·리플레이·ORM은 `django_apps/asteroid_lab/` 쪽에 둔다. optimization DTO·GA 등은 별도 패키지로 두는 설계였으나, 문서에 남은 `django_apps/shapez_asteroid/optimization/` 인용은 **역사적**이다(저장소에서 해당 앱은 제거됨).
- **테스트·픽스처 나열:** 이 절에 있던 pytest 경로·통과 수·JSON 픽스처 목록은 **문서 보관용**이며, 2026-05-18 폴더 정리에서 내용을 갱신하지 않았다. 실제 검증은 코드와 CI를 본다.

---

## Sequence 1A — Domain DTO contracts

DTO·좌표 계약만 먼저 고정해 PR을 작게 유지한다. **hole asteroid fixture·adapter 검증은 1B로 분리**한다.

### 작업

```text
[ ] RouteGoal / RouteGoalKind
[ ] TopologyNode / TopologyEdge / TopologyGraph (무방향 계약)
[ ] OptimizationInput DTO (route_goals·topology_graph·existing_transport_cells·trunk·protected)
[ ] RouteProbeFailureReason / CandidateRejectReason / ValidationIssueCode / ValidationSeverity
[ ] EvolutionConvergenceReason / CommitConflictReason / OptimizationReplayEventType / ReservationState
[ ] RouteDomainSnapshotBuilder 시그니처(단일 route_domain 스냅샷 생성 진입점)
[ ] RouteDomainCellTransition / RecoveryBudget DTO (Phase 7과 동기)
[ ] GenomeDiversityMetrics / EvolutionConfig.forced_distant_mutation_period (Phase 6과 동기)
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_optimization_input.py (DTO·좌표·빈 transport greenfield)
```

### 완료 기준

```text
[ ] 관련 DTO·enum import 가능 (순환 없음)
[ ] enum 멤버 이름·값이 Phase 문서와 동기화됨
[ ] OptimizationInput·그래프·goal의 모든 Coord가 Server X/Y 정본
[ ] `neighbors4_server` 밀집 4방 이웃 단위 테스트 (server x=0 포함 케이스)
[ ] route_goals가 kind·priority 계약을 만족하는 최소 factory 가능
[ ] greenfield = existing_transport_cells 비어 있음 ∧ trunk·protected 공집합 (별도 코드 경로 없음)
```

---

## Sequence 1B — Reconstruction adapter + RouteCellDomain seed builder

입력을 실제 reconstruction 출력과 연결하고, Phase 4가 소비할 domain 초안을 만든다.

### 작업

```text
[ ] Reconstruction → OptimizationInput adapter
[ ] rim / interior / route_goals 추출
[ ] RouteCellDomain 빌더 초안 (**RouteDomainSnapshotBuilder**; existing_transport_cells → transport_mask, trunk·protected·blocked 반영)
[ ] topology_graph 이웃이 neighbors4_server와 모순 없음 (그래프 빌더 테스트)
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_optimization_input.py (adapter·builder 구간)
pytest tests/unit/shapez_asteroid/test_route_cell_domain_builder.py (파일명은 구현에 맞게)
```

### 완료 기준

```text
[ ] hole asteroid fixture에서 interior fill이 mineable로 유지됨
[ ] adapter가 greenfield·비-greenfield 동일 경로로 OptimizationInput을 생산
[ ] 빌더 출력이 blocked/hard_blocked와 모순 없음
```

---

## Sequence 2 — Pattern Library

### 작업

```text
[ ] BundlePattern DTO (attachments·throughput_factor)
[ ] linear 0~3 extension pattern
[ ] rotation support
[ ] deterministic pattern id
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_pattern_library.py
```

### 완료 기준

```text
[ ] ExtensionAttachment·throughput_factor·canonical E (output_dir=E) 계약
[ ] extractor + 0~3 extension linear pattern 생성
[ ] output_stub가 occupied_cells에 포함되지 않음
```

---

## Sequence 3 — Candidate Generator + Route Probe (통합)

후보가 normal pool에 들어가기 전 **반드시** probe를 통과한다.

### 작업

```text
[ ] BundleCandidate DTO (topology_signature·probe 스냅샷; factory만 생성; normal은 rejection 필드 없음)
[ ] CandidateGenerationResult (normal vs rejected)
[ ] CandidateEquivalenceKey + dedupe (max_candidates 전)
[ ] rim-only extractor **후보 생성만** — commit·greedy rim 설치 없음
[ ] extension mineable validation
[ ] reject reason tracking (enum)
[ ] RouteProbeInput / RouteProbeResult (route_domain·RouteGoal·reached_goal·topology_graph·goal_priority_weight)
[ ] bounded uniform-cost probe + transport mask
[ ] reachable → normal pool / unreachable → diagnostic 또는 폐기
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_bundle_candidate_generator.py
pytest tests/unit/shapez_asteroid/test_route_probe.py
pytest tests/unit/shapez_asteroid/test_candidate_route_probe_integration.py
```

### 완료 기준

```text
[ ] valid candidate와 rejected candidate가 deterministic
[ ] 연결 불가능 candidate가 normal pool에 들어가지 않음
[ ] Candidate Generator가 placement를 확정하지 않음 (풀·probe만)
[ ] output_stub에서 RouteGoal 계약에 맞는 도달성 평가
[ ] blocked / hard_blocked 통과 금지
[ ] budget exceeded failure reason 기록
```

---

## Sequence 3B — Replay 최소 골격 (권장, 조기)

candidate/probe 디버깅을 **Sequence 8까지 미루지 않으면** 구현 난이도가 급증한다. UI timeline 전체는 Sequence 8이 담당하고, 여기서는 **기록 파이프라인만** 최소로 연다.

### 작업

```text
[ ] OptimizationReplayEventType + OptimizationReplayFrame 직렬화 (Phase 9 상수 MAX_REPLAY_*·replay_truncated 포함)
[ ] candidate.generated / candidate.rejected / route_probe.succeeded|failed 이벤트만 우선 기록
[ ] replay artifact는 algorithm input 금지 invariant 단위 테스트
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_optimization_replay_skeleton.py (파일명은 구현에 맞게)
```

### 완료 기준

```text
[ ] Sequence 3에서 한 번의 run에 대해 replay NDJSON(또는 동등 바이너리)이 쓰이고, 탐색 결과는 replay on/off 동일(Phase 9 invariant)
```

---

## Sequence 4 — Genome / Fitness

### 작업

```text
[ ] Gene / Genome DTO (Gene.commit_order)
[ ] FitnessBreakdown + FitnessMetrics
[ ] overlap penalty
[ ] unreachable penalty
[ ] route cost penalty
[ ] route_fragility_penalty / shared_corridor_pressure_penalty 필드 (v0는 0 허용)
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_genome_fitness.py
```

### 완료 기준

```text
[ ] same input + same seed = same fitness
[ ] overlap/unreachable penalty가 throughput gain보다 강함
[ ] trunk vs margin 등 동일 reachable이라도 route goal 품질이 점수에 반영됨
[ ] 좁은 통로 점유 시나리오에서 탐욕적 고처리량 우위가 깨질 수 있는 훅(패널티 필드) 존재
```

---

## Sequence 5 — Evolution Search v0

### 작업

```text
[ ] initial population
[ ] mutation
[ ] repair
[ ] elitism
[ ] forced_distant_mutation_period (None 허용) + GenomeDiversityMetrics 자리(0 허용)
[ ] EvolutionConvergenceReason enum + EvolutionResult
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_evolutionary_search.py
```

### 완료 기준

```text
[ ] same seed deterministic (population·mutation·fitness tie-break 포함)
[ ] best fitness non-decreasing under elitism
[ ] best genome 반환
```

---

## Sequence 6 — Incremental Commit

### 작업

```text
[ ] best genome candidate 정렬 (**Gene.commit_order** 정본; candidate 생성·rim 순 기본 금지)
[ ] route probe 재실행 (갱신된 route_domain)
[ ] RouteReservation (reservation_id·reached_goal·goal_priority·state·domain_cell_transitions)
[ ] CommitConflictReason 처리
[ ] commit / rollback + route_domain 반영
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_incremental_commit.py
```

### 완료 기준

```text
[ ] confirmed candidate는 exterior trunk route를 가진다
[ ] commit 실패 candidate는 local rollback된다
[ ] commit 순서가 genome `commit_order`와 일치하고 생성 enumeration 순에 묶이지 않는다
```

---

## Sequence 7 — Validation

### 작업

```text
[ ] final validation result
[ ] confirmed candidate ↔ 정확히 하나의 CONFIRMED RouteReservation 검증
[ ] reserved_cells ↔ path 일관성 검증
[ ] ValidationIssue (ValidationIssueCode·route_goal_kind·transport_kind·optional route_reservation_id·path_index)
[ ] extractor output connectivity check
[ ] orphan transport check
[ ] overlap check
[ ] Coord·`neighbors4_server` 밀집 격자 검증
[ ] RouteGoal·transport 일관성 (read-only 검증만)
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_optimization_validation.py
```

### 완료 기준

```text
[ ] validation은 read-only
[ ] Validation must not invent new routes.
[ ] Validation must not mutate placement.
[ ] Validation must not fix topology.
```

(정본 서술: `documents/plans/asteroid_lab_optimization/asteroid_lab_08_validation.md` — 계약(금지))

---

## Sequence 8 — Replay Debug (전체 timeline·UI)

Sequence 3B에서 연 **최소 골격**을 확장해 전 이벤트·오버레이·컨트롤러를 완성한다.

### 작업

```text
[ ] optimization replay event (OptimizationReplayEventType)
[ ] frame serializer
[ ] route probe overlay
[ ] generation metric frame
[ ] validation frame
```

### 테스트

```text
pytest tests/unit/shapez_asteroid/test_optimization_replay.py
```

### 완료 기준

```text
[ ] optimization 과정을 timeline으로 확인 가능
[ ] replay artifact는 algorithm input으로 사용되지 않음
```

---

## Sequence 9 — UI Integration

### 작업

```text
[ ] replay controller에 optimization track 추가
[ ] candidate overlay
[ ] route probe overlay
[ ] best genome overlay
[ ] validation issue overlay
```

### 테스트

```text
pytest tests/integration/shapez_asteroid/test_optimization_ui_payload.py
```

### 완료 기준

```text
[ ] UI에서 candidate/probe/commit/validation frame 확인 가능
```

---

## Sequence 10 — Regression Fixtures

> **상태 (2026-05-18 재설정):** 아래 체크리스트는 **미착수**다. 과거에 “완료·반영됨”으로 읽히던 문장은 보관용이며, pytest·픽스처 경로는 갱신하지 않았다. Lab UI `10A–10F` 번호와 본 `Sequence 10`은 **다른 계층**이다.

### 작업

```text
[ ] simple asteroid fixture
[ ] hole asteroid fixture
[ ] narrow corridor asteroid fixture — test helper 기반 narrow bridge
[ ] shape/fluid mixed fixture
[ ] unreachable output fixture
[ ] existing trunk / protected corridor 스텁 fixture
```

### 10A 참고 목록 (보관)

```text
[ ] 3-cell narrow bridge OptimizationInput builder
[ ] dual-goal symmetric narrow bridge builder (`build_symmetric_narrow_bridge_optimization_input`)
[ ] rim competition candidate pool
[ ] candidate probe reachable → commit-time reprobe failure regression
[ ] shared bridge rollback regression
[ ] shape/fluid transport conflict regression
[ ] protected ∩ existing trunk seed-domain precedence regression
[ ] replay event order deterministic regression
[ ] targeted pytest / ruff / mypy green
```

### 남은 범위

```text
[ ] JSON fixture under tests/fixtures/shapez_asteroid/optimization/ (narrow corridor asymmetric + symmetric rim competition v0)
[ ] same seed → same best genome on full narrow evolution run
```

### Sequence 10B — Commit Survivability Metrics v0 (Regression Fixtures 하위; Lab UI 10B 아님)

> **상태:** 계약·관측 목표만 문서화됨. 구현·fixture는 **미착수**로 본다(체크리스트 재설정).

**스펙 초안 (v0):**

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

- 경로·케이스 이름은 **문서 보관용**이다. 실제 테스트 트리·검증은 코드와 CI를 본다.

---

## Sequence 11 — Quality Gates

### 작업

```text
[ ] ruff check .
[ ] black --check .
[ ] mypy .
[ ] targeted pytest
[ ] integration pytest
```

### 완료 기준

```text
[ ] all gates pass (ruff / black / mypy / pytest — 구체 통과 수는 문서 갱신 범위 밖)
```

> **참고:** 과거 로컬에서 green을 확인했다는 기록은 **보관용**이다. 2026-05-18 폴더 정리에서는 pytest·통과 수·경로를 갱신하지 않았다.

> **참고 (12E 이후):** POST·persist 관련 경로는 코드와 CI를 본다. 전 저장소 게이트는 아래 `### 알려진 부채 (전역 게이트)`로 추적한다.

---

## Asteroid Lab — Run Solver POST · optimization replay 영속 (시퀀스 12C–12H)

Lab **검사(디코드) 리플레이**가 성공한 뒤 같은 요청 안에서 **POST 동기** bounded GA를 돌리고, optimization replay 프레임을 `SolverRun.config_json`에 합친다. Lab 응답 JSON에 inspection 번들을 넣기 **전**에 attach를 실행해야 동일 응답에 optimization 트랙이 포함된다 (`django_apps/web/views/public_pages.py`, `django_apps/web/services/asteroid_lab_post_inspection_evolution.py`). `replay_pipeline_service`는 `shapez_asteroid`를 import하지 않는 경계를 유지한다.

### 진행 표 (12C–12H)

| 시퀀스 | 상태 | 요약 |
|--------|------|------|
| 12C | 미착수 | `optimization_replay_persist` — 성공한 inspection replay 빌드 이후에만 `SolverRun.config_json`에 프레임 기록 (output-only) |
| 12D | 미착수 | 검사 replay `ok` 직후 post-inspection evolution + attach로 UI optimization 트랙 동기 반영 |
| 12E | 미착수 | POST 전용 하드캡(`max_candidates`, `route_probe_max_expansions`, `time_budget_ms`, `population_size` 등), `empty_candidate_pool` / `evolution_failed` 분리, JSON `optimization_replay_attach` `{attached, reason}`, `_finalize_attach` INFO 로그, `event_type`·접두사 스모크 및 attach 계약 통합 테스트 |
| 12F | 미착수 | persist 프레임 리스트 가드: `validate_optimization_replay_frame_list_payload` + 역직렬화 시 절단 짝·연속 `frame_index`·알려진 `event_type`; malformed 시 읽기 빈 트랙·쓰기 스킵(`invalid_replay_payload`); `build_optimization_replay_track_payload`가 잘림 시 첫 `truncation_reason` 집계; schema/truncation **sibling·봉투·cap·migration** 비범위 유지(정본: `asteroid_lab_12_runtime_replay_wiring.md`) |
| 12G | 미착수 | 읽기 실패 시 빈 트랙 + `metrics.optimization_replay_diagnostic_reason`만 추가 (`optimization_ui_payload` 분류 + `optimization_replay_payload_for_project`); 정상 페이로드에서는 키 부재; 솔버·리플레이 의미·schema/truncation sibling 비변경(정본: `asteroid_lab_12_runtime_replay_wiring.md` §7) |
| 12H | 미착수 | Optimization replay 패널 HUD: `replay_truncated` / `truncation_reason` / `optimization_replay_diagnostic_reason` 표시 전용(`asteroid_miner_layout_solver.html` SSR + `asteroid_miner_layout_lab.js`); 리플레이 시맨틱·Lab 타임라인 제어·암묵적 동기화 없음 |

### 12E 구현 요약

- **응답 지연:** POST 인라인 GA에 동기 상한을 둔다 (v0는 응답 안정성 우선).
- **관측성:** 스킵·실패 시에도 `optimization_replay_attach.reason`으로 UI·테스트·로그가 동일 어휘를 공유한다. (의미상 `empty_candidate_pool`은 orchestration 결과에 가깝고 `empty_frames`는 attach 결과에 가깝다; v1에서 타입 분리 여지는 있으나 12E 범위에서는 단일 `OptimizationReplayAttachReason`에 포함해 둔다.)
- **검증:** 코드·CI 기준(문서에 pytest 구간을 열거하지 않음).

### 알려진 부채 (전역 게이트)

전 저장소 린트·타입·테스트 게이트는 환경·드리프트에 따라 달라질 수 있다. 이 절은 **추적용**이며, 2026-05-18 문서 정리에서는 통과 수·날짜를 갱신하지 않았다.

---

## Sequence 13 — Replay payload scalability (로드맵, 구현 게이트)

**정본:** [`asteroid_lab_13_replay_payload_scalability.md`](asteroid_lab_13_replay_payload_scalability.md)  
계측·13A·13B 역사: [`asteroid_lab_09_replay_debug.md`](asteroid_lab_09_replay_debug.md) · **제품 replay:** [`asteroid_lab_09_unified_step_replay.md`](asteroid_lab_09_unified_step_replay.md) (단일 unified timeline; dual-track **폐기**). 13A·13B의 Lab/optimization **귀속(attribution)** 명칭은 계측 시점의 historical 라벨이다.

| 하위 | 상태 | 요약 |
|------|------|------|
| 13A | 미착수 | 최상위 JSON 섹션 계측, optimization replay 하드 캡 회귀, HAR 근거 |
| 13B | 미착수 | Lab replay 귀속·`largest_lab_frames`·redundancy, Lab 미캡 갭 문서화 |
| 13C | **승인 대기** | Full Lab replay **lazy-load 엔드포인트**(선호 1차 구현); 인라인과 시맨틱 동등 |
| 13D | 로드맵 | UI lazy-load·로딩/오류·소유권 유지·인라인 폴백 허용 |
| 13E | 로드맵 | Delta prototype — lazy-load 불충분 시, 재구성 동등성 테스트 필수 |
| 13F | 로드맵 | Cell interning — redundancy 근거 후, 렌더·조회 동등성 |
| 13G | 로드맵 | gzip/Brotli 등 전송 — 시맨틱 작업 대체 금지 |

**금지(문서 단계):** 응답 계약·JS 로딩·delta 본구현·solver semantics 선제 변경. 13C 구현은 **명시 승인 후**.

---

## Asteroid Lab — Optimization replay UI (시퀀스 10A–10F) — **마이그레이션 대상**

> **2026-05-19:** 제품 정본은 [`asteroid_lab_09_unified_step_replay.md`](asteroid_lab_09_unified_step_replay.md). 아래 10A–10F·11A–11B(dual-track·별도 optimization controller·HUD-only)는 **obsolete**이다. 신규 작업은 **Phase 9 시퀀스 9A–9H**를 따른다. **9E**(단일 unified controller UI)는 2026-05-19 구현 완료.

**번호 주의:** 아래 `10A–10F`는 Lab 페이지 **optimization 리플레이 UI** 전용 진행 번호(역사)이다. 본 문서 상단의 `## Sequence 10 — Regression Fixtures`(회귀 fixture)와 **같은 “10” 계층이 아니다.**

<details>
<summary>Deprecated historical: 시퀀스 10A–11B (dual-track·별도 optimization controller) — 펼치기</summary>

### 진행 표 (10A–10F)

| 시퀀스 | 상태 | 요약 |
|--------|------|------|
| 10A | 미착수 | parse-only — optimization 리플레이 JSON 파싱만 |
| 10B | 미착수 | metadata summary — 요약 메타데이터 표시 |
| 10C | 미착수 | summary panel — 요약 패널 UI |
| 10D | 미착수 | selected frame metadata — 선택 프레임 메타데이터 |
| 10E | 미착수 | independent metadata navigation — `optimizationReplayFrameIndex`만 clamp·갱신, Lab replay 타임라인 비침해 |
| 10F | 미착수 | dual-track sync policy document — `asteroid_lab_09_replay_debug.md`에 이중 트랙·비동기화 계약 문서화 |

### 향후 (오버레이·동기화)

| 시퀀스 | 상태 | 요약 |
|--------|------|------|
| 11A | 미착수 | readonly overlay projection — `projectOptimizationReplayFrameToLabOverlay(frame)` → `{ cells, diagnostics }`; Lab/optimization 인덱스·Lab 페이로드 미변경; bbox는 `metrics`에서만 |
| 11B | 미착수 | overlay rendering — **env 플래그 없음**(미구현); 11A projection + 별도 `#lab-optimization-overlay-layer`; Lab 셀 DOM·페이로드 비변형·인덱스 비동기화 유지. 구현 시 [`environment.md`](../ai/manuals/environment.md)에 canonical 이름 등록 |
| 11C | 미착수 | frame sync policy — **필요할 때만** 명시적 동기화 정책 검토 (기본은 비동기화, `09` 정본 참조) |

#### 11B 완료 기준 (요약)

```text
[ ] asteroid_lab_09에 Sequence 11B 정책(플래그·별도 레이어·금지) 문서화
[ ] 템플릿에 lab-optimization-overlay-layer / lab-optimization-overlay-diagnostics
[ ] asteroid_miner_layout_lab.js: 플래그, clear/render, Lab 그리드와 동기 grid 스타일, 패널·applyFrame·줌 훅
[ ] test_asteroid_lab_page_context.py 11B 정적 계약 테스트
```

#### 11A 완료 기준 (요약)

```text
[ ] asteroid_lab_09에 Sequence 11A 계약(입출력·금지·bbox·drop) 문서화
[ ] asteroid_miner_layout_lab.js에 projectOptimizationReplayFrameToLabOverlay 구현 (렌더/DOM/인덱스 sync 없음)
[ ] test_asteroid_lab_page_context.py에 11A 정적 계약 테스트
```

</details>
