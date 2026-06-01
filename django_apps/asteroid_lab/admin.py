from __future__ import annotations

import json
from io import StringIO

from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.core.management.base import CommandError
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import SafeString

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.genetic_sample_mini_map import genetic_sample_mini_map_html
from django_apps.asteroid_lab.reconstruction.display_map import (
    reconstruction_summary_from_decoded_json,
)
from django_apps.asteroid_lab.services.reconstructed_map_thumbnail_service import (
    clear_admin_list_thumbnail,
    sync_admin_list_thumbnail,
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


@admin.register(m.IslandExtractorBlueprint)
class IslandExtractorBlueprintAdmin(admin.ModelAdmin):
    list_display = (
        "variant_key",
        "carrier_kind",
        "layout_t",
        "display_name",
        "inner_fingerprint_short",
        "updated_at",
    )
    list_filter = ("carrier_kind",)
    search_fields = ("variant_key", "display_name", "layout_t")
    readonly_fields = ("inner_fingerprint", "updated_at")

    @staticmethod
    def inner_fingerprint_short(obj: m.IslandExtractorBlueprint) -> str:
        fp = (obj.inner_fingerprint or "").strip()
        return fp[:12] + "?" if len(fp) > 12 else fp or "-"


@admin.register(m.GeneSeed)
class GeneSeedAdmin(admin.ModelAdmin):
    change_list_template = "admin/asteroid_lab/geneseed/change_list.html"
    list_display = (
        "id",
        "mini_map_list",
        "name",
        "gene_key",
        "seed_rank_display",
        "intrinsic_priority_rank_display",
        "difficulty_rank_display",
        "difficulty_score_display",
        "extension_count_display",
        "topology_signature_short",
        "updated_at",
    )
    list_display_links = ("id", "name")
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
        ("???", {"fields": ("decoded_json_pretty", "mini_map_preview")}),
        ("??", {"fields": ("metadata_json_pretty", "created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import (
            MINER_SEED_SCHEMA_V2,
        )

        qs = super().get_queryset(request)
        return qs.filter(
            metadata_json__schema=MINER_SEED_SCHEMA_V2,
            metadata_json__is_seed=True,
        ).order_by("metadata_json__seed_rank", "gene_key")

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            path(
                "seed-miner-patterns/",
                self.admin_site.admin_view(self.seed_miner_patterns_view),
                name=f"{info[0]}_{info[1]}_seed_miner_patterns",
            ),
            *super().get_urls(),
        ]

    def seed_miner_patterns_view(self, request):
        changelist_url = reverse("admin:asteroid_lab_geneseed_changelist")
        if not self.has_change_permission(request):
            raise PermissionDenied

        if request.method != "POST":
            self.message_user(
                request,
                "?? ?? ???? miner seed ?? ??? ?????.",
                level=messages.INFO,
            )
            return redirect(changelist_url)

        dry_run = request.POST.get("dry_run") == "on"
        replace_stale = request.POST.get("replace_stale") == "on"
        purge_non_seed = request.POST.get("purge_non_seed") == "on"
        out = StringIO()
        cmd_kwargs: dict[str, object] = {
            "verbosity": 1,
            "stdout": out,
        }
        if dry_run:
            cmd_kwargs["dry_run"] = True
        if replace_stale:
            cmd_kwargs["replace_stale"] = True
        if purge_non_seed and not dry_run:
            cmd_kwargs["purge_non_seed"] = True

        try:
            call_command("seed_miner_patterns", **cmd_kwargs)
        except CommandError as exc:
            self.message_user(request, str(exc), level=messages.ERROR)
            return redirect(changelist_url)

        output = out.getvalue().strip()
        if dry_run:
            self.message_user(
                request,
                "dry-run: DB ?? ??. " + (output.splitlines()[-1] if output else "??? ???."),
                level=messages.SUCCESS,
            )
        else:
            tail = output.splitlines()[-1] if output else "?? ??."
            self.message_user(request, tail, level=messages.SUCCESS)
            for line in output.splitlines():
                if "deleted stale exhaustive" in line or "deleted stale miner_seed" in line:
                    self.message_user(request, line.strip(), level=messages.WARNING)
        return redirect(changelist_url)

    @admin.display(description="Catalog rank", ordering="metadata_json__seed_rank")
    def seed_rank_display(self, obj: m.GeneSeed) -> str:
        meta = obj.metadata_json if isinstance(obj.metadata_json, dict) else {}
        rank = meta.get("seed_rank")
        return str(rank) if isinstance(rank, int) else "-"

    @admin.display(
        description="Intrinsic priority",
        ordering="metadata_json__intrinsic_priority_rank",
    )
    def intrinsic_priority_rank_display(self, obj: m.GeneSeed) -> str:
        meta = obj.metadata_json if isinstance(obj.metadata_json, dict) else {}
        rank = meta.get("intrinsic_priority_rank")
        score = meta.get("intrinsic_priority_score")
        if isinstance(rank, int) and isinstance(score, int):
            return f"{rank} ({score})"
        return "-"

    @admin.display(description="Intrinsic difficulty", ordering="metadata_json__difficulty_rank")
    def difficulty_rank_display(self, obj: m.GeneSeed) -> str:
        meta = obj.metadata_json if isinstance(obj.metadata_json, dict) else {}
        rank = meta.get("difficulty_rank")
        tier = meta.get("difficulty_tier")
        if isinstance(rank, int) and isinstance(tier, int):
            return f"{rank} (T{tier})"
        return "-"

    @admin.display(
        description="Difficulty score",
        ordering="metadata_json__difficulty_score",
    )
    def difficulty_score_display(self, obj: m.GeneSeed) -> str:
        meta = obj.metadata_json if isinstance(obj.metadata_json, dict) else {}
        score = meta.get("difficulty_score")
        return str(score) if isinstance(score, int) else "-"

    @admin.display(description="Ext")
    def extension_count_display(self, obj: m.GeneSeed) -> str:
        meta = obj.metadata_json if isinstance(obj.metadata_json, dict) else {}
        ext = meta.get("extension_count")
        return str(ext) if isinstance(ext, int) else "-"

    @admin.display(description="Topology")
    def topology_signature_short(self, obj: m.GeneSeed) -> str:
        meta = obj.metadata_json if isinstance(obj.metadata_json, dict) else {}
        sig = meta.get("topology_signature")
        if not isinstance(sig, str) or not sig:
            return "-"
        return sig[:10] + "?" if len(sig) > 10 else sig

    @admin.display(description="??? JSON")
    def decoded_json_pretty(self, obj: m.GeneSeed) -> SafeString | str:
        if not obj.decoded_json:
            return "-"
        text = json.dumps(obj.decoded_json, indent=2, ensure_ascii=False)
        pre_style = (
            "max-height:420px;overflow:auto;font-size:11px;line-height:1.35;"
            "background:#0f172a;color:#e2e8f0;padding:12px;border-radius:6px;"
            "white-space:pre-wrap;word-break:break-word;"
        )
        return format_html('<pre style="{}">{}</pre>', pre_style, text)

    @admin.display(description="?")
    def mini_map_list(self, obj: m.GeneSeed) -> SafeString | str:
        return genetic_sample_mini_map_html(obj.decoded_json, for_list=True)

    @admin.display(description="???")
    def mini_map_preview(self, obj: m.GeneSeed) -> SafeString | str:
        if obj.pk is None:
            return "?? ? ???? ?????."
        return genetic_sample_mini_map_html(obj.decoded_json)

    @admin.display(description="metadata_json")
    def metadata_json_pretty(self, obj: m.GeneSeed) -> SafeString | str:
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
    actions = [
        "regenerate_admin_list_thumbnails",
        "clear_admin_list_thumbnails",
    ]
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
            "?? JSON",
            {"fields": ("original_decoded_json_pretty",)},
        ),
        (
            "full_map JSON",
            {"fields": ("decoded_json_pretty", "mini_map_preview")},
        ),
        (None, {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):  # type: ignore[no-untyped-def]
        qs = super().get_queryset(request)
        if request.resolver_match and request.resolver_match.url_name.endswith("_changelist"):
            return qs.defer("decoded_json", "original_decoded_json")
        return qs

    def save_model(self, request, obj, form, change):  # type: ignore[no-untyped-def]
        super().save_model(request, obj, form, change)
        row = m.ReconstructedAsteroidMap.objects.get(pk=int(obj.pk))
        sync_admin_list_thumbnail(row)

    @admin.action(description="Regenerate admin list thumbnails")
    def regenerate_admin_list_thumbnails(self, request, queryset):  # type: ignore[no-untyped-def]
        pks = list(queryset.values_list("pk", flat=True))
        qs = m.ReconstructedAsteroidMap.objects.filter(pk__in=pks).only(
            "pk",
            "decoded_json",
            "admin_list_thumbnail",
            "admin_list_thumbnail_hash",
            "admin_list_thumbnail_renderer_version",
        )
        count = 0
        for row in qs.iterator():
            if sync_admin_list_thumbnail(row, force=True):
                count += 1
        self.message_user(request, f"Regenerated thumbnails for {count} row(s).")

    @admin.action(description="Clear admin list thumbnails")
    def clear_admin_list_thumbnails(self, request, queryset):  # type: ignore[no-untyped-def]
        for pk in queryset.values_list("pk", flat=True):
            clear_admin_list_thumbnail(int(pk))
        self.message_user(request, "Cleared admin list thumbnails.")

    @admin.display(description="?? ??? JSON")
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

    @admin.display(description="full_map ??? JSON")
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

    @admin.display(description="??")
    def reconstruction_quality_tier(self, obj: m.ReconstructedAsteroidMap) -> str:
        summary = reconstruction_summary_from_decoded_json(obj.decoded_json or {})
        return str(summary.get("quality_tier") or "-")

    @admin.display(description="??")
    def reconstruction_acceptance(self, obj: m.ReconstructedAsteroidMap) -> str:
        summary = reconstruction_summary_from_decoded_json(obj.decoded_json or {})
        if summary.get("reconstruction_acceptance_ok") is True:
            return "ok"
        if summary.get("reconstruction_acceptance_ok") is False:
            return "no"
        return "-"

    @admin.display(description="?")
    def mini_map_list(self, obj: m.ReconstructedAsteroidMap) -> SafeString | str:
        if obj.admin_list_thumbnail:
            truncated = " ?" if obj.admin_list_thumbnail_truncated else ""
            return format_html(
                '<img src="{}" alt="" width="120" height="120" loading="lazy" '
                'style="object-fit:contain;background:#020617;border-radius:6px;" />'
                '<span style="font-size:10px;color:#94a3b8;">{} cells{}</span>',
                obj.admin_list_thumbnail.url,
                obj.admin_list_thumbnail_cell_count,
                truncated,
            )
        return format_html(
            '<span style="color:#64748b;font-size:11px;">{}</span>',
            "no thumbnail",
        )

    @admin.display(description="???")
    def mini_map_preview(self, obj: m.ReconstructedAsteroidMap) -> SafeString | str:
        if obj.pk is None:
            return "?? ? ???? ?????."
        return genetic_sample_mini_map_html(obj.decoded_json)
