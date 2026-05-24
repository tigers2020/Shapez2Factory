# Plan: solver_timeline split (2026-05-01)

Related research: [documents/research_solver_timeline_split_2026-05-01.md](./research_solver_timeline_split_2026-05-01.md)

Original request summary: split [django_apps/web/static/web/js/solver_timeline.js](../../../../../django_apps/web/static/web/js/solver_timeline.js) into responsibility-based ES modules while preserving entry filename, auto-init, DOM `data-*` contract, and server response shape.

## Implementation approach

1. Create folder [django_apps/web/static/web/js/solver_timeline/](../../../../../django_apps/web/static/web/js/solver_timeline/).
2. Extract constants and shared DOM utils first, then split graph markup and viewport logic.
3. Consolidate selection detail panel and graph mount wiring in one module; separate throughput summary and request orchestration.
4. Finally shrink [solver_timeline.js](../../../../../django_apps/web/static/web/js/solver_timeline.js) to a thin entry.

## Compatibility criteria

- Do not change `solver.html` `<script type="module" src="{% static 'web/js/solver_timeline.js' %}"></script>`.
- Preserve auto-init via `document.querySelectorAll("[data-solver-timeline]")`.
- Keep existing `code`, `target_count` request payload and `ok`, `warnings`, `graph`, `target_count`, `base_demands` response usage.
- Preserve quantity badge, throughput summary, and `target_count` behavior already in dirty worktree without functional regression.

## Verification

- Run `pytest tests/integration/web/test_web_smoke.py`.
- Manually verify solver page load and timeline entry when possible.
- On failure, report whether JS refactor regression or pre-existing backend import issue.
