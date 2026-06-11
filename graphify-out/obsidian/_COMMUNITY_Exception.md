---
type: community
cohesion: 0.12
members: 22
---

# Exception

**Cohesion:** 0.12 - loosely connected
**Members:** 22 nodes

## Members
- [[.__init__()_15]] - code - src/shapez2_factory/adapters/asteroid_lab/run_key_safety.py
- [[.from_json()]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_manifest.py
- [[.from_json_dict()]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_manifest.py
- [[.to_json()]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_manifest.py
- [[.to_json_dict()_1]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_manifest.py
- [[ArtifactManifest]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_manifest.py
- [[ArtifactPathError]] - code - src/shapez2_factory/adapters/asteroid_lab/run_key_safety.py
- [[Exception]] - code
- [[Guard C — run_key + artifact-root safety (pure stdlib).  This module validates]] - rationale - src/shapez2_factory/adapters/asteroid_lab/run_key_safety.py
- [[ManifestSchemaVersionError]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_manifest.py
- [[Parse a manifest JSON string, rejecting unsupported schema versions.      Sche]] - rationale - src/shapez2_factory/adapters/asteroid_lab/artifact_manifest.py
- [[Raised when a manifest declares an unsupported ``schema_version``.]] - rationale - src/shapez2_factory/adapters/asteroid_lab/artifact_manifest.py
- [[Raised when a run_key is unsafe or escapes the allowed artifact root.]] - rationale - src/shapez2_factory/adapters/asteroid_lab/run_key_safety.py
- [[Resolve ``artifact_root  run_key`` and assert it nests under ``allowed_root``.]] - rationale - src/shapez2_factory/adapters/asteroid_lab/run_key_safety.py
- [[Run lifecycle status enum (spec §4).  Authority split ``manifest.lifecycle_st]] - rationale - src/shapez2_factory/adapters/asteroid_lab/run_status.py
- [[RunLifecycleStatus]] - code - src/shapez2_factory/adapters/asteroid_lab/run_status.py
- [[``ArtifactManifest`` DTO + (de)serialization (spec §2 manifest.json schema).]] - rationale - src/shapez2_factory/adapters/asteroid_lab/artifact_manifest.py
- [[artifact_manifest.py]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_manifest.py
- [[parse_manifest_checked()]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_manifest.py
- [[resolve_artifact_dir()]] - code - src/shapez2_factory/adapters/asteroid_lab/run_key_safety.py
- [[run_key_safety.py]] - code - src/shapez2_factory/adapters/asteroid_lab/run_key_safety.py
- [[run_status.py]] - code - src/shapez2_factory/adapters/asteroid_lab/run_status.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Exception
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_ingest_artifact_for_project()]]
- 2 edges to [[_COMMUNITY__run_artifact()]]
- 1 edge to [[_COMMUNITY_Path]]
- 1 edge to [[_COMMUNITY_StrEnum]]
- 1 edge to [[_COMMUNITY_read_verified_artifact_manifest()]]
- 1 edge to [[_COMMUNITY_ReplayRecorder]]
- 1 edge to [[_COMMUNITY_SolverRun]]
- 1 edge to [[_COMMUNITY_run_solver_subprocess()]]
- 1 edge to [[_COMMUNITY_build_game_data_snapshot_payload()]]
- 1 edge to [[_COMMUNITY_AtomicArtifactWriter]]
- 1 edge to [[_COMMUNITY_genetic_sample_seed_snapshot.py]]
- 1 edge to [[_COMMUNITY_json_snapshot_rules.py]]
- 1 edge to [[_COMMUNITY_space_transport_catalog_snapshot.py]]
- 1 edge to [[_COMMUNITY_Enum]]

## Top bridge nodes
- [[Exception]] - degree 13, connects to 10 communities
- [[resolve_artifact_dir()]] - degree 5, connects to 2 communities
- [[parse_manifest_checked()]] - degree 6, connects to 1 community
- [[.from_json_dict()]] - degree 5, connects to 1 community
- [[.to_json_dict()_1]] - degree 3, connects to 1 community