# Game Rules Document Index

Reference documents on **shape algebra and solver perspective** rules for the shapez / shapez 2 family, organized by topic. Before implementing, read each file's **sources & trust** and **when unverified** sections together.

| File | Summary |
| --- | --- |
| [sources_and_trust.md](sources_and_trust.md) | Source references and trust levels |
| [core_abstraction.md](core_abstraction.md) | Core abstraction: shapes as token structure, not physics |
| [shape_encoding.md](shape_encoding.md) | Layer, quadrant, and code string rules (**project canonical: SW→NW→NE→SE**; may differ from official viewer strings) |
| [operation_cutter.md](operation_cutter.md) | Cutter / Quad Cutter |
| [operation_rotater.md](operation_rotater.md) | Rotation (quadrant permutation) |
| [operation_stacker.md](operation_stacker.md) | Stacker — same-layer merge vs layer stacking |
| [operation_painter.md](operation_painter.md) | Painter (preserve shape, change color only) |
| [operation_color_mixer.md](operation_color_mixer.md) | Liquid color mixing (solver: prefer separate resource dependency) |
| [shapez2_spatial_model.md](shapez2_spatial_model.md) | 3D factory vs shapes remain 2D layer structure |
| [shapez2_cutter_outputs.md](shapez2_cutter_outputs.md) | Shapez 2 Cutter output order (east/west) |
| [shapez2_stacker_inputs.md](shapez2_stacker_inputs.md) | Stacker bottom/top input roles |
| [shapez2_swapper.md](shapez2_swapper.md) | Simulated Swapper (west-half exchange) |
| [shapez2_pin_support.md](shapez2_pin_support.md) | Pin, floating shapes, support validation |
| [shapez2_crystal.md](shapez2_crystal.md) | Crystal Generator summary and implementation links |
| [shapez2_asteroid_space_transport_throughput.md](shapez2_asteroid_space_transport_throughput.md) | Asteroid Miner/Pump and Space Belt/Pipe absolute throughput (30/m, 300 L/m, ×16, 12·72 saturation) |
| [shapez2_space_transport_connectivity.md](shapez2_space_transport_connectivity.md) | Island belt/pipe topology: miner belt sharing, merger/splitter, Rift (Space Lift) 1:1 and `z`/`R` egress |
| [shapez2_asteroid_inner_quad_templates.md](shapez2_asteroid_inner_quad_templates.md) | Asteroid inner fill: T junction + Q quad tile canon (fixtures; solver wiring deferred) |
| [crystal_mechanics.md](crystal_mechanics.md) | Crystal generation, clusters, shatter, per-operation notes (canonical) |
| [solver_domain_model.md](solver_domain_model.md) | Actual `shapez_core` types (`ShapePart`, `ShapeLayer`, `Shape`) |
| [solver_operation_interface.md](solver_operation_interface.md) | Operation interface and required operation list |
| [solver_graph_dag.md](solver_graph_dag.md) | Intermediate shape reuse and DAG |
| [solver_quantity_flow.md](solver_quantity_flow.md) | Quantities needed on edges and plans, not just nodes |
| [solver_search_strategy.md](solver_search_strategy.md) | Shortest path — BFS/Dijkstra/A* |
| [implementation_priorities.md](implementation_priorities.md) | Project implementation priority order |

Upstream domain research: [research_shapez2_game_systems_2026-05-01.md](../research/research_shapez2_game_systems_2026-05-01.md)
