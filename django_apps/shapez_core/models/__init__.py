"""ORM models for shapez_core (IVVD basedata + domain persistence)."""

from django_apps.shapez_core.models.artifacts import ShapezCanonicalArtifact
from django_apps.shapez_core.models.documents import ShapezBasedataDocument
from django_apps.shapez_core.models.identifiers import (
    ShapezGameIdentifier,
    ShapezIdentifierCategory,
)
from django_apps.shapez_core.models.integrity import ShapezIntegrityIssue
from django_apps.shapez_core.models.ivvd_lookups import (
    ShapezIntegrityIssueCode,
    ShapezIvvdArtifactType,
    ShapezIvvdDocumentKind,
    ShapezIvvdLifecycleStatus,
    ShapezIvvdSeverity,
    ShapezIvvdValidationPhase,
)
from django_apps.shapez_core.models.release import ShapezBasedataRelease
from django_apps.shapez_core.models.validation import ShapezValidationRun

__all__ = [
    "ShapezBasedataDocument",
    "ShapezBasedataRelease",
    "ShapezCanonicalArtifact",
    "ShapezGameIdentifier",
    "ShapezIdentifierCategory",
    "ShapezIntegrityIssue",
    "ShapezIntegrityIssueCode",
    "ShapezIvvdArtifactType",
    "ShapezIvvdDocumentKind",
    "ShapezIvvdLifecycleStatus",
    "ShapezIvvdSeverity",
    "ShapezIvvdValidationPhase",
    "ShapezValidationRun",
]
