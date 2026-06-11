---
type: community
cohesion: 0.14
members: 20
---

# build_golden_oracle()

**Cohesion:** 0.14 - loosely connected
**Members:** 20 nodes

## Members
- [[GoldenOracle_1]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_loader.py
- [[Load and summarize golden fixture copy strings (domain-only; no Django).]] - rationale - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_loader.py
- [[Map copy JSON ``X`` to the compact official-export column.      이 변환은 파일 내보내기용]] - rationale - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[Precomputed golden-map features for eval (oracle only; never solver input).]] - rationale - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_loader.py
- [[Return ``(cell_kind, transport_kind)`` for one blueprint entry type string ``T``]] - rationale - src/shapez2_factory/domain/asteroid_lab/cell_classifier.py
- [[Return summary dict including per-tile-type counts and bbox list.]] - rationale - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_loader.py
- [[Top-level ``BP.Entries.T`` → lab cell  transport classification (A5).]] - rationale - src/shapez2_factory/domain/asteroid_lab/cell_classifier.py
- [[Top-level ``BP.Entries`` dict rows only (no nested ``B`` scan).]] - rationale - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[_belt_adjacency_edges()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_loader.py
- [[_extractor_anchor_export_xy()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_loader.py
- [[_normalize_coords()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_loader.py
- [[build_golden_oracle()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_loader.py
- [[cell_classifier.py]] - code - src/shapez2_factory/domain/asteroid_lab/cell_classifier.py
- [[classify_blueprint_entry()]] - code - src/shapez2_factory/domain/asteroid_lab/cell_classifier.py
- [[golden_fixture_loader.py]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_loader.py
- [[iter_entry_dicts()]] - code - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[load_golden_fixture_summary()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_loader.py
- [[raw_x_to_export_column()]] - code - src/shapez2_factory/domain/asteroid_lab/copy_json_coords.py
- [[summarize_blueprint()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_loader.py
- [[write_decoded_snapshots()]] - code - src/shapez2_factory/application/asteroid_lab/experiments/golden_fixture_loader.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/build_golden_oracle
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_Any]]
- 5 edges to [[_COMMUNITY_entry_island_raw_coord()]]
- 2 edges to [[_COMMUNITY_blueprint_canonical_export.py]]
- 2 edges to [[_COMMUNITY_build_decoded_blueprint_snapshot()]]
- 2 edges to [[_COMMUNITY_Path]]
- 2 edges to [[_COMMUNITY_normalize_decoded_blueprint()]]
- 1 edge to [[_COMMUNITY_ValueError]]
- 1 edge to [[_COMMUNITY_golden_fixture_fixtures.py]]
- 1 edge to [[_COMMUNITY_decode_copy_string()]]

## Top bridge nodes
- [[build_golden_oracle()]] - degree 12, connects to 2 communities
- [[golden_fixture_loader.py]] - degree 11, connects to 2 communities
- [[summarize_blueprint()]] - degree 6, connects to 2 communities
- [[classify_blueprint_entry()]] - degree 6, connects to 2 communities
- [[raw_x_to_export_column()]] - degree 6, connects to 2 communities