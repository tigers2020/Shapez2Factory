# Asteroid inner quad placement templates (canon)

**Status:** Canon for **placement design intent** and **frozen decode fixtures**.  
**Not implemented** in L5 inner fill solver until a follow-up cycle (quad tile catalog + extension reroute).

## Sources and trust

| Source | Trust |
| --- | --- |
| In-game paste blueprints (T1–T4, Q1–Q4) | **High** — frozen as `tests/fixtures/asteroid_lab/inner_quad_templates/*.shapez.txt` |
| Decode regression (`test_inner_quad_template_decode.py`) | **High** — locks entry counts and transport types |
| L5 greedy / trunk-first solver behavior | **Out of scope** for this document |

## Boundary (hard)

| Allowed | Forbidden |
| --- | --- |
| Reference templates when designing L5 placement | Use `golden.shapez.txt` / golden summary as **solver input** |
| Decode templates for regression and tooling | Treat Q tiles as eval oracle |
| Copy fixture strings into admin/GeneSeed manually | Mix template canon change + solver change in one cycle |

Solver input for golden loop remains: `empty.shapez.txt`, `genetic_sample_seeds.json`, `game_data_snapshot_min.json`. Golden map is **eval oracle only**.

Related: [shapez2_space_transport_connectivity.md](shapez2_space_transport_connectivity.md), [shapez2_asteroid_space_transport_throughput.md](shapez2_asteroid_space_transport_throughput.md).

## Design intent

Fill the asteroid **field interior** by:

1. Placing **T-family** junction primitives at rim/void egress (miners + belt merger/lift).
2. Growing **Q-family** quad tiles inward: each miner may carry up to **3** `Layout_ShapeMinerExtension` cells on field (same cap as gene seeds / L3 degradation).
3. Prefer **rectangular / quad** footprints (Q1 → Q4 scale examples).
4. When corners or gaps are tight, **reroute** extension chains (bend) instead of forcing a straight inward chain.

**T templates** are **not** extension chains — they are local belt topology at the void boundary.

## Template catalog

Fixtures: `tests/fixtures/asteroid_lab/inner_quad_templates/`  
Manifest: `manifest.json` (`inner_quad_template_v1`).

### T family — junction primitives

| ID | Role | Miners | Extensions | Transport |
| --- | --- | ---: | ---: | --- |
| T1 | solo miner + lift corner | 1 | 0 | `SpaceBelt_Lift1UpForward` |
| T2 | triple miner + triple merger | 3 | 0 | `TripleMerger`, `Lift1UpForward` |
| T3 | dual miner + left merger | 2 | 0 | `LeftFwdMerger`, `Lift1UpForward` |
| T4 | dual miner + Y merger | 2 | 0 | `YMerger`, `Lift1UpForward` |

### Q family — quad tile scale examples

| ID | Role | Miners | Extensions | Transport |
| --- | --- | ---: | ---: | --- |
| Q1 | minimal quad | 2 | 6 | 2× `Lift1UpForward` |
| Q2 | small quad | 4 | 12 | `Lift1UpForward`, `TripleMerger` |
| Q3 | medium quad | 6 | 18 | `Lift1UpForward`, `TripleMerger` |
| Q4 | large quad | 14 | 42 | 14× `Lift1UpForward` |

Island-local coordinates use the copy JSON convention (`X`/`Y`/`R` on `BP.Entries`). See `tests/unit/asteroid_lab/test_copy_json_island_local_coords.py`.

## Deferred (next cycle)

- L5 quad tile catalog wired from manifest
- Extension reroute / weighted rip-up integration
- Golden loop before/after metrics for placement changes

## Change policy

- Fixture string or manifest count change → update this doc + decode test in the **same PR**.
- Solver behavior using these templates → **separate PR** with its own golden loop cycle.
