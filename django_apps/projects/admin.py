from django.contrib import admin

from django_apps.projects.models import SolverProject, SolverRun


@admin.register(SolverProject)
class SolverProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "target_shape", "target_rate_per_min", "created_at", "updated_at")
    search_fields = ("title", "target_shape")


@admin.register(SolverRun)
class SolverRunAdmin(admin.ModelAdmin):
    list_display = ("project", "status", "runtime_ms", "explored_states", "created_at")
    list_filter = ("status",)
    search_fields = ("project__title", "project__target_shape")
