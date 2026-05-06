import json
from functools import wraps
from typing import Any

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from django_apps.shapez_solver.models import MacroRecipe
from django_apps.shapez_solver.services.graph_document_primitive_chain import (
    try_linear_operation_sequence,
)
from django_apps.shapez_solver.services.macro_recipe_graph_visual import (
    enrich_react_flow_with_macro_visual_previews,
    serialize_macro_recipe_visual,
)
from django_apps.shapez_solver.services.macro_recipe_staff_catalog import (
    MACRO_RECIPE_DETAIL_PREFETCHES,
    apply_graph_derived_catalog_fields,
    build_catalog_snapshot,
    create_draft_macro_recipe,
    create_recipe,
    delete_recipe,
    serialize_recipe,
    sync_macro_recipe_steps_from_graph_document,
    update_recipe,
)
from django_apps.shapez_solver.services.recipe_graph_cost_hints import graph_cost_hint_from_document
from django_apps.shapez_solver.services.recipe_graph_react_flow_adapter import (
    domain_graph_to_react_flow,
    react_flow_to_domain_graph,
)
from django_apps.shapez_solver.services.recipe_graph_recipe_validation import (
    annotate_visual_graph_with_issues,
    validate_recipe_graph_context,
)
from django_apps.shapez_solver.services.recipe_graph_recompute import (
    recompute_validated_graph_document,
    validate_graph_document,
)
from django_apps.web.constants import JSON_API_ERROR_INVALID
from django_apps.web.models import ShapePartSprite
from django_apps.web.services.graph_preview import (
    NoopGraphPreviewRenderer,
    get_graph_preview_renderer,
)


def staff_site_required(view_func):
    """Require login at ``settings.LOGIN_URL`` and ``is_staff`` (403 if logged-in but not staff)."""

    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped


def _macro_staff_catalog_json(request: HttpRequest) -> JsonResponse:
    del request
    return JsonResponse(build_catalog_snapshot())


def _macro_staff_graph_bootstrap(request: HttpRequest, recipe_pk: int) -> dict[str, Any]:
    out: dict[str, Any] = {
        "api_catalog": reverse("web:macro-pattern-staff-api-catalog"),
        "api_recipes": reverse("web:macro-pattern-staff-api-recipes-create"),
        "api_recipe_detail_pattern": reverse(
            "web:macro-pattern-staff-api-recipe-detail",
            kwargs={"pk": recipe_pk},
        ),
        "api_recipe_graph_recompute": reverse(
            "web:macro-pattern-staff-api-recipe-graph-recompute",
            kwargs={"pk": recipe_pk},
        ),
        "api_shape_part_sprite_manifest": reverse("web:shape-part-sprite-manifest"),
        "csrf_token": get_token(request),
        "staff_catalog_url": reverse("web:macro-pattern-staff"),
        "staff_recipe_edit_url": reverse(
            "web:macro-pattern-recipe-edit",
            kwargs={"pk": recipe_pk},
        ),
    }
    return out


def _recompute_graph_source_or_error(data: dict[str, Any]) -> JsonResponse | bool:
    """Return JsonResponse on invalid input, or bool: True = react_flow, False = graph_document."""
    has_doc = "graph_document" in data and data["graph_document"] is not None
    has_rf = "react_flow" in data and data["react_flow"] is not None
    if has_doc and has_rf:
        return JsonResponse(
            {"ok": False, "error": "provide only one of graph_document or react_flow"},
            status=400,
        )
    if not has_doc and not has_rf:
        return JsonResponse(
            {"ok": False, "error": "graph_document or react_flow is required"},
            status=400,
        )
    return has_rf


def _validated_graph_from_recompute_body(
    data: dict[str, Any], from_react_flow: bool
) -> tuple[dict[str, Any] | None, JsonResponse | None]:
    try:
        if from_react_flow:
            if not isinstance(data["react_flow"], dict):
                return None, JsonResponse(
                    {"ok": False, "error": "react_flow must be an object"},
                    status=400,
                )
            raw_doc = react_flow_to_domain_graph(data["react_flow"])
            validated = validate_graph_document(raw_doc)
        else:
            validated = validate_graph_document(data["graph_document"])
    except ValueError as exc:
        return None, JsonResponse({"ok": False, "error": str(exc)}, status=400)
    return validated, None


@staff_site_required
def macro_pattern_list(request: HttpRequest) -> HttpResponse:
    catalog = build_catalog_snapshot()
    return render(
        request,
        "web/macro_pattern_list.html",
        {"catalog": catalog, "staff_macro_nav": "list"},
    )


