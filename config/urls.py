"""Root URL configuration for the scaffold."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("django_apps.api.urls")),
    path("", include("django_apps.web.urls")),
]
