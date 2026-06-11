# Pattern Family and Macro Taxonomy (Solver Catalog)

## Canonical Source

The base catalog (6 `PatternFamily` types + 2 built-in macros and steps) **canonical source is the Django data migration**.

- File: [`django_apps/shapez_solver/migrations/0006_seed_pattern_catalog.py`](../../django_apps/shapez_solver/migrations/0006_seed_pattern_catalog.py)
- `PatternFamily` uses `update_or_create` on `code`; if legacy family `code="abcc-batch"` exists, rename row to `pair-plus-singles` or move macro FK when duplicating `pair-plus-singles`, then delete legacy row.
- `MacroRecipe.code` keeps `abcc-batch` (macro code)·`swap-rotate-swap-checker` unchanged.
- Reverse (`migrate` rollback) is **noop** — catalog rows are not auto-deleted on rollback.

[`django_apps/shapez_solver/fixtures/pattern_catalog_seed.json`](../../django_apps/shapez_solver/fixtures/pattern_catalog_seed.json) is a **reference·demo** copy kept in sync with the migration; not the single source of truth for application behavior.

## Summary

Viewing four quadrants of one layer as **set partition**, maximum distinct equivalence classes is Bell number \(B_4 = 15\). For macro design, grouping rotation·reflection equivalence yields **6 practical axes** stably.

DB `PatternFamily` does not add a new enum; expresses via **`signature` string + `allow_rotation` / `allow_reflection`**.

## Signature String (`PatternFamily.signature`)

Runtime computation: `django_apps.shapez_solver.services.pattern_classifier.pattern_signature`.

- Read tokens in quadrant order (SW → NW → NE → SE, same as layer string); assign `A`, `B`, `C`, … in **first-seen order**.
- So this string is **not** Bell partition canonical name but **left-to-right read labeling**.

Same partition type can yield **different strings** like `AABC` and `ABCC` depending on quadrant placement.

## Catalog Lookup

`PatternCatalogRepository.find_macro_candidates` selects `MacroRecipe` rows where **`family__signature` exactly matches** request signature.

So changing seed representative of 2+1+1 class to `AABC` only causes **macro candidate mismatch regression** when `pattern_signature` still yields `ABCC` for targets.

Current implementation binds:

- `macro_strategy_registry` `ABCC_BATCH` branch assumes `pattern_signature(...) == "ABCC"`.
- Seed step output slots for AB half + CC half geometry also use `ABCC` notation.

**Conclusion**: Keep DB representative string for 2+1+1 class as **`ABCC`**; treat Bell-progression-friendly `AABC` as doc·explanation only. To unify all to `AABC`, change `pattern_signature` normalization and repository lookup·macro branch strings **together**.

## 6 Axes (Practical Families) and Seed `code`

| Meaning | Recommended `code` | Example `signature` |
|------|-------------|------------------|
| All identical | `full-source` | `AAAA` |
| 3+1 | `single-different` | `AAAB` |
| Adjacent 2+2 | `half-split` | `AABB` |
| Checker 2+2 | `checker` | `ABAB` |
| 2+1+1 | `pair-plus-singles` | `ABCC` (representative; `AABC` possible in same class) |
| All distinct | `full-mixed` | `ABCD` |

Above 6 families guaranteed by migration. Families without macro recipes stay active only or get macros later.

## `allow_rotation` / `allow_reflection`

Indicate whether equivalence expansion is allowed in pattern lab·macro stage. Detailed rules follow pattern lab service and solver candidate selection logic.

## Reference

Counting atoms (shape·color, etc.) per quadrant as \(36^4\) form is closer to an **upper bound**; excluding empty quadrants and game-impossible combinations yields fewer valid combinations. Reconcile in separate doc after family classification stabilizes.
