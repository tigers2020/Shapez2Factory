from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import Client

from django_apps.shapez_asteroid.models import AsteroidCellStatusKind, AsteroidMapCell
from django_apps.shapez_asteroid.services.asteroid_map_cells import (
    list_map_cells_json,
    parse_bbox,
)


@pytest.mark.django_db
def test_map_cell_rejects_x_zero() -> None:
    void = AsteroidCellStatusKind.objects.get(slug="void")
    cell = AsteroidMapCell(x=0, y=1, kind=void)
    with pytest.raises(ValidationError):
        cell.full_clean()


@pytest.mark.django_db
def test_map_cell_unique_xy() -> None:
    k = AsteroidCellStatusKind.objects.get(slug="shape_asteroid")
    AsteroidMapCell.objects.create(x=2, y=3, kind=k)
    with pytest.raises(IntegrityError):
        AsteroidMapCell.objects.create(x=2, y=3, kind=k)


def test_parse_bbox_missing_param() -> None:
    from django.http import QueryDict

    err, bbox = parse_bbox(QueryDict())
    assert bbox is None
    assert err is not None
    assert err["ok"] is False


def test_parse_bbox_rejects_x_zero_inside_range() -> None:
    from django.http import QueryDict

    err, bbox = parse_bbox(QueryDict("x_min=-1&x_max=1&y_min=0&y_max=0"))
    assert bbox is None
    assert err is not None
    assert "x=0" in err["error"]


def test_parse_bbox_accepts_negative_x_block() -> None:
    from django.http import QueryDict

    err, bbox = parse_bbox(QueryDict("x_min=-5&x_max=-1&y_min=-2&y_max=2"))
    assert err is None
    assert bbox == (-5, -1, -2, 2)


@pytest.mark.django_db
def test_list_map_cells_json_void_defaults() -> None:
    body = list_map_cells_json(1, 2, 0, 1)
    assert body["ok"] is True
    assert body["cells"] == []
    assert body["void_slug"] == "void"
    assert body["void_label"] == "void"


@pytest.mark.django_db
def test_list_map_cells_json_returns_rows() -> None:
    k = AsteroidCellStatusKind.objects.get(slug="fluid_asteroid")
    AsteroidMapCell.objects.create(x=-1, y=2, kind=k)
    body = list_map_cells_json(-2, 3, 0, 5)
    assert body["cells"] == [{"x": -1, "y": 2, "slug": "fluid_asteroid", "label": "fluid asteroid"}]


@pytest.mark.django_db
def test_map_cells_api_400_and_200() -> None:
    client = Client()
    r = client.get("/api/asteroid/map-cells/")
    assert r.status_code == 400
    err = r.json()
    assert err["error_code"] == "bbox_missing_params"
    r2 = client.get("/api/asteroid/map-cells/?x_min=1&x_max=3&y_min=0&y_max=1")
    assert r2.status_code == 200
    data = r2.json()
    assert data["ok"] is True
    assert data["cells"] == []
