from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.domain.operations import OperationType


def test_operation_catalog_covers_all_operation_types() -> None:
    assert set(OPERATION_CATALOG) == set(OperationType)


def test_operation_catalog_definitions_are_renderable() -> None:
    for operation_type, definition in OPERATION_CATALOG.items():
        assert definition.type is operation_type
        assert definition.label
        assert definition.icon.endswith(".png")
        assert definition.input_count >= 1
        assert definition.output_count >= 1
        assert definition.description
