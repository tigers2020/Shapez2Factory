from django.urls import path

from django_apps.shapez_core import views

app_name = "shapez_core"

urlpatterns = [
    path("health/", views.health, name="health"),
    path("shape-preview/", views.shape_preview, name="shape_preview"),
]
