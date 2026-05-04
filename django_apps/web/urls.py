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
