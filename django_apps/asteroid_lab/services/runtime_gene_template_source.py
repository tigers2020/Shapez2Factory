"""Gene template source contracts for the runtime loader (DB-only path)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class GeneTemplateSourceKind(StrEnum):
    """Where run-time gene templates come from (wire string, persisted in config_json)."""

    GENETIC_SAMPLE_DB = "genetic_sample_db"


class GeneTemplateLoadErrorCode(StrEnum):
    """Structured failure codes for gene template loading (never free-form strings)."""

    NO_GENE_TEMPLATES_IN_DB = "no_gene_templates_in_db"
    GENE_TEMPLATE_EXPORT_FAILED = "gene_template_export_failed"


@dataclass(frozen=True, slots=True)
class GeneTemplateSourceMetadata:
    """Provenance record written to SolverRun.config_json and HTTP response.

    Output/debug only — must NOT be used as solver algorithm input.
    """

    source: GeneTemplateSourceKind
    gene_count: int
    generator_version: str
    gene_ids: tuple[str, ...]
    export_skipped_count: int = 0
    export_error_codes: tuple[str, ...] = field(default_factory=tuple)
    gene_key_filter: tuple[str, ...] | None = None

    def to_json_dict(self) -> dict[str, object]:
        d: dict[str, object] = {
            "source": self.source.value,
            "gene_count": self.gene_count,
            "generator_version": self.generator_version,
            "gene_ids": list(self.gene_ids),
            "export_skipped_count": self.export_skipped_count,
            "export_error_codes": list(self.export_error_codes),
        }
        if self.gene_key_filter is not None:
            d["gene_key_filter"] = list(self.gene_key_filter)
        return d


__all__ = [
    "GeneTemplateLoadErrorCode",
    "GeneTemplateSourceKind",
    "GeneTemplateSourceMetadata",
]
