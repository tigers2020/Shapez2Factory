# django_apps/web AGENTS.md

## Scope

Public pages, templates, static assets, thin web views, solver UI, Asteroid Lab UI, and staff tooling.

## Rules

- UI displays state; business policy belongs in services or core modules.
- Use Tailwind utilities in templates unless reusable component CSS is justified.
- Preserve accessibility basics: labels, focus visibility, keyboard path, and icon button aria labels.
- Avoid layout shift, `transition: all`, unbounded images, and hidden state that cannot be tested.
- Asteroid Lab viewer must read indexed/persisted artifacts; it must not become solver authority.

## Verify

- Focused tests under `tests/unit/web/` or `tests/integration/web/`.
- Browser/screenshot verification for visible UI changes when practical.
