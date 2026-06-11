---
source_file: "django_apps/web/services/shape_part_sprite_generation.py"
type: "code"
community: "_build_work_queue()"
location: "L163"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/_build_work_queue
---

# build_sample_quadrant_work_queue()

## Connections
- [[.start_sample_quadrants_job_view()]] - `calls` [INFERRED]
- [[_prepend_pedestal_if_needed()]] - `calls` [EXTRACTED]
- [[_variant_row_exists_with_image()]] - `calls` [EXTRACTED]
- [[``default_rect`` + red, quadrants 0..3 only; optional skip of complete rows.]] - `rationale_for` [EXTRACTED]
- [[shape_part_sprite_generation.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/_build_work_queue