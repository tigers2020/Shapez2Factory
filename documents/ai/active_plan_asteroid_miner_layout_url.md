---
status: ACTIVE
owner: web-backend
last_reviewed: 2026-05-15
supersedes: []
superseded_by:
related_epics: []
---

# Asteroid Mining Lab: remove copy string from URL

## Goal

- Remove huge Shapez2 blueprint copy string from **GET query `?code=`**.
- **POST** submit then **PRG (302)** to short URL based on `AsteroidProject.slug`.
- On resubmit of same content, dedupe via **`AsteroidMapInput.content_sha256`**.

## URL contract

| Method | Path | Behavior |
|--------|------|----------|
| GET | `/asteroid-miner-layout/` | Empty lab (ignore query `code`) |
| POST | `/asteroid-miner-layout/projects/` | Save `copy_code`, dedupe, redirect to `/asteroid-miner-layout/p/<slug>/` |
| GET | `/asteroid-miner-layout/p/<slug>/` | Render lab with latest `AsteroidMapInput.copy_code` for project |

## Dedupe

- Hash: `sha256` on UTF-8 bytes — same rule in `django_apps.asteroid_lab.services.input_service.content_sha256_for_copy_code` and `create_copy_code_map_input`.
- **Strip leading/trailing whitespace** before hash · persist (empty string → redirect to base URL).

## GET `?code=` compatibility

- **Breaking**: large payload bookmarks cannot be recovered due to URL limits. Base GET does not read `code`.

## Test scope

- Integration: POST → 302 Location → GET body reflects `copy_code`.
- Unit: two submits of same string → no project count increase · same slug.

## Implementation references

- Views: `django_apps/web/views/public_pages.py`
- URLs: `django_apps/web/urls.py`
- Service: `django_apps/asteroid_lab/services/project_service.py`
