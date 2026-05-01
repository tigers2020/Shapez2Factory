from django.urls import path
from django.views.generic import RedirectView

from django_apps.web import views

app_name = "web"

urlpatterns = [
    path("", views.home, name="home"),
    path("gallery/", views.gallery, name="gallery"),
    path("demo/", views.demo, name="demo"),
    path("solver/", views.solver, name="solver"),
    path(
        "solve/",
        RedirectView.as_view(pattern_name="web:solver", permanent=False, query_string=True),
    ),
]
