"""Django views for ``web`` (staff macro tools vs public pages)."""

from django_apps.web.views.macro_staff import (
    macro_pattern_graph,
    macro_pattern_list,
    macro_pattern_new,
    macro_pattern_recipe_edit,
    macro_pattern_staff_api_catalog,
    macro_pattern_staff_api_graph_preview_warm,
    macro_pattern_staff_api_recipe_detail,
    macro_pattern_staff_api_recipe_graph_recompute,
    macro_pattern_staff_api_recipes_create,
    shape_part_sprite_manifest,
    staff_site_required,
)
from django_apps.web.views.public_pages import (
    asteroid_optimizer,
    demo,
    gallery,
    graph_preview_cache,
    home,
    pattern_lab,
    solver,
    support,
)

__all__ = [
    "asteroid_optimizer",
    "demo",
    "gallery",
    "graph_preview_cache",
    "home",
    "macro_pattern_graph",
    "macro_pattern_list",
    "macro_pattern_new",
    "macro_pattern_recipe_edit",
    "macro_pattern_staff_api_catalog",
    "macro_pattern_staff_api_graph_preview_warm",
    "macro_pattern_staff_api_recipe_detail",
    "macro_pattern_staff_api_recipe_graph_recompute",
    "macro_pattern_staff_api_recipes_create",
    "pattern_lab",
    "shape_part_sprite_manifest",
    "solver",
    "staff_site_required",
    "support",
]
