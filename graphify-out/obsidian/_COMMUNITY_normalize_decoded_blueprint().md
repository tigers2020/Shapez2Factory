---
type: community
cohesion: 0.23
members: 12
---

# normalize_decoded_blueprint()

**Cohesion:** 0.23 - loosely connected
**Members:** 12 nodes

## Members
- [[Attach lab-local summary metadata to decoded blueprint JSON (pure, no IO).]] - rationale - src/shapez2_factory/domain/asteroid_lab/normalization.py
- [[NormalizedBlueprintDTO]] - code - src/shapez2_factory/domain/asteroid_lab/normalization.py
- [[RawDecodedBlueprintDTO]] - code - src/shapez2_factory/domain/asteroid_lab/normalization.py
- [[Return a shallow-copied root dict with ``_asteroid_lab_summary`` injected.]] - rationale - src/shapez2_factory/domain/asteroid_lab/normalization.py
- [[Root with summary + island coord meta (persist ``decoded_json``).]] - rationale - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[_as_int()_2]] - code - src/shapez2_factory/domain/asteroid_lab/normalization.py
- [[_build_summary()]] - code - src/shapez2_factory/domain/asteroid_lab/normalization.py
- [[_coerce_int_version()]] - code - src/shapez2_factory/domain/asteroid_lab/normalization.py
- [[build_reconstructed_normalized_dto()]] - code - django_apps/asteroid_lab/adapters/reconstruction_blueprint_export.py
- [[normalization.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/normalization.py
- [[normalize_blueprint_entries()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_loader.py
- [[normalize_decoded_blueprint()]] - code - src/shapez2_factory/domain/asteroid_lab/normalization.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/normalize_decoded_blueprint
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_Any]]
- 4 edges to [[_COMMUNITY_AsteroidMapInput]]
- 3 edges to [[_COMMUNITY_DecodedCellDTO]]
- 2 edges to [[_COMMUNITY_build_golden_oracle()]]
- 1 edge to [[_COMMUNITY_GeneSeed]]
- 1 edge to [[_COMMUNITY_build_reconstructed_map_persist_payload(]]
- 1 edge to [[_COMMUNITY_build_initial_replay_for_map_input()]]
- 1 edge to [[_COMMUNITY_decode_copy_string()]]
- 1 edge to [[_COMMUNITY_entry_island_raw_coord()]]
- 1 edge to [[_COMMUNITY_deconstruct_snapshot()]]

## Top bridge nodes
- [[normalize_decoded_blueprint()]] - degree 12, connects to 4 communities
- [[build_reconstructed_normalized_dto()]] - degree 8, connects to 3 communities
- [[normalize_blueprint_entries()]] - degree 5, connects to 2 communities
- [[_build_summary()]] - degree 5, connects to 2 communities
- [[NormalizedBlueprintDTO]] - degree 5, connects to 1 community