---
source_file: "django_apps/shapez_solver/services/recipe_graph_source_carrier.py"
type: "code"
community: "pure_fluid_color()"
location: "L10"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/pure_fluid_color
---

# assert_source_fluid_shape_valid()

## Connections
- [[``source_carrier`` 유체 소스의 ``shape_code``는 순수 유체이며 색은 rgb만.]] - `rationale_for` [EXTRACTED]
- [[assert_fluid_carrier_shape_for_role()]] - `calls` [EXTRACTED]
- [[parse_shape()]] - `calls` [INFERRED]
- [[pure_fluid_color()]] - `calls` [INFERRED]
- [[recipe_graph_source_carrier.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/pure_fluid_color