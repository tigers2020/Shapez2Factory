"""Run Playwright atomic sprite bake (CLI and admin)."""

from __future__ import annotations

import io
import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from django_apps.web.models import ShapePartSprite
from django_apps.web.services.graph_preview import _playwright_subprocess_env
from django_apps.web.services.shape_part_sprites import (
    MESH_KEY_TO_SHAPE_CODE,
    PEDESTAL_ONLY_MESH_KEY,
    build_atomic_preview_scene,
    build_pedestal_only_preview_scene,
    iter_atomic_sprite_specs,
    make_pedestal_sprite_key,
    make_sprite_key,
)

JOB_CACHE_PREFIX = "shape_part_sprite_job:"
JOB_CACHE_TIMEOUT_SECONDS = 7200


def job_cache_key(job_id: str) -> str:
    return f"{JOB_CACHE_PREFIX}{job_id}"


def merge_job_state(cache_key: str, updates: dict[str, Any]) -> None:
    """Merge ``updates`` into an existing job dict (admin progress polling)."""
    cur = cache.get(cache_key)
    if cur is None:
        return
    merged = {**cur, **updates}
    cache.set(cache_key, merged, timeout=JOB_CACHE_TIMEOUT_SECONDS)


@dataclass(frozen=True, slots=True)
class ShapePartSpriteGenerationStats:
    rendered: int
    skipped: int
    errors: int


def _prepend_pedestal_if_needed(
    atomic_work: list[tuple[str, str, str, int]],
    skipped: int,
    *,
    renderer_version: str,
    skip_existing: bool,
) -> tuple[list[tuple[str, str, str, int]], int]:
    """Pedestal bake runs before quadrant variants when not already stored."""
    spec = (PEDESTAL_ONLY_MESH_KEY, "", "", 0)
    mk, cc, mat, qi = spec
    if skip_existing and _variant_row_exists_with_image(
        mesh_key=mk,
        color_code=cc,
        material_key=mat,
        quadrant_index=qi,
        renderer_version=renderer_version,
    ):
        return atomic_work, skipped + 1
    return [spec] + atomic_work, skipped


def _variant_row_exists_with_image(
    *,
    mesh_key: str,
    color_code: str,
    material_key: str,
    quadrant_index: int,
    renderer_version: str,
) -> bool:
    row = (
        ShapePartSprite.objects.filter(
            mesh_key=mesh_key,
            color_code=color_code,
            material_key=material_key,
            quadrant_index=quadrant_index,
            renderer_version=renderer_version,
        )
        .only("image")
        .first()
    )
    if row is None:
        return False
    name = row.image.name if row.image else ""
    if not name:
        return False
    try:
        return default_storage.exists(name)
    except OSError:
        return False


def _build_work_queue(
    *,
    renderer_version: str,
    skip_existing: bool,
    limit: int | None,
) -> tuple[list[tuple[str, str, str, int]], int]:
    """Return variants to render and how many were skipped as already complete."""
    skipped_count = 0
    if skip_existing:
        work: list[tuple[str, str, str, int]] = []
        for tup in iter_atomic_sprite_specs(limit=None):
            mesh_key, color_code, material_key, quadrant_index = tup
            if _variant_row_exists_with_image(
                mesh_key=mesh_key,
                color_code=color_code,
                material_key=material_key,
                quadrant_index=quadrant_index,
                renderer_version=renderer_version,
            ):
                skipped_count += 1
            else:
                work.append(tup)
                if limit is not None and len(work) >= limit:
                    break
        return _prepend_pedestal_if_needed(
            work,
            skipped_count,
            renderer_version=renderer_version,
            skip_existing=True,
        )
    work = list(iter_atomic_sprite_specs(limit=limit))
    return _prepend_pedestal_if_needed(
        work,
        0,
        renderer_version=renderer_version,
        skip_existing=False,
    )


# One mesh × one color, four quadrants (for admin sample bake).
SAMPLE_QUADRANT_MESH_KEY = "default_rect"
SAMPLE_QUADRANT_COLOR_CODE = "r"
SAMPLE_QUADRANT_MATERIAL_KEY = "r"


def build_sample_quadrant_work_queue(
    *,
    renderer_version: str,
    skip_existing: bool,
) -> tuple[list[tuple[str, str, str, int]], int]:
    """``default_rect`` + red, quadrants 0..3 only; optional skip of complete rows."""
    base = [
        (
            SAMPLE_QUADRANT_MESH_KEY,
            SAMPLE_QUADRANT_COLOR_CODE,
            SAMPLE_QUADRANT_MATERIAL_KEY,
            q,
        )
        for q in range(4)
    ]
    skipped = 0
    work: list[tuple[str, str, str, int]] = []
    for tup in base:
        mesh_key, color_code, material_key, quadrant_index = tup
        if skip_existing and _variant_row_exists_with_image(
            mesh_key=mesh_key,
            color_code=color_code,
            material_key=material_key,
            quadrant_index=quadrant_index,
            renderer_version=renderer_version,
        ):
            skipped += 1
        else:
            work.append(tup)
    return _prepend_pedestal_if_needed(
        work,
        skipped,
        renderer_version=renderer_version,
        skip_existing=skip_existing,
    )


