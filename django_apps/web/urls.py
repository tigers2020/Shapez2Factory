from django.urls import path
from django.views.generic import RedirectView

from django_apps.web import views

app_name = "web"

urlpatterns = [
    path("", views.home, name="home"),
    path("gallery/", views.gallery, name="gallery"),
    path("demo/", views.demo, name="demo"),
    path("support/", views.support, name="support"),
    path("asteroid/", views.asteroid_optimizer, name="asteroid"),
    path("solver/", views.solver, name="solver"),
    path("solver/pattern-lab/", views.pattern_lab, name="pattern-lab"),
    path(
        "asteroid-miner-layout/",
        views.asteroid_miner_layout_solver,
        name="asteroid-miner-layout",
    ),
    path(
        "internal/staff/macro-patterns/",
        views.macro_pattern_list,
        name="macro-pattern-staff",
    ),
    path(
        "internal/staff/macro-patterns/new/",
        views.macro_pattern_new,
        name="macro-pattern-new",
    ),
    path(
        "internal/staff/macro-patterns/<int:pk>/edit/",
        views.macro_pattern_recipe_edit,
        name="macro-pattern-recipe-edit",
    ),
    path(
        "internal/staff/macro-patterns/<int:pk>/graph/",
        views.macro_pattern_graph,
        name="macro-pattern-graph",
    ),
    path(
        "internal/staff/macro-patterns/api/graph-preview/warm/",
        views.macro_pattern_staff_api_graph_preview_warm,
        name="macro-pattern-staff-api-graph-preview-warm",
    ),
    path(
        "internal/staff/shape-part-sprites/manifest/",
        views.shape_part_sprite_manifest,
        name="shape-part-sprite-manifest",
    ),
    path(
        "internal/staff/macro-patterns/api/catalog/",
        views.macro_pattern_staff_api_catalog,
        name="macro-pattern-staff-api-catalog",
    ),
    path(
        "internal/staff/macro-patterns/api/recipes/",
        views.macro_pattern_staff_api_recipes_create,
        name="macro-pattern-staff-api-recipes-create",
    ),
    path(
        "internal/staff/macro-patterns/api/recipes/<int:pk>/graph/recompute/",
        views.macro_pattern_staff_api_recipe_graph_recompute,
        name="macro-pattern-staff-api-recipe-graph-recompute",
    ),
    path(
        "internal/staff/macro-patterns/api/recipes/<int:pk>/",
        views.macro_pattern_staff_api_recipe_detail,
        name="macro-pattern-staff-api-recipe-detail",
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
