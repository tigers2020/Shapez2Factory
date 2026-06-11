---
type: community
cohesion: 0.25
members: 8
---

# miner_seed_constants.py

**Cohesion:** 0.25 - loosely connected
**Members:** 8 nodes

## Members
- [[Constants for miner seed ingest and projection (GeneticSample DB canonical).]] - rationale - django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py
- [[Legacy v1 rank 1..14 — retained for tests referencing old keys only.]] - rationale - django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py
- [[PatternMetrics]] - code - django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py
- [[Return canonical difficultypriority metrics for ``pattern_id``.]] - rationale - django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py
- [[gene_key_for_pattern_id()]] - code - django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py
- [[gene_key_for_rank()]] - code - django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py
- [[metrics_for_pattern_id()]] - code - django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py
- [[miner_seed_constants.py]] - code - django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/miner_seed_constantspy
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_.handle()]]

## Top bridge nodes
- [[gene_key_for_pattern_id()]] - degree 2, connects to 1 community