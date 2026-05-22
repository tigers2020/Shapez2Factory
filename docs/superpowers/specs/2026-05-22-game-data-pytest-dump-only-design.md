# game_data pytest — Tier B dump-only fixture

**Status:** Approved 2026-05-22 (Test Architecture Reviewer + user A)  
**Plan:** [`2026-05-22-game-data-pytest-dump-only.md`](../plans/2026-05-22-game-data-pytest-dump-only.md)

## Decision

Unit pytest for `game_data` uses a **Tier B pinned ORM fixture** loaded by `loaddata` from `game_data_backup/game_data_dump.json`.

Full `import_game_data` / `--verify` / dump regeneration is **no longer** a unit pytest responsibility.

**Tier A** (JSON interchange under `documents/game_data/`) is owned by **manual CI / release runbook gate** — required before regenerating `game_data_backup/game_data_dump.json`. Not part of `test_fast`.

## Non-goals

- Do not validate full `GameDataImporter` idempotency inside `test_fast`.
- Do not read source JSON manifests as test oracles in Tier B tests.
- Do not create session-scoped full `game_data` DB load.
- Do not call global Django `flush` in fixtures (app-local delete only).

## A vs B (unchanged domain model)

| Tier | Path | Role in pytest |
| ---- | ---- | -------------- |
| **A** | `documents/game_data/` (external / CI gate only) | Regenerate Tier B; not pytest oracle |
| **B** | `game_data_backup/game_data_dump.json` | **Only** full-bundle pytest seed |

Slice importer unit tests may keep **`tests/fixtures/game_data/*.json`** (e.g. `simulation_systems_min.json`). That is **not** the removed full-source `game_data_dir` fixture.

## Pinned dump contract

All constants in `tests/unit/game_data/_dump_expectations.py` are tied to:

```text
PINNED_MANIFEST_HASH = sha256:a7f71325bb779ff6c2a1665ff6c9fa3067943cc6335a7926567d2ee76be8dd09
```

Regenerating the dump **must** update `_dump_expectations.py` and this spec’s hash line in the same PR.

### ORM row counts (manifest `a7f71325…`)

| Constant | Value |
| -------- | ----- |
| `TOOLBAR_TREE_NODE_COUNT` | 204 |
| `TOOLBAR_ELEMENT_COUNT` | 142 |
| `TOOLBAR_ACTION_KIND_NODE_COUNT` | 142 |
| `SHAPE_RECIPE_COUNT` | 1170 |
| `ITEMS_SOURCE_APPEARANCE_COUNT` | 70 |
| `FULL_SOURCE_APPEARANCE_COUNT` | 1170 |
| `SIMULATION_SYSTEM_COUNT` | 180 |

## Fixture requirements (mandatory)

### 1. Dump missing — CI must fail, local may skip

```python
def _require_game_data_dump(path: Path) -> None:
    if path.is_file():
        return
    if os.environ.get("CI") or os.environ.get("REQUIRE_GAME_DATA_DUMP") == "1":
        pytest.fail(f"Missing pinned game_data dump: {path}")
    pytest.skip(f"Missing pinned game_data dump: {path}")
```

- GitHub Actions sets `CI=true` → `test-fast` / `test-slow` fail if dump absent.
- Optional local strict mode: `$env:REQUIRE_GAME_DATA_DUMP = "1"`.

### 2. Pinned batch assert after `loaddata`

```python
batch = ImportBatch.objects.get(pk=1)
assert batch.batch_name == "default"
assert batch.manifest_self_hash == PINNED_MANIFEST_HASH
```

### 3. App-local flush only

Use existing `_flush_committed_game_data(django_db_blocker)`:

- Deletes all `game_data` app model tables via cursor (FK off on SQLite).
- **Do not** call `call_command("flush")`.

Module teardown runs the same flush after yield.

### 4. Module scope + `django_db_blocker`

```python
@pytest.fixture(scope="module")
def imported_game_data_batch_module(
    django_db_setup: None,
    django_db_blocker,
) -> Iterator[ImportBatch]:
    dump_path = _GAME_DATA_DUMP
    _require_game_data_dump(dump_path)
    with django_db_blocker.unblock():
        _flush_committed_game_data(django_db_blocker)
        call_command("loaddata", str(dump_path), verbosity=0)
        batch = ImportBatch.objects.get(pk=1)
        assert batch.batch_name == "default"
        assert batch.manifest_self_hash == PINNED_MANIFEST_HASH
    yield batch
    _flush_committed_game_data(django_db_blocker)
```

