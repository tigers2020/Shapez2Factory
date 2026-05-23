"""Django views for ``web`` (public pages and staff utilities)."""

from django_apps.web.views.public_pages import (
    asteroid_miner_layout_create_project,
    asteroid_miner_layout_project,
    asteroid_miner_layout_project_reset_map,
    asteroid_miner_layout_project_run_solver,
    asteroid_miner_layout_replay_frame_cell,
    asteroid_miner_layout_solver,
    demo,
    gallery,
    graph_preview_cache,
    home,
    pattern_lab,
    solver,
    support,
)
from django_apps.web.views.staff_shared import (
    shape_part_sprite_manifest,
    staff_site_required,
)

__all__ = [
    "asteroid_miner_layout_create_project",
    "asteroid_miner_layout_project",
    "asteroid_miner_layout_project_reset_map",
    "asteroid_miner_layout_project_run_solver",
    "asteroid_miner_layout_replay_frame_cell",
    "asteroid_miner_layout_solver",
    "demo",
    "gallery",
    "graph_preview_cache",
    "home",
    "pattern_lab",
    "shape_part_sprite_manifest",
    "solver",
    "staff_site_required",
    "support",
]
