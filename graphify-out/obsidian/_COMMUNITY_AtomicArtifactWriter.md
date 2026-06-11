---
type: community
cohesion: 0.15
members: 21
---

# AtomicArtifactWriter

**Cohesion:** 0.15 - loosely connected
**Members:** 21 nodes

## Members
- [[.__init__()_11]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[._hash_payloads()]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[.final_dir()]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[.finalize()]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[.open_staging()]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[.staging_dir()]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[.write_output()]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[ArtifactExistsError]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[ArtifactManifest_1]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[ArtifactWriterError]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[AtomicArtifactWriter]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[Base error for the atomic artifact writer.]] - rationale - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[Final artifact directory already exists and ``replace_existing`` is False.]] - rationale - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[InvalidRunKeyError]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[Staging directory already exists and ``replace_existing`` is False.]] - rationale - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[StagingExistsError]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[_normalize_relpath()]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[_validate_run_key()]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[``AtomicArtifactWriter`` — BA-5 atomic artifact write protocol (spec §5).  Pro]] - rationale - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[``run_key`` failed the writer-level safety guard.]] - rationale - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py
- [[artifact_writer.py]] - code - src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/AtomicArtifactWriter
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_Path]]
- 1 edge to [[_COMMUNITY_Exception]]
- 1 edge to [[_COMMUNITY__run_artifact()]]

## Top bridge nodes
- [[ArtifactWriterError]] - degree 9, connects to 1 community
- [[AtomicArtifactWriter]] - degree 9, connects to 1 community
- [[.finalize()]] - degree 6, connects to 1 community
- [[.__init__()_11]] - degree 3, connects to 1 community
- [[.open_staging()]] - degree 3, connects to 1 community