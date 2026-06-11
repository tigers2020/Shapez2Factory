---
type: community
cohesion: 0.20
members: 11
---

# is_asteroid_evidence()

**Cohesion:** 0.20 - loosely connected
**Members:** 11 nodes

## Members
- [[Adapter-only field kind for mineable sets (does not mutate ``cell``).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py
- [[Decoded-cell predicates for asteroid reconstruction walls (flood-fill obstacles)]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/evidence.py
- [[Field kind implied by a stripped minerextension anchor (replay synthetic field]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/evidence.py
- [[Mineable field kind for voting, or None if this evidence cell carries no fluids]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/evidence.py
- [[Shell  mineable anchors from decode only (not replay-derived).]] - rationale - src/shapez2_factory/domain/asteroid_lab/reconstruction/evidence.py
- [[evidence.py]] - code - django_apps/asteroid_lab/reconstruction/evidence.py
- [[evidence.py_1]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/evidence.py
- [[evidence_field_kind()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/evidence.py
- [[inferred_field_kind_from_removed_miner_extension()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/evidence.py
- [[is_asteroid_evidence()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/evidence.py
- [[mineable_field_kind()]] - code - src/shapez2_factory/domain/asteroid_lab/reconstruction/acceptance_topology.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/is_asteroid_evidence
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_DecodedCellDTO]]
- 2 edges to [[_COMMUNITY_ReconstructionResult]]
- 2 edges to [[_COMMUNITY_stamp_islands_uniform()]]
- 1 edge to [[_COMMUNITY_deconstruct_snapshot()]]
- 1 edge to [[_COMMUNITY_reconstruct_after_cleanup()]]
- 1 edge to [[_COMMUNITY_build_normalized_reconstruction_topology]]

## Top bridge nodes
- [[is_asteroid_evidence()]] - degree 7, connects to 5 communities
- [[mineable_field_kind()]] - degree 5, connects to 2 communities
- [[evidence_field_kind()]] - degree 5, connects to 2 communities
- [[inferred_field_kind_from_removed_miner_extension()]] - degree 5, connects to 2 communities
- [[evidence.py_1]] - degree 5, connects to 1 community