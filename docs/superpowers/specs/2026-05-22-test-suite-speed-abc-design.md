# Test Suite Speed (A+B+C) — Design Spec

> **pytest output:** [`AGENTS.md`](../../../AGENTS.md) · [`documents/ai/manuals/testing.md`](../../../documents/ai/manuals/testing.md) — `-q` / `--quiet` / `--tb=no` **forbidden**.

**Status:** Approved 2026-05-22  
**Supersedes:** Extends [`2026-05-21-test-suite-speed`](../plans/2026-05-21-test-suite-speed.md) (Phase 1 largely done)

## Problem

Developers need three speed wins:

| ID | Pain | Success criteria |
|----|------|------------------|
| **A** | Unclear which pytest command to run locally | One-command daily loop; PR command documented |
| **B** | Fast slice still ~100s (864 tests) | Target **≤70s** on Win dev with `-n auto` (measure after changes) |
| **C** | PR/CI full `pytest` wall time high | CI test stage wall ≈ **max(shard)** via parallel matrix jobs |

## Already landed (do not redo)

- `pytest-xdist`, `--reuse-db`, `slow` marker in `pytest.ini`
- Auto `slow` tagging in `tests/conftest.py` (864 fast / 117 slow)
- Module-scoped `exhaustive_genes_*` in `tests/unit/asteroid_lab/conftest.py`
- CI: `pytest -n auto --dist loadscope` (single test job)

## Approach (approved)

**Workflow + structure + CI sharding** — not aggressive session DB or mass test deletion.

### A — Local workflow

- `scripts/test_fast.ps1` — `unit and not slow`, parallel
- `scripts/test_slow.ps1` — `-m slow`, parallel
- `scripts/test_full.ps1` — full suite, parallel
- `documents/ai/manuals/testing.md` — “local default = test_fast”
- Optional: `AGENTS.md` one-line pointer

### B — Fast slice reduction

1. **Module-scoped** `game_data` import for files that only read imported state (`test_toolbar_tree.py`, `test_source_object_coverage.py`, etc.). Keep **function-scoped** `imported_game_data_batch` for tests that mutate DB or need empty precondition.
2. **Phase 2** from 2026-05-21 plan: remove provably duplicate tests (exhaustive roundtrips, blueprint golden dup, redundant re-import).
3. Replace remaining inline `generate_exhaustive_sample_genes` with existing module fixtures where parameters match.
4. Run `--durations=20` on slow slice; extend `_SLOW_MODULE_SUFFIXES` if needed.

**Forbidden:** Session-scoped import (leaked into empty-DB tests per baseline). No deleting tests without invariant ownership table.

### C — CI

Replace single `test` matrix cell with **three parallel pytest jobs**:

- `test-fast`: `-m "unit and not slow" -n auto --dist loadscope`
- `test-slow`: `-m slow -n auto --dist loadscope`
- `test-integration`: `-m integration -n auto --dist loadscope`

Lint/typecheck/format unchanged. All three must pass for green CI.

## Verification

| Gate | Command |
|------|---------|
| Daily | `scripts/test_fast.ps1` |
| PR local | `scripts/test_full.ps1` + ruff/black/mypy per AGENTS.md |
| CI | three pytest shards + lint/typecheck/format |

Record before/after in [`2026-05-21-test-suite-speed-baseline.md`](../plans/2026-05-21-test-suite-speed-baseline.md).

## Out of scope

- `pytest.ini` default `-n auto` (surprising on small machines)
- Vitest / frontend test parallelization
- Replacing Django tests with mocks for speed
