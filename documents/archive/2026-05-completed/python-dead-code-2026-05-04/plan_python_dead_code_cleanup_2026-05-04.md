# Python dead, duplicate, and legacy code cleanup — execution plan (2026-05-04)

## Delete vs isolate criteria (plan canonical)

| Judgment | Action |
|------|------|
| No references from tests, URLs, or other apps; no domain meaning | **Delete** + regression tests |
| No references but preservation value | **Move** to `django_apps/.../_deprecated/` etc. + one-line docstring |
| Uncertain (reflection, string loading) | **Keep** + defer reason in research |

Layer rules: follow `architecture.mdc` (deprecated stays in same layer).

## First implementation targets (from research)

1. **Ruff I001**: apply sortable sections via `ruff check --fix`.
2. **Ruff E501**: wrap/split imports at four locations to stay within 100 chars.
3. **Module delete / `_deprecated` move**: at research time **no wholly unused modules confirmed** — no separate quarantine. (Vulture not run; additional candidates optional in pass 2 after install.)

## Human approval

- [x] **Approved**: user directed implementation of this plan in Cursor (2026-05-04). Implementation phase allowed.

## Verification (post-implementation)

- `python -m pytest` (full or affected areas)
- `ruff check .` → `mypy .` → `black .` (CI uses `black --check .`)

**Update (follow-up)**: reflected web allauth integration module overrides, `context_processors` types, and test `dict` generics so `mypy .` passes.
