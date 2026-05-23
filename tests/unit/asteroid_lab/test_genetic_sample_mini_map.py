"""Genetic sample admin mini-map: ``data-*`` contract, grid neighbors, rotation degrees."""

from __future__ import annotations

from html.parser import HTMLParser

import pytest

from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.adapters.normalization import normalize_decoded_blueprint
from django_apps.asteroid_lab.genetic_sample_mini_map import genetic_sample_mini_map_html
from django_apps.asteroid_lab.lab_screen_grid import mini_map_grid_coord

USER_FLUID_MINER_J_COPY = "SHAPEZ2-4-H4sIAAAAAAACCo2QwQrCMBBE/2XwGA+lByFHUaGgUFRKRUSWNmIgJiVJ0VLy78Z48SKUhYVl38zAjKjAsyxfMCxL8BEzP3QCHIVTpFswFI3Rn8eKPIGfIePNS0X+ZuzDgeleqe+Cu1Mn+L7/Di6BYa29lcJF4YgafJ4xnGIgwzFmbGkwvb9uVC/bndTCrl9eaCdjYGDjB5z/IxOwB8+nOkWjyXid8J/4Q0eNKGUnrhtjn2RbhEssTGqyQyVsEqYWQ3gD2adCLVEBAAA="  # noqa: E501


