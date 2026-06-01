"""Admin list thumbnail ??hash, bbox cap, raster bytes."""

from __future__ import annotations

from django_apps.asteroid_lab.admin_map_list_thumbnail import (
    ADMIN_LIST_THUMBNAIL_RENDERER_VERSION,
    canonical_decoded_json_hash,
    compute_list_thumbnail_window,
    render_list_thumbnail_image_bytes,
)


def test_canonical_hash_stable_key_order() -> None:
    a = {"BP": {"Entries": []}, "V": 1}
    b = {"V": 1, "BP": {"Entries": []}}
    assert canonical_decoded_json_hash(a) == canonical_decoded_json_hash(b)


def test_canonical_hash_changes_when_entries_change() -> None:
    base = {"V": 1, "BP": {"Entries": [{"X": 1, "Y": 1, "T": "SpaceBelt_Forward", "R": 0}]}}
    other = {"V": 1, "BP": {"Entries": [{"X": 2, "Y": 1, "T": "SpaceBelt_Forward", "R": 0}]}}
    assert canonical_decoded_json_hash(base) != canonical_decoded_json_hash(other)


def test_compute_window_caps_at_48_and_sets_truncated() -> None:
    entries = [{"X": x, "Y": 0, "T": "SpaceBelt_Forward", "R": 0} for x in range(1, 80)]
    decoded = {"V": 1, "BP": {"$type": "Island", "Entries": entries}}
    win = compute_list_thumbnail_window(decoded)
    assert win is not None
    assert win.grid_w <= 48
    assert win.truncated is True


def test_compute_window_crop_stays_inside_tight_bbox() -> None:
    entries = [{"X": x, "Y": 1, "T": "SpaceBelt_Forward", "R": 0} for x in range(1, 80)]
    decoded = {"V": 1, "BP": {"$type": "Island", "Entries": entries}}
    win = compute_list_thumbnail_window(decoded)
    assert win is not None
    assert win.min_x >= 1
    assert win.min_x + win.grid_w - 1 <= 79
    assert win.min_y >= 1
    assert win.min_y + win.grid_h - 1 <= 1


def test_renderer_version_is_non_empty() -> None:
    assert ADMIN_LIST_THUMBNAIL_RENDERER_VERSION


def test_render_list_thumbnail_returns_webp_or_png_bytes() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 1, "T": "SpaceBelt_Forward", "R": 0},
                {"X": 2, "Y": 1, "T": "Layout_ShapeMiner", "R": 0},
            ],
        },
    }
    data, ext = render_list_thumbnail_image_bytes(decoded)
    assert ext in ("webp", "png")
    assert len(data) > 64
