---
source_file: "django_apps/asteroid_lab/services/genetic_sample_gene_export.py"
type: "code"
community: "GeneTemplate"
location: "L132"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/GeneTemplate
---

# load_gene_templates_from_gene_seeds()

## Connections
- [[GeneSeed]] - `references` [EXTRACTED]
- [[GeneTemplate_1]] - `references` [EXTRACTED]
- [[QuerySet]] - `references` [EXTRACTED]
- [[_load_exhaustive_templates()]] - `calls` [EXTRACTED]
- [[_load_miner_seed_templates()]] - `calls` [EXTRACTED]
- [[build_genetic_sample_seed_snapshot()]] - `calls` [INFERRED]
- [[expand_gene_templates_with_fluid_clones()]] - `calls` [INFERRED]
- [[genetic_sample_gene_export.py]] - `contains` [EXTRACTED]
- [[queryset_has_miner_seed_v2()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/GeneTemplate