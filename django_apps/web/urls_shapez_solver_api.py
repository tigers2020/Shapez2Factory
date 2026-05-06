"""Solver JSON routes under ``/api/solver/`` (namespace ``shapez_solver``)."""

from django.urls import path

from django_apps.web import views_solver_api

app_name = "shapez_solver"

urlpatterns = [
    path("solve/", views_solver_api.solve_shape, name="solve_shape"),
]
