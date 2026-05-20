---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: —
pr: 전 PR
related_docs:
  - documents/Algorithm/solver_runtime/README.md
  - documents/Algorithm/asteroid_lab_00_overview.md
  - .cursor/rules/asteroid-lab-invariants.mdc
---

# 핵심 원칙 (§0)

Solver Runtime 전 Phase에 공통으로 적용한다.

## 0.1 설치하면서 탐색하지 않는다

**금지:**

```text
server x/y 순서대로 실제 extractor / extension / belt / pipe 설치
```

**허용:**

```text
server x/y 순서대로 deterministic candidate enumeration
```

좌표 순서는 **후보 생성 순서**일 뿐 **commit 순서가 아니다.**

## 0.2 외곽 void에 실제 목표 belt/pipe를 먼저 설치하지 않는다

**금지:**

```text
void에 임의 belt/pipe를 먼저 설치하고 거기로 모두 연결
```

**허용:**

```text
external void / margin / existing trunk를 RouteGoal로 생성
```

실제 transport materialization은 **commit 이후** route network 해석 단계에서 수행한다. ([`phase_k_route_materialization.md`](phase_k_route_materialization.md))

## 0.3 Reconstruction map 로드 직후 extension kind를 field로 정규화

DB reconstruction map은 miner extension kind를 원본 그대로 보존할 수 있다. Solver runtime 1차 공정은 optimization용 **field kind**로 변환한다.

```text
shapeMinerExtension / Layout_ShapeMinerExtension
→ asteroid_shape_field

fluidMinerExtension / Layout_FluidMinerExtension
→ asteroid_fluid_field
```

- 변환은 **DB 원본을 수정하지 않는다.**
- 경계: `LoadedReconstructionSnapshot → OptimizationInput` **adapter**에서만 수행.

Optimizer는 변환 이후 다음 집합을 정본으로 사용한다.

```text
OptimizationInput.asteroid_cells
OptimizationInput.mineable_cells
OptimizationInput.rim_cells
OptimizationInput.external_void_cells
OptimizationInput.route_goals
OptimizationInput.route_domain
```

규칙:

```text
asteroid_shape_field → asteroid_cells + mineable_cells
asteroid_fluid_field → asteroid_cells + mineable_cells
```

extension 원본 kind는 resource/evidence 용도로 **보존 가능**.

**금지 (optimizer 내부):**

```python
# candidate_geometry / route_probe 내부에서 직접 kind 판정 금지
cell.kind == "shapeMinerExtension"
cell.kind == "fluidMinerExtension"
cell.kind == "asteroid_fluid_field"
cell.kind == "asteroid_shape_field"
```

kind 판정은 adapter 1차 정규화 책임이며, optimizer 내부는 `asteroid_cells` / `mineable_cells` 집합만 본다.

## 0.4 모든 candidate는 route probe를 통과해야 normal pool에 들어간다

```text
projected gene
→ geometry validation
→ route probe
→ reachable=True only normal_candidates
```

unreachable candidate는 diagnostic / rejected candidate로만 남긴다.

## 0.5 Candidate phase reachable은 commit success가 아니다

commit 시점에는 항상 **최신 route domain**으로 다시 probe한다.

```text
candidate probe success ≠ final commit success
```

상세: [`phase_j_incremental_commit.md`](phase_j_incremental_commit.md).

## 0.6 좌표 용어 (Runtime 정본, alias 금지)

| 이름 | 의미 |
|------|------|
| `fixed_output_transport` | extractor 직후 **첫 belt/pipe** 셀 (canonical E에서 offset `(1,0)`) |
| `route_probe_start` | route search **시작** 셀 (offset `(2,0)`; `occupied_offsets`에 **포함 금지**) |
| `output_stub` | **레거시** — 신규 DTO·함수·문서 필드명으로 **사용 금지** |

`CandidateRejectReason.output_stub_*` enum 멤버 이름은 **기존 enum 호환용**이며 의미는 `route_probe_start`이다.

## 0.7 신규 테스트·문서 명명 (reject / geometry)

| 범위 | 규칙 |
|------|------|
| **신규 pytest 함수명** | `route_probe_start_*` · `fixed_output_transport_*` — `output_stub_*` **사용 금지** |
| **신규 문서 본문·주석** | `route_probe_start` 정본 ([§0.6](#06-좌표-용어-runtime-정본-alias-금지)) |
| **기존 enum 값** | `output_stub_inside_occupied` 등 **rename 금지** (하위 호환); assert는 enum 값·의미 매핑으로 검증 |

예: `test_geometry_rejects_route_probe_start_inside_occupied` (O) · `test_geometry_rejects_output_stub_inside_occupied` (신규 추가 X).

상세: [`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) §4 · [`open_decisions.md`](open_decisions.md) OD-1.

## 좌표·replay (교차 참조)

- OptimizationInput 이후 모든 `Coord` = **Server X/Y** only. raw↔server 재변환은 optimization 내부 금지.
- Replay·NDJSON·metrics는 **algorithm input 금지**.

[`asteroid_lab_00_overview.md`](../asteroid_lab_00_overview.md) · [`.cursor/rules/asteroid-lab-invariants.mdc`](../../../.cursor/rules/asteroid-lab-invariants.mdc)
