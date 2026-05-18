"""Genetic sample admin mini-map: grid row order matches Lab replay (raw Y increases downward)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.genetic_sample_mini_map import genetic_sample_mini_map_html


@pytest.mark.django_db
def test_genetic_sample_mini_map_top_row_is_smaller_raw_y() -> None:
    decoded = {
        "V": 88,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "SpacePipe_Forward", "R": 0},
                {"X": 1, "Y": 1, "T": "SpacePipe_LeftTurn", "R": 0},
            ],
        },
    }
    html = str(genetic_sample_mini_map_html(decoded))
    # Sprite URLs require identifier rows; tile type text is always emitted for non-empty T.
    assert "SpacePipe_Forward" in html
    assert "SpacePipe_LeftTurn" in html
    assert html.index("SpacePipe_Forward") < html.index("SpacePipe_LeftTurn")
