"""Browse-first game_data admin dashboard grouped by taxonomy."""

from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from django_apps.game_data.browse.registry import (
    build_browse_groups,
    validate_section_admin_targets,
)


@require_GET
@staff_member_required
def game_data_browse(request):
    groups = build_browse_groups()
    section_errors = validate_section_admin_targets()
    missing_count = sum(
        1 for group in groups for section in group.sections if section.missing_admin
    )
    return render(
        request,
        "admin/game_data/browse_index.html",
        {
            "title": "Game data browse",
            "groups": groups,
            "section_errors": section_errors,
            "missing_count": missing_count,
        },
    )
