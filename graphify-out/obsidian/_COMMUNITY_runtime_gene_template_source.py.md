---
type: community
cohesion: 0.22
members: 9
---

# runtime_gene_template_source.py

**Cohesion:** 0.22 - loosely connected
**Members:** 9 nodes

## Members
- [[.to_json_dict()]] - code - django_apps/asteroid_lab/services/runtime_gene_template_source.py
- [[Gene template source contracts for the runtime loader (DB-only path).]] - rationale - django_apps/asteroid_lab/services/runtime_gene_template_source.py
- [[GeneTemplateLoadErrorCode]] - code - django_apps/asteroid_lab/services/runtime_gene_template_source.py
- [[GeneTemplateSourceKind]] - code - django_apps/asteroid_lab/services/runtime_gene_template_source.py
- [[GeneTemplateSourceMetadata]] - code - django_apps/asteroid_lab/services/runtime_gene_template_source.py
- [[Provenance record written to SolverRun.config_json and HTTP response.      Out]] - rationale - django_apps/asteroid_lab/services/runtime_gene_template_source.py
- [[Structured failure codes for gene template loading (never free-form strings).]] - rationale - django_apps/asteroid_lab/services/runtime_gene_template_source.py
- [[Where run-time gene templates come from (wire string, persisted in config_json).]] - rationale - django_apps/asteroid_lab/services/runtime_gene_template_source.py
- [[runtime_gene_template_source.py]] - code - django_apps/asteroid_lab/services/runtime_gene_template_source.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/runtime_gene_template_sourcepy
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_StrEnum]]
- 1 edge to [[_COMMUNITY_Any]]
- 1 edge to [[_COMMUNITY_Enum]]

## Top bridge nodes
- [[runtime_gene_template_source.py]] - degree 5, connects to 1 community
- [[GeneTemplateSourceKind]] - degree 3, connects to 1 community
- [[GeneTemplateLoadErrorCode]] - degree 3, connects to 1 community
- [[.to_json_dict()]] - degree 2, connects to 1 community