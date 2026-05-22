# Test suite speed baseline (2026-05-21)

Pre-change collection: **1053 tests collected** (unit 977 / integration 75).

Full `--durations=40` run deferred (aborted on dev machine after >5 min). Hot spots from static analysis:

- `generate_exhaustive_sample_genes(max_extensions=3)` — 40+ call sites
- `test_toolbar_tree.py` — 9× `GameDataImporter.run()` per file
- `test_sample_gene_exhaustive.py` — 24 tests, combinatorial generator

Post-change: **1049 tests collected** (−4 duplicate removals).

Implementation notes:
- `imported_game_data_batch` is **function-scoped** with `db` (transaction-isolated). Session scope was dropped: it leaked rows into tests expecting an empty DB.
- `test_toolbar_tree.py` uses the shared function fixture (one import per test; still faster than duplicate inline imports before conftest).
- `pytest-xdist` + `slow` marker + module exhaustive-gene fixtures landed.

2026-05-22 follow-up (auto `slow` in `tests/conftest.py`):
- Collect: **864** `unit and not slow`, **117** `slow` (of 1057 total).
- Wall time (Win dev, parallel): `pytest -m "unit and not slow" -n auto --dist loadscope -q` ≈ **100s** (863 passed, 1 skipped).

PR2-before (2026-05-22): `test_fast.ps1` ≈ **100s** (baseline for module import + dedup work).

PR2 notes:
- Tasks 9–10 duplicate removals already absent in tree (skip).
- Task 11: kept domain-specific re-import tests (`test_reimport_speed_rows_idempotent`, `test_reimport_does_not_inflate_occurrence_count`, etc.).
- Module `imported_game_data_batch_module` migrated: toolbar_tree, source_object_coverage, cross_references, lazy_localized_text, toolbar_identity, snapshot_*.
- Collect after PR2: **854** fast / **127** slow (was 864 / 117).
- PR2-after wall: `unit and not slow` parallel **≈93s** (853 passed, 1 skipped; was ≈100s).

shapez2solver env (2026-05-22, user verified):
- `test_fast.ps1`: **853 passed**, 1 skipped, **108.4s**
- `test_slow.ps1`: **127 passed**, **56.8s**
- `test_full.ps1`: **1056 passed**, 1 skipped, **137.8s**
- CI shard wall ≈ max(108, 57) ≈ **109s** (not 108+57; full parallel suite ~138s)
- Migrated inline exhaustive fixtures: gene_template_loader, genetic_sample_gene_export, solver_runtime_entry, solver_runtime_replay_recorder (one test).

PR3 (2026-05-22): CI matrix `test-fast` | `test-slow` | `test-integration`; `mypy django_apps config src` on typecheck job.

## Phase D pre-D1 (2026-05-23)

- collect: `python -m pytest -m "unit and not slow" --collect-only -q` → **858** collected (205 deselected)
- wall: `test_fast.ps1` **88.6s** (pytest reports 84.2s)
- passed/skipped: **857** passed, **1** skipped

## Phase D post-D1 (2026-05-23)

- collect: **858** fast (unchanged; D1 audit only, no test deletions)
- ownership table + Removed in D1 audit: complete in spec

## Phase D post-D2 (2026-05-23)

- Changes: parametrized `test_source_object_coverage`, exhaustive module fixtures, `tests/integration/conftest.py`
- wall: `test_fast.ps1` **100.6s** (pytest 96.15s; pre-D1 was 88.6s — variance / env)
- passed/skipped: **857** passed, **1** skipped

## Phase D D3 — duration evidence (fast slice)

Measured: `pytest -m "unit and not slow" -n auto --dist loadscope --durations=25` (2026-05-23).

| Rank | Duration (s) | Test node id |
|------|--------------|--------------|
| 1 | 81.70 | `tests/unit/game_data/test_toolbar_tree.py::test_canonical_id_stable_across_reimport` |
| 2 | 80.92 | `tests/unit/game_data/test_import_idempotency.py::test_import_is_idempotent` |
| 3 | 10.43 | `tests/unit/game_data/test_admin_browse.py::test_game_data_browse_groups_sections_by_namespace` (setup) |
| 4 | 10.14 | `tests/unit/asteroid_lab/test_cell_snapshot_service.py::test_build_decoded_blueprint_snapshot_from_input_reads_decoded_json` (setup) |

Wall for this run (before slow tags): **99.78s** (857 passed, 1 skipped).

## Phase D3 — slow-tag candidates (do not delete tests)

Target ≤70s not met after D2 (**100.6s**). Applied `@pytest.mark.slow` on top call-duration tests.

| Candidate | Type | Rationale (from durations) | Applied? |
|-----------|------|----------------------------|----------|
| `test_canonical_id_stable_across_reimport` | test mark | 81.7s call, double full import | yes |
| `test_import_is_idempotent` | test mark | 80.9s call, full manifest import ×2 | yes |
| `test_admin_browse.py` setup cluster | module suffix | ~10s setup (many tests share DB) | no — setup only |
| `imported_game_data_batch_module` | fixture | already auto-slow | already |

### Phase D3 post-tag fast slice (2026-05-23)

- collect: **855** fast (208 deselected; −3 vs pre-D1)
- wall: `test_fast.ps1` **27.5s** (pytest 22.9s) — **≤70s target met**
- passed/skipped: **854** passed, **1** skipped
- Phase D3: fast target met. No further slow-tag changes required in this pass.

## Phase D scope note (2026-05-23)

Game-data snapshot tests (`test_asteroid_game_data_snapshot`, `test_solver_with_game_data_snapshot`) were removed from `phase-d-pytest-slim`; they belong on `feature/asteroid-lab-game-data-integration`, not the pytest-slim branch.

## Phase E — stratified toolbar canonical_id (2026-05-23)

- `tests/unit/game_data/_stratified.py`: head/mid/tail + `TOOLBAR_CANONICAL_ID_ANCHOR_PATHS`
- Fast contract: `test_canonical_id_fast_stability_stratified_toolbar_sample` (module fixture + 1× re-import)
- Slow contract: `test_canonical_id_stable_across_reimport_full_toolbar_tree` (renamed from prior slow test)
- Uses `imported_game_data_batch_module` → auto-`slow`; not in `test_fast` slice by design
