---
type: community
cohesion: 0.18
members: 18
---

# miner_seed_intrinsic_difficulty.py

**Cohesion:** 0.18 - loosely connected
**Members:** 18 nodes

## Members
- [[IntrinsicDifficultyResult]] - code - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
- [[ParentEdge]] - code - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
- [[Pattern-intrinsic difficulty scoring for miner seed catalog rows.]] - rationale - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
- [[Production-adjusted intrinsic priority (lower = try first in gene picker).]] - rationale - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
- [[Return (pattern_id, result, difficulty_rank) sorted easiest-first; ranks 1..N.]] - rationale - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
- [[Return (pattern_id, result, intrinsic_priority_rank) sorted highest-priority-fir]] - rationale - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
- [[Return (pattern_id_a, pattern_id_b, shared_key) for colliding pre-pattern_id key]] - rationale - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
- [[Sort key before final ``pattern_id`` tie-break (for strict ambiguity checks).]] - rationale - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
- [[_branch_count()]] - code - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
- [[_difficulty_tier()]] - code - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
- [[_turn_count()]] - code - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
- [[assign_difficulty_ranks()]] - code - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
- [[assign_intrinsic_priority_ranks()]] - code - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
- [[find_rank_ambiguity()]] - code - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
- [[intrinsic_difficulty_from_root()]] - code - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
- [[intrinsic_priority_score()]] - code - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
- [[miner_seed_intrinsic_difficulty.py]] - code - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
- [[pre_pattern_id_sort_key()]] - code - django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/miner_seed_intrinsic_difficultypy
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_.handle()]]
- 3 edges to [[_COMMUNITY_ValueError]]
- 1 edge to [[_COMMUNITY_Any]]
- 1 edge to [[_COMMUNITY_topology_signature_from_decoded_root()]]

## Top bridge nodes
- [[intrinsic_difficulty_from_root()]] - degree 10, connects to 4 communities
- [[find_rank_ambiguity()]] - degree 5, connects to 1 community
- [[_turn_count()]] - degree 4, connects to 1 community
- [[intrinsic_priority_score()]] - degree 4, connects to 1 community
- [[assign_intrinsic_priority_ranks()]] - degree 4, connects to 1 community