from django.urls import path
from django.views.generic import RedirectView

from django_apps.web import views

app_name = "web"

urlpatterns = [
    path("", views.home, name="home"),
    path("gallery/", views.gallery, name="gallery"),
    path("demo/", views.demo, name="demo"),
    path("support/", views.support, name="support"),
    path("solver/", views.solver, name="solver"),
    path("solver/pattern-lab/", views.pattern_lab, name="pattern-lab"),
    path(
        "asteroid-miner-layout/projects/",
        views.asteroid_miner_layout_create_project,
        name="asteroid-miner-layout-projects-create",
    ),
    path(
        "asteroid-miner-layout/replay-frame-cell/",
        views.asteroid_miner_layout_replay_frame_cell,
        name="asteroid-miner-layout-replay-frame-cell",
    ),
    path(
        "asteroid-miner-layout/p/<slug:slug>/run-solver/",
        views.asteroid_miner_layout_project_run_solver,
        name="asteroid-miner-layout-project-run-solver",
    ),
    path(
        "asteroid-miner-layout/p/<slug:slug>/solver-runs/<int:run_id>/status/",
        views.asteroid_miner_layout_project_solver_run_status,
        name="asteroid-miner-layout-project-solver-run-status",
    ),
    path(
        "asteroid-miner-layout/p/<slug:slug>/solver-runs/<int:run_id>/lab-replay/",
        views.asteroid_miner_layout_project_solver_run_lab_replay,
        name="asteroid-miner-layout-project-solver-run-lab-replay",
    ),
    path(
        "asteroid-miner-layout/p/<slug:slug>/reset-map/",
        views.asteroid_miner_layout_project_reset_map,
        name="asteroid-miner-layout-project-reset-map",
    ),
    path(
        "asteroid-miner-layout/p/<slug:slug>/",
        views.asteroid_miner_layout_project,
        name="asteroid-miner-layout-project",
    ),
    path(
        "asteroid-miner-layout/",
        views.asteroid_miner_layout_solver,
        name="asteroid-miner-layout",
    ),
    path(
        "internal/staff/shape-part-sprites/manifest/",
        views.shape_part_sprite_manifest,
        name="shape-part-sprite-manifest",
    ),
    path(
        "internal/staff/macro-patterns/api/graph-preview/warm/",
        views.macro_pattern_staff_api_graph_preview_warm,
        name="macro-pattern-staff-api-graph-preview-warm",
    ),
    path(
        "signup/",
        RedirectView.as_view(pattern_name="account_signup", permanent=False),
        name="sign-up",
    ),
    path(
        "login/",
        RedirectView.as_view(pattern_name="account_login", permanent=False),
        name="log-in",
    ),
    path(
        "logout/",
        RedirectView.as_view(pattern_name="account_logout", permanent=False),
        name="log-out",
    ),
    path(
        "internal/graph-preview-cache/<str:filename>",
        views.graph_preview_cache,
        name="graph_preview_cache",
    ),
    path(
        "solve/",
        RedirectView.as_view(pattern_name="web:solver", permanent=False, query_string=True),
    ),
]