@staff_site_required
def macro_pattern_new(request: HttpRequest) -> HttpResponse:
    catalog = build_catalog_snapshot()
    error: str | None = None
    if request.method == "POST":
        try:
            name = (request.POST.get("name") or "").strip()
            recipe = create_draft_macro_recipe(name=name)
            return redirect("web:macro-pattern-graph", pk=recipe.pk)
        except (ValueError, TypeError) as exc:
            error = str(exc)
    return render(
        request,
        "web/macro_pattern_new.html",
        {
            "catalog": catalog,
            "staff_macro_nav": "new",
            "form_error": error,
        },
    )


@staff_site_required
def macro_pattern_recipe_edit(request: HttpRequest, pk: int) -> HttpResponse:
    recipe = get_object_or_404(
        MacroRecipe.objects.select_related("family").prefetch_related(
            *MACRO_RECIPE_DETAIL_PREFETCHES,
        ),
        pk=pk,
    )
    catalog = build_catalog_snapshot()
    preview_renderer = get_graph_preview_renderer()
    serialized = serialize_recipe(recipe, preview_renderer=preview_renderer)
    bootstrap = {
        "api_recipe_detail": reverse(
            "web:macro-pattern-staff-api-recipe-detail",
            kwargs={"pk": pk},
        ),
        "api_catalog": reverse("web:macro-pattern-staff-api-catalog"),
    }
    return render(
        request,
        "web/macro_pattern_recipe_edit.html",
        {
            "recipe": serialized,
            "catalog": catalog,
            "bootstrap": bootstrap,
            "staff_macro_nav": "edit",
        },
    )


@staff_site_required
def macro_pattern_graph(request: HttpRequest, pk: int) -> HttpResponse:
    recipe = get_object_or_404(
        MacroRecipe.objects.select_related("family").prefetch_related(
            *MACRO_RECIPE_DETAIL_PREFETCHES,
        ),
        pk=pk,
    )
    preview_renderer = get_graph_preview_renderer()
    serialized = serialize_recipe(recipe, sync_png=False, preview_renderer=preview_renderer)
    bootstrap = _macro_staff_graph_bootstrap(request, pk)
    react_flow_initial: dict[str, Any] | None = None
    rf_status: str = "missing"
    if recipe.graph_document:
        try:
            validated_doc = validate_graph_document(recipe.graph_document)
            react_flow_initial = domain_graph_to_react_flow(validated_doc)
            visual_cached = serialized.get("visual_graph")
            react_flow_initial = enrich_react_flow_with_macro_visual_previews(
                react_flow_initial,
                validated_doc,
                preview_renderer=preview_renderer,
                macro_visual=visual_cached if isinstance(visual_cached, dict) else None,
            )
            rf_status = "ok"
        except ValueError:
            react_flow_initial = None
            rf_status = "invalid"
    bootstrap["react_flow_initial"] = react_flow_initial
    bootstrap["react_flow_initial_status"] = rf_status
    bootstrap["macro_step_count"] = len(recipe.steps.all())
    return render(
        request,
        "web/macro_pattern_graph.html",
        {
            "recipe": serialized,
            "bootstrap": bootstrap,
            "catalog": build_catalog_snapshot(),
            "staff_macro_nav": "graph",
            "recipe_graph_editor_asset_version": "20260507-graph-editor-no-warm",
        },
    )


@staff_site_required
@require_http_methods(["POST"])
def macro_pattern_staff_api_graph_preview_warm(request: HttpRequest) -> JsonResponse:
    """Generate one graph-preview PNG (Playwright) from ``preview_scene``; staff-only."""
    try:
        data = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": JSON_API_ERROR_INVALID}, status=400)
    cache_key = str(data.get("cache_key") or "").strip()
    preview_scene = data.get("preview_scene")
    if not cache_key or not isinstance(preview_scene, dict):
        return JsonResponse(
            {"ok": False, "error": "cache_key and preview_scene object required"},
            status=400,
        )
    renderer = get_graph_preview_renderer()
    if isinstance(renderer, NoopGraphPreviewRenderer):
        return JsonResponse(
            {"ok": False, "error": "graph preview renderer is noop"},
            status=503,
        )
    if renderer.cache_key(preview_scene) != cache_key:
        return JsonResponse(
            {"ok": False, "error": "cache_key does not match preview_scene"},
            status=400,
        )
    gp = renderer.render(preview_scene)
    if not gp.image_url:
        return JsonResponse(
            {
                "ok": False,
                "error": "preview generation failed",
                "cache_key": cache_key,
            },
            status=500,
        )
    return JsonResponse(
        {
            "ok": True,
            "cache_key": cache_key,
            "preview_image_url": gp.image_url,
            "preview_alt": gp.alt_text,
        }
    )


