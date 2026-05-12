# Pattern template registry plan (2026-05-03)

## Summary

Refactor prebuilt pattern handling so repeated patterns are matched by pattern definitions and
expanded through template definitions. The result remains the existing expanded recipe graph.

## Changes

- Add `PatternTemplateDefinition` with `template_id`, input/output port names, and an internal
  builder callable.
- Change `PrebuiltPatternDefinition` to reference templates by `template_id`.
- Return matched template metadata from `match_prebuilt_pattern`.
- Replace the explicit `if template == ...` expansion branch with a template registry lookup.
- Keep `half_and_half` and `checker` behavior identical to the current recipe expansion.

## Tests

- Verify `half_and_half` and `checker` resolve to the expected template ids.
- Verify template expansion keeps the existing operation sequence for both patterns.
- Keep fallback coverage for unregistered patterns.

## Acceptance

- `pytest`
- `ruff check .`
- `mypy .`
- `black --check .`

No migration is required.
