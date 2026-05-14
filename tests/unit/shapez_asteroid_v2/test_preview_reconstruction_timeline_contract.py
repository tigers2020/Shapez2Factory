"""v2 preview map timeline: mining_map rows must reflect full reconstruction, not shell-only."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2 import (
    preview_reconstruction_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction import (
    reconstruct_asteroid_mining_field,
)

_dominant_surface_for_shell = preview_reconstruction_timeline._dominant_surface_for_shell
build_v2_preview_map_frames = preview_reconstruction_timeline.build_v2_preview_map_frames
PREVIEW_TILE = preview_reconstruction_timeline.PREVIEW_ASTEROID_REPLACE_TILE_T


def test_transport_shell_frame_includes_extractors_without_asteroid_field_tiles() -> None:
    """Regression: shell = AsteroidField* only; island layouts still need visible cells."""

    decoded = {
        "BP": {
            "Entries": [
                {"X": 5, "Y": 5, "T": "Layout_FluidMiner"},
                {"X": 6, "Y": 5, "T": "SpacePipe_Straight"},
            ]
        }
    }
    recon = reconstruct_asteroid_mining_field(decoded)
    assert recon.extraction_shell_cells == ()
    assert recon.extractor_cells and recon.pipe_cells

    frames = build_v2_preview_map_frames(decoded, recon, source_kind="existing_fluid_layout")
    first = next(f for f in frames if f.get("id") == "v2_recon_transport_shell")
    mm = first["mining_map"]
    xs = {int(r["x"]) for r in mm}
    assert 5 in xs and 6 in xs
    roles = {(int(r["x"]), int(r["y"])): r.get("role") for r in mm}
    assert roles.get((5, 5)) == "occupied"
    assert roles.get((6, 5)) == "pipe"


def test_transport_shell_frame_includes_asteroid_shell_when_present() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 2, "Y": 2, "T": "AsteroidField_Test"},
                {"X": 3, "Y": 2, "T": "AsteroidField_Test"},
            ]
        }
    }
    recon = reconstruct_asteroid_mining_field(decoded)
    frames = build_v2_preview_map_frames(decoded, recon, source_kind="raw_asteroid_field")
    first = next(f for f in frames if f.get("id") == "v2_recon_transport_shell")
    assert len(first["mining_map"]) >= 2


def test_reconstruction_preview_frame_order_includes_strip_and_inner_patch() -> None:
    entries: list[dict[str, int | str]] = []
    for x in range(2, 7):
        for y in range(2, 7):
            if x in (2, 6) or y in (2, 6):
                entries.append({"X": x, "Y": y, "T": "AsteroidField_Test"})
    entries.append({"X": 7, "Y": 3, "T": "Belt_Straight"})
    entries.append({"X": 4, "Y": 4, "T": "Layout_ShapeMiner"})
    entries.append({"X": 5, "Y": 4, "T": "Layout_ShapeMinerExtension"})
    decoded = {"BP": {"Entries": entries}}
    recon = reconstruct_asteroid_mining_field(decoded)
    frames = build_v2_preview_map_frames(decoded, recon, source_kind="mixed_existing_layout")
    ids = [f.get("id") for f in frames if isinstance(f, dict) and f.get("id")]
    assert ids[:7] == [
        "v2_recon_transport_shell",
        "v2_recon_strip_transport",
        "v2_recon_strip_extractors",
        "v2_recon_strip_extensions",
        "v2_recon_interior_void",
        "v2_recon_inner_patch",
        "v2_recon_mineable",
    ]
    shell = next(f for f in frames if f["id"] == "v2_recon_transport_shell")
    stripped = next(f for f in frames if f["id"] == "v2_recon_strip_transport")
    assert len(shell["mining_map"]) > len(stripped["mining_map"])

    strip_ex = next(f for f in frames if f["id"] == "v2_recon_strip_extractors")
    by_xy_ex = {(int(r["x"]), int(r["y"])): r for r in strip_ex["mining_map"]}
    assert by_xy_ex[(4, 4)]["layout_kind"] == "asteroid_field"
    assert by_xy_ex[(4, 4)].get("t") == PREVIEW_TILE

    strip_ext = next(f for f in frames if f["id"] == "v2_recon_strip_extensions")
    by_xy_sx = {(int(r["x"]), int(r["y"])): r for r in strip_ext["mining_map"]}
    assert by_xy_sx[(5, 4)]["layout_kind"] == "asteroid_field"
    assert by_xy_sx[(5, 4)].get("t") == PREVIEW_TILE

    inner = next(f for f in frames if f["id"] == "v2_recon_inner_patch")
    roles = {((int(r["x"]), int(r["y"])), r.get("role")) for r in inner["mining_map"]}
    assert any(role == "inferred" for (_xy, role) in roles)


def test_dominant_surface_includes_fluid_miner_not_on_shell_tiles() -> None:
    """Shell entries are only ``AsteroidField*`` (no surface hint); fluid miner must set default."""

    entries: list[dict[str, int | str]] = []
    for x in range(2, 7):
        for y in range(2, 7):
            if x in (2, 6) or y in (2, 6):
                entries.append({"X": x, "Y": y, "T": "AsteroidField_Test"})
    entries.append({"X": 4, "Y": 4, "T": "Layout_FluidMiner"})
    decoded = {"BP": {"Entries": entries}}
    recon = reconstruct_asteroid_mining_field(decoded)
    assert _dominant_surface_for_shell(decoded, recon) == "fluid"

    inner = next(
        f
        for f in build_v2_preview_map_frames(decoded, recon, source_kind="mixed_existing_layout")
        if f.get("id") == "v2_recon_inner_patch"
    )
    by_xy = {(int(r["x"]), int(r["y"])): r for r in inner["mining_map"]}
    assert by_xy[(2, 4)]["surface"] == "fluid"


def test_strip_extensions_does_not_fill_voids_from_belt_extension_coord_collision() -> None:
    """Belt + extension at same coord: transport removes the cell; extension strip must not paint."""

    entries: list[dict[str, int | str]] = []
    for x in range(2, 7):
        for y in range(2, 7):
            if x in (2, 6) or y in (2, 6):
                entries.append({"X": x, "Y": y, "T": "AsteroidField_Test"})
    entries.append({"X": 4, "Y": 4, "T": "Belt_Straight"})
    entries.append({"X": 4, "Y": 4, "T": "Layout_ShapeMinerExtension"})
    decoded = {"BP": {"Entries": entries}}
    recon = reconstruct_asteroid_mining_field(decoded)
    assert (4, 4) in recon.belt_cells
    assert (4, 4) in recon.extension_cells

    frames = build_v2_preview_map_frames(decoded, recon, source_kind="mixed_existing_layout")
    strip_ext = next(f for f in frames if f["id"] == "v2_recon_strip_extensions")
    keys = {(int(r["x"]), int(r["y"])) for r in strip_ext["mining_map"]}
    assert (4, 4) not in keys


def test_strip_asteroid_surface_follows_extractor_or_extension_kind() -> None:
    """Preview-replaced field cells inherit shape vs fluid from the stripped equipment ``T``."""

    entries: list[dict[str, int | str]] = []
    for x in range(2, 7):
        for y in range(2, 7):
            if x in (2, 6) or y in (2, 6):
                entries.append({"X": x, "Y": y, "T": "AsteroidField_Test"})
    entries.append({"X": 4, "Y": 4, "T": "Layout_FluidMiner"})
    entries.append({"X": 5, "Y": 4, "T": "Layout_ShapeMiner"})
    entries.append({"X": 5, "Y": 5, "T": "Layout_FluidMinerExtension"})
    entries.append({"X": 4, "Y": 5, "T": "Layout_ShapeMinerExtension"})
    decoded = {"BP": {"Entries": entries}}
    recon = reconstruct_asteroid_mining_field(decoded)
    frames = build_v2_preview_map_frames(decoded, recon, source_kind="mixed_existing_layout")

    strip_ex = next(f for f in frames if f["id"] == "v2_recon_strip_extractors")
    by_ex = {(int(r["x"]), int(r["y"])): r for r in strip_ex["mining_map"]}
    assert by_ex[(4, 4)].get("surface") == "fluid"
    assert by_ex[(5, 4)].get("surface") == "shape"

    strip_ext = next(f for f in frames if f["id"] == "v2_recon_strip_extensions")
    by_sx = {(int(r["x"]), int(r["y"])): r for r in strip_ext["mining_map"]}
    assert by_sx[(5, 5)].get("surface") == "fluid"
    assert by_sx[(4, 5)].get("surface") == "shape"
