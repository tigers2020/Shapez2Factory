# Import Pipeline — `simulation_systems.json`

**Prerequisites:** `manifest.json` hash gate; stream parse (~38 MB).

## Stages

1. **Load** — streaming JSON parser; verify SHA-256 `37f0cf1a…`.
2. **Validate** — 180 rows; required envelope keys; unique `stable_id`.
3. **Normalize** — parse CLR → `system_family` / `SimulationType` / `SimulationStateType`; `SimulationProfile` FK from `simulation_parameters` signature; CLR full string → `SimulationClrProvenance` only ([`10_clr_provenance.md`](10_clr_provenance.md)).
4. **Register** `source_object_record` per index (optional).
5. **Sample** — seed `20260521`, indices 16, 103, 115 logged.
6. **Upsert** `simulation_system` on `(import_batch, source_stable_id)`; set non-unique `canonical_id` for grouping.
7. **Children** — connectable graph (signatures → `connectable_key`); typed speeds (`simulation_buffable_speed`, `simulation_multiple_belt_speed`) + `global_belt_speed_policy` sync from `BeltSpeed`; converter → `simulation_runtime_audit` only.
8. **Migrations** — `0005` create → `0006` clear legacy → `0007` validate → `0008` drop `SimulationSystemEntry`.
10. **Audit path** — converter/heavy rows → `simulation_runtime_audit` optional JSON blob.
11. **Invariants** — 180 entries; 143 factory profile; 6 connectable profiles; 18 converter audits.
12. **Audit** — file size, profile counts, sample kinds, unresolved building FK count.

## Idempotency

Natural key: `stable_id` per row; belt policy keyed by `import_batch_id`.

## Performance

- Batch inserts; never load entire file into ORM JSONField on domain tables.
- Mark full-file test `@pytest.mark.slow`.

## Ignored simulation_parameters keys → `unknown_property`

Non-domain top-level keys (`event_delegate`, `reflection_dump`, `runtime_state`, `cache_snapshot`, `ignored_runtime`) are recorded per `SimulationSystem` stable_id with `reason_code` prefix `sim_param_*` and `classification` — preview + hash only (no domain JSONField).

## Other unknown fields → `unknown_property` only.
