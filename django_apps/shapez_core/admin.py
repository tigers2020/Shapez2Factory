"""Admin registrations for shapez_core (IVVD basedata)."""

from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from django_apps.shapez_core import models as m
from django_apps.shapez_core.admin_filters import (
    GameIdentifierCategoryKeyFilter,
    GameIdentifierReleaseVersionFilter,
)
from django_apps.shapez_core.admin_identifier_sprite import identifier_sprite_admin_preview


class _IvvdReadOnlyAdminMixin:
    """IVVD rows are created by import pipeline; admin is browse-first."""

    def has_add_permission(self, _request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, _obj: Any | None = None) -> bool:
        return bool(request.user.is_superuser)


class ShapezBasedataDocumentInline(admin.TabularInline):
    model = m.ShapezBasedataDocument
    extra = 0
    can_delete = False
    show_change_link = True
    fields = (
        "source_relative_path",
        "document_kind",
        "logical_key",
        "byte_size",
        "schema_valid",
        "sha256",
        "imported_at",
    )
    readonly_fields = fields
    ordering = ("source_relative_path",)


@admin.register(m.ShapezBasedataRelease)
class ShapezBasedataReleaseAdmin(_IvvdReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "game_version",
        "integrity_status",
        "document_count",
        "imported_at",
        "sealed_at",
        "hash_prefix",
    )
    list_display_links = ("game_version",)
    list_filter = ("integrity_status", "seal_algorithm")
    raw_id_fields = ("integrity_status",)
    search_fields = ("notes", "release_integrity_hash")
    readonly_fields = (
        "game_version",
        "imported_at",
        "notes",
        "document_count",
        "integrity_status",
        "sealed_at",
        "release_integrity_hash",
        "seal_algorithm",
        "seal_input_canonical_json",
    )
    inlines = (ShapezBasedataDocumentInline,)

    @staticmethod
    def hash_prefix(obj: m.ShapezBasedataRelease) -> str:
        h = (obj.release_integrity_hash or "").strip()
        return f"{h[:16]}…" if len(h) > 16 else h or "—"

    hash_prefix.short_description = "Release hash"


