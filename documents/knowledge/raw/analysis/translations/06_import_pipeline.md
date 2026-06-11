# Import Pipeline — `translations.json`

**Prerequisites:** `manifest.json` imported first.

## Stages

1. **Load** — expect `[]`; UTF-8-SIG.
2. **Validate** — root is array; length 0; hash equals SHA-256(`[]`).
3. **Normalize** — N/A.
4. **Register** source artifact metadata (empty file).
5. **Sample** — seed `20260521`; population size 0 → **no row samples**; log manifest evidence.
6. **DTO** — `LocalizationExportStatusDTO(is_empty=True, is_incomplete=True, failure_reason=…)`.
7. **Validate** — `manifest.incomplete_sections` contains `translations`.
8. **Upsert** `localization_export_status` (singleton per batch).
9. **Children** — none.
10. **Resolve FK** — none.
11. **Invariants** — `localized_message` count = 0; status row exists; other importers must not require translation FK for this batch.
12. **Audit** — explicit "translations empty by design" message.

## Idempotency

Status row upsert on `import_batch_id`. Zero message rows.

## Future non-empty dump

Re-run stages 6–11 with row DTOs; upsert `localized_message` on `(message_key, locale_code)`.

## Forbidden

Failing import because count is 0.
