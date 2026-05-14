from __future__ import annotations

import hashlib
import json
from typing import Any

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST

from django_apps.shapez_asteroid.services.asteroid_map_cells import (
    list_map_cells_json,
    parse_bbox,
)
from django_apps.shapez_asteroid.services.asteroid_optimizer_dev_report import (
    format_asteroid_optimizer_dev_report_md,
    resolve_dev_report_md_path,
    write_asteroid_optimizer_dev_report,
)
from django_apps.shapez_asteroid.services.behavior_artifact_collector import (
    BehaviorArtifactCollector,
    build_decode_failure_behavior_document,
)
from django_apps.shapez_asteroid.services.copy_preview_debug_dump import (
    dump_copy_preview_debug,
)
from django_apps.shapez_asteroid.services.style_classifier import asteroid_map_style_catalog
from django_apps.shapez_asteroid.services.v2_behavior_artifact_dump import (
    dump_v2_behavior_artifact_json,
    input_digest_prefix_from_code,
)
from django_apps.shapez_core.services.shapez_copy_decode import decode_shapez2_copy_trace


def _map_cells_error_code(message: str) -> str:
    return {
        "missing x_min, x_max, y_min, or y_max": "bbox_missing_params",
        "bounds must be integers": "bbox_not_integers",
        "min must be <= max for each axis": "bbox_min_max_order",
        "bbox span too large": "bbox_span_too_large",
        "bbox must not include x=0": "bbox_includes_x_zero",
    }.get(message, "bbox_validation_error")


@require_GET
def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


@require_GET
def map_cells(request: HttpRequest) -> JsonResponse:
    err, bbox = parse_bbox(request.GET)
    if err is not None:
        raw = str(err.get("error", ""))
        return JsonResponse(
            {
                "ok": False,
                "error": _(raw),
                "error_code": _map_cells_error_code(raw),
            },
            status=400,
        )
    assert bbox is not None
    x_min, x_max, y_min, y_max = bbox
    return JsonResponse(list_map_cells_json(x_min, x_max, y_min, y_max))


@require_POST
def copy_preview(request: HttpRequest) -> JsonResponse:
    """Return copy-preview JSON using **mining layout v2 only**.

    ``map_timeline`` is ``v2_preview_map_timeline`` from ``build_copy_preview_v2_sidecars``
    (variable length; each frame has a full ``mining_map``). Root ``summary`` / ``mining_map``
    match the last timeline frame (or empty placeholders when reconstruction yields no frames).

    ``reconstruction`` is the full STEP 1 DTO (JSON-safe). ``partial_pipeline`` lists which
    solver phases are included in this response vs not yet wired—no replay/NDJSON input.
    Legacy v1 ``include_solver_*`` query parameters are ignored.
    """

    try:
        body = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"ok": False, "error": _("invalid json"), "error_code": "invalid_json"},
            status=400,
        )

    code = body.get("code")
    if not isinstance(code, str):
        return JsonResponse(
            {
                "ok": False,
                "error": _("code must be a string"),
                "error_code": "code_not_string",
            },
            status=400,
        )

    trace = decode_shapez2_copy_trace(code)
    artifact_dir = (getattr(settings, "SHAPEZ_COPY_DEBUG_DIR", "") or "").strip()
    digest_prefix = input_digest_prefix_from_code(code)
    if artifact_dir and not trace.success:
        dump_v2_behavior_artifact_json(
            build_decode_failure_behavior_document(
                trace=trace,
                input_digest_prefix=digest_prefix,
            ),
            artifact_dir,
        )
    if not trace.success:
        user_error = trace.error or _("decode failed")
        return JsonResponse(
            {
                "ok": False,
                "error": user_error,
                "error_code": "decode_trace_error" if trace.error else "decode_failed",
            },
            status=400,
        )
    decoded = trace.data
    assert decoded is not None

    debug_dir = getattr(settings, "SHAPEZ_COPY_DEBUG_DIR", "") or ""
    if debug_dir:
        dump_copy_preview_debug(code, decoded, debug_dir)

    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.solver import (
        build_copy_preview_v2_sidecars,
    )

    behavior_artifact: BehaviorArtifactCollector | None = None
    if artifact_dir:
        behavior_artifact = BehaviorArtifactCollector(input_digest_prefix=digest_prefix)
        behavior_artifact.record_decode_trace(trace)

    v2_side = build_copy_preview_v2_sidecars(decoded, behavior_artifact=behavior_artifact)
    if artifact_dir and behavior_artifact is not None:
        dump_v2_behavior_artifact_json(behavior_artifact.build_document(), artifact_dir)
    existing_layout_analysis = v2_side["existing_layout_analysis"]
    v2_append = v2_side.get("v2_preview_map_timeline")
    if not isinstance(v2_append, list):
        v2_append = []
    map_timeline: list[dict[str, Any]] = list(v2_append)

    if map_timeline:
        last_frame = map_timeline[-1]
        last_summary = last_frame["summary"]
        last_mining_map = last_frame["mining_map"]
    else:
        last_summary = {
            "entry_count": 0,
            "x_min": 0,
            "x_max": 0,
            "y_min": 0,
            "y_max": 0,
            "phase": "v2_empty",
        }
        last_mining_map: list[dict[str, Any]] = []

    payload: dict[str, Any] = {
        "ok": True,
        "summary": last_summary,
        "mining_map": last_mining_map,
        "map_timeline": map_timeline,
        "style_catalog": asteroid_map_style_catalog(),
        "existing_layout_analysis": existing_layout_analysis,
        "mining_layout_engine": v2_side["mining_layout_engine"],
        "reconstruction": v2_side.get("reconstruction"),
        "partial_pipeline": v2_side.get("partial_pipeline"),
        "reconstruction_summary": v2_side["reconstruction_summary"],
        "preview_schema_version": 2,
    }

    if getattr(settings, "SHAPEZ_DEV_ASTEROID_STEP_REPORT", False):
        report_path = resolve_dev_report_md_path(
            base_dir=settings.BASE_DIR,
            override=getattr(settings, "SHAPEZ_DEV_ASTEROID_REPORT_MD", "") or "",
        )
        st_raw = payload.get("solver_timeline")
        st_list = st_raw if isinstance(st_raw, list) else None
        sr_raw = payload.get("solver_replay")
        sr_dict = sr_raw if isinstance(sr_raw, dict) else None
        mlf = payload.get("mining_layout_runtime_flags")
        fp = hashlib.sha256(code.encode("utf-8", errors="surrogatepass")).hexdigest()[:16]
        md_text = format_asteroid_optimizer_dev_report_md(
            map_timeline=payload["map_timeline"],
            root_summary=payload["summary"],
            reconstruction_summary=(
                payload.get("reconstruction_summary")
                if isinstance(payload.get("reconstruction_summary"), dict)
                else None
            ),
            mining_layout_engine=(
                payload.get("mining_layout_engine")
                if isinstance(payload.get("mining_layout_engine"), str)
                else None
            ),
            include_solver_overlay=False,
            include_solver_replay=False,
            solver_timeline=st_list,
            solver_replay=sr_dict,
            solver_layout_package_unavailable=False,
            mining_layout_runtime_flags=mlf if isinstance(mlf, dict) else None,
            preview_schema_version=(
                int(payload["preview_schema_version"])
                if isinstance(payload.get("preview_schema_version"), int)
                else None
            ),
            code_fingerprint=fp,
        )
        write_asteroid_optimizer_dev_report(report_path, md_text)

    return JsonResponse(payload)
