"""Canonical import-metadata names mapped to existing Django models (no parallel tables)."""

from __future__ import annotations

from django.apps import apps
from django.db.models import Model

# Logical / schema-doc names → Django model class names (game_data app).
CANONICAL_IMPORT_MODELS: dict[str, str] = {
    "game_data_import_batch": "ImportBatch",
    "game_data_artifact_checksum": "ArtifactChecksum",
    "export_warning": "ExportWarning",
    "export_incomplete_section": "ExportIncompleteSection",
    "localization_export_status": "LocalizationExportStatus",
    "source_object_record": "SourceObject",
    "unknown_property": "UnknownProperty",
}

REJECTED_PARALLEL_MODELS = frozenset(
    {
        "GameDataImportRun",
        "GameDataSourceFile",
        "GameDataIgnoredField",
        "GameDataUnknownFieldOccurrence",
        "GameDataSchemaFinding",
        "ImportAudit",
    }
)


def model_for_canonical(canonical_name: str) -> type[Model]:
    class_name = CANONICAL_IMPORT_MODELS[canonical_name]
    return apps.get_model("game_data", class_name)
