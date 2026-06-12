---
title: Reconstructed Map (full_map persistence)
created: 2026-06-12
updated: 2026-06-12
type: concept
tags: [asteroid-lab, reconstruction]
sources:
  - django_apps/asteroid_lab/models.py
  - django_apps/asteroid_lab/services/reconstructed_map_persist_builder.py
  - django_apps/asteroid_lab/services/reconstructed_asteroid_service.py
confidence: high
---

# Reconstructed Map

> **ORM:** `ReconstructedAsteroidMap` · **Payload builder:** `build_reconstructed_map_persist_payload`.

## Definition (source)

Persisted **full_map** lab copy after reconstruction + cleanup merge: original paste snapshot plus merged `copy_code` / `decoded_json` suitable for export and admin inspection. **Not** solver algorithm input; **not** read from replay artifacts when building persist payload.

## Lifecycle (source)

```text
ReconstructionResult + CleanupResult
  → build_reconstructed_map_persist_payload()
  → ReconstructedAsteroidMap.update_or_create(map_input, run_key)
```

| Stage | Module |
|---|---|
| Merge display cells | `reconstruction/display_map.py` |
| Normalize + encode copy | `reconstruction_blueprint_export.py` |
| Persist ORM | `reconstructed_asteroid_service.py` |
| Admin thumbnail | `reconstructed_map_thumbnail_service.py` |

## Key fields (source)

| Field | Meaning |
|---|---|
| `original_copy_code` / `original_decoded_json` | Input paste at persist time |
| `copy_code` / `decoded_json` | full_map merged lab output |
| `run_key` | Tied to solver run that produced reconstruction |
| `solver_run` | Optional FK; SET_NULL on delete |

Migration `0009_reconstructed_map_full_map_only`: layers model simplified to full_map-only persistence.

## Coordinate frame

Merged cells use **world / reconstruction** display semantics for export; distinct from copy JSON island-local input. See [[island-mechanics]].

## Cross-References

- [[island-mechanics]]: copy-local vs world reconstruction frames
- [[asteroid-lab-algorithm]]: L4/L5 use `ReconstructionCompleteMap`, not this ORM row directly
- [[algorithm-doc-authority]]: doc routing
- [`docs/ubiquitous-language.md`](../../../../docs/ubiquitous-language.md): **ReconstructedMap** / `ReconstructedAsteroidMap`
