from __future__ import annotations

from django.contrib import admin

from django_apps.asteroid_lab import models as m


class ReplayFrameInline(admin.TabularInline):
    model = m.ReplayFrame
    extra = 0
    ordering = ("frame_index",)


class RoutingProbeInline(admin.TabularInline):
    model = m.RoutingProbe
    extra = 0


@admin.register(m.AsteroidProject)
class AsteroidProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "updated_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(m.AsteroidMapInput)
class AsteroidMapInputAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "source_kind", "layout_fp", "created_at")
    list_filter = ("source_kind",)
    raw_id_fields = ("project",)

    @staticmethod
    def layout_fp(obj: m.AsteroidMapInput) -> str:
        fp = (obj.layout_fingerprint or "").strip()
        return fp[:12] + "..." if len(fp) > 12 else fp or "-"


@admin.register(m.AsteroidCellSnapshot)
class AsteroidCellSnapshotAdmin(admin.ModelAdmin):
    list_display = ("id", "map_input", "layer", "captured_at")
    list_filter = ("layer",)
    raw_id_fields = ("map_input",)


@admin.register(m.PatternTemplate)
class PatternTemplateAdmin(admin.ModelAdmin):
    list_display = ("template_key", "title", "created_at")
    search_fields = ("template_key", "title")


@admin.register(m.PatternVariant)
class PatternVariantAdmin(admin.ModelAdmin):
    list_display = ("id", "template", "variant_key", "transport_kind")
    search_fields = ("variant_key",)
    raw_id_fields = ("template",)


@admin.register(m.SolverRun)
class SolverRunAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "run_key", "algorithm_label", "status", "created_at")
    list_filter = ("status", "algorithm_label")
    search_fields = ("run_key",)
    raw_id_fields = ("project",)


@admin.register(m.SolverMetricSnapshot)
class SolverMetricSnapshotAdmin(admin.ModelAdmin):
    list_display = ("id", "solver_run", "frame_index", "phase", "aggregate_score")
    raw_id_fields = ("solver_run",)


@admin.register(m.CandidateBundle)
class CandidateBundleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "solver_run",
        "bundle_key",
        "generation_index",
        "placement_state",
        "local_score",
    )
    list_filter = ("placement_state",)
    search_fields = ("bundle_key",)
    raw_id_fields = ("solver_run",)
    inlines = (RoutingProbeInline,)


@admin.register(m.RoutingProbe)
class RoutingProbeAdmin(admin.ModelAdmin):
    list_display = ("id", "candidate_bundle", "probe_kind", "reachable", "path_cost")
    list_filter = ("reachable", "probe_kind")
    raw_id_fields = ("candidate_bundle",)


@admin.register(m.ReplayTrack)
class ReplayTrackAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "track_key", "solver_run", "created_at")
    search_fields = ("track_key", "title")
    raw_id_fields = ("project", "solver_run")
    inlines = (ReplayFrameInline,)


@admin.register(m.ReplayFrame)
class ReplayFrameAdmin(admin.ModelAdmin):
    list_display = ("id", "replay_track", "frame_index", "frame_key", "phase", "is_keyframe")
    list_filter = ("is_keyframe", "is_placeholder")
    ordering = ("replay_track", "frame_index")
    raw_id_fields = ("replay_track",)


@admin.register(m.UIPlaybackSession)
class UIPlaybackSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "replay_track",
        "current_frame_index",
        "is_playing",
        "playback_speed_ms",
        "selected_layer",
        "updated_at",
    )
    raw_id_fields = ("replay_track",)


@admin.register(m.TopologyRule)
class TopologyRuleAdmin(admin.ModelAdmin):
    list_display = ("rule_key", "title", "rule_group", "severity", "is_active", "sort_order")
    list_filter = ("rule_group", "severity", "is_active")
    search_fields = ("rule_key", "title", "short_label")


@admin.register(m.TopologyRuleModalContent)
class TopologyRuleModalContentAdmin(admin.ModelAdmin):
    list_display = ("id", "rule", "modal_title", "updated_at")
    raw_id_fields = ("rule",)
