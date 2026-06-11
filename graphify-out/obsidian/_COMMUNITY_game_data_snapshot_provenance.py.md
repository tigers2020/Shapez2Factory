---
type: community
cohesion: 0.18
members: 22
---

# game_data_snapshot_provenance.py

**Cohesion:** 0.18 - loosely connected
**Members:** 22 nodes

## Members
- [[.__init__()_19]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[.reproducibility_key()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[.reproducibility_key_v1()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[Alias for ``parse_provenance_config`` (v2 strict).]] - rationale - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[Frozen provenance for game_data snapshot builds (metadata only — not algorithm i]] - rationale - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[GameDataSnapshotProvenance]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[Historical Track A wire (8 keys). Read-only for pre-B2 ``SolverRun`` rows.]] - rationale - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[Latest strict parser — Track B2 provenance v2 (10 keys). RTTP persistreadback.]] - rationale - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[ProvenanceParseError]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[ProvenanceParseErrorCode]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[Slim deploy diagnostic for P1 RTTP-off responses (not full provenance wire).]] - rationale - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[Track A reproducibility key (3-tuple). ``built_at_utc`` excluded.]] - rationale - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[Track B2 reproducibility key (5-tuple). ``built_at_utc`` excluded.]] - rationale - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[_parse_provenance_payload()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[_validate_parsed_provenance_base()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[_validate_parsed_provenance_v2()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[game_data_snapshot_provenance.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[parse_provenance_config()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[parse_provenance_config_latest()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[parse_provenance_config_v1()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[provenance_stub_diagnostic_dict()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py
- [[provenance_to_config_dict()]] - code - src/shapez2_factory/domain/asteroid_lab/game_data_snapshot_provenance.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/game_data_snapshot_provenancepy
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_building_catalog_slice_hash.py]]
- 1 edge to [[_COMMUNITY_ValueError]]
- 1 edge to [[_COMMUNITY_StrEnum]]
- 1 edge to [[_COMMUNITY_Enum]]
- 1 edge to [[_COMMUNITY__run_solver_post_traced()]]

## Top bridge nodes
- [[game_data_snapshot_provenance.py_1]] - degree 14, connects to 2 communities
- [[GameDataSnapshotProvenance]] - degree 12, connects to 1 community
- [[ProvenanceParseError]] - degree 8, connects to 1 community
- [[provenance_stub_diagnostic_dict()]] - degree 5, connects to 1 community
- [[ProvenanceParseErrorCode]] - degree 3, connects to 1 community