def generate_shape_part_sprites(
    *,
    renderer_version: str = "v1",
    skip_existing: bool = False,
    limit: int | None = None,
    dry_run: bool = False,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    progress_cache_key: str | None = None,
    work_queue: list[tuple[str, str, str, int]] | None = None,
    pre_skipped: int | None = None,
) -> ShapePartSpriteGenerationStats:
    """Bake PNGs for atomic variants; optionally skip rows that already have a stored image file.

    If ``work_queue`` is set (e.g. admin background job), it is used as-is and
    ``skip_existing`` / ``limit`` are ignored.
    """
    out = stdout
    err = stderr

    def _write(msg: str, stream: TextIO | None) -> None:
        if stream is None:
            return
        stream.write(msg)

    if work_queue is not None:
        specs = work_queue
        skipped = pre_skipped if pre_skipped is not None else 0
    else:
        specs, skipped = _build_work_queue(
            renderer_version=renderer_version,
            skip_existing=skip_existing,
            limit=limit,
        )

    if dry_run:
        would = len(specs)
        _write(
            f"Would process {would} sprite variants (skipped_existing={skipped}, dry-run).\n",
            out,
        )
        return ShapePartSpriteGenerationStats(rendered=0, skipped=skipped, errors=0)

    total = len(specs)
    if total == 0:
        if progress_cache_key:
            merge_job_state(
                progress_cache_key,
                {
                    "status": "done",
                    "total": 0,
                    "current": 0,
                    "skipped": skipped,
                    "rendered": 0,
                    "errors": 0,
                },
            )
        return ShapePartSpriteGenerationStats(rendered=0, skipped=skipped, errors=0)

    if progress_cache_key:
        merge_job_state(
            progress_cache_key,
            {
                "status": "running",
                "total": total,
                "current": 0,
                "skipped": skipped,
                "rendered": 0,
                "errors": 0,
            },
        )

    script_path = Path(settings.BASE_DIR) / "scripts" / "render_part_sprite.mjs"
    if not script_path.is_file():
        _write(f"Missing renderer script: {script_path}\n", err)
        if progress_cache_key:
            merge_job_state(
                progress_cache_key,
                {"status": "error", "message": f"Missing renderer script: {script_path}"},
            )
        return ShapePartSpriteGenerationStats(rendered=0, skipped=skipped, errors=0)

    node_bin = _which_node()
    if node_bin is None:
        _write("node executable not found on PATH.\n", err)
        if progress_cache_key:
            merge_job_state(
                progress_cache_key,
                {"status": "error", "message": "node executable not found on PATH."},
            )
        return ShapePartSpriteGenerationStats(rendered=0, skipped=skipped, errors=0)

    try:
        from PIL import Image  # noqa: PLC0415
    except ImportError as exc:
        _write("Pillow is required (pip install pillow).\n", err)
        raise RuntimeError("Pillow is required (pip install pillow).") from exc

    env = _playwright_subprocess_env()
    ok = 0
    n_err = 0
    for i, (mesh_key, color_code, material_key, quadrant_index) in enumerate(specs, start=1):
        if mesh_key == PEDESTAL_ONLY_MESH_KEY:
            sprite_key = make_pedestal_sprite_key(renderer_version)
            scene = build_pedestal_only_preview_scene()
        else:
            shape_code = MESH_KEY_TO_SHAPE_CODE.get(mesh_key)
            if shape_code is None:
                raise ValueError(f"unknown mesh_key for sprite bake: {mesh_key!r}")
            sprite_key = make_sprite_key(shape_code, color_code, quadrant_index, renderer_version)
            scene = build_atomic_preview_scene(mesh_key, color_code, material_key, quadrant_index)
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".json",
                delete=False,
                encoding="utf-8",
            ) as tf:
                json.dump(scene, tf, separators=(",", ":"))
                scene_path = Path(tf.name)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as pf:
                png_path = Path(pf.name)
            try:
                subprocess.run(
                    [
                        node_bin,
                        str(script_path),
                        "--scene-file",
                        str(scene_path),
                        "--out",
                        str(png_path),
                    ],
                    check=True,
                    env=env,
                    timeout=120,
                    cwd=str(settings.BASE_DIR),
                )
            finally:
                scene_path.unlink(missing_ok=True)

            png_bytes = png_path.read_bytes()
            png_path.unlink(missing_ok=True)

            with Image.open(io.BytesIO(png_bytes)) as im:
                w, h = im.size

            safe_name = sprite_key.replace(":", "_") + ".png"
            defaults = {
                "sprite_key": sprite_key,
                "image_width": w,
                "image_height": h,
                "image": ContentFile(png_bytes, name=safe_name),
            }
            ShapePartSprite.objects.update_or_create(
                mesh_key=mesh_key,
                color_code=color_code,
                material_key=material_key,
                quadrant_index=quadrant_index,
                renderer_version=renderer_version,
                defaults=defaults,
            )
            ok += 1
        except (OSError, subprocess.CalledProcessError, ValueError) as e:
            _write(f"{sprite_key}: {e}\n", err)
            n_err += 1

        if progress_cache_key:
            merge_job_state(
                progress_cache_key,
                {
                    "current": i,
                    "rendered": ok,
                    "errors": n_err,
                },
            )

    if progress_cache_key:
        merge_job_state(
            progress_cache_key,
            {
                "status": "done",
                "current": total,
                "rendered": ok,
                "errors": n_err,
            },
        )

    return ShapePartSpriteGenerationStats(rendered=ok, skipped=skipped, errors=n_err)


def _which_node() -> str | None:
    import shutil

    return shutil.which("node")


__all__ = [
    "JOB_CACHE_PREFIX",
    "JOB_CACHE_TIMEOUT_SECONDS",
    "ShapePartSpriteGenerationStats",
    "build_sample_quadrant_work_queue",
    "generate_shape_part_sprites",
    "job_cache_key",
    "merge_job_state",
]
