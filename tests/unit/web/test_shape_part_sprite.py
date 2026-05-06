"""Tests for atomic part sprite helpers and manifest API."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.test import Client, override_settings

from django_apps.web.models import ShapePartSprite
from django_apps.web.services.shape_part_sprite_generation import (
    SAMPLE_QUADRANT_MESH_KEY,
    build_sample_quadrant_work_queue,
)
from django_apps.web.services.shape_part_sprites import (
    PEDESTAL_ONLY_MESH_KEY,
    atomic_layer_game_code,
    build_atomic_preview_scene,
    build_pedestal_only_preview_scene,
    iter_atomic_sprite_specs,
    make_sprite_key,
)

User = get_user_model()


def _minimal_png_bytes() -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGBA", (16, 16), (10, 11, 28, 255)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.django_db
def test_manifest_requires_staff(tmp_path: Path) -> None:
    media = tmp_path / "media"
    media.mkdir()
    with override_settings(MEDIA_ROOT=media):
        client = Client()
        rsp = client.get("/internal/staff/shape-part-sprites/manifest/")
        assert rsp.status_code == 302

        user = User.objects.create_user("u1", password="pass-word-123")
        client.force_login(user)
        rsp = client.get("/internal/staff/shape-part-sprites/manifest/")
        assert rsp.status_code == 403


@pytest.mark.django_db
def test_manifest_json_shape(tmp_path: Path) -> None:
    sprite_root = tmp_path / "shape_static_web"
    sprite_root.mkdir(parents=True)
    with override_settings(
        SHAPE_PART_SPRITE_STATIC_ROOT=sprite_root,
        SHAPE_PART_SPRITE_URL_PREFIX="/static/web/",
    ):
        staff = User.objects.create_user("staff", password="pass-word-123", is_staff=True)
        sprite_key = make_sprite_key("R", "r", 0, "v1")
        png = _minimal_png_bytes()
        ShapePartSprite.objects.create(
            sprite_key=sprite_key,
            mesh_key="default_rect",
            color_code="r",
            material_key="r",
            quadrant_index=0,
            image=ContentFile(png, name="t.png"),
            image_width=16,
            image_height=16,
            renderer_version="v1",
        )
        client = Client()
        client.force_login(staff)
        rsp = client.get("/internal/staff/shape-part-sprites/manifest/")
        assert rsp.status_code == 200
        data = rsp.json()
        assert data["renderer_version"] == "v1"
        assert sprite_key in data["sprites"]
        entry = data["sprites"][sprite_key]
        assert entry["width"] == 16
        assert entry["height"] == 16
        assert entry["url"].startswith("/static/web/")


def test_make_sprite_key_stable() -> None:
    assert make_sprite_key("R", "r", 0, "v1") == "Rr------:v1"


def test_atomic_layer_game_code_examples() -> None:
    assert atomic_layer_game_code("C", "r", 0) == "Cr------"
    assert atomic_layer_game_code("W", "b", 2) == "----Wb--"


def test_build_atomic_preview_scene_single_cell() -> None:
    scene = build_atomic_preview_scene("default_rect", "r", "r", 0)
    assert scene["normalized_code"] == "Rr------"
    assert scene.get("include_pedestal") is False
    assert scene.get("transparent_background") is True
    cells = scene["cells"]
    assert isinstance(cells, list) and len(cells) == 1
    c0 = cells[0]
    assert c0["mesh_key"] == "default_rect"
    assert c0["quadrant_index"] == 0


def test_build_pedestal_only_preview_scene() -> None:
    scene = build_pedestal_only_preview_scene()
    assert scene["normalized_code"] == "--------"
    assert scene["cells"] == []
    assert scene.get("include_pedestal") is True
    assert scene.get("transparent_background") is True


def test_iter_atomic_sprite_specs_limit() -> None:
    specs = list(iter_atomic_sprite_specs(limit=3))
    assert len(specs) == 3


@pytest.mark.django_db
def test_build_sample_quadrant_work_queue_pedestal_first() -> None:
    specs, skipped = build_sample_quadrant_work_queue(
        renderer_version="v1",
        skip_existing=True,
    )
    assert skipped == 0
    assert len(specs) == 5
    assert specs[0][0] == PEDESTAL_ONLY_MESH_KEY
    rest = specs[1:]
    assert sorted(t[3] for t in rest) == [0, 1, 2, 3]
    assert all(t[0] == SAMPLE_QUADRANT_MESH_KEY for t in rest)


@pytest.mark.django_db
def test_build_work_queue_prepends_pedestal() -> None:
    from django_apps.web.services.shape_part_sprite_generation import _build_work_queue

    specs, skipped = _build_work_queue(
        renderer_version="v1",
        skip_existing=False,
        limit=0,
    )
    assert skipped == 0
    assert len(specs) == 1
    assert specs[0][0] == PEDESTAL_ONLY_MESH_KEY


@pytest.mark.django_db
def test_shape_part_sprite_unique_constraint(tmp_path: Path) -> None:
    sprite_root = tmp_path / "shape_static_web"
    sprite_root.mkdir(parents=True)
    with override_settings(
        SHAPE_PART_SPRITE_STATIC_ROOT=sprite_root,
        SHAPE_PART_SPRITE_URL_PREFIX="/static/web/",
    ):
        png = _minimal_png_bytes()
        ShapePartSprite.objects.create(
            sprite_key=make_sprite_key("C", "g", 2, "v1"),
            mesh_key="default_circle",
            color_code="g",
            material_key="g",
            quadrant_index=2,
            image=ContentFile(png, name="a.png"),
            image_width=8,
            image_height=8,
            renderer_version="v1",
        )
        with pytest.raises(IntegrityError):
            ShapePartSprite.objects.create(
                sprite_key=make_sprite_key("C", "g", 2, "v1") + "_x",
                mesh_key="default_circle",
                color_code="g",
                material_key="g",
                quadrant_index=2,
                image=ContentFile(png, name="b.png"),
                image_width=8,
                image_height=8,
                renderer_version="v1",
            )
