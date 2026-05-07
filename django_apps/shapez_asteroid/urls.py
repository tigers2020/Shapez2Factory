from django.urls import path

from django_apps.shapez_asteroid import views

app_name = "shapez_asteroid"

urlpatterns = [
    path("health/", views.health, name="health"),
    path("copy-preview/", views.copy_preview, name="copy_preview"),
]
