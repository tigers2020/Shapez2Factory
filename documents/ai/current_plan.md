# Current plan

**상태 (2026-05-19)**: Solver 버튼 v0 E2E 파이프라인 완료 (PR1–PR9 + 9A–9E). 768 tests green.

## 완료된 것

| PR | Phase | 내용 |
|----|-------|------|
| PR1 | D | GeneTemplate, projection |
| PR1B | A, B | Reconstruction → OptimizationInput, §0.3 adapter |
| PR2.5 | C | Capacity planner, RouteGoal planner |
| PR2 | E, F, G | Geometry validation, route probe |
| PR3 | H | Candidate pool (dedupe, truncate) |
| PR4 | I | Candidate selection v0 (greedy) |
| PR5 | J | Incremental commit, reservation overlay |
| PR6 | K | Route network materialization |
| PR7 | L, M, Entry | Final validation, persist, orchestration (A→M) |
| PR8 | Entry | HTTP POST run-solver, optimization replay page context |
| PR9 | M UI | Lab JS Run Solver, optimization replay HUD (12H) |
| 9A–9E | — | 통합 replay DTO·adapter·timeline·UI 계약 |

## 패키지 정본

```text
django_apps/asteroid_lab/optimization/   ← 모든 Runtime 모듈
django_apps/shapez_asteroid/             ← 제거됨 (import 금지)
```

## 다음 초점 (v1 후보 — 사람 승인 후 착수)

Open Decisions 잔여 항목 ([`open_decisions.md`](../Algorithm/solver_runtime/open_decisions.md)):

- **OD-3**: capacity enforcement v1 — hard edge capacity + reroute / trunk split
- **OD-4**: GA selector v1 — Evolution Search (route/probe/commit 안정화 후)

## 불변식·금지

- `reconstruction` barrier: `barrier_xy = wall_coords ∪ infer_shell_barrier_coords(...)` — `passes_two_axis_evidence_guard`는 원본 `wall_coords`만 사용.
- replay artifact를 solver 입력으로 주입 금지.
- 제거된 `shapez_asteroid` 패키지 전제 코드 작성 금지.
