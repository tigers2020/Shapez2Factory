# Current plan

**상태 (2026-05-23)**: Asteroid Lab **solver/optimization 파이프라인 제거** 완료. **PR-F** island-local 좌표 병합 완료([#49](https://github.com/tigers2020/Shapez2Factory/pull/49)). Reconstruction → persist → Lab replay만 유지. HTTP `Run Solver` → `SOLVER_NOT_AVAILABLE` (200, never 500).

**Surgery:** [`docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md`](../../docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md) · 실행 기록: [`docs/superpowers/plans/2026-05-22-strip-solver-keep-recon-complete.md`](../../docs/superpowers/plans/2026-05-22-strip-solver-keep-recon-complete.md)

## ACTIVE 코드 경로

```text
django_apps/asteroid_lab/reconstruction/     ← topology, confidence, complete
django_apps/asteroid_lab/contracts/          ← game_data snapshot DTOs
django_apps/asteroid_lab/genetic_sample/     ← admin gene templates (non-runtime)
django_apps/asteroid_lab/services/solver_runtime_entry.py  ← stub only
```

## ARCHIVED (문서·역사)

- `django_apps/asteroid_lab/optimization/` — **삭제됨**
- `solver_runtime/` Phase A–M — [`documents/Algorithm/solver_runtime/README.md`](../Algorithm/solver_runtime/README.md)
- `docs/superpowers/specs/2026-05-22-*commit*`, `*shadow*` — **CANCELLED** (strip spec으로 대체)

## 검증 (narrow)

```bash
python -m pytest tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py tests/integration/web/test_asteroid_run_solver.py
python -m ruff check django_apps/asteroid_lab/reconstruction django_apps/asteroid_lab/contracts django_apps/asteroid_lab/genetic_sample django_apps/asteroid_lab/services/solver_runtime_entry.py
```

Full gate: [`AGENTS.md`](../../AGENTS.md) · `scripts/test_full.ps1`

## 다음 초점

- Reconstruction replay·topology 회귀 유지 (narrow gate below)
- Persisted `full_map_server_bbox` → `full_map_island_bbox` read-compat (one release; `island_bbox.py`)
- RTTP **3B-S-3** canonical `rttp.*` types — merged on `master` (2026-05-23)
- Solver 재구현 시 **새 spec** 필수 (strip spec이 취소한 shadow/commit/RD gate 설계 구현 금지)
