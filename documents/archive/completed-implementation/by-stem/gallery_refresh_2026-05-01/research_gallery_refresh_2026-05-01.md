# Gallery refresh research

- Date: 2026-05-01
- Scope: gallery page redesign and viewer behavior cleanup for the Django web app.
- Sources: approved gallery refresh plan, current `django_apps/web` templates, `gallery-viewer.js`, and smoke tests.

## Findings

- The current gallery is rendered from static files discovered under `django_apps/web/static/web/img/screenshots/` and `factory-templates/`.
- `django_apps/web/templates/web/gallery.html` duplicates the same featured-plus-grid markup twice, once per section.
- The current modal viewer only opens and closes a single image. It does not keep per-section state, support previous/next navigation, or expose image context inside the dialog.
- The page has visual clutter that does not help an image-only browsing flow: a large explanatory hero, sticky jump nav, and a notes accordion.
- Several UI strings in the web templates still contain mojibake-like separators (`??`, corrupted middle dots) and both the nav and footer include dead `href="#"` GitHub links.

## Implementation Notes

- Keep the two gallery sections separate and browseable, rather than introducing search or tag filtering.
- Build lightweight image metadata in the view layer from filenames so templates and the viewer can show readable titles without adding a database model.
- Reuse one section template pattern for both collections by passing a normalized `gallery_sections` structure from the view.
- Restrict previous/next navigation to the active section so users do not jump between screenshots and templates unexpectedly.
- Replace dead links with non-interactive labels until a real destination exists.
