# Plan: Gallery refresh

- Date: 2026-05-01
- Status: approved for implementation
- Basis: user-approved gallery refresh plan in chat

## Goal

Turn `/gallery/` into a cleaner image-first page with stronger preview behavior while keeping separate screenshot and factory template sections.

## Scope

1. Normalize gallery asset metadata in `django_apps/web/views.py`.
2. Replace duplicated gallery markup with a reusable section-driven template.
3. Simplify the gallery page layout around featured images, thumbnails, and a more focused dark presentation.
4. Expand `gallery-viewer.js` to support section-aware previous/next navigation, keyboard controls, captions, and an original-image link.
5. Remove or neutralize obvious quality issues tied to this surface, including broken title strings and dead GitHub links.
6. Update smoke coverage for the new gallery structure.

## Non-goals

- Search, tag filters, or persistent gallery state.
- Database-backed asset metadata.
- Changes to solver behavior or non-gallery product workflows.

## Validation

Run the project harness in this order:

```text
pytest
ruff check .
mypy src
black .
```

Also verify manually that both gallery sections open the same modal system, navigation buttons and arrow keys work, close behavior works, and mobile layout remains intact.
