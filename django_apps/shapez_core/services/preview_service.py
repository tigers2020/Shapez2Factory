from __future__ import annotations

import json
from typing import Any

from django_apps.shapez_core.domain.shape_catalog import (
    COLOR_KINDS,
    SHAPE_KINDS,
    ColorKind,
    ShapeKind,
)
from django_apps.shapez_core.domain.shape_pattern import NormalizedShapePattern
from django_apps.shapez_core.services.shape_code_parser import (
    ShapeCodeParseError,
    parse_shape_code_list,
)
from django_apps.shapez_core.services.shape_render_scene import (
    ShapeRenderScene,
    build_shape_render_scene,
)


def get_shape_catalog_rows() -> list[ShapeKind]:
    return sorted(
        SHAPE_KINDS.values(),
        key=lambda shape_kind: (shape_kind.empty, shape_kind.code.lower()),
    )


def get_color_catalog_rows() -> list[ColorKind]:
    return sorted(COLOR_KINDS.values(), key=lambda color_kind: (color_kind.empty, color_kind.code))


def build_demo_parse_rows(try_code: str, fixed_samples: tuple[str, ...]) -> list[dict[str, Any]]:
    parse_rows: list[dict[str, Any]] = []
    if try_code:
        parse_rows.append(build_demo_parse_row(try_code))

    for sample in fixed_samples:
        if try_code and sample == try_code:
            continue
        parse_rows.append(build_demo_parse_row(sample))
    return parse_rows


def build_shape_preview_response(code: str) -> tuple[dict[str, Any], int]:
    stripped_code = code.strip()
    if not stripped_code:
        return (
            {
                "ok": False,
                "error": "Shape code is empty.",
                "input": "",
                "warnings": [],
                "patterns": [],
            },
            400,
        )

    row = build_demo_parse_row(stripped_code)
    if not row["ok"]:
        return (
            {
                "ok": False,
                "error": row["error"],
                "input": row["input"],
                "warnings": [],
                "patterns": [],
            },
            200,
        )

    warnings: list[str] = []
    patterns_payload: list[dict[str, Any]] = []
    for pattern in row["patterns"]:
        if pattern["raw_code"] != pattern["normalized_code"]:
            warnings.append(
                f"Pattern '{pattern['raw_code']}' was normalized to '{pattern['normalized_code']}'."
            )
        patterns_payload.append({"preview_scene": pattern["preview_scene"]})

    return (
        {
            "ok": True,
            "error": None,
            "input": row["input"],
            "warnings": warnings,
            "patterns": patterns_payload,
        },
        200,
    )


def build_demo_parse_row(code: str) -> dict[str, Any]:
    try:
        patterns = parse_shape_code_list(code)
        pattern_rows: list[dict[str, Any]] = []
        for pattern in patterns:
            scene = build_shape_render_scene(pattern)
            serialized_scene = _serialize_render_scene(scene)
            pattern_rows.append(
                {
                    **_serialize_pattern(pattern),
                    "preview_scene": serialized_scene,
                    "preview_scene_json": json.dumps(serialized_scene),
                }
            )
        return {
            "input": code,
            "ok": True,
            "error": None,
            "patterns": pattern_rows,
        }
    except ShapeCodeParseError as exc:
        return {
            "input": code,
            "ok": False,
            "error": str(exc),
            "patterns": [],
        }


def _serialize_pattern(pattern: NormalizedShapePattern) -> dict[str, Any]:
    return {
        "raw_code": pattern.raw_code,
        "normalized_code": pattern.normalized_code,
        "layers": [
            {
                "layer_index": layer.layer_index,
                "cells": [
                    {
                        "quadrant_index": cell.quadrant_index,
                        "position": cell.position.value,
                        "shape_code": cell.shape_code,
                        "color_code": cell.color_code,
                        "shape_kind": cell.shape_kind,
                        "color_kind": cell.color_kind,
                        "raw_token": cell.raw_token,
                    }
                    for cell in layer.cells
                ],
            }
            for layer in pattern.layers
        ],
    }


def _serialize_render_scene(scene: ShapeRenderScene) -> dict[str, Any]:
    return {
        "normalized_code": scene.normalized_code,
        "cells": [
            {
                "layer_index": cell.layer_index,
                "quadrant_index": cell.quadrant_index,
                "position": cell.position.value,
                "shape_code": cell.shape_code,
                "color_code": cell.color_code,
                "shape_kind": cell.shape_kind,
                "color_kind": cell.color_kind,
                "mesh_key": cell.mesh_key,
                "material_key": cell.material_key,
                "transform_key": cell.transform_key,
            }
            for cell in scene.cells
        ],
    }
