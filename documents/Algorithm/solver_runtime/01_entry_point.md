---
status: ARCHIVED
owner: solver-runtime-pipeline
last_reviewed: 2026-05-22
archived_reason: Solver A→M orchestration removed; HTTP entry returns SOLVER_NOT_AVAILABLE only
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
phase: Entry
related_docs:
  - documents/Algorithm/solver_runtime/README.md
  - django_apps/web/views/public_pages.py
---

# Solver Button Entry Point (stub)

## 현재 동작 (2026-05-22)

`Run Solver` / `Solver` 버튼은 **HTTP 200** + JSON `ok: false`, `error_code: "SOLVER_NOT_AVAILABLE"` 를 반환한다. **500 금지.**

```text
POST /asteroid-miner-layout/p/<slug>/run-solver/
```

- URL name: `web:asteroid-miner-layout-project-run-solver`
- 뷰: `asteroid_miner_layout_project_run_solver` ([`public_pages.py`](../../../django_apps/web/views/public_pages.py))
- 서비스: `run_solver_runtime_for_project` ([`solver_runtime_entry.py`](../../../django_apps/asteroid_lab/services/solver_runtime_entry.py))
- Lab replay frames: 프로젝트에 저장된 reconstruction 타임라인만 (`build_lab_replay_frames_for_project`)

## 제거됨

- `solver_runtime_pipeline` (A→M orchestration)
- `manage.py run_solver`, `scripts/run_solver.ps1`
- `optimization/` 패키지 전체
- Optimization replay persist·12H optimization HUD 입력

## Reconstruction (ACTIVE)

맵 디코드·재구성·persist·Lab replay는 Solver 버튼과 **독립** 경로로 유지한다. [`asteroid_lab_09_replay_timeline.md`](../asteroid_lab_09_replay_timeline.md).

## 금지 (불변)

- replay artifact를 algorithm **입력**으로 사용
- 진입점에서 layout commit·belt/pipe 선설치

## 테스트

- `tests/integration/web/test_asteroid_run_solver.py` — POST → `SOLVER_NOT_AVAILABLE`
- `tests/unit/asteroid_lab/test_solver_runtime_entry.py`

## 역사

Phase A–M 계약: `phase_*.md` (모두 `ARCHIVED`). strip spec: [`docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md`](../../../docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md).
