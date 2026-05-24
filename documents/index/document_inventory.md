# 문서 Inventory

기준일: 2026-05-24  
범위: `documents/`의 주요 설계·계획·조사·보고·보관 문서. 전체 파일 목록이 아니라 AI context 선택을 위한 authority 지도다.

상태 enum은 [`document_lifecycle.md`](document_lifecycle.md)를 따른다.

## Hot path (Asteroid Lab / RTTP)

1. Code + tests → [`documents/ai/current_plan.md`](../ai/current_plan.md)
2. **Topic row** in § Asteroid Lab authority by topic (below) — **conflict resolver**
3. Row-designated spec or Algorithm doc
4. [`documents/ai/contamination_policy.md`](../ai/contamination_policy.md)

**QUARANTINE (never implementation authority):** [`documents/plans/asteroid_lab_optimization/`](../plans/asteroid_lab_optimization/)

There is no separate `authority_index.md`; this file is the sole authority map.

## 정본 문서

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`AGENTS.md`](../../AGENTS.md) | `CANON` | workflow spec | YES | 라우팅·문서 권위·승인 금지 |
| [`.cursor/rules/shapez2-core.mdc`](../../.cursor/rules/shapez2-core.mdc) | `CANON` | rule | YES | Cursor 단일 alwaysApply (Caveman·게이트·검증) |
| [`documents/ai/START_HERE.md`](../ai/START_HERE.md) | `CANON` | context entrypoint | YES | AI context 선택 시작점 |
| [`documents/ai/manuals/`](../ai/manuals/) | `CANON` | workflow manuals | YES | 작업 유형별 온디맨드 매뉴얼 |
| [`documents/ai/contamination_policy.md`](../ai/contamination_policy.md) | `CANON` | governance policy | YES | 오염 패턴·legacy 토큰·PR playbook |
| [`documents/index/document_lifecycle.md`](document_lifecycle.md) | `CANON` | document governance | YES | 문서 상태 enum과 읽기 우선순위 |
| [`documents/index/document_inventory.md`](document_inventory.md) | `CANON` | document governance | YES | 현재 문서 authority 지도 |
| [`documents/adr/`](../adr/) | `CANON` | architecture decisions | YES | 정본 spec의 결정 이유 |
| [`documents/game_rules/`](../game_rules/) | `CANON` | domain spec | YES | shapez 2 규칙과 solver domain abstraction |
| [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../game_rules/shapez2_asteroid_space_transport_throughput.md) | `CANON` | domain throughput | YES | Asteroid Miner/Pump·Space Belt/Pipe 절대 L/min·shapes/min |
| [`documents/research/research_blueprint_grid_coordinates_2026-05-10.md`](../research/research_blueprint_grid_coordinates_2026-05-10.md) | `CANON` | domain invariant | YES | blueprint grid coordinate invariant |

## Active 작업·백로그

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`documents/ai/current_plan.md`](../ai/current_plan.md) | `ACTIVE` | work queue | NO | 현재 작업 흐름 |
| [`documents/ai/checklist.md`](../ai/checklist.md) | `ACTIVE` | checklist | NO | 진행 상태와 검증 게이트 |
| [`documents/plans/`](../plans/) | `ACTIVE` | plans/backlog | NO | 완료 근거 미확정 계획. **예외:** `plans/asteroid_lab_optimization/` = **QUARANTINE** — § Asteroid Lab authority by topic 참조 |
| [`documents/ai/plans/`](../ai/plans/) | `ACTIVE` | scoped plans | NO | 범위 한정 플랜 |
| [`documents/Algorithm/solver_runtime/`](../Algorithm/solver_runtime/) | `HISTORICAL` | solver button pipeline | NO | Phase A–M 오케스트레이션 아카이브. **RTTP runtime ≠ 본 시리즈** — [`current_plan.md`](../ai/current_plan.md) 정본 |
| [`documents/Algorithm/asteroid_lab_11_future_execution_plan_post_sequence.md`](../Algorithm/asteroid_lab_11_future_execution_plan_post_sequence.md) | `ACTIVE` | post-v0 roadmap | NO | 2026-05-18 스펙·체크리스트 미착수 베이스라인; v0 완료와 **대조 금지** — [`current_plan.md`](../ai/current_plan.md) 우선 |

