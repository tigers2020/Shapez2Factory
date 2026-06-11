---
source_file: "django_apps/web/services/shape_part_sprite_generation.py"
type: "code"
community: "_build_work_queue()"
location: "L200"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/_build_work_queue
---

# build_tank_sprite_work_queue()

## Connections
- [[.start_tank_missing_job_view()]] - `calls` [INFERRED]
- [[_prepend_pedestal_if_needed()]] - `calls` [EXTRACTED]
- [[_variant_row_exists_with_image()]] - `calls` [EXTRACTED]
- [[``default_fluid_tank_vortex`` (``t``) × colors × quadrants; skip complete rows.]] - `rationale_for` [EXTRACTED]
- [[iter_atomic_sprite_specs()]] - `calls` [INFERRED]
- [[shape_part_sprite_generation.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/_build_work_queue