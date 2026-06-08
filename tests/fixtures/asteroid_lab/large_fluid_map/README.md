# Large fluid map fixture (Run #437 class)

**Provenance (offline generation only):**

- Source run: `var/runs/asteroid-23-d6e546dee6e34b8fbba3790c50ae5984`
- Regression class: fluid field ~307 cells, 55 rim anchors; fixed 64-cell route probe budget left 35/55 unreachable before #139 scaling fix.

**Files:**

| File | Source artifact path |
|------|----------------------|
| `complete_map.json` | `output/layer01_complete_map.json` |
| `genetic_sample_seeds.json` | `input/genetic_sample_seeds.json` |
| `game_data_snapshot.json` | `input/game_data_snapshot.json` |

**Runtime rule:** Tests load **only** this directory. `var/runs` must not be read at test runtime.

**Contract:** `test_layer03_route_probe_map_budget.py` — `feasible == rim`, `committed >= 0.95 * rim`.
