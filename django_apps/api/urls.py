from django.urls import path

from django_apps.api import views

app_name = "api"

urlpatterns = [
    path("health/", views.health, name="health"),
]
