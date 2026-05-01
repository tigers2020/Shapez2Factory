from django.urls import path

from django_apps.shapez_solver import views

app_name = "shapez_solver"

urlpatterns = [
    path("solve/", views.solve_shape, name="solve_shape"),
]
