# Validation Plan — `belts_pipes_transport.json`

Suggested path: `tests/unit/game_data/test_transport_building_registry_import.py`

Fixtures: 3 sampled rows (indices 1, 3, 6, seed `20260521`) + matching `building_variants` snippets.

---

## 1. No orphan FK rows

```python
def test_transport_registry_variant_fk(db, imported_transport):
    for row in TransportBuildingRegistry.objects.all():
        assert BuildingVariant.objects.filter(
            internal_name=row.building_variant.internal_name
        ).exists()
```

```python
def test_building_connector_parent_variant(db, imported_variants):
    assert BuildingConnector.objects.filter(building_variant__isnull=True).count() == 0
```

---

## 2. Unique canonical IDs

```python
def test_transport_stable_id_unique(db, imported_transport):
    assert TransportBuildingRegistry.objects.count() == len(
        set(TransportBuildingRegistry.objects.values_list("stable_id", flat=True))
    )

def test_transport_kind_unique(db, imported_transport):
    kinds = list(TransportBuildingRegistry.objects.values_list("transport_kind", flat=True))
    assert len(kinds) == 9 and len(set(kinds)) == 9
```

---

## 3. All referenced IDs resolve

```python
@pytest.mark.parametrize("internal_name", [
    "BeltPortSenderInternalVariant",
    "FluidPortSenderInternalVariant",
    "WireDefaultForwardInternalVariant",
])
def test_sampled_variant_names_resolve(db, imported_transport, internal_name):
    assert TransportBuildingRegistry.objects.filter(
        building_variant__internal_name=internal_name
    ).exists()
```

```python
def test_snapshot_hash_matches_variant_file(import_service, transport_path, variants_path):
    for dto in import_service.iter_transport(transport_path):
        variant_hash = import_service.variant_hash(variants_path, dto.internal_variant_name)
        assert dto.snapshot_content_hash == variant_hash
```

---

## 4. Enum values are valid

```python
def test_transport_category_enum(db, imported_transport):
    allowed = {"belt", "belt_port", "fluid_port", "pipe", "wire", "signal_port"}
    assert set(
        TransportBuildingRegistry.objects.values_list("transport_category", flat=True)
    ) <= allowed

def test_connector_role_mapped(db, imported_variants):
    assert BuildingConnector.objects.exclude(connector_role__in=ConnectorRole.values).count() == 0
```

---

## 5. Required fields are present

```python
@pytest.mark.parametrize("field", [
    "stable_id", "transport_kind", "display_name_key", "building_variant_id"
])
def test_transport_required_non_null(db, imported_transport, field):
    assert TransportBuildingRegistry.objects.filter(**{f"{field}__isnull": True}).count() == 0
```

---

## 6. Ordered arrays preserve order

```python
def test_connector_ordinal_contiguous(db, variant_belt_port_sender):
    ordinals = list(
        BuildingConnector.objects.filter(building_variant=variant_belt_port_sender)
        .order_by("ordinal")
        .values_list("ordinal", flat=True)
    )
    assert ordinals == list(range(len(ordinals)))
```

```python
def test_source_row_index_stable(import_service, transport_path):
    assert import_service.row_indexes(transport_path) == list(range(9))
```

---

## 7. Same input gives same output

```python
def test_import_idempotent_nine_rows(db, import_twice):
    assert TransportBuildingRegistry.objects.count() == 9
    assert import_twice.duplicate_count == 0

def test_import_idempotent_connector_count(db, import_variants_once):
    # second transport import must not duplicate connectors
    assert BuildingConnector.objects.count() == 13
```

---

## 8. Runtime/debug identifiers are not domain keys

```python
def test_no_model_named_building_definition():
    assert "BuildingDefinition" not in [m.__name__ for m in apps.get_models()]

def test_no_backing_field_columns(db):
    for model in [TransportBuildingRegistry, BuildingConnector]:
        for f in model._meta.fields:
            assert "k__BackingField" not in f.name
```

---

## 9. No primary raw_json dump tables

```python
def test_transport_registry_no_jsonfield(db):
    assert not any(
        isinstance(f, JSONField) for f in TransportBuildingRegistry._meta.fields
    )
```

---

## 10. JSONField only on audit/unknown

```python
def test_jsonfield_only_unknown_property():
    # UnknownProperty may hold JSON; domain tables may not
    ...
```

---

## 11. Sampled objects traceable to schema

```python
@pytest.mark.parametrize("index,kind", [(1, "BeltPortSender"), (3, "FluidPortSender"), (6, "WireForward")])
def test_sampled_transport_kinds(db, imported_transport, index, kind):
    row = TransportBuildingRegistry.objects.get(source_row_index=index)
    assert row.transport_kind == kind
```

```python
def test_belt_port_sender_connector_roles(db, variant_belt_port_sender):
    roles = list(
        BuildingConnector.objects.filter(building_variant=variant_belt_port_sender)
        .order_by("ordinal")
        .values_list("connector_role", flat=True)
    )
    assert roles == [ConnectorRole.ITEM_INPUT, ConnectorRole.BELT_PORT_OUTPUT]
```

---

## 12. Cross-file integrity

```python
def test_nine_transport_kinds_match_file(import_service, transport_path):
    kinds = import_service.transport_kinds(transport_path)
    assert kinds == {
        "ForwardBelt", "BeltPortSender", "BeltPortReceiver",
        "FluidPortSender", "FluidPortReceiver", "PipeForward",
        "WireForward", "WireTransmitterSender", "WireTransmitterReceiver",
    }
```

---

## CI

| Tier | Command |
| ---- | ------- |
| Narrow | `pytest tests/unit/game_data/test_transport_building_registry_import.py -q` |
| Full | `pytest` when game_data app lands |
