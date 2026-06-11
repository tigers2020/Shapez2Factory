# PR-CLI-2b — `GameDataRulesPort` + JSON Snapshot Adapter (L2 decouple)

**Type:** contract change · refactoring
**Depends on:** PR-CLI-2a
**Enables:** PR-CLI-2d
**Branch (suggested):** `feat/asteroid-cli-first-gamedata-port`

---

## Goal

Break the L2 EVTC capacity dependency on `django_apps.game_data` ORM. Introduce a port that the core
satisfies via a frozen `game_data_snapshot.json`, with the Django path producing the same snapshot
(ORM → export → JSON adapter — single semantics). Implements BA-8.

## Behavior contract

- L2 capacity resolution no longer imports `django_apps.game_data` inside core.
- `JsonSnapshotGameDataRulesAdapter` reads snapshot file and returns same capacity values as today.
- Snapshot fail-closed: missing / unsupported `schema_version` / hash mismatch → typed failure.
- A new `manage.py export_game_data_snapshot --out <path>` produces the snapshot from ORM.

## Non-goals

- No stack_runner move (2d).
- No CLI (3).
- No removal of ORM models — only removal of in-layer ORM coupling.

---

## Current coupling

[`layer_02_exterior_transport/capacity.py`](../../../../django_apps/asteroid_lab/layers/layer_02_exterior_transport/capacity.py)
imports `django_apps.game_data.services.exterior_transport_capacity`. Layer capacity tests use `@pytest.mark.django_db`
([`test_layer_02_capacity.py`](../../../../tests/unit/asteroid_lab/layers/test_layer_02_capacity.py)).

## File map

| Action | Path | Why |
|--------|------|-----|
| Define | `src/shapez2_factory/application/asteroid_lab/ports/game_data_rules.py` | `GameDataRulesPort` (from CLI-1) finalized |
| Create | `src/shapez2_factory/adapters/asteroid_lab/json_snapshot_rules.py` | `JsonSnapshotGameDataRulesAdapter` + fail-closed |
| Create | `src/shapez2_factory/domain/asteroid_lab/exterior_capacity_row.py` | `ExteriorCapacityRow` DTO |
| Modify | `layer_02_exterior_transport/capacity.py` | accept injected `GameDataRulesPort` instead of direct ORM import |
| Create | `django_apps/game_data/management/commands/export_game_data_snapshot.py` | ORM → JSON snapshot |
| Create | `django_apps/asteroid_lab/adapters/orm_game_data_rules.py` | ORM → export → JSON adapter (transitional, lives in Django side) |
| Create | `tests/fixtures/asteroid_lab/game_data_snapshot_min.json` | deterministic fixture |
| Create | `tests/unit/shapez2_factory/test_layer_02_capacity_snapshot.py` | no-django capacity test |
| Modify | `tests/unit/asteroid_lab/layers/test_layer_02_capacity.py` | keep ORM-path test (export → adapter parity) |

---

## Snapshot schema (BA-8)

```json
{
  "schema_version": "game_data_snapshot_v1",
  "game_data_dump_hash": "sha256:...",
  "generated_at_utc": "2026-05-30T00:00:00Z",
  "game_version": "...",
  "provenance": { "...": "..." },
  "exterior_transport_capacity": [
    { "speed_tier": 1, "per_connector_capacity_per_min": "..." }
  ]
}
```

Fail-closed rules:

```text
missing file                         → GAME_DATA_SNAPSHOT_INVALID (missing)
schema_version not in {supported}    → GAME_DATA_SNAPSHOT_INVALID (unsupported)
expected_hash given && != dump_hash  → GAME_DATA_SNAPSHOT_INVALID (hash_mismatch)
```

---

## Tasks

- [x] **Step 1 (SDD):** `test_layer_02_capacity_snapshot.py` — feeds fixture JSON to `JsonSnapshotGameDataRulesAdapter`; asserts shape/fluid capacity from the snapshot and via `resolve_per_connector_capacity`.
- [x] **Step 2:** Implemented `JsonSnapshotGameDataRulesAdapter` + domain `ExteriorCapacityRow`; `capacity.py` now takes an injected `GameDataRulesPort`; `plan.py` lazily defaults to the ORM adapter.
- [x] **Step 3:** Implemented `export_game_data_snapshot` command; `orm_game_data_rules.py` builds the payload from the ORM resolver and delegates to the JSON adapter (single path).
- [x] **Step 4:** Parity tests in `test_layer_02_capacity.py`: ORM export → adapter == direct EVTC service (shape tier-1 = 5760, fluid tier-1 = 345600 confirmed via real export).
- [x] **Step 5:** Fail-closed unit tests (missing file / unsupported schema / hash mismatch / malformed) + hash-match accept.
- [x] **Step 6:** ruff clean on changed paths; `mypy src` clean (28 files); full `mypy django_apps config src` adds 0 new errors (1025 baseline); core-purity gate green. FIX-1: missing-row test rewritten to inject a `LookupError`-raising port (no DB).

## Tests / verification

```powershell
python -m pytest tests/unit/shapez2_factory/test_layer_02_capacity_snapshot.py -v
python -m pytest tests/unit/asteroid_lab/layers/test_layer_02_capacity.py tests/unit/asteroid_lab/layers/test_layer_02_evtc_no_literals.py -v
python -m ruff check src/shapez2_factory/adapters/asteroid_lab django_apps/asteroid_lab/layers/layer_02_exterior_transport
python -m mypy django_apps config src
```

## Risks

- `invariant:` EVTC caps must come from resolver, never literals ([`test_layer_02_evtc_no_literals.py`](../../../../tests/unit/asteroid_lab/layers/test_layer_02_evtc_no_literals.py)) — snapshot carries resolver output, not new literals.
- `assumption:` snapshot fixture stays in sync with game_data dump; CI parity test guards drift.
- Decimal precision: serialize capacity as string to preserve `Decimal`.

## Done criteria

- `capacity.py` core-pure; both no-db and ORM-parity tests green; export command works; fail-closed covered.
