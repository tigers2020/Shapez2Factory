# Current plan

**상태 (2026-05-19)**: Solver 버튼 v0 E2E 파이프라인 완료 (PR1–PR9 + 9A–9E). 통합 runtime replay recorder·timeline 연동 완료. **813** tests green (full gate).

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
| Replay+ | — | `SolverRuntimeReplayRecorder` → persist → lab timeline |
| OD-3 v1 | I | Hard trunk capacity + alternate-trunk (selector) |

## 패키지 정본

```text
django_apps/asteroid_lab/optimization/   ← 모든 Runtime 모듈
django_apps/shapez_asteroid/             ← 제거됨 (import 금지)
```

## 문서 권위 (충돌 해소)

| 문서 | 역할 |
|------|------|
| **본 파일** + 코드 + pytest | Solver runtime **구현 완료** 판단의 정본 |
| [`asteroid_lab_11_future_execution_plan_post_sequence.md`](../Algorithm/asteroid_lab_11_future_execution_plan_post_sequence.md) | 2026-05-18 **계획·스펙** 베이스라인; 체크리스트는 미착수로 재설정된 **로드맵**이며 v0 완료와 대조하지 않음 |
| [`asteroid_lab_10_development_sequence.md`](../Algorithm/asteroid_lab_10_development_sequence.md) | 시퀀스 인덱스; 완료 여부는 본 파일·테스트로 갱신 |

## 승인된 다음 초점 (2026-05-19)

1. **OD-3 v1** — selector hard trunk capacity (완료) → commit 단계 reroute는 v1.1
2. **Phase 2 golden** — `tests/golden/` + `harness/validators/` (진행)
3. **OD-4** — GA selector v1 (OD-3·replay 안정 후; 미착수)

## 다음 초점 (미착수)

- **OD-4**: GA selector v1 — Evolution Search ([`open_decisions.md`](../Algorithm/solver_runtime/open_decisions.md))
- **Phase 3**: `src/shapez2_factory/` hexagonal 추출 (한 모듈부터)

## 불변식·금지

- `reconstruction` barrier: `barrier_xy = wall_coords ∪ infer_shell_barrier_coords(...)` — `passes_two_axis_evidence_guard`는 원본 `wall_coords`만 사용.
- replay artifact를 solver 입력으로 주입 금지.
- 제거된 `shapez_asteroid` 패키지 전제 코드 작성 금지.