Function-scoped alias (no second load):

```python
@pytest.fixture
def imported_game_data_batch(
    imported_game_data_batch_module: ImportBatch,
    db: None,
) -> ImportBatch:
    return imported_game_data_batch_module
```

### 5. Remove full-source `game_data_dir` only

- Delete session/module `game_data_dir` → `documents/game_data`.
- Keep `tests/fixtures/game_data/` paths for importer slice tests (`min_sim_rows`, etc.).

## pytest deletions (Tier A / full bundle)

| Remove | Reason |
| ------ | ------ |
| `tests/unit/game_data/test_import_idempotency.py` | Full manifest re-import |
| `tests/unit/game_data/test_import_game_data_verify.py` | `--verify` + disk manifest |
| `test_full_simulation_systems_import_180_rows` | Full bundle import |
| `test_full_dump_speed_key_counts` | Raw `simulation_systems.json` scan |
| `test_canonical_id_stable_across_reimport_full_toolbar_tree` | Full re-import |
| `test_canonical_id_fast_stability_stratified_toolbar_sample` (re-import half) | In-test `GameDataImporter` |

## pytest rewrites (JSON oracle → ORM + `_dump_expectations`)

| Module | Change |
| ------ | ------ |
| `test_toolbar_closure.py` | Assert `ToolbarTreeNode` count / edges / acyclicity vs pinned counts; no `load_json` |
| `test_toolbar_tree.py` | Count tests use expectations; drop `_source_rows` / JSON imports |
| `test_shape_recipe_provenance.py` | Drop `items_rows` / `game_data_dir`; overlap via ORM; drop pure-JSON subset test |
| `test_shape_recipe_provenance.py::test_items_layer_slot_parity_*` | ORM-only layer/slot parity per `items` appearance (no JSON snapshot) |

## Tier A owner — manual CI / release gate

New runbook: [`docs/runbooks/game_data_tier_a_release_gate.md`](../../runbooks/game_data_tier_a_release_gate.md)

Required **before** committing an updated `game_data_backup/game_data_dump.json`:

1. `python manage.py import_game_data --source <tier-a-path> --verify`
2. `python manage.py seed_game_data_taxonomy`
3. `python manage.py dumpdata game_data --indent 2 -o game_data_backup/game_data_dump.json`
4. Refresh `_dump_expectations.py` + `PINNED_MANIFEST_HASH`
5. `python -m pytest tests/unit/game_data/ --durations=20`

Not run in `test_fast` / default PR matrix unit slice.

## Invariant ownership (pytest-slim)

| Invariant | Owner after this change |
| --------- | ------------------------ |
| Full manifest import idempotent | **manual CI / release gate** (not pytest) |
| `import_game_data --verify` | **manual CI / release gate** |
| simulation slice re-import | `test_simulation_systems_import.py` (min fixture) |
| simulation speed re-import | `test_simulation_speed_import.py` (slice rows) |
| Toolbar / shape / cross-ref ORM contracts | Tier B tests + `_dump_expectations` |
| `manifest_self_hash` in asteroid snapshot | `imported_game_data_batch*` → pinned dump |

Update [`2026-05-23-pytest-slim-optimization-design.md`](2026-05-23-pytest-slim-optimization-design.md) ownership table when implementing.

## Documentation updates

- [`docs/domain/game_data_coverage.md`](../../domain/game_data_coverage.md) — pytest uses Tier B only
- [`documents/ai/manuals/testing.md`](../../../documents/ai/manuals/testing.md) — dump fixture, `REQUIRE_GAME_DATA_DUMP`, no `-q`
- [`docs/runbooks/game_data_snapshot_deploy.md`](../../runbooks/game_data_snapshot_deploy.md) — point Tier A gate to new runbook for dump refresh

## Verification

```powershell
python -m pytest tests/unit/game_data/ --durations=20
powershell -File scripts/test_fast.ps1
python -m ruff check tests/unit/game_data/
```

## Risks

| Risk | Mitigation |
| ---- | ---------- |
| Dump regen without updating expectations | Pinned hash assert fails immediately |
| `reuse-db` + stale PKs | App-local flush before each module `loaddata` |
| Weaker items layer/slot test without JSON | Still asserts ORM internal parity per appearance row |
