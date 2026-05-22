---
status: AUDIT
owner: asteroid-lab
last_reviewed: 2026-05-22
language: ko
related_docs:
  - asteroid_lab_mining_installation/README.md
  - asteroid_lab_mining_installation/00_source_of_truth.md
  - asteroid_lab_mining_installation/03_db_cross_reference.md
  - documents/game_rules/shapez2_asteroid_space_transport_throughput.md
---

# 설치 가이드 — 채굴기·확장기 (Asteroid Lab)

Shapez 2 인게임 규칙과 이 Lab에서의 **채굴기·확장기** 흐름을 처음부터 끝까지 서술한다. 규칙 판정은 [`01_rule_reconciliation.md`](01_rule_reconciliation.md), DB 사실은 [`03_db_cross_reference.md`](03_db_cross_reference.md)를 본다.

Phase 상세 계약(RESEARCH): [`asteroid_lab_02_pattern_library.md`](../asteroid_lab_02_pattern_library.md) · [`asteroid_lab_03_candidate_generator.md`](../asteroid_lab_03_candidate_generator.md) · [`asteroid_lab_07_incremental_commit.md`](../asteroid_lab_07_incremental_commit.md).

---

## 핵심 구분 (Lab)

> **Lab에서 miner/extension은 candidate 생성 시점에 설치되지 않는다.**  
> route feasibility 통과 → selection → **commit 시점 reprobe** + reservation 통과 후 **confirmed placement**가 된다.

| 단계 | 맵에 miner/extension이 보이는가 | 확정 설치인가 |
|------|--------------------------------|---------------|
| decode / 붙여넣은 blueprint | 예 (사용자 레이아웃) | 아니오 — 입력만 |
| cleanup | 제거됨 | 아니오 |
| reconstruction | mineable field만 | 아니오 |
| 후보 생성 + route probe | 아니오 (메모리 geometry만) | **아니오** |
| selection / fitness | 아니오 | 아니오 |
| incremental commit | reprobe 후 예 | **예** |
| replay 스크럽 | 관측 | 알고리즘 입력 아님 |

`rim-only` / `ExtractorPlacementPolicy.RIM_ONLY`는 후보 생성 시 **extractor 앵커 좌표 ∈ rim_cells** 제한이지, rim을 순회하며 설치하는 순서가 아니다. [`01`](01_rule_reconciliation.md) *rim-only* 행 참고.

---

## 1. 인게임 규칙 (Shapez 2)

### 채굴기·펌프 플랫폼

- **도형(Shape):** Asteroid Miner가 Space Belt로 도형을 보낸다.
- **액체(Fluid):** Asteroid Pump가 Space Pipe로 액체를 보낸다.
- **확장기 체인 (v0 linear):** 추출기당 확장기 **최대 3대**; 확장기마다 처리량 배수 +×4 (기본 ×4에서 누적).

| 확장기 수 | `throughput_factor` (Lab 코드) |
|-----------|-------------------------------|
| 0 | 4 |
| 1 | 8 |
| 2 | 12 |
| 3 | 16 |