class _MiniMapCellParser(HTMLParser):
    """Collect ``div.genetic-sample-mini-map-cell`` start tags (row-major order)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cells: list[dict[str, int | str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "div":
            return
        d = {k: v or "" for k, v in attrs}
        cls = d.get("class", "")
        if "genetic-sample-mini-map-cell" not in cls.split():
            return
        self.cells.append(
            {
                "data-server-x": int(d["data-server-x"]),
                "data-server-y": int(d["data-server-y"]),
                "data-grid-row": int(d["data-grid-row"]),
                "data-grid-col": int(d["data-grid-col"]),
                "data-linear-index": int(d["data-linear-index"]),
                "data-sprite": d.get("data-sprite", ""),
                "data-rotation-deg": int(d["data-rotation-deg"]),
            }
        )


def _parse_mini_map_cells(html: str) -> list[dict[str, int | str]]:
    p = _MiniMapCellParser()
    p.feed(html)
    p.close()
    return p.cells


def _by_server(cells: list[dict[str, int | str]]) -> dict[tuple[int, int], dict[str, int | str]]:
    return {(int(c["data-server-x"]), int(c["data-server-y"])): c for c in cells}


@pytest.mark.django_db
def test_for_list_wrap_includes_four_by_four_viewport_css(
    lab_sprite_identifiers_for_admin: object,
) -> None:
    """Changelist mini-map: outer box fits 4×4 cells at 52px (see genetic_sample_mini_map)."""

    decoded = {
        "V": 88,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "SpacePipe_Forward", "R": 0},
            ],
        },
    }
    html = str(genetic_sample_mini_map_html(decoded, for_list=True))
    cell_px, cols, rows, gap, pad = 52, 4, 4, 2, 12
    vw = cols * cell_px + (cols - 1) * gap + pad
    vh = rows * cell_px + (rows - 1) * gap + pad
    assert vw == vh == 226
    assert f"min-width:{vw}px" in html
    assert f"max-height:{vh}px" in html
    assert "border-radius:" in html


@pytest.mark.django_db
def test_mini_map_forward_r_quarters_degrees(
    lab_sprite_identifiers_for_admin: object,
) -> None:
    decoded = {
        "V": 88,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "SpacePipe_Forward", "R": 0},
                {"X": 2, "Y": 0, "T": "SpacePipe_Forward", "R": 1},
                {"X": 3, "Y": 0, "T": "SpacePipe_Forward", "R": 2},
                {"X": 4, "Y": 0, "T": "SpacePipe_Forward", "R": 3},
            ],
        },
    }
    html = str(genetic_sample_mini_map_html(decoded))
    cells = _parse_mini_map_cells(html)
    by_s = _by_server(cells)
    fwd = "SpacePipe/SpacePipe_Forward.svg"
    assert by_s[(1, 0)]["data-sprite"] == fwd and by_s[(1, 0)]["data-rotation-deg"] == 0
    assert by_s[(2, 0)]["data-sprite"] == fwd and by_s[(2, 0)]["data-rotation-deg"] == 90
    assert by_s[(3, 0)]["data-sprite"] == fwd and by_s[(3, 0)]["data-rotation-deg"] == 180
    assert by_s[(4, 0)]["data-sprite"] == fwd and by_s[(4, 0)]["data-rotation-deg"] == 270


@pytest.mark.django_db
def test_mini_map_neighbor_col_and_row_increment(
    lab_sprite_identifiers_for_admin: object,
) -> None:
    decoded = {
        "V": 88,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "SpacePipe_Forward", "R": 0},
                {"X": 2, "Y": 0, "T": "SpacePipe_Forward", "R": 0},
                {"X": 1, "Y": 1, "T": "SpacePipe_Forward", "R": 0},
                {"X": 2, "Y": 1, "T": "SpacePipe_Forward", "R": 0},
            ],
        },
    }
    html = str(genetic_sample_mini_map_html(decoded))
    cells = _parse_mini_map_cells(html)
    by_s = _by_server(cells)
    a00 = by_s[(1, 0)]
    a10 = by_s[(2, 0)]
    a01 = by_s[(1, 1)]
    assert a00["data-grid-row"] == a10["data-grid-row"]
    assert int(a10["data-grid-col"]) == int(a00["data-grid-col"]) + 1
    assert int(a01["data-grid-row"]) == int(a00["data-grid-row"]) + 1
    assert a01["data-grid-col"] == a00["data-grid-col"]


@pytest.mark.django_db
def test_mini_map_data_attrs_match_mini_map_grid_coord(
    lab_sprite_identifiers_for_admin: object,
) -> None:
    decoded = {
        "V": 88,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "SpacePipe_Forward", "R": 0},
                {"X": 2, "Y": 1, "T": "SpacePipe_LeftTurn", "R": 0},
            ],
        },
    }
    html = str(genetic_sample_mini_map_html(decoded))
    cells = _parse_mini_map_cells(html)
    from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
        build_decoded_blueprint_snapshot,
    )

    snap = build_decoded_blueprint_snapshot(decoded)
    bbox = snap.bbox_json
    sminx = int(bbox["min_x"])
    sminy = int(bbox["min_y"])
    sw = max(int(bbox["width"]), 4)
    for c in cells:
        sx = int(c["data-server-x"])
        sy = int(c["data-server-y"])
        g = mini_map_grid_coord(sx, sy, server_min_x=sminx, server_min_y=sminy, server_width=sw)
        assert c["data-grid-row"] == g.row
        assert c["data-grid-col"] == g.col
        assert c["data-linear-index"] == g.linear_index


@pytest.mark.django_db
def test_mini_map_renders_distinct_cells_when_raw_x_zero_and_one_share_row(
    lab_sprite_identifiers_for_admin: object,
) -> None:
    """Regression: ``X==0`` miner and ``X==1`` pipe must not collide on one server cell."""

    norm = normalize_decoded_blueprint(
        decode_copy_string(USER_FLUID_MINER_J_COPY.strip().removesuffix("$"))
    )
    html = str(genetic_sample_mini_map_html(norm.decoded_json))
    by_s = _by_server(_parse_mini_map_cells(html))
    assert (0, -1) in by_s
    assert (1, -1) in by_s
    assert "Miner/" in str(by_s[(0, -1)]["data-sprite"])
    assert "SpacePipe/" in str(by_s[(1, -1)]["data-sprite"])


@pytest.mark.django_db
def test_mini_map_left_and_right_turn_sprites(
    lab_sprite_identifiers_for_admin: object,
) -> None:
    decoded = {
        "V": 88,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "SpacePipe_LeftTurn", "R": 0},
                {"X": 2, "Y": 0, "T": "SpacePipe_RightTurn", "R": 0},
            ],
        },
    }
    html = str(genetic_sample_mini_map_html(decoded))
    by_s = _by_server(_parse_mini_map_cells(html))
    assert by_s[(1, 0)]["data-sprite"] == "SpacePipe/SpacePipe_LeftTurn.svg"
    assert by_s[(2, 0)]["data-sprite"] == "SpacePipe/SpacePipe_RightTurn.svg"
