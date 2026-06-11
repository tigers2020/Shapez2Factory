---
type: community
cohesion: 0.16
members: 26
---

# GeneTemplate

**Cohesion:** 0.16 - loosely connected
**Members:** 26 nodes

## Members
- [[Build a ``genetic_sample_seed_v1`` payload from a ``GeneSeed`` queryset.]] - rationale - django_apps/asteroid_lab/services/genetic_sample_catalog_snapshot.py
- [[Convert GeneSeed ORM rows to GeneTemplate objects (adapter boundary, ORM allowed]] - rationale - django_apps/asteroid_lab/services/genetic_sample_gene_export.py
- [[ExtensionAttachment_1]] - code - django_apps/asteroid_lab/genetic_sample/gene_template_loader.py
- [[GeneTemplate_1]] - code - django_apps/asteroid_lab/services/miner_gene_seed_template.py
- [[GeneTemplateExportErrorCode]] - code - django_apps/asteroid_lab/services/genetic_sample_gene_export.py
- [[GeneratedSampleGene_1]] - code - django_apps/asteroid_lab/services/genetic_sample_gene_export.py
- [[Load ``GeneTemplate`` from JSON fixtures or ``GeneratedSampleGene`` (no Django O]] - rationale - django_apps/asteroid_lab/genetic_sample/gene_template_loader.py
- [[ORM - GeneticSampleSeedSnapshot payload serializer (adapter boundary; ORM allow]] - rationale - django_apps/asteroid_lab/services/genetic_sample_catalog_snapshot.py
- [[QuerySet]] - code - django_apps/shapez_core/admin_filters.py
- [[_build_exhaustive_cache()]] - code - django_apps/asteroid_lab/services/genetic_sample_gene_export.py
- [[_entry_from_template()]] - code - django_apps/asteroid_lab/services/genetic_sample_catalog_snapshot.py
- [[_extension_attachments_from_generated()]] - code - django_apps/asteroid_lab/genetic_sample/gene_template_loader.py
- [[_load_exhaustive_templates()]] - code - django_apps/asteroid_lab/services/genetic_sample_gene_export.py
- [[_load_miner_seed_templates()]] - code - django_apps/asteroid_lab/services/genetic_sample_gene_export.py
- [[_parse_coord_pair()]] - code - django_apps/asteroid_lab/genetic_sample/gene_template_loader.py
- [[_parse_direction()]] - code - django_apps/asteroid_lab/genetic_sample/gene_template_loader.py
- [[build_genetic_sample_seed_snapshot()]] - code - django_apps/asteroid_lab/services/genetic_sample_catalog_snapshot.py
- [[gene_template_from_gene_seed()]] - code - django_apps/asteroid_lab/services/genetic_sample_gene_export.py
- [[gene_template_from_generated_sample()]] - code - django_apps/asteroid_lab/genetic_sample/gene_template_loader.py
- [[gene_template_loader.py]] - code - django_apps/asteroid_lab/genetic_sample/gene_template_loader.py
- [[genetic_sample_catalog_snapshot.py]] - code - django_apps/asteroid_lab/services/genetic_sample_catalog_snapshot.py
- [[genetic_sample_gene_export.py]] - code - django_apps/asteroid_lab/services/genetic_sample_gene_export.py
- [[load_gene_templates_from_gene_seeds()]] - code - django_apps/asteroid_lab/services/genetic_sample_gene_export.py
- [[load_gene_templates_from_json()]] - code - django_apps/asteroid_lab/genetic_sample/gene_template_loader.py
- [[parse_gene_template_record()]] - code - django_apps/asteroid_lab/genetic_sample/gene_template_loader.py
- [[queryset_has_miner_seed_v2()]] - code - django_apps/asteroid_lab/services/genetic_sample_gene_export.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/GeneTemplate
SORT file.name ASC
```

## Connections to other communities
- 6 edges to [[_COMMUNITY_GeneSeed]]
- 6 edges to [[_COMMUNITY_gene_template_from_miner_gene_seed()]]
- 5 edges to [[_COMMUNITY_Any]]
- 3 edges to [[_COMMUNITY_expand_gene_templates_with_fluid_clones(]]
- 2 edges to [[_COMMUNITY_HttpRequest]]
- 1 edge to [[_COMMUNITY_generate_candidates()]]
- 1 edge to [[_COMMUNITY_Coord]]
- 1 edge to [[_COMMUNITY_exhaustive_generator.py]]
- 1 edge to [[_COMMUNITY_gene_template.py]]
- 1 edge to [[_COMMUNITY_Path]]
- 1 edge to [[_COMMUNITY_StrEnum]]
- 1 edge to [[_COMMUNITY_entry_result_to_json_dict()]]
- 1 edge to [[_COMMUNITY_Enum]]

## Top bridge nodes
- [[build_genetic_sample_seed_snapshot()]] - degree 9, connects to 3 communities
- [[GeneTemplate_1]] - degree 11, connects to 2 communities
- [[gene_template_from_gene_seed()]] - degree 10, connects to 2 communities
- [[load_gene_templates_from_gene_seeds()]] - degree 9, connects to 2 communities
- [[_load_exhaustive_templates()]] - degree 8, connects to 2 communities