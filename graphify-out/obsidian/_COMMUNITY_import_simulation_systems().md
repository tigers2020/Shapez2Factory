---
type: community
cohesion: 0.14
members: 21
---

# import_simulation_systems()

**Cohesion:** 0.14 - loosely connected
**Members:** 21 nodes

## Members
- [[Classify simulation_parameters top-level keys (registry only; no values).]] - rationale - django_apps/game_data/services/simulation_parameter_classify.py
- [[Detect simulation_parameters profile from dump row (simulation_parameters only).]] - rationale - django_apps/game_data/services/simulation_profile_detect.py
- [[ParameterClassification]] - code - django_apps/game_data/services/simulation_parameter_classify.py
- [[Record delegatereflectionruntime keys on UnknownProperty (preview+hash only).]] - rationale - django_apps/game_data/services/simulation_parameter_registry.py
- [[Record top-level keys for one system; drop stale occurrences. Returns key names]] - rationale - django_apps/game_data/services/simulation_parameter_registry.py
- [[SimulationSystemParameterKey_1]] - code - django_apps/game_data/services/simulation_parameter_registry.py
- [[Sync simulation_parameters top-level keys into ParameterKey  Occurrence tables.]] - rationale - django_apps/game_data/services/simulation_parameter_registry.py
- [[_ensure_parameter_key()]] - code - django_apps/game_data/services/simulation_parameter_registry.py
- [[_reconcile_occurrence_count()]] - code - django_apps/game_data/services/simulation_parameter_registry.py
- [[_source_path_for_key()]] - code - django_apps/game_data/services/simulation_parameter_registry.py
- [[classify_simulation_parameter_key()]] - code - django_apps/game_data/services/simulation_parameter_classify.py
- [[detect_simulation_profile_key()]] - code - django_apps/game_data/services/simulation_profile_detect.py
- [[import_simulation_systems()]] - code - django_apps/game_data/importers/simulation_systems.py
- [[is_non_domain_simulation_parameter()]] - code - django_apps/game_data/services/simulation_parameter_classify.py
- [[reason_code_for_simulation_parameter()]] - code - django_apps/game_data/services/simulation_parameter_classify.py
- [[reconcile_parameter_key_counts()]] - code - django_apps/game_data/services/simulation_parameter_registry.py
- [[simulation_parameter_classify.py]] - code - django_apps/game_data/services/simulation_parameter_classify.py
- [[simulation_parameter_registry.py]] - code - django_apps/game_data/services/simulation_parameter_registry.py
- [[simulation_profile_detect.py]] - code - django_apps/game_data/services/simulation_profile_detect.py
- [[sync_ignored_simulation_parameters()]] - code - django_apps/game_data/services/simulation_parameter_registry.py
- [[sync_simulation_parameter_registry()]] - code - django_apps/game_data/services/simulation_parameter_registry.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/import_simulation_systems
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_Any]]
- 3 edges to [[_COMMUNITY_ImportContext]]
- 3 edges to [[_COMMUNITY__import_connectable_attachment()]]
- 2 edges to [[_COMMUNITY_simulation_speed_extract.py]]
- 1 edge to [[_COMMUNITY_GameDataImporter]]
- 1 edge to [[_COMMUNITY_parse_simulation_clr()]]

## Top bridge nodes
- [[import_simulation_systems()]] - degree 13, connects to 6 communities
- [[sync_ignored_simulation_parameters()]] - degree 9, connects to 2 communities
- [[sync_simulation_parameter_registry()]] - degree 7, connects to 2 communities
- [[detect_simulation_profile_key()]] - degree 3, connects to 1 community