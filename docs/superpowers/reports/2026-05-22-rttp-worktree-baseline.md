# RTTP worktree baseline — fast suite green (post baseline cleanup)

**Branch:** `feature/rttp-hybrid-c` (merged `master` @ `3216a50d` seam baseline)  
**Worktree:** `F:\Python_Projects\shapez2Factory\.worktrees\rttp-hybrid-c`  
**Base:** `37975015` (`fix(asteroid_lab): raw X=0과 양수 X가 admin 미니맵에서 겹치지 않도록 서버 좌표 보정`)  
**Recorded:** 2026-05-22 (initial known-red on branch fork)  
**Updated:** 2026-05-22 (baseline cleanup merged from `master`; RTTP PR-1..6 on branch tip)

## Command

```powershell
powershell -File scripts/test_fast.ps1
```

## Result (after baseline cleanup)

```text
1061 passed (1044 pre-RTTP + 16 RTTP + 1 conftest merge)
0 failed
0 errors
~25s (pytest-xdist 16 workers)
```

**Classification:** baseline cleanup (회귀 수정) — not RTTP feature code.

## What was fixed

### Collection errors (10 → 0)

| Area | Fix |
|------|-----|
| `test_asteroid_lab_replay_timeline_smoke.py` | Restored `_project_slug_via_create` in `test_asteroid_run_solver.py` |
| 9 modules with `SyntaxError` / invalid UTF-8 | Restored Korean literals from `6175607c` or UTF-8-safe rewrite (`test_genetic_sample_admin_seed.py`) |

### Reconstruction fixture contract (6 → 0)

Root cause: explicit raw `X == 0` seam maps still used legacy dense-gap walkable/flood (column `x == 0` skipped).

| Change | Module |
|--------|--------|
| `include_raw_x_zero` on bbox iteration, external flood, components, diagonal close | `grid.py`, `flood_fill.py`, `fill.py`, `perimeter_closing.py`, `pipeline.py` |
| Seam span + bridge gap fills before merge | `fill.py` (`seam_column_span_gap_fill_coords`, `seam_column_bridge_gap_fill_coords`), `pipeline.py` |
| Extension-shell / small-pocket guards for seam column | `pipeline.py` |
| Allow `_replay_synthetic` at `x == 0` when map has explicit raw X=0 | `test_reconstruction_fixture_contract.py` |

## Policy on RTTP branch (`feature/rttp-hybrid-c`)

| Suite | Expectation |
|-------|-------------|
| Full `test_fast.ps1` | **Must** stay green (1061+ on branch with RTTP; 0 failed, 0 errors) |
| RTTP targeted tests (`tests/unit/asteroid_lab/test_rttp_*.py`) | **Must** be green per PR |
| Merge bar | RTTP-G1~G8 green; fast suite failure count must **not increase** vs this report |

Re-run after RTTP PRs:

```powershell
powershell -File scripts/test_fast.ps1 2>&1 | Select-String "passed|failed|error"
```

## Prerequisites verified for RTTP work

| Check | Status |
|-------|--------|
| `django_apps/asteroid_lab/optimization/` present (RTTP rebuild) | yes on `feature/rttp-hybrid-c` |
| `reconstruction/` imports `optimization` | no matches |
| `Coord` / grid types | `django_apps/asteroid_lab/snapshots/grid_contract.py` |
| Solver entry | `solver_runtime_entry.py` returns `SOLVER_NOT_AVAILABLE` (runtime wire optional PR-5 step 8) |
| Reconstruction fixture contract | green after seam topology fix (`3216a50d`) |
| RTTP targeted suite (16 tests) | green on branch tip |

## Historical note

Initial capture on `feature/rttp-hybrid-c` worktree: **947 passed, 6 failed, 10 errors**. Those failures were pre-existing on branch fork, not caused by RTTP implementation. Cleanup landed on `master` as `3216a50d` 2026-05-22; merged into feature branch before RTTP merge gate.
