from __future__ import annotations

import threading
import uuid
from typing import Any
from urllib.parse import quote

from django.contrib import admin, messages
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from django_apps.web.models import ShapePartSprite
from django_apps.web.services.shape_part_sprite_generation import (
    JOB_CACHE_TIMEOUT_SECONDS,
    _build_work_queue,
    build_sample_quadrant_work_queue,
    generate_shape_part_sprites,
    job_cache_key,
    merge_job_state,
)


def _run_sprite_job_background(
    cache_key: str,
    renderer_version: str,
    specs: list[tuple[str, str, str, int]],
    skipped: int,
) -> None:
    from django.db import close_old_connections

    close_old_connections()
    try:
        generate_shape_part_sprites(
            renderer_version=renderer_version,
            dry_run=False,
            stdout=None,
            stderr=None,
            progress_cache_key=cache_key,
            work_queue=specs,
            pre_skipped=skipped,
        )
    except RuntimeError as exc:
        merge_job_state(cache_key, {"status": "error", "message": str(exc)})
    except Exception as exc:  # noqa: BLE001 — surface unexpected failures to job UI
        merge_job_state(cache_key, {"status": "error", "message": str(exc)})
    finally:
        close_old_connections()


@admin.register(ShapePartSprite)
class ShapePartSpriteAdmin(admin.ModelAdmin):
    change_list_template = "admin/web/shapepartsprite/change_list.html"
    list_display = (
        "preview_image",
        "sprite_key",
        "mesh_key",
        "renderer_version",
        "quadrant_index",
        "created_at",
    )
    list_filter = ("renderer_version",)
    search_fields = ("sprite_key", "mesh_key")

    @admin.display(description=_("Image"))
    def preview_image(self, obj: ShapePartSprite) -> str:
        field = obj.image
        name = getattr(field, "name", "") if field else ""
        if not name:
            return "—"
        try:
            url = field.url
        except ValueError:
            return "—"
        return format_html(
            '<img src="{}" alt="" width="56" height="56" '
            'style="object-fit:contain;image-rendering:pixelated;vertical-align:middle;" />',
            url,
        )

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            path(
                "start-missing-job/",
                self.admin_site.admin_view(self.start_missing_job_view),
                name=f"{info[0]}_{info[1]}_start_missing_job",
            ),
            path(
                "start-sample-quadrants-job/",
                self.admin_site.admin_view(self.start_sample_quadrants_job_view),
                name=f"{info[0]}_{info[1]}_start_sample_quadrants_job",
            ),
            path(
                "render-progress/",
                self.admin_site.admin_view(self.render_progress_view),
                name=f"{info[0]}_{info[1]}_render_progress",
            ),
            path(
                "job-status/",
                self.admin_site.admin_view(self.job_status_view),
                name=f"{info[0]}_{info[1]}_job_status",
            ),
            *super().get_urls(),
        ]

    def start_missing_job_view(self, request):
        if not self.has_change_permission(request):
            raise PermissionDenied

        if request.method != "POST":
            self.message_user(
                request,
                _("Use the button on the changelist to run generation."),
                level=messages.INFO,
            )
            return redirect(reverse("admin:web_shapepartsprite_changelist"))

        renderer_version = (request.POST.get("renderer_version") or "v1").strip() or "v1"

        try:
            import PIL  # noqa: F401 — ensure Pillow is installed before heavy job
        except ImportError:
            self.message_user(
                request,
                _("Pillow is required (pip install pillow)."),
                level=messages.ERROR,
            )
            return redirect(reverse("admin:web_shapepartsprite_changelist"))

        specs, skipped = _build_work_queue(
            renderer_version=renderer_version,
            skip_existing=True,
            limit=None,
        )
        if not specs:
            self.message_user(
                request,
                _("Nothing to render; skipped %(n)d existing sprites.") % {"n": skipped},
                level=messages.SUCCESS,
            )
            return redirect(reverse("admin:web_shapepartsprite_changelist"))

        job_id = str(uuid.uuid4())
        ck = job_cache_key(job_id)
        cache.set(
            ck,
            {
                "status": "queued",
                "total": len(specs),
                "current": 0,
                "skipped": skipped,
                "rendered": 0,
                "errors": 0,
                "user_id": request.user.pk,
            },
            timeout=JOB_CACHE_TIMEOUT_SECONDS,
        )

        thread = threading.Thread(
            target=_run_sprite_job_background,
            args=(ck, renderer_version, specs, skipped),
            daemon=True,
        )
        thread.start()

        url = (
            reverse("admin:web_shapepartsprite_render_progress")
            + "?job_id="
            + quote(job_id, safe="")
        )
        return redirect(url)

    def start_sample_quadrants_job_view(self, request):
        if not self.has_change_permission(request):
            raise PermissionDenied

        if request.method != "POST":
            self.message_user(
                request,
                _("Use the button on the changelist to run sample generation."),
                level=messages.INFO,
            )
            return redirect(reverse("admin:web_shapepartsprite_changelist"))

        renderer_version = (request.POST.get("renderer_version") or "v1").strip() or "v1"

        try:
            import PIL  # noqa: F401 — ensure Pillow is installed before heavy job
        except ImportError:
            self.message_user(
                request,
                _("Pillow is required (pip install pillow)."),
                level=messages.ERROR,
            )
            return redirect(reverse("admin:web_shapepartsprite_changelist"))

        specs, skipped = build_sample_quadrant_work_queue(
            renderer_version=renderer_version,
            skip_existing=True,
        )
        if not specs:
            self.message_user(
                request,
                _("Sample quadrants already complete; skipped %(n)d.") % {"n": skipped},
                level=messages.SUCCESS,
            )
            return redirect(reverse("admin:web_shapepartsprite_changelist"))

        job_id = str(uuid.uuid4())
        ck = job_cache_key(job_id)
        cache.set(
            ck,
            {
                "status": "queued",
                "total": len(specs),
                "current": 0,
                "skipped": skipped,
                "rendered": 0,
                "errors": 0,
                "user_id": request.user.pk,
            },
            timeout=JOB_CACHE_TIMEOUT_SECONDS,
        )

        thread = threading.Thread(
            target=_run_sprite_job_background,
            args=(ck, renderer_version, specs, skipped),
            daemon=True,
        )
        thread.start()

        url = (
            reverse("admin:web_shapepartsprite_render_progress")
            + "?job_id="
            + quote(job_id, safe="")
        )
        return redirect(url)

    def render_progress_view(self, request):
        if not self.has_change_permission(request):
            raise PermissionDenied

        job_id = (request.GET.get("job_id") or "").strip()
        if not job_id:
            raise Http404

        ck = job_cache_key(job_id)
        state = cache.get(ck)
        if state is None:
            self.message_user(
                request,
                _("Job not found or expired. Start a new render from the list."),
                level=messages.WARNING,
            )
            return redirect(reverse("admin:web_shapepartsprite_changelist"))
        if state.get("user_id") != request.user.pk:
            raise PermissionDenied

        status_url = (
            reverse("admin:web_shapepartsprite_job_status") + "?job_id=" + quote(job_id, safe="")
        )
        changelist_url = reverse("admin:web_shapepartsprite_changelist")

        context: dict[str, Any] = {
            **self.admin_site.each_context(request),
            "title": _("Sprite render progress"),
            "opts": self.model._meta,
            "job_id": job_id,
            "poll_url": status_url,
            "changelist_url": changelist_url,
        }
        return render(request, "admin/web/shapepartsprite/render_progress.html", context)

    def job_status_view(self, request):
        if not self.has_change_permission(request):
            return JsonResponse({"error": "forbidden"}, status=403)

        job_id = (request.GET.get("job_id") or "").strip()
        if not job_id:
            return JsonResponse({"error": "missing_job_id"}, status=400)

        ck = job_cache_key(job_id)
        state = cache.get(ck)
        if state is None:
            return JsonResponse({"error": "unknown_job"}, status=404)
        if state.get("user_id") != request.user.pk:
            return JsonResponse({"error": "forbidden"}, status=403)

        public = {k: v for k, v in state.items() if k != "user_id"}
        return JsonResponse(public)
