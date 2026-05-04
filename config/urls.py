"""Root URL configuration for the scaffold."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include("django_apps.web.urls")),
    path("api/", include("django_apps.shapez_core.urls")),
    path("api/solver/", include("django_apps.shapez_solver.urls")),
]
