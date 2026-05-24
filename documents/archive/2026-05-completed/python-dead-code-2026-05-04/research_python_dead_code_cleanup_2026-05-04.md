# Python dead, duplicate, and legacy code cleanup — research summary (2026-05-04)

## Scope

- Runtime/test Python under `django_apps/shapez_core/`, `django_apps/shapez_solver/`, `django_apps/web/`, `tests/`, `config/`.
- Out of scope: `frontend/recipe_graph_editor/`, `django_apps/web/static/web/js/recipe_graph_editor/` (per plan).

## Static analysis: Ruff

Run: `python -m ruff check .` (project root).

### Selected rules `F401`, `F821`, `F841`

- **Pass** — no unused import, undefined name, or unused local variable candidates.

### Items found under full rules (handled in first implementation)

| Rule | File | Action |
|------|------|------|
| I001 | `django_apps/shapez_solver/migrations/0004_patternfamily_graph_draft.py` | `ruff check --fix` |
| I001 | `tests/integration/web/test_macro_pattern_staff.py` | `ruff check --fix` |
| E501 | `tests/integration/web/test_macro_pattern_staff.py` | import paren line break (Ruff auto) |
| E501 | `tests/unit/shapez_solver/test_recipe_graph_react_flow_adapter.py` | multiline dict literal |
| E501 | `tests/unit/shapez_solver/test_recipe_graph_topology.py` | multiline dict literal |

After implementation: full `python -m ruff check .` pass.

### Mypy (verification reinforcement)

- Initial research had errors in `django_apps/web` allauth integration, `context_processors`, some unit tests.
- Follow-up: added request/return types to `context_processors.django_debug`, `dict[str, object]` for `empty_doc` in `test_macro_recipe_staff_catalog`, mypy overrides in `pyproject.toml` for `django_apps.web.social_adapter` and `django_apps.web.socialaccount_forms` → `python -m mypy .` pass.

## Vulture

- Run: `python -m vulture django_apps tests config --min-confidence 80`
- **Result**: `vulture` package not installed locally; high-confidence unused symbol list not included in this research.

## Reference tracing (sample)

- `recipe_graph_*`, `graph_document_primitive_chain`, `macro_recipe_staff_catalog` under `shapez_solver/services/` confirmed imported/called from `django_apps/web/views.py`, URLs, integration/unit tests.
- `shapez_core` module tree (e.g. `shape_pattern.py`) referenced from services/tests.
- **Do not label entire `services/*.py` files orphan** — Django string references and dynamic loading false positives match plan risk section.

## Legacy naming (plan citation)

- `tests/unit/shapez_solver/test_legacy_planner_characterization.py` kept for **regression/spec lock**. Not a deletion target.

## Notes

- Root `.gitignore` includes `documents/`; Git tracking follows separate policy. Recorded at this workspace path.
