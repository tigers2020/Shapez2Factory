# Position — UI / Interface Owner

## Lens

`frontend/`, `django_apps/web/`, `src/shapez2_factory/interfaces/` — templates, static, React/Vite, thin views.

## Responsibility

- UI depends on DTOs/use cases — not adapter internals.
- UI/regression first for visual or serialization changes.
- Follow [Web Interface Guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md) ([web-interface.mdc](../.cursor/rules/web-interface.mdc)).

## Authority

- **May:** edit UI assets · templates · frontend tests · fixture regressions when scoped.
- **Must not:** business policy in templates/JS; direct DB/HTTP from UI layer.

## Primary paths

- [`documents/ai/manuals/frontend.md`](../documents/ai/manuals/frontend.md)
- `django_apps/web/static/`, `frontend/`

## Stop conditions

- DOM/serialization contract change without fixture test
- Solver/algorithm logic in UI layer

## Verification habit

```bash
python -m pytest tests/unit/…<web or frontend path>…
```

Visual check: Playwright/browser when user requests.
