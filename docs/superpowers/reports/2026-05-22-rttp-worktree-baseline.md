# RTTP worktree baseline — known pre-existing red

**Branch:** `feature/rttp-hybrid-c`  
**Worktree:** `F:\Python_Projects\shapez2Factory\.worktrees\rttp-hybrid-c`  
**Base:** `master` @ `37975015` (`fix(asteroid_lab): raw X=0과 양수 X가 admin 미니맵에서 겹치지 않도록 서버 좌표 보정`)  
**Recorded:** 2026-05-22  
**RTTP source edits at capture:** none (docs-only branch start)

## Command

```powershell
powershell -File scripts/test_fast.ps1
```

## Result

```text
947 passed
6 failed
10 errors
~29s (pytest-xdist 16 workers)
```

**Classification:** pre-existing baseline on branch tip; **not** caused by RTTP implementation.

## Policy on this branch

| Suite | Expectation |
|-------|-------------|
| Full `test_fast.ps1` | Recorded as known-red; do **not** claim global green until baseline cleanup lands (separate effort) |
| RTTP targeted tests (`tests/unit/asteroid_lab/test_rttp_*.py`) | **Must** be green per PR |
| Merge bar | RTTP-G1~G8 green; fast suite failure count must **not increase** vs this report |

## Failures (6)

All in `tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py`:

| Test | Notes |
|------|-------|
| `test_reconstruction_fixture_line_topology_matches_solved[0]` | mineable/topology diff vs fixture line 0 |
| `test_reconstruction_fixture_line_topology_matches_solved[1]` | mineable/topology diff vs fixture line 1 |
| `test_reconstruction_fixture_line_export_topology_equivalent[0]` | export roundtrip topology drift |
| `test_reconstruction_fixture_line_export_topology_equivalent[1]` | export roundtrip topology drift |
| `test_reconstruction_fixture_line_coord_and_optimization_contract[1]` | `(17,20)` extra vs `(16,*)` missing on line 1 |
| `test_reconstruction_canon_line_confident_and_topology_match` | canon line 1 topology |

Representative diff (line 1): extra mineable `(17, 20)`; missing cells around `(16, 4)`–`(16, 20)`.

## Collection errors (10)

| Module | Error kind |
|--------|------------|
| `tests/integration/web/test_asteroid_lab_replay_timeline_smoke.py` | `ImportError`: `_project_slug_via_create` missing from `test_asteroid_run_solver` |
| `tests/integration/web/test_web_smoke.py` | `SyntaxError`: non-UTF-8 on line 225 (encoding) |
| `tests/unit/asteroid_lab/test_equipment_bundles.py` | collection / parse error |
| `tests/unit/asteroid_lab/test_genetic_sample_admin_seed.py` | collection / parse error |
| `tests/unit/asteroid_lab/test_models.py` | collection / parse error |
| `tests/unit/shapez_core/test_admin_identifier_sprite.py` | collection / parse error |
| `tests/unit/shapez_solver/test_macro_recipe_graph_visual.py` | collection / parse error |
| `tests/unit/shapez_solver/test_recipe_graph_react_flow_adapter.py` | collection / parse error |
| `tests/unit/shapez_solver/test_recipe_graph_recompute.py` | collection / parse error |
| `tests/unit/web/test_shape_part_sprite.py` | collection / parse error |

Re-run after RTTP PRs to diff counts:

```powershell
powershell -File scripts/test_fast.ps1 2>&1 | Select-String "passed|failed|error"
```

## Prerequisites verified for RTTP work

| Check | Status on `37975015` |
|-------|----------------------|
| `django_apps/asteroid_lab/optimization/` removed | yes (strip-solver executed) |
| `reconstruction/` imports `optimization` | no matches |
| `Coord` / grid types | `django_apps/asteroid_lab/snapshots/grid_contract.py` |
| Solver entry | `solver_runtime_entry.py` returns `SOLVER_NOT_AVAILABLE` |
