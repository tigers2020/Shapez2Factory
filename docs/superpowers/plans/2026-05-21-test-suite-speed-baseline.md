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
