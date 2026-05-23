# Current plan

**상태 (2026-05-23)**: **RTTP Hybrid C v0.1** (`django_apps/asteroid_lab/optimization/`) + **3B-S** Lab replay compose. **PR-F** island-local 좌표 병합 완료([#49](https://github.com/tigers2020/Shapez2Factory/pull/49)). Reconstruction → RTTP pipeline → persist → Lab interleaved replay.

**Runtime (코드 정본):**

- `ASTEROID_LAB_RTTP_ENABLED=True` (기본) → `solver_runtime_entry`가 `run_rttp_pipeline` + replay sink를 실행한다.
- `ASTEROID_LAB_RTTP_ENABLED=False` → HTTP `Run Solver`는 **200** + `SOLVER_NOT_AVAILABLE` (reconstruction만 안내). 이것이 유일한 stub 경로다.
- “optimization 삭제·항상 stub”은 **아님** — strip-solver로 제거된 것은 **구 monolith/shadow/RD** 이며, RTTP Hybrid C는 별도 패키지로 복구·배선됨.

**Surgery (역사):** [`docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md`](../../docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md) · 실행 기록: [`docs/superpowers/plans/2026-05-22-strip-solver-keep-recon-complete.md`](../../docs/superpowers/plans/2026-05-22-strip-solver-keep-recon-complete.md)

## ACTIVE 코드 경로

```text
django_apps/asteroid_lab/reconstruction/     ← topology, confidence, complete
django_apps/asteroid_lab/optimization/       ← RTTP Hybrid C (skeleton → candidates → regret → commit/LNS)
django_apps/asteroid_lab/contracts/          ← game_data snapshot DTOs
django_apps/asteroid_lab/genetic_sample/     ← admin gene templates (non-runtime)
django_apps/asteroid_lab/services/solver_runtime_entry.py  ← RTTP runtime entry (config-gated)
django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py  ← 3B-S product timeline projection
```

## ARCHIVED (문서·역사)

- strip-solver 이전 monolith optimization / shadow·RD gate — **CANCELLED**
- `solver_runtime/` Phase A–M — [`documents/Algorithm/solver_runtime/README.md`](../Algorithm/solver_runtime/README.md)
- `docs/superpowers/specs/2026-05-22-*commit*`, `*shadow*` — **CANCELLED** (strip spec으로 대체)

## 검증 (narrow)

```bash
python -m pytest tests/unit/asteroid_lab/ -k rttp
python -m pytest tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py tests/integration/web/test_asteroid_run_solver.py
python -m ruff check django_apps/asteroid_lab/optimization django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py django_apps/asteroid_lab/services/solver_runtime_entry.py
```

Full gate: [`AGENTS.md`](../../AGENTS.md) · `scripts/test_full.ps1`

## 다음 초점

- Reconstruction replay·topology 회귀 유지 (narrow gate below)
- Persisted `full_map_server_bbox` → `full_map_island_bbox` read-compat (one release; `island_bbox.py`)
- **DONE (2026-05-23):** RTTP v1 MacroBundleT3 PR-A..H on `master` — macro DTOs, compiler, dedupe, macro regret/commit, `macro_only_mode` pipeline, replay metrics, G9–G16 tests. Plan: [`2026-05-23-rttp-v1-macrobundle-t3.md`](../../docs/superpowers/plans/2026-05-23-rttp-v1-macrobundle-t3.md)
- **DONE (2026-05-23):** PR-I DB `:rttp` macro persist/read — `SolverRun.config_json` keys `macro_only_mode` / `max_macro_candidates` → `RttpPipelineConfig`; unit tests `test_rttp_db_macro_integration.py`
- **NEXT:** enable macro-only in production solver runs via `config_json` when ready; optional integration `run_solver` macro fixture
- RTTP regression fixtures: `test_rttp_narrow_corridor.py` (10A), `test_rttp_reconstruction_fixture_e2e.py` (copy-code lines 0–2)
- ~~`asteroid_lab_10` Sequence 2–7 체크박스~~ → **done (2026-05-23)** [`asteroid_lab_10_development_sequence.md`](../Algorithm/asteroid_lab_10_development_sequence.md) RTTP gate sync 절