## Asteroid Lab authority by topic

When two documents disagree on Asteroid Lab / RTTP implementation, resolve by this table. **Do not merge competing specs.**

| Topic | `authority_for_implementation` | Inventory status | Notes |
|-------|-------------------------------|------------------|-------|
| Runtime entry / config gate | [`current_plan.md`](../ai/current_plan.md) + `django_apps/asteroid_lab/services/solver_runtime_entry.py` | CANON → code | `ASTEROID_LAB_RTTP_ENABLED`; strip removed monolith only |
| RTTP Hybrid C pipeline | [`docs/superpowers/specs/2026-05-22-rttp-hybrid-c-layout-design.md`](../../docs/superpowers/specs/2026-05-22-rttp-hybrid-c-layout-design.md) + `django_apps/asteroid_lab/optimization/` | ACTIVE spec | Merged baseline on `master` |
| Macro bundle T3 | [`docs/superpowers/specs/2026-05-23-rttp-v1-macrobundle-t3-design.md`](../../docs/superpowers/specs/2026-05-23-rttp-v1-macrobundle-t3-design.md) | ACTIVE spec | **PAUSE** per `current_plan` — no new macro work |
| B2 catalog slice / transport T2 | [`docs/superpowers/specs/2026-05-24-b2-t2-per-cell-transport-resolution-design.md`](../../docs/superpowers/specs/2026-05-24-b2-t2-per-cell-transport-resolution-design.md) | CLOSED | PR #62; tests ground truth |
| B2 transport-aware route domain T3 | [`docs/superpowers/specs/2026-05-24-b2-t3-transport-aware-route-domain-design.md`](../../docs/superpowers/specs/2026-05-24-b2-t3-transport-aware-route-domain-design.md) | CLOSED | PR #61 |
| Track D footprint/connector | [`docs/superpowers/specs/2026-05-24-building-catalog-slice-first-consumption-design.md`](../../docs/superpowers/specs/2026-05-24-building-catalog-slice-first-consumption-design.md) | ACTIVE | Design parent; plan TBD |
| OptimizationInput / adapter | [`documents/Algorithm/asteroid_lab_01_optimization_input.md`](../Algorithm/asteroid_lab_01_optimization_input.md) | CANON | **Not** `plans/asteroid_lab_optimization/01` |
| Route probe / candidate pool | [`documents/Algorithm/asteroid_lab_04_route_probe.md`](../Algorithm/asteroid_lab_04_route_probe.md) | CANON | Probe at creation |
| Validation read-only | [`documents/Algorithm/asteroid_lab_08_validation.md`](../Algorithm/asteroid_lab_08_validation.md) + [`documents/adr/ADR-003-final-validation-assertion-gate.md`](../adr/ADR-003-final-validation-assertion-gate.md) | CANON | |
| Replay timeline / 3B-S | [`documents/Algorithm/asteroid_lab_09_replay_timeline.md`](../Algorithm/asteroid_lab_09_replay_timeline.md) + [`docs/superpowers/specs/2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md`](../../docs/superpowers/specs/2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md) | CANON + ACTIVE spec | Output-only product replay |
| Development sequence | [`documents/Algorithm/asteroid_lab_10_development_sequence.md`](../Algorithm/asteroid_lab_10_development_sequence.md) + `current_plan` RTTP gate sync | ACTIVE doc | Checkbox state may lag; gate sync note wins |
| Pre-RTTP plans tree | [`documents/plans/asteroid_lab_optimization/`](../plans/asteroid_lab_optimization/) | **QUARANTINE** (`ARCHIVED`) | `do_not_use_as_authority: true` |
| Solver runtime Phase A–M | [`documents/Algorithm/solver_runtime/`](../Algorithm/solver_runtime/) | **HISTORICAL** | Orchestration archive; RTTP ≠ this series |
| Mining layout solver (removed) | git history only | **REMOVED** | No START_HERE table |
| Lab replay wiring | [`documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md`](../Algorithm/asteroid_lab_12_runtime_replay_wiring.md) | CANON | Distinct from optimization search |

