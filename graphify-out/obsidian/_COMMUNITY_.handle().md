---
type: community
cohesion: 0.32
members: 12
---

# .handle()

**Cohesion:** 0.32 - loosely connected
**Members:** 12 nodes

## Members
- [[._build_metadata()]] - code - django_apps/asteroid_lab/management/commands/seed_miner_patterns.py
- [[._parse_bootstrap()]] - code - django_apps/asteroid_lab/management/commands/seed_miner_patterns.py
- [[._print_rank_table()]] - code - django_apps/asteroid_lab/management/commands/seed_miner_patterns.py
- [[._purge_stale_miner_seed_rows()]] - code - django_apps/asteroid_lab/management/commands/seed_miner_patterns.py
- [[._raise_on_rank_ambiguity()]] - code - django_apps/asteroid_lab/management/commands/seed_miner_patterns.py
- [[.add_arguments()_3]] - code - django_apps/asteroid_lab/management/commands/seed_miner_patterns.py
- [[.handle()_4]] - code - django_apps/asteroid_lab/management/commands/seed_miner_patterns.py
- [[Command_4]] - code - django_apps/asteroid_lab/management/commands/seed_miner_patterns.py
- [[Ingest 18 canonical miner seed patterns from bootstrap copy strings into GeneSee]] - rationale - django_apps/asteroid_lab/management/commands/seed_miner_patterns.py
- [[IntrinsicDifficultyResult_1]] - code - django_apps/asteroid_lab/management/commands/seed_miner_patterns.py
- [[_ParsedSeed]] - code - django_apps/asteroid_lab/management/commands/seed_miner_patterns.py
- [[seed_miner_patterns.py]] - code - django_apps/asteroid_lab/management/commands/seed_miner_patterns.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/handle
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_miner_seed_intrinsic_difficulty.py]]
- 3 edges to [[_COMMUNITY_Any]]
- 2 edges to [[_COMMUNITY_ValueError]]
- 2 edges to [[_COMMUNITY_topology_signature_from_decoded_root()]]
- 1 edge to [[_COMMUNITY_miner_seed_constants.py]]
- 1 edge to [[_COMMUNITY_BaseCommand]]
- 1 edge to [[_COMMUNITY_decode_copy_string()]]

## Top bridge nodes
- [[.handle()_4]] - degree 11, connects to 3 communities
- [[._parse_bootstrap()]] - degree 8, connects to 3 communities
- [[._build_metadata()]] - degree 6, connects to 2 communities
- [[Command_4]] - degree 9, connects to 1 community
- [[._raise_on_rank_ambiguity()]] - degree 4, connects to 1 community