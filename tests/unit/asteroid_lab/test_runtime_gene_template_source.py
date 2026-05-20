"""Contract tests for GeneTemplateSourceMetadata and related enums."""

from __future__ import annotations

from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_GENE_TEMPLATE_SOURCE_KEY,
)
from django_apps.asteroid_lab.services.runtime_gene_template_source import (
    GeneTemplateLoadErrorCode,
    GeneTemplateSourceKind,
    GeneTemplateSourceMetadata,
)


def test_source_kind_wire_value() -> None:
    assert GeneTemplateSourceKind.GENETIC_SAMPLE_DB.value == "genetic_sample_db"


def test_load_error_code_values() -> None:
    assert GeneTemplateLoadErrorCode.NO_GENE_TEMPLATES_IN_DB.value == "no_gene_templates_in_db"
    assert (
        GeneTemplateLoadErrorCode.GENE_TEMPLATE_EXPORT_FAILED.value == "gene_template_export_failed"
    )


def test_metadata_to_json_dict_round_trip() -> None:
    meta = GeneTemplateSourceMetadata(
        source=GeneTemplateSourceKind.GENETIC_SAMPLE_DB,
        gene_count=3,
        generator_version="exhaustive_sample_gene_v1",
        gene_ids=("g1", "g2", "g3"),
        export_skipped_count=0,
        export_error_codes=(),
    )
    d = meta.to_json_dict()
    assert d["source"] == "genetic_sample_db"
    assert d["gene_count"] == 3
    assert d["generator_version"] == "exhaustive_sample_gene_v1"
    assert d["gene_ids"] == ["g1", "g2", "g3"]
    assert d["export_skipped_count"] == 0
    assert d["export_error_codes"] == []
    assert "gene_key_filter" not in d


def test_metadata_to_json_dict_with_filter() -> None:
    meta = GeneTemplateSourceMetadata(
        source=GeneTemplateSourceKind.GENETIC_SAMPLE_DB,
        gene_count=1,
        generator_version="exhaustive_sample_gene_v1",
        gene_ids=("g1",),
        gene_key_filter=("g1", "g2"),
    )
    d = meta.to_json_dict()
    assert d["gene_key_filter"] == ["g1", "g2"]


def test_metadata_with_skip_and_errors() -> None:
    meta = GeneTemplateSourceMetadata(
        source=GeneTemplateSourceKind.GENETIC_SAMPLE_DB,
        gene_count=2,
        generator_version="exhaustive_sample_gene_v1",
        gene_ids=("ga", "gb"),
        export_skipped_count=1,
        export_error_codes=("gene_template_export_failed",),
    )
    d = meta.to_json_dict()
    assert d["export_skipped_count"] == 1
    assert d["export_error_codes"] == ["gene_template_export_failed"]


def test_config_key_constant_is_stable() -> None:
    assert SOLVER_RUN_CONFIG_GENE_TEMPLATE_SOURCE_KEY == "gene_template_source"
