"""Admin list filters (dropdown-style for IVVD changelists)."""

from __future__ import annotations

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from django_apps.shapez_core.models import ShapezBasedataRelease
from django_apps.shapez_core.services.basedata_import_service import IDENTIFIER_JSON_KEYS


class _DropdownSimpleListFilter(admin.SimpleListFilter):
    """Renders as ``<select>`` via ``admin/shapez_core/dropdown_list_filter.html``."""

    template = "admin/shapez_core/dropdown_list_filter.html"


class GameIdentifierCategoryKeyFilter(_DropdownSimpleListFilter):
    title = _("Category key")
    parameter_name = "category_key"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> list[tuple[str, str]]:
        return [(k, k) for k in sorted(IDENTIFIER_JSON_KEYS)]

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        if not self.value():
            return queryset
        return queryset.filter(identifier_category__key=self.value())


class GameIdentifierReleaseVersionFilter(_DropdownSimpleListFilter):
    title = _("Release (version)")
    parameter_name = "release_version"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> list[tuple[str, str]]:
        versions = (
            ShapezBasedataRelease.objects.filter(game_identifiers__isnull=False)
            .order_by("-game_version")
            .values_list("game_version", flat=True)
            .distinct()
        )
        return [(str(v), f"v{v}") for v in versions]

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        if not self.value():
            return queryset
        return queryset.filter(release__game_version=int(self.value()))