@admin.register(m.ShapezBasedataDocument)
class ShapezBasedataDocumentAdmin(_IvvdReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "source_relative_path",
        "release",
        "document_kind",
        "logical_key",
        "byte_size",
        "schema_valid",
        "sha256_short",
        "imported_at",
        "id",
    )
    list_display_links = ("source_relative_path",)
    list_select_related = ("release", "document_kind")
    list_filter = (
        ("document_kind", admin.RelatedOnlyFieldListFilter),
        "schema_valid",
        ("release", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ("source_relative_path", "logical_key", "sha256")
    raw_id_fields = ("release",)
    autocomplete_fields = ("document_kind",)
    readonly_fields = (
        "release",
        "document_kind",
        "logical_key",
        "source_relative_path",
        "byte_size",
        "sha256",
        "raw_text",
        "compressed_raw_blob",
        "raw_compression_codec",
        "payload",
        "imported_at",
        "schema_valid",
        "schema_validation_errors",
        "validated_at",
        "schema_version",
    )
    fieldsets = (
        (None, {"fields": ("release", "document_kind", "logical_key", "source_relative_path")}),
        ("Integrity", {"fields": ("byte_size", "sha256", "imported_at")}),
        (
            "Schema",
            {
                "fields": (
                    "schema_valid",
                    "schema_validation_errors",
                    "validated_at",
                    "schema_version",
                )
            },
        ),
        (
            "Storage",
            {
                "fields": ("raw_compression_codec", "compressed_raw_blob"),
                "classes": ("collapse",),
            },
        ),
        ("Raw + parsed", {"fields": ("raw_text", "payload"), "classes": ("collapse",)}),
    )

    @staticmethod
    def sha256_short(obj: m.ShapezBasedataDocument) -> str:
        h = (obj.sha256 or "").strip()
        return f"{h[:12]}…" if len(h) > 12 else h or "—"

    sha256_short.short_description = "SHA-256"


@admin.register(m.ShapezIdentifierCategory)
class ShapezIdentifierCategoryAdmin(_IvvdReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("key", "release", "sort_order", "label", "id")
    list_display_links = ("key",)
    list_select_related = ("release",)
    list_filter = (
        ("release", admin.RelatedOnlyFieldListFilter),
        "key",
    )
    search_fields = ("key", "label")
    raw_id_fields = ("release",)
    readonly_fields = ("release", "key", "sort_order", "label")


@admin.register(m.ShapezIvvdSeverity)
class ShapezIvvdSeverityAdmin(_IvvdReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "label", "sort_order")
    ordering = ("sort_order", "code")
    search_fields = ("code", "label")


@admin.register(m.ShapezIvvdValidationPhase)
class ShapezIvvdValidationPhaseAdmin(_IvvdReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "label", "sort_order")
    ordering = ("sort_order", "code")
    search_fields = ("code", "label")


@admin.register(m.ShapezIvvdLifecycleStatus)
class ShapezIvvdLifecycleStatusAdmin(_IvvdReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "label", "sort_order")
    ordering = ("sort_order", "code")
    search_fields = ("code", "label")


@admin.register(m.ShapezIvvdDocumentKind)
class ShapezIvvdDocumentKindAdmin(_IvvdReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "label", "sort_order")
    ordering = ("sort_order", "code")
    search_fields = ("code", "label")


@admin.register(m.ShapezIvvdArtifactType)
class ShapezIvvdArtifactTypeAdmin(_IvvdReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "label", "sort_order")
    ordering = ("sort_order", "code")
    search_fields = ("code", "label")


@admin.register(m.ShapezIntegrityIssueCode)
class ShapezIntegrityIssueCodeAdmin(_IvvdReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("code", "summary", "default_severity")
    list_filter = (("default_severity", admin.RelatedOnlyFieldListFilter),)
    search_fields = ("code", "summary")
    autocomplete_fields = ("default_severity",)
    readonly_fields = ("code", "summary", "default_severity")


@admin.register(m.ShapezGameIdentifier)
class ShapezGameIdentifierAdmin(_IvvdReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "value",
        "sprite_preview_thumb",
        "sprite_static_relpath",
        "release",
        "identifier_category",
        "normalized_value",
        "id",
    )
    list_display_links = ("value",)
    list_select_related = ("release", "identifier_category")
    list_filter = (
        GameIdentifierCategoryKeyFilter,
        GameIdentifierReleaseVersionFilter,
    )
    search_fields = ("value", "normalized_value", "identifier_category__key")
    raw_id_fields = ("release",)
    autocomplete_fields = ("identifier_category",)
    readonly_fields = (
        "release",
        "identifier_category",
        "value",
        "normalized_value",
        "sprite_static_relpath",
        "sprite_preview",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "release",
                    "identifier_category",
                    "value",
                    "normalized_value",
                ),
            },
        ),
        (
            "Lab sprite",
            {
                "fields": (
                    "sprite_static_relpath",
                    "sprite_preview",
                ),
            },
        ),
    )

    @admin.display(description="Sprite")
    def sprite_preview_thumb(self, obj: m.ShapezGameIdentifier) -> str:
        return identifier_sprite_admin_preview(obj.sprite_static_relpath, img_px=32)

    @admin.display(description="Sprite preview")
    def sprite_preview(self, obj: m.ShapezGameIdentifier) -> str:
        return identifier_sprite_admin_preview(
            obj.sprite_static_relpath,
            img_px=64,
            show_relpath=True,
        )


@admin.register(m.ShapezValidationRun)
class ShapezValidationRunAdmin(_IvvdReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "run_label",
        "release",
        "validation_phase",
        "success",
        "duration_ms",
        "validator_version",
        "created_at",
        "id",
    )
    list_display_links = ("run_label",)
    list_select_related = ("release", "validation_phase")
    list_filter = (
        "validation_phase",
        "success",
        ("release", admin.RelatedOnlyFieldListFilter),
    )
    raw_id_fields = ("release",)
    autocomplete_fields = ("validation_phase",)
    search_fields = ("validator_version", "summary_json")
    readonly_fields = (
        "release",
        "validation_phase",
        "success",
        "duration_ms",
        "summary_json",
        "validator_version",
        "created_at",
    )

    @staticmethod
    def run_label(obj: m.ShapezValidationRun) -> str:
        gv = obj.release.game_version if obj.release_id else "?"
        ph = obj.validation_phase_id or "?"
        return f"v{gv} · {ph} · #{obj.pk}"

    run_label.short_description = "Run"


@admin.register(m.ShapezIntegrityIssue)
class ShapezIntegrityIssueAdmin(_IvvdReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "issue_type",
        "message_preview",
        "release",
        "validation_run",
        "severity",
        "is_superseded",
        "related_identifier",
        "id",
    )
    list_display_links = ("issue_type",)
    list_select_related = (
        "release",
        "validation_run",
        "validation_run__validation_phase",
        "issue_type",
        "severity",
        "document",
        "document__document_kind",
    )
    list_filter = (
        ("validation_run__validation_phase", admin.RelatedOnlyFieldListFilter),
        ("document__document_kind", admin.RelatedOnlyFieldListFilter),
        ("severity", admin.RelatedOnlyFieldListFilter),
        "is_superseded",
        ("issue_type", admin.RelatedOnlyFieldListFilter),
        ("release", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ("issue_type__code", "message", "related_identifier", "json_path")
    raw_id_fields = ("release", "validation_run", "superseded_by_run")
    autocomplete_fields = ("document", "issue_type")
    readonly_fields = (
        "release",
        "validation_run",
        "document",
        "severity",
        "issue_type",
        "json_path",
        "message",
        "related_identifier",
        "is_superseded",
        "superseded_by_run",
    )

    @staticmethod
    def message_preview(obj: m.ShapezIntegrityIssue) -> str:
        msg = (obj.message or "").strip()
        return (msg[:120] + "…") if len(msg) > 120 else msg or "—"

    message_preview.short_description = "Message"


@admin.register(m.ShapezCanonicalArtifact)
class ShapezCanonicalArtifactAdmin(_IvvdReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "link_summary",
        "release",
        "artifact_type",
        "derivation_step",
        "source_document",
        "parent_artifact",
        "created_at",
        "id",
    )
    list_display_links = ("link_summary",)
    list_select_related = ("release", "artifact_type", "source_document", "parent_artifact")
    list_filter = (
        ("artifact_type", admin.RelatedOnlyFieldListFilter),
        ("release", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ("derivation_step", "artifact_type__code", "artifact_type__label")
    raw_id_fields = ("release", "parent_artifact")
    autocomplete_fields = ("artifact_type", "source_document")
    readonly_fields = (
        "release",
        "artifact_type",
        "source_document",
        "derivation_step",
        "parent_artifact",
        "payload",
        "created_at",
    )

    @staticmethod
    def link_summary(obj: m.ShapezCanonicalArtifact) -> str:
        step = (obj.derivation_step or "").strip()
        if step:
            return step
        return str(obj.artifact_type)

    link_summary.short_description = "Step / type"