@staff_site_required
@require_http_methods(["GET"])
def shape_part_sprite_manifest(request: HttpRequest) -> JsonResponse:
    """JSON manifest of baked atomic part PNGs (for recipe graph tile Canvas2D composition)."""
    renderer_version = (request.GET.get("renderer_version") or "v1").strip()
    sprites: dict[str, dict[str, int | str]] = {}
    qs = ShapePartSprite.objects.filter(renderer_version=renderer_version).order_by(
        "sprite_key",
    )
    for row in qs:
        sprites[row.sprite_key] = {
            "url": row.image.url,
            "width": row.image_width,
            "height": row.image_height,
        }
    return JsonResponse({"renderer_version": renderer_version, "sprites": sprites})


@staff_site_required
@require_http_methods(["GET"])
def macro_pattern_staff_api_catalog(request: HttpRequest) -> JsonResponse:
    return _macro_staff_catalog_json(request)


@staff_site_required
@require_http_methods(["POST"])
def macro_pattern_staff_api_recipes_create(request: HttpRequest) -> JsonResponse:
    try:
        data = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": JSON_API_ERROR_INVALID}, status=400)
    try:
        recipe = create_recipe(data)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
    preview_renderer = get_graph_preview_renderer()
    serialized = serialize_recipe(recipe, preview_renderer=preview_renderer)
    return JsonResponse({"ok": True, "recipe": serialized})


@staff_site_required
@require_http_methods(["POST"])
def macro_pattern_staff_api_recipe_graph_recompute(request: HttpRequest, pk: int) -> JsonResponse:
    recipe = get_object_or_404(MacroRecipe, pk=pk)
    try:
        data = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": JSON_API_ERROR_INVALID}, status=400)
    source = _recompute_graph_source_or_error(data)
    if isinstance(source, JsonResponse):
        return source
    validated, err = _validated_graph_from_recompute_body(data, source)
    if err is not None:
        return err
    doc, warnings = recompute_validated_graph_document(validated)
    steps_synced = False
    if data.get("commit"):
        with transaction.atomic():
            locked = (
                MacroRecipe.objects.select_for_update().select_related("family").get(pk=recipe.pk)
            )
            locked.graph_document = doc
            locked.save(update_fields=["graph_document"])
            steps_synced = sync_macro_recipe_steps_from_graph_document(locked, doc)
            apply_graph_derived_catalog_fields(locked, doc)
    renderer = get_graph_preview_renderer()
    try:
        visual_graph = serialize_macro_recipe_visual(doc, preview_renderer=renderer)
    except (ValueError, TypeError, KeyError):
        visual_graph = None
    issues = validate_recipe_graph_context(
        family_signature=recipe.family.signature,
        family_allow_rotation=recipe.family.allow_rotation,
        graph_document=doc,
    )
    validation_ok = not any(i.get("severity") == "error" for i in issues)
    if isinstance(visual_graph, dict):
        annotate_visual_graph_with_issues(visual_graph, issues)
    cost_hint = graph_cost_hint_from_document(doc)
    linear_ops = try_linear_operation_sequence(doc)
    react_flow = domain_graph_to_react_flow(doc)
    react_flow = enrich_react_flow_with_macro_visual_previews(
        react_flow,
        doc,
        preview_renderer=renderer,
        macro_visual=visual_graph if isinstance(visual_graph, dict) else None,
    )
    return JsonResponse(
        {
            "ok": True,
            "graph_document": doc,
            "react_flow": react_flow,
            "warnings": warnings,
            "visual_graph": visual_graph,
            "validation": {"ok": validation_ok, "issues": issues},
            "steps_synced": steps_synced,
            "graph_cost_hint": cost_hint,
            "graph_linear_operation_sequence": linear_ops,
        }
    )


@staff_site_required
@require_http_methods(["GET", "PATCH", "DELETE"])
def macro_pattern_staff_api_recipe_detail(request: HttpRequest, pk: int) -> JsonResponse:
    if request.method == "GET":
        try:
            recipe = (
                MacroRecipe.objects.select_related("family")
                .prefetch_related(*MACRO_RECIPE_DETAIL_PREFETCHES)
                .get(pk=pk)
            )
        except MacroRecipe.DoesNotExist:
            return JsonResponse({"ok": False, "error": "recipe not found"}, status=404)
        return JsonResponse(
            {
                "ok": True,
                "recipe": serialize_recipe(recipe, preview_renderer=get_graph_preview_renderer()),
            },
        )

    if request.method == "DELETE":
        try:
            delete_recipe(pk)
        except ValueError as exc:
            return JsonResponse({"ok": False, "error": str(exc)}, status=404)
        return JsonResponse({"ok": True})

    try:
        data = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": JSON_API_ERROR_INVALID}, status=400)
    try:
        recipe = update_recipe(pk, data)
    except ValueError as exc:
        msg = str(exc)
        status = 404 if msg == "recipe not found" else 400
        return JsonResponse({"ok": False, "error": msg}, status=status)
    preview_renderer = get_graph_preview_renderer()
    serialized = serialize_recipe(recipe, preview_renderer=preview_renderer)
    return JsonResponse({"ok": True, "recipe": serialized})
