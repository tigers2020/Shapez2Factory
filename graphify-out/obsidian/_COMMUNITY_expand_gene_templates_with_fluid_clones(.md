---
type: community
cohesion: 0.40
members: 6
---

# expand_gene_templates_with_fluid_clones(

**Cohesion:** 0.40 - moderately connected
**Members:** 6 nodes

## Members
- [[Append fluid projections for every shape template; sort by ``gene_id``.]] - rationale - django_apps/asteroid_lab/genetic_sample/shape_fluid_gene_projection.py
- [[Clone a shape miner template as a fluid pump (canonical-E footprint unchanged).]] - rationale - django_apps/asteroid_lab/genetic_sample/shape_fluid_gene_projection.py
- [[Project shape miner ``GeneTemplate`` rows to fluid pump variants (same topology)]] - rationale - django_apps/asteroid_lab/genetic_sample/shape_fluid_gene_projection.py
- [[expand_gene_templates_with_fluid_clones()]] - code - django_apps/asteroid_lab/genetic_sample/shape_fluid_gene_projection.py
- [[fluid_gene_template_from_shape()]] - code - django_apps/asteroid_lab/genetic_sample/shape_fluid_gene_projection.py
- [[shape_fluid_gene_projection.py]] - code - django_apps/asteroid_lab/genetic_sample/shape_fluid_gene_projection.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/expand_gene_templates_with_fluid_clones
SORT file.name ASC
```

## Connections to other communities
- 3 edges to [[_COMMUNITY_GeneTemplate]]

## Top bridge nodes
- [[expand_gene_templates_with_fluid_clones()]] - degree 5, connects to 1 community
- [[fluid_gene_template_from_shape()]] - degree 4, connects to 1 community