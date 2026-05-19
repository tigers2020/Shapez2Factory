from __future__ import annotations

import json

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import SafeString

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.genetic_sample_mini_map import genetic_sample_mini_map_html
from django_apps.asteroid_lab.reconstruction.display_map import (
    reconstruction_summary_from_decoded_json,
)


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


@admin.register(m.GeneticSample)
class GeneticSampleAdmin(admin.ModelAdmin):
    list_display = ("id", "mini_map_list", "name", "gene_key", "project", "updated_at")
    list_display_links = ("id", "name")
    list_select_related = ("project",)
    search_fields = ("name", "gene_key", "code")
    raw_id_fields = ("project",)
    readonly_fields = (
        "decoded_json_pretty",
        "mini_map_preview",
        "metadata_json_pretty",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (None, {"fields": ("name", "gene_key", "project", "code")}),
        ("디코드", {"fields": ("decoded_json_pretty", "mini_map_preview")}),
        ("메타", {"fields": ("metadata_json_pretty", "created_at", "updated_at")}),
    )

    @admin.display(description="디코드 JSON")
    def decoded_json_pretty(self, obj: m.GeneticSample) -> SafeString | str:
        if not obj.decoded_json:
            return "-"
        text = json.dumps(obj.decoded_json, indent=2, ensure_ascii=False)
        pre_style = (
            "max-height:420px;overflow:auto;font-size:11px;line-height:1.35;"
            "background:#0f172a;color:#e2e8f0;padding:12px;border-radius:6px;"
            "white-space:pre-wrap;word-break:break-word;"
        )
        return format_html('<pre style="{}">{}</pre>', pre_style, text)

    @admin.display(description="맵")
    def mini_map_list(self, obj: m.GeneticSample) -> SafeString | str:
        return genetic_sample_mini_map_html(obj.decoded_json, for_list=True)

    @admin.display(description="미니맵")
    def mini_map_preview(self, obj: m.GeneticSample) -> SafeString | str:
        if obj.pk is None:
            return "저장 후 미니맵이 표시됩니다."
        return genetic_sample_mini_map_html(obj.decoded_json)

    @admin.display(description="metadata_json")
    def metadata_json_pretty(self, obj: m.GeneticSample) -> SafeString | str:
        meta = obj.metadata_json
        if not meta:
            return "-"
        text = json.dumps(meta, indent=2, ensure_ascii=False)
        pre_style = (
            "max-height:280px;overflow:auto;font-size:11px;line-height:1.35;"
            "background:#0f172a;color:#e2e8f0;padding:12px;border-radius:6px;"
            "white-space:pre-wrap;word-break:break-word;"
        )
        return format_html('<pre style="{}">{}</pre>', pre_style, text)


@admin.register(m.ReconstructedAsteroidMap)
class ReconstructedAsteroidMapAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "mini_map_list",
        "reconstruction_quality_tier",
        "reconstruction_acceptance",
        "map_input",
        "run_key",
        "updated_at",
        "created_at",
    )
    list_display_links = ("id",)
    list_select_related = ("map_input", "project")
    search_fields = ("run_key", "copy_code", "original_copy_code")
    raw_id_fields = ("map_input", "project", "solver_run")
    readonly_fields = (
        "original_decoded_json_pretty",
        "decoded_json_pretty",
        "mini_map_preview",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "map_input",
                    "project",
                    "solver_run",
                    "run_key",
                    "original_copy_code",
                    "copy_code",
                )
            },
        ),
        (
            "원본 JSON",
            {"fields": ("original_decoded_json_pretty",)},
        ),
        (
            "full_map JSON",
            {"fields": ("decoded_json_pretty", "mini_map_preview")},
        ),
        (None, {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="원본 디코드 JSON")
    def original_decoded_json_pretty(self, obj: m.ReconstructedAsteroidMap) -> SafeString | str:
        if not obj.original_decoded_json:
            return "-"
        text = json.dumps(obj.original_decoded_json, indent=2, ensure_ascii=False)
        pre_style = (
            "max-height:420px;overflow:auto;font-size:11px;line-height:1.35;"
            "background:#0f172a;color:#e2e8f0;padding:12px;border-radius:6px;"
            "white-space:pre-wrap;word-break:break-word;"
        )
        return format_html('<pre style="{}">{}</pre>', pre_style, text)

    @admin.display(description="full_map 디코드 JSON")
    def decoded_json_pretty(self, obj: m.ReconstructedAsteroidMap) -> SafeString | str:
        if not obj.decoded_json:
            return "-"
        text = json.dumps(obj.decoded_json, indent=2, ensure_ascii=False)
        pre_style = (
            "max-height:420px;overflow:auto;font-size:11px;line-height:1.35;"
            "background:#0f172a;color:#e2e8f0;padding:12px;border-radius:6px;"
            "white-space:pre-wrap;word-break:break-word;"
        )
        return format_html('<pre style="{}">{}</pre>', pre_style, text)

    @admin.display(description="품질")
    def reconstruction_quality_tier(self, obj: m.ReconstructedAsteroidMap) -> str:
        summary = reconstruction_summary_from_decoded_json(obj.decoded_json or {})
        return str(summary.get("quality_tier") or "-")

    @admin.display(description="수용")
    def reconstruction_acceptance(self, obj: m.ReconstructedAsteroidMap) -> str:
        summary = reconstruction_summary_from_decoded_json(obj.decoded_json or {})
        if summary.get("reconstruction_acceptance_ok") is True:
            return "ok"
        if summary.get("reconstruction_acceptance_ok") is False:
            return "no"
        return "-"

    @admin.display(description="맵")
    def mini_map_list(self, obj: m.ReconstructedAsteroidMap) -> SafeString | str:
        return genetic_sample_mini_map_html(obj.decoded_json, for_list=True)

    @admin.display(description="미니맵")
    def mini_map_preview(self, obj: m.ReconstructedAsteroidMap) -> SafeString | str:
        if obj.pk is None:
            return "저장 후 미니맵이 표시됩니다."
        return genetic_sample_mini_map_html(obj.decoded_json)
