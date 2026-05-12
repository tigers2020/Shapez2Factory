from django.contrib import admin

from django_apps.shapez_asteroid.models import AsteroidCellStatusKind, AsteroidMapCell


@admin.register(AsteroidCellStatusKind)
class AsteroidCellStatusKindAdmin(admin.ModelAdmin):
    list_display = ("slug", "label")
    search_fields = ("slug", "label")


@admin.register(AsteroidMapCell)
class AsteroidMapCellAdmin(admin.ModelAdmin):
    list_display = ("x", "y", "kind")
    list_filter = ("kind",)
    search_fields = ("x", "y")
