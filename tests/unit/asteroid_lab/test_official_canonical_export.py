"""Official island export: dense anchor, connected-branch golden JSON, spread bug regression."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.asteroid_lab.adapters.blueprint_canonical_export import (
    CONNECTED_BRANCH_FLUID_PIPE_COPY,
    CONNECTED_BRANCH_FLUID_PIPE_JSON_BYTES,
    export_dense_x_is_contiguous,
    serialize_game_island_export_bytes,
    to_official_island_root,
)
from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.genetic_sample.exhaustive_generator import (
    GeneratedSampleGene,
    build_layout_root,
    encode_layout_with_suffix,
)
from django_apps.asteroid_lab.snapshots.blueprint_equivalence import decoded_json_layout_equivalent
from django_apps.asteroid_lab.snapshots.server_coords import attach_server_coords_to_decoded_json


def _fixture_line(name: str) -> str:
    p = Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab" / name
    return p.read_text(encoding="utf-8").splitlines()[0].strip()


def _occupied_server_x_is_contiguous(decoded: dict) -> bool:
    d = dict(decoded)
    attach_server_coords_to_decoded_json(d)
    bp = d.get("BP")
    if not isinstance(bp, dict):
        return False
    entries = bp.get("Entries")
    if not isinstance(entries, list):
        return False
    sxs = [
        int(e["server_x"])
        for e in entries
        if isinstance(e, dict) and isinstance(e.get("server_x"), int)
    ]
    if not sxs:
        return True
    lo, hi = min(sxs), max(sxs)
    return hi - lo + 1 == len(set(sxs))


def test_connected_branch_fixture_matches_module_constant() -> None:
    text = _fixture_line("connected_branch_fluid_pipe.txt")
    assert text == CONNECTED_BRANCH_FLUID_PIPE_COPY


def test_connected_branch_gene_encode_json_matches_user_golden_bytes(
    connected_branch_gene_ext3: GeneratedSampleGene,
) -> None:
    official = to_official_island_root(connected_branch_gene_ext3.layout_json)
    body = serialize_game_island_export_bytes(official)
    assert body == CONNECTED_BRANCH_FLUID_PIPE_JSON_BYTES
    assert export_dense_x_is_contiguous(official["BP"]["Entries"])


def test_connected_branch_gene_layout_equivalent_to_fixture_decode(
    connected_branch_gene_ext3: GeneratedSampleGene,
) -> None:
    official = to_official_island_root(connected_branch_gene_ext3.layout_json)
    ref = decode_copy_string(CONNECTED_BRANCH_FLUID_PIPE_COPY).root
    assert decoded_json_layout_equivalent(official, ref, include_transport=True)


def test_encode_layout_with_suffix_roundtrip_decode() -> None:
    exts = [
        {"id": "E1", "coord": (0, 1), "parent_id": "E0", "parent_coord": (0, 0), "attach_dir": "S"},
        {"id": "E2", "coord": (0, 2), "parent_id": "E1", "parent_coord": (0, 1), "attach_dir": "S"},
        {"id": "E3", "coord": (0, 3), "parent_id": "E2", "parent_coord": (0, 2), "attach_dir": "S"},
    ]
    lab = build_layout_root(transport_kind="pipe", exts=exts)
    code = encode_layout_with_suffix(lab)
    dto = decode_copy_string(code.strip().removesuffix("$"))
    assert dto.root["V"] == 1137
    assert dto.root["BP"]["BinaryVersion"] == 1137
    assert export_dense_x_is_contiguous(dto.root["BP"]["Entries"])


def test_serialize_rejects_non_official_icon() -> None:
    exts = [
        {"id": "E1", "coord": (0, 1), "parent_id": "E0", "parent_coord": (0, 0), "attach_dir": "S"},
    ]
    lab = build_layout_root(transport_kind="pipe", exts=exts)
    official = to_official_island_root(lab)
    official["BP"]["Icon"] = {"Data": ["icon:Platforms", None, None, "shape:CuCuCuCu"]}
    with pytest.raises(ValueError, match="OFFICIAL_ISLAND_ICON"):
        serialize_game_island_export_bytes(official)


def test_west_branch_official_entries_no_x_minus_three() -> None:
    exts = [
        {
            "id": "E1",
            "coord": (-1, 0),
            "parent_id": "E0",
            "parent_coord": (0, 0),
            "attach_dir": "W",
        },
        {
            "id": "E2",
            "coord": (-1, 1),
            "parent_id": "E1",
            "parent_coord": (-1, 0),
            "attach_dir": "S",
        },
        {"id": "E3", "coord": (0, 1), "parent_id": "E0", "parent_coord": (0, 0), "attach_dir": "S"},
    ]
    lab = build_layout_root(transport_kind="pipe", exts=exts)
    official = to_official_island_root(lab)
    for row in official["BP"]["Entries"]:
        assert row.get("X") != -3
    assert export_dense_x_is_contiguous(official["BP"]["Entries"])
    assert _occupied_server_x_is_contiguous(official)


def test_connected_branch_gene_encode_not_equal_spread_bug_fixture(
    connected_branch_gene_ext3: GeneratedSampleGene,
) -> None:
    got = connected_branch_gene_ext3.encoded_copy_string.strip().removesuffix("$")
    bug = _fixture_line("spread_branch_fluid_pipe_bug.txt")
    assert got != bug
    assert not decoded_json_layout_equivalent(
        decode_copy_string(got).root,
        decode_copy_string(bug).root,
        include_transport=True,
    )


def test_fixture_spread_branch_decode_has_server_x_hole() -> None:
    bad = decode_copy_string(_fixture_line("spread_branch_fluid_pipe_bug.txt")).root
    assert not _occupied_server_x_is_contiguous(bad)


def test_fixture_connected_branch_decode_server_x_contiguous() -> None:
    good = decode_copy_string(_fixture_line("connected_branch_fluid_pipe.txt")).root
    assert _occupied_server_x_is_contiguous(good)


def test_blueprint_identifier_version_is_resolved_not_hardcoded() -> None:
    """resolve_blueprint_code_version must produce version-dependent prefixes
    and raise ValueError for unknown versions."""
    from django_apps.asteroid_lab.adapters.blueprint_canonical_export import (
        resolve_blueprint_code_version,
    )

    prefix_v4 = resolve_blueprint_code_version(4)
    assert prefix_v4 == "SHAPEZ2-4-"

    with pytest.raises(ValueError):
        resolve_blueprint_code_version(999)


def test_encode_official_copy_string_uses_version_prefix() -> None:
    """encode_official_copy_string with explicit target_game_version must
    produce a string starting with the correct versioned prefix."""
    from django_apps.asteroid_lab.adapters.blueprint_canonical_export import (
        encode_official_copy_string,
        make_minimal_official_root,
    )

    root = make_minimal_official_root()
    result = encode_official_copy_string(root, target_game_version=4)
    assert result.startswith("SHAPEZ2-4-")


def test_encode_official_copy_string_unknown_version_raises() -> None:
    """Passing an unknown target_game_version must raise ValueError."""
    from django_apps.asteroid_lab.adapters.blueprint_canonical_export import (
        encode_official_copy_string,
        make_minimal_official_root,
    )

    root = make_minimal_official_root()
    with pytest.raises(ValueError):
        encode_official_copy_string(root, target_game_version=999)
