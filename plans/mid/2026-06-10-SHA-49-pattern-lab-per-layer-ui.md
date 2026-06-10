---
linear_issue: SHA-49
title: Pattern Lab rejects multi-layer shape codes that recipe family validation accepts
priority: Mid
labels:
  - bug
  - ui
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Pattern Lab per-layer UI rendering

## Source Issue

- Linear: SHA-49
- Status at planning time: In Progress
- Priority: Mid

## Problem

Even after service-layer multi-layer support, `pattern_lab.html` renders a single signature/symbol-map/rotation block. Multi-layer targets need per-layer canonical code, structural signature, rotation variants, and symbol map sections consistent with recipe graph's four-layer contract.

## Scope

Update Pattern Lab template and view context wiring to render per-layer analysis blocks for multi-layer codes. Single-layer layout stays visually equivalent to today.

## Non-goals

- Recipe graph editor changes
- New JS client; server-rendered template only
- Changing `public_pages.pattern_lab` URL or auth

## Implementation Plan

1. Read `django_apps/web/views/public_pages.py` `pattern_lab` view — confirm it passes `analysis` from `analyze_pattern_lab_shape` unchanged.
2. After High plan lands, extend template `django_apps/web/templates/web/pattern_lab.html`:
   - When `analysis.layers` is non-empty (or layer count > 1), render a stacked section per layer with heading `Layer N`.
   - Each block shows canonical, signature, symbol map grid, and rotation variant table (reuse existing markup patterns from lines 63–113).
   - When single-layer, keep current flat layout using top-level fields to avoid visual regression.
3. Add layer count / multi-layer hint in page intro or warnings when input contains `:`.
4. Ensure error state still shows `analysis.error` and optional `canonical_code` without per-layer blocks.
5. Update placeholder example in code input to mention colon-separated multi-layer (e.g. `CuCuCuCu:CuCuCuCu`).
6. Run `pytest tests/integration/web/test_pattern_lab.py -v` after Low plan integration test is added; fix any template regressions on empty state and single-layer GET.

## Files / Areas Likely Affected

- `django_apps/web/templates/web/pattern_lab.html`
- `django_apps/web/views/public_pages.py` (only if context shaping needed)
- `django_apps/shapez_solver/services/pattern_lab_service.py` (dataclass fields from High plan)

## Validation Plan

- lint: `ruff check django_apps/web/views/public_pages.py`
- tests: `pytest tests/integration/web/test_pattern_lab.py -v`
- manual verification: GET `/solver/pattern-lab/?code=CuCuCuCu:CuCuCuCu` shows two layer sections with signatures (not error banner)

## Acceptance Criteria

- [ ] Per-layer signature/rotation/symbol output rendered for multi-layer codes.
- [ ] Single-layer page appearance unchanged.
- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.

## Risks / Open Questions

- Macro candidates table: show per-layer matches, aggregate, or layer-0 only — prefer per-layer subsection or clear label if aggregated.
