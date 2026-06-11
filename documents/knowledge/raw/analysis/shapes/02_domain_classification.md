# Domain Classification — `shapes.json`

## Envelope

| Path | Classification |
| ---- | -------------- |
| `stable_id` | source metadata (unique here; still prefer `Hash` / `operation_uid` for domain) |
| `source_type_name` | source metadata (`ShapeDefinition`) |
| `source_guid`, `source_path` | source metadata |
| `display_name_key` | source metadata (`#N` labels) |
| `simulation_parameters` | source metadata |
| `definition_snapshot` | domain payload root |

## Definition (directly under snapshot)

| Path | Classification |
| ---- | -------------- |
| `UniqueOperationId` | entity attribute |
| `Hash` | entity attribute (canonical string) |
| `PartCount` | entity attribute |
| `Id.Uid` | entity attribute |
| `Layers[]` | ordered child record |
| `Layers[i].Parts[j].Shape` | relationship → shape_component_kind |
| `Layers[i].Parts[j].Color` | relationship → fluid_color |
| `Layers[i].Parts[j].Shape.instance_id` | runtime metadata |
| `$type` | source metadata |

## Rejected

| Label | Reason |
| ----- | ------ |
| `ShapeDefinition` model | `$type` / source_type_name |
| `MetaShapeSubPart` table | Unity wrapper |
| `#132` as PK | display_name_key |

## Entity

**Shape recipe** (1,170 instances) — same domain as `items.json`, expanded catalog.