**Operational label QUARANTINE:** Maps to lifecycle enum `ARCHIVED` or `SUPERSEDED` plus `do_not_use_as_authority: true` in front matter (see [`document_lifecycle.md`](document_lifecycle.md)).

## Research·Report

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`project_harness_research.md`](../../project_harness_research.md) | `RESEARCH` | harness design | NO | Cursor 하니스·에이전트 운영 설계 보고서 (루트 위치, 2026-05-19) |
| [`documents/research/`](../research/) | `RESEARCH` | research | NO | 조사·근거. 개별 문서만 정본 승격 가능 |
| [`documents/research/research_shapez2_space_transport_throughput_2026-05-18.md`](../research/research_shapez2_space_transport_throughput_2026-05-18.md) | `SUPERSEDED` | game throughput | NO | → [`game_rules/shapez2_asteroid_space_transport_throughput.md`](../game_rules/shapez2_asteroid_space_transport_throughput.md) |
| [`documents/reports/README.md`](../reports/README.md) | `REPORT` | report index | NO | report 묶음 라우팅. 정본 계약 아님 |
| [`documents/debug/`](../debug/) | `REPORT` | debug report | NO | 로그/복사본 분석 |
| [`documents/notes/`](../notes/) | `REPORT` | notes | NO | 장기 메모. 정본 아님 |
| [`documents/Algorithm/README.md`](../Algorithm/README.md) | `RESEARCH` | algorithm memos index | NO | Asteroid Lab optimization 시리즈·초안(`drafts/`). 진입점 README. 구현 정본은 코드·CANON 우선 |

## Archive·완료 문서

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`documents/archive/README.md`](../archive/README.md) | `CANON` | archive index | YES | archive bucket 지도 |
| [`documents/archive/2026-05-completed/README.md`](../archive/2026-05-completed/README.md) | `COMPLETED` | completed index | NO | 2026-05 완료 묶음 |
| [`documents/archive/completed-implementation/README.md`](../archive/completed-implementation/README.md) | `COMPLETED` | completed plan/research pairs | NO | 구현 완료 stem별 pair |
| [`documents/archive/obsolete-src-shapez2-solver-plans-2026-05-01/`](../archive/obsolete-src-shapez2-solver-plans-2026-05-01/) | `ARCHIVED` | obsolete plan set | NO | Django-first 전환 전 계획 |
| [`documents/refactory/README.md`](../refactory/README.md) | `ARCHIVED` | redirect | NO | v1-era 트리 제거됨. 과거 본문은 git 기록 참고 |

## 다음 정리 후보

| 항목 | 현재 상태 | 조치 |
|------|----------|------|
| 루트 `v2_behavior_artifact_*.json` | generated artifact | 실행 산출물 정리 대상으로 별도 판단 |

## 구조 반영

- `django_apps.shapez_asteroid` 및 `tests/unit/shapez_asteroid*`는 제거되었다.
- 채굴 레이아웃 솔버 canonical step 스펙(`documents/Algorithm/mining_solver_cursor_sessions/`) 및 관련 archive/plan 대량 정리는 **git 기록**으로만 남는다.
- `documents/plans/asteroid_lab_optimization/` 트리는 strip-solver 이전 plan 스냅샷. **QUARANTINE** — 구현 정본 아님. RTTP runtime은 `django_apps/asteroid_lab/optimization/` + [`current_plan.md`](../ai/current_plan.md).
