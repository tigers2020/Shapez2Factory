# Import Pipeline — `simulation_systems.json`

**Prerequisites:** `manifest.json` hash gate; stream parse (~38 MB).

## Stages

1. **Load** — streaming JSON parser; verify SHA-256 `37f0cf1a…`.
2. **Validate** — 180 rows; required envelope keys; unique `stable_id`.
3. **Normalize** — parse `simulation_kind_key` from `source_type_name`; classify `parameter_profile`; strip backing fields from extracts.
4. **Register** `source_object_record` per index (optional).
5. **Sample** — seed `20260521`, indices 16, 103, 115 logged.
6. **DTOs** — `SimulationSystemEntryDTO`, optional `BeltSpeedDTO`, `ConnectableAttachmentDTO`, `FactoryStubDTO`.
7. **Validate** — enum families; belt row singleton; do not require converter graphs in domain tables.
8. **Upsert** `simulation_system_entry` on `stable_id`.
9. **Children** — factory stubs, connectable attachments (ordered index), belt policy singleton.
10. **Audit path** — converter/heavy rows → `simulation_runtime_audit` optional JSON blob.
11. **Invariants** — 180 entries; 143 factory profile; 6 connectable profiles; 18 converter audits.
12. **Audit** — file size, profile counts, sample kinds, unresolved building FK count.

## Idempotency

Natural key: `stable_id` per row; belt policy keyed by `import_batch_id`.

## Performance

- Batch inserts; never load entire file into ORM JSONField on domain tables.
- Mark full-file test `@pytest.mark.slow`.

## Unknown fields → `unknown_property` only.
