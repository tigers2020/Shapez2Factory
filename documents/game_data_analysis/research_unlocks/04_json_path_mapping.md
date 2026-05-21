# JSON Path Mapping — `research_unlocks.json`

| JSON path | Observed meaning | Classification | Target table | Target column | Notes |
| --------- | ---------------- | -------------- | ------------ | ------------- | ----- |
| `[i].source_type_name` | Row kind | enum | (discriminator) | — | routes importer |
| `[i].stable_id` | Dump hash | source metadata | audit | `dump_stable_id` | not unique |
| `[i].definition_snapshot.Id` | Upgrade key string | entity attribute | `research_upgrade` | `upgrade_key` | UpgradeId rows |
| `[i].definition_snapshot.Id.Id` | Node key | entity attribute | milestone/quest/upgrade tables | `node_key` | dict form |
| `[i].definition_snapshot.Title` | Label | entity attribute | `*_quest` / milestone | `title` | |
| `[i].definition_snapshot.Costs[]` | Costs | ordered child | `research_unlock_cost` | — | |
| `[i].definition_snapshot.Costs[j].ShapeHash` | Shape payment | relationship | `research_unlock_cost` | `shape_hash` | FK items |
| `[i].definition_snapshot.Rewards[]` | Rewards | ordered child | `research_unlock_reward` | — | |
| `[i].definition_snapshot.RequiredUpgrades[]` | Prereqs | relationship | `research_prerequisite` | `required_upgrade_key` | |
| `[i].definition_snapshot.Lines[]` | Milestone lines | ordered child | `research_milestone_line` | — | level only |
| `[i].progression_layout` | Full graph | ordered child | layout index tables | — | manager row |
| `[i].research_config` | Global config | entity attribute | `research_global_config` | scalars | |
| `[i].manager_snapshot` | Runtime handlers | runtime metadata | audit only | — | never FK |
| `[i].simulation_parameters` | Sim params | source metadata | audit / batch | — | |
| `definition_snapshot.*.k__BackingField` | CLR backing | runtime metadata | — | — | skip |
| `Costs[].$type` | Cost DTO type | source metadata | — | — | enum `ResearchCostShapes` |
