from django.urls import path

from django_apps.web import views

app_name = "web"

urlpatterns = [
    path("", views.home, name="home"),
    path("api/shape-preview/", views.api_shape_preview, name="api_shape_preview"),
    path("gallery/", views.gallery, name="gallery"),
    path("demo/", views.demo, name="demo"),
]
