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

# Plan: Render per-layer Pattern Lab analysis blocks

## Source Issue

- Linear: SHA-49
- Status at planning time: Todo
- Priority: Mid

## Problem

Even after service support lands (High plan), `pattern_lab.html` only renders a single signature/symbol-map/rotation block. Multi-layer codes need per-layer output consistent with `explain_pattern_family_mismatch` layer-walking (one block per layer, up to four).

## Scope

- Reuse per-layer data from extended `PatternLabAnalysis.layers`
- Update `pattern_lab.html` to render per-layer signature, symbol map, and rotation variant sections
- Preserve existing single-layer layout and copy when `layers` has length 1

## Non-goals

- Changing `public_pages.pattern_lab` view logic beyond passing through analysis
- Macro candidate aggregation across layers
- Playwright visual regression (optional follow-up)

## Implementation Plan

1. Confirm High plan landed: `PatternLabAnalysis.layers` populated for multi-layer codes.

2. In `pattern_lab.html`, wrap the existing signature + symbol-map grid in a conditional:
   - If `analysis.layers|length == 1`: keep current layout unchanged.
   - If `analysis.layers|length > 1`: loop `{% for layer in analysis.layers %}` and render a bordered subsection per layer.

3. Per-layer subsection structure (mirror single-layer sections):

```html
<section aria-labelledby="pattern-layer-{{ layer.layer_index }}-heading">
  <h2 id="pattern-layer-{{ layer.layer_index }}-heading">
    {% blocktrans with idx=layer.layer_index %}Layer {{ idx }}{% endblocktrans %}
  </h2>
  <p class="font-mono text-xs text-slate-400">{{ layer.layer_code }}</p>
  <!-- canonical, signature dl -->
  <!-- symbol_map grid -->
  <!-- rotation_variants table -->
</section>
```

4. Show overall `analysis.canonical_code` and warnings once above the per-layer grid.

5. Keep macro-candidates section at bottom using layer-0 signature (or first layer `db_candidates`) — document in template comment that catalog lookup is per-layer signature when multiple layers differ.

6. Update form placeholder to mention colon-separated multi-layer example: `CuCuCuCu:CuCuCuCu`.

7. Manual check: start dev server, open `/solver/pattern-lab/?code=CuCuCuCu:CuCuCuCu`, confirm two layer headings and `AAAA` signatures without error banner.

## Files / Areas Likely Affected

- `django_apps/web/templates/web/pattern_lab.html`
- `django_apps/shapez_solver/services/pattern_lab_service.py` (read-only dependency on `PatternLabLayerAnalysis`)
- `django_apps/web/views/public_pages.py` (no change expected)

## Validation Plan

- lint: not applicable (template)
- typecheck: not applicable
- tests: existing unit tests from High plan; manual browser check for multi-layer render
- build: `python manage.py check`
- manual verification: GET `/solver/pattern-lab/?code=CuCuCuCu:CuCuCuCu` shows per-layer blocks, not hard error

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Long multi-layer pages may need anchor nav; out of scope unless staff feedback.
- i18n: new "Layer N" strings need `{% trans %}` / `{% blocktrans %}`.