절대 처리량(기본 30 shapes/min, 벨트 포화 등): CANON [`shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md).

### facing·출력 운송

- 확장기는 추출기 또는 이전 확장기에 부착한다. **parent-facing**은 게임 부착 규칙과 일치해야 한다 (Lab: [`asteroid_lab_02`](../asteroid_lab_02_pattern_library.md)의 `ExtensionAttachment.required_facing`).
- **출력 쪽:** 추출기 출력 직후 첫 **belt 또는 pipe** 셀이 필수 (`GeneTemplate`의 `fixed_output_transport`; `occupied_offsets`에 포함하지 않음).
- 경로 탐색은 그 운송 stub **다음**에서 시작 (`route_probe_start_offset`).

### Blueprint 타입명 vs DB

붙여넣기 코드는 `Layout_ShapeMiner`, `Layout_FluidMiner`, `Layout_*MinerExtension`을 쓴다. 정규화 `game_data`에는 `ExtractorDefaultInternalVariant` 같은 이름이 올 수 있다 — [`03`](03_db_cross_reference.md) § Blueprint vs DB.

---

## 2. Lab 입력 파이프라인

제품·solver 상위 흐름:

```text
POST blueprint copy_code (또는 project slug 열기)
  → decode (경계에서 raw X/Y 보존)
  → cleanup: 기존 miner, extension, belt/pipe 제거 (정책)
  → reconstruction: 채굴 가능 소행성 필드 + topology
  → OptimizationInput (Server X/Y만)
  → solver runtime (후보 → selection → commit)
  → replay 타임라인 + 결과 레이아웃
```

### Cleanup (기존 채굴기가 사라지는 이유)

최적화 전에 기존 **extractor / extension** 셀을 제거한다. 좌표는 flood-fill에서 **벽/장벽**(`wall_coords`)으로 남을 수 있다. belt/pipe는 cleanup 정책으로 strip하며 `wall_coords` 처리는 다를 수 있다 — [`plan_asteroid_reconstruction_topology_2026-05-16.md`](../../ai/plan_asteroid_reconstruction_topology_2026-05-16.md).

### 좌표

정규화 이후 최적화 계층은 **Server X/Y만** 사용한다. 후보·commit 코드 안에서 raw↔server 재변환 금지 ([`00`](00_source_of_truth.md), [`asteroid_lab_01`](../asteroid_lab_01_optimization_input.md)).

---

## 3. 후보 생성 (설치 아님)

**패키지:** `django_apps/asteroid_lab/optimization/`

1. **GeneTemplate 라이브러리** — canonical **E** 로컬 topology: extractor `(0,0)`, linear 확장 체인, `throughput_factor` 4/8/12/16 ([`gene_template.py`](../../../django_apps/asteroid_lab/optimization/gene_template.py)).
2. **Projection** — 템플릿을 맵 rim(또는 정책) 앵커에 회전·이동.
3. **BundleCandidate** — occupied = extractor + extensions만; output stub·첫 transport 셀은 정의만 하고 **commit 안 함**.
4. **Route probe (즉시)** — `output_stub`에서 `run_route_probe`; unreachable은 normal pool **제외**.

```text
후보 생성 → local geometry 검증 → route probe → normal pool | rejected
```

**잘못된 mental model:** “솔버가 탐색하면서 miner를 깔고 있다.” 실제로는 **잠정 bundle을 열거**하고 외부 `RouteGoal` 도달 가능성만 검사한다.

**테스트:** `test_candidate_generator_does_not_commit_placements`, `test_candidate_generator_reachable_only_enters_normal_pool`.

---

## 4. 선택 (selection)

v0 solver는 **후보 선택**(처리량 예산, 점수)과 **genome / fitness** 정렬을 사용할 수 있다 — [`asteroid_lab_05_genome_fitness.md`](../asteroid_lab_05_genome_fitness.md), [`solver_runtime/README.md`](../solver_runtime/README.md).

- **Fitness / penalty**는 예측용(probe 시점).
- **Commit survivability**는 commit 시점 관측 — replay로 역산하지 않음 ([`asteroid_lab_10`](../asteroid_lab_10_development_sequence.md) §10B).

Selection은 **어떤 bundle을 commit 시도할지** 고르지, 최종 레이아웃을 혼자 확정하지는 않는다.

---

## 5. 확정 설치 (incremental commit)

**패키지:** incremental commit + `RouteDomainSnapshotBuilder`

순서는 **`Gene.commit_order`만** — rim 스캔 순서·후보 enumeration 순서가 아니다 ([`asteroid_lab_07`](../asteroid_lab_07_incremental_commit.md)).

`commit_order`마다:

```text
1. route_domain 스냅샷 재빌드 (최신 reservation + committed 점유)
2. route probe 재실행 (후보 단계 probe는 참고용)
3. 성공 시: 경로 reserve, 장비 셀 materialize
4. 실패 시: rolled_back (v0: 구현에 따라 abort/rollback)
```

원칙 ([`asteroid_lab_00`](../asteroid_lab_00_overview.md)):

```text
외부 trunk에 연결되기 전까지 모든 것은 잠정(provisional)이다.
```

**테스트 정본:** `test_incremental_commit_reprobes_latest_domain`.

상태(개념): `PROVISIONAL` → `FEASIBLE` → `ROUTED` → `CONFIRMED` | `ROLLED_BACK` — Phase 7 문서.

---

## 6. Replay (관측 전용)

Replay는 **단일 lab 타임라인** ([`asteroid_lab_09_replay_timeline.md`](../asteroid_lab_09_replay_timeline.md) ACTIVE). 프레임은 **알고리즘 입력이 아니다** ([`asteroid_lab_00`](../asteroid_lab_00_overview.md)).

wire `event_type` (enum): `django_apps/asteroid_lab/replay/replay_enums.py` · [`asteroid_lab_12_runtime_replay_wiring.md`](../asteroid_lab_12_runtime_replay_wiring.md).

| phase (대표) | `ReplayEventType` (예) | miner/extension 관점 |
|--------------|------------------------|----------------------|
| reconstruction | `reconstruction.*` | 필드 준비; replay 스토리상 기존 miner는 이미 strip |
| optimization | `optimization.input_loaded` | topology + goals 준비 |
| 후보 | `candidate.generated` / `candidate.rejected` | bundle 평가, **미설치** |
| probe | `route_probe.succeeded` / `route_probe.failed` | 생성 시점 도달성 |
| selection | `candidate_selection.completed`, `genome.evaluated` | 정렬·풀 통계 |
| commit | `route.commit_attempted`, `route.committed`, `route.rolled_back` | **설치 시도** |
| materialize | `route.materialized` | 확정 경로 셀 기록 |
| 종료 | `result.layout` | 최종 맵 |

UI: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` — 단일 스크럽 인덱스; `event_type`을 격자 오버레이에 매핑 (세부 UI 문자열은 여기서 중복하지 않음).

---

## 빠른 링크

| 필요 | 문서 |
|------|------|
| 정본 우선순위 | [`00`](00_source_of_truth.md) |
| 규칙 vs DB vs 코드 | [`01`](01_rule_reconciliation.md) |
| 기존 문서 상태 | [`02`](02_doc_drift_matrix.md) |
| dump / ORM 목록 | [`03`](03_db_cross_reference.md) |
| 처리량 CANON | [`game_rules/...throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md) |

---

## 독자 자가 점검

**이 파일만** 읽은 뒤 아래에 답할 수 있어야 한다.

1. cleanup이 붙여넣은 blueprint의 miner를 제거하는가? → **예**
2. 후보 생성이 맵에 miner를 설치하는가? → **아니오**
3. commit 시점 reprobe가 후보 시점과 동일한 스냅샷을 쓰는가? → **아니오** (항상 최신 `route_domain`)
4. replay를 optimization 입력으로 쓸 수 있는가? → **아니오**
