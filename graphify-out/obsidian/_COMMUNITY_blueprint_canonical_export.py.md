---
type: community
cohesion: 0.10
members: 34
---

# blueprint_canonical_export.py

**Cohesion:** 0.10 - loosely connected
**Members:** 34 nodes

## Members
- [[Anchor for lab → official XY miner first, else min ``Layout_MinerExtension``.]] - rationale - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[Build ``V````BP`` dict matching game island export (1137 + Icon + BinaryVersion]] - rationale - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[Build island JSON for in-game paste.      Field tiles only (``Layout_MinerExt]] - rationale - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[Dense column indices for export ``X`` values (omitted ``X`` → 0).]] - rationale - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[Deterministic JSON bytes for island export (field order + default key omission).]] - rationale - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[Keep only Extension field tiles for in-game asteroid-field paste (no minerspipe]] - rationale - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[Lab raw ``X,Y`` → game export ``X,Y`` (dense column anchor).      Let ``(ex_x,]] - rationale - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[Official-style Shapez2 v4 island blueprint JSON bytes + copy-string encoding.]] - rationale - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[Return a shallow copy without lab-only top-level keys.]] - rationale - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[Return a valid empty island root dict (useful for tests and stub exports).]] - rationale - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[Return the copy-string prefix for target_game_version.      Raises ``ValueEr]] - rationale - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[True when blueprint ``X`` values match in-game paste space (negative columns com]] - rationale - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[True when dense(export X) values form a contiguous interval with no gaps.]] - rationale - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[_as_int()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[_coords_look_like_game_export()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[_export_anchor()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[_extractor_anchor()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[_field_export_entries()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[_is_extractor_tile()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[_is_field_extension_tile()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[_serialize_entry_row()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[_strip_lab_entry()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[blueprint_canonical_export.py]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[encode_official_copy_string()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[export_dense_x_is_contiguous()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[export_dense_x_set()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[gzip + base64 + versioned prefix.      target_game_version defaults to 4 (th]] - rationale - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[make_minimal_official_root()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[resolve_blueprint_code_version()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[serialize_game_island_export_bytes()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[strip_lab_fields_from_root()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[to_game_paste_island_root()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[to_official_island_root()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py
- [[translate_lab_entries_to_official_xy()]] - code - django_apps/asteroid_lab/adapters/blueprint_canonical_export.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/blueprint_canonical_exportpy
SORT file.name ASC
```

## Connections to other communities
- 15 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_build_golden_oracle()]]
- 2 edges to [[_COMMUNITY_exhaustive_generator.py]]

## Top bridge nodes
- [[translate_lab_entries_to_official_xy()]] - degree 8, connects to 2 communities
- [[to_official_island_root()]] - degree 7, connects to 2 communities
- [[export_dense_x_set()]] - degree 6, connects to 2 communities
- [[encode_official_copy_string()]] - degree 6, connects to 2 communities
- [[_as_int()]] - degree 9, connects to 1 community