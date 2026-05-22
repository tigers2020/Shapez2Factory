"""Provenance-preserving shape_recipe import (shapes.json + items.json)."""

from __future__ import annotations

from typing import Any

from django_apps.game_data.importers.base import ImportContext, dig
from django_apps.game_data.models import (
    FluidColor,
    ShapeComponentKind,
    ShapeQuadrantSlot,
    ShapeRecipe,
    ShapeRecipeLayer,
    ShapeRecipeSourceAppearance,
)
from django_apps.game_data.services import identifiers


def _shape_definition(row: dict[str, Any]) -> dict[str, Any]:
    snap = row.get("definition_snapshot") or {}
    if isinstance(snap.get("Definition"), dict):
        return snap["Definition"]
    return snap if isinstance(snap, dict) else {}


def refresh_primary_source_object(recipe: ShapeRecipe) -> None:
    """First FULL appearance wins; else first ITEMS."""
    full_app = (
        ShapeRecipeSourceAppearance.objects.filter(
            shape_recipe=recipe,
            catalog_source=ShapeRecipeSourceAppearance.CatalogSource.FULL,
        )
        .select_related("source_object")
        .order_by("source_row_index")
        .first()
    )
    if full_app is not None:
        primary = full_app.source_object
    else:
        items_app = (
            ShapeRecipeSourceAppearance.objects.filter(
                shape_recipe=recipe,
                catalog_source=ShapeRecipeSourceAppearance.CatalogSource.ITEMS,
            )
            .select_related("source_object")
            .order_by("source_row_index")
            .first()
        )
        primary = items_app.source_object if items_app else None
    if primary is not None and recipe.source_object_id != primary.pk:
        recipe.source_object = primary
        recipe.save(update_fields=["source_object"])


def import_shape_rows(
    ctx: ImportContext,
    *,
    catalog_source: str,
    filename: str,
    rows: list[dict[str, Any]],
    record_source_row: Any,
) -> None:
    touched_recipe_ids: set[int] = set()
    for i, row in enumerate(rows):
        defn = _shape_definition(row)
        op_uid = int(defn.get("UniqueOperationId") or dig(defn, "Id", "Uid") or 0)
        shape_hash = str(defn.get("Hash", ""))
        if not op_uid or not shape_hash:
            continue
        src = record_source_row(filename, i, row)
        cid = identifiers.canonical_shape_recipe(op_uid, shape_hash)
        recipe_defaults: dict[str, Any] = {
            "import_batch": ctx.batch,
            "operation_uid": op_uid,
            "shape_hash": shape_hash,
            "quadrant_count": int(defn.get("PartCount", 4)),
            "layer_count": len(defn.get("Layers") or []),
            "source_stable_id": str(row.get("stable_id", "")),
            "source_object": src,
        }
        recipe, _created = ShapeRecipe.objects.update_or_create(
            canonical_id=cid,
            defaults=recipe_defaults,
        )

        ShapeRecipeSourceAppearance.objects.update_or_create(
            import_batch=ctx.batch,
            artifact_filename=filename,
            source_row_index=i,
            defaults={
                "shape_recipe": recipe,
                "source_object": src,
                "catalog_source": catalog_source,
            },
        )
        ShapeRecipeLayer.objects.filter(shape_recipe=recipe).delete()
        ShapeQuadrantSlot.objects.filter(layer__shape_recipe=recipe).delete()
        for layer_index, layer in enumerate(defn.get("Layers") or []):
            layer_cid = identifiers.canonical_shape_layer(cid, layer_index)
            layer_obj, _ = ShapeRecipeLayer.objects.update_or_create(
                canonical_id=layer_cid,
                defaults={
                    "shape_recipe": recipe,
                    "layer_index": layer_index,
                    "sort_order": layer_index,
                },
            )
            for qidx, part in enumerate(layer.get("Parts") or []):
                shape_name = dig(part, "Shape", "name", default="") or ""
                color_name = dig(part, "Color", "name", default="") or ""
                comp = None
                if shape_name:
                    comp_cid = identifiers.canonical_component_kind(shape_name)
                    comp, _ = ShapeComponentKind.objects.update_or_create(
                        canonical_id=comp_cid,
                        defaults={"component_key": shape_name},
                    )
                fluid = None
                if color_name:
                    fluid = FluidColor.objects.filter(color_name=color_name).first()
                slot_cid = identifiers.canonical_quadrant_slot(layer_cid, qidx)
                ShapeQuadrantSlot.objects.update_or_create(
                    canonical_id=slot_cid,
                    defaults={
                        "layer": layer_obj,
                        "quadrant_index": qidx,
                        "shape_component_kind": comp,
                        "fluid_color": fluid,
                        "is_empty_shape": shape_name == "",
                        "is_empty_color": color_name == "",
                    },
                )
        touched_recipe_ids.add(recipe.pk)
        ctx.bump("shape_recipe")
        ctx.bump("shape_recipe_source_appearance")

    for recipe in ShapeRecipe.objects.filter(pk__in=touched_recipe_ids):
        refresh_primary_source_object(recipe)
