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
from django_apps.asteroid_lab.services.sample_gene_exhaustive_generator import (
    build_layout_root,
    encode_layout_with_suffix,
    generate_exhaustive_sample_genes,
)
from django_apps.asteroid_lab.snapshots.blueprint_equivalence import decoded_json_layout_equivalent
from django_apps.asteroid_lab.snapshots.server_coords import attach_server_coords_to_decoded_json

CONNECTED_BRANCH_GENE_KEY = (
    '{"e":[[[-1,1],[-1,2],"S"],[[0,0],[0,1],"S"],[[0,1],[-1,1],"W"]],"ec":3,"tk":"pipe"}'
)


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


def test_connected_branch_gene_encode_json_matches_user_golden_bytes() -> None:
    genes, _stats = generate_exhaustive_sample_genes(max_extensions=3)
    match = next(g for g in genes if g.key == CONNECTED_BRANCH_GENE_KEY)
    official = to_official_island_root(match.layout_json)
    body = serialize_game_island_export_bytes(official)
    assert body == CONNECTED_BRANCH_FLUID_PIPE_JSON_BYTES
    assert export_dense_x_is_contiguous(official["BP"]["Entries"])


def test_connected_branch_gene_layout_equivalent_to_fixture_decode() -> None:
    genes, _stats = generate_exhaustive_sample_genes(max_extensions=3)
    match = next(g for g in genes if g.key == CONNECTED_BRANCH_GENE_KEY)
    official = to_official_island_root(match.layout_json)
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


def test_connected_branch_gene_encode_not_equal_spread_bug_fixture() -> None:
    genes, _stats = generate_exhaustive_sample_genes(max_extensions=3)
    match = next(g for g in genes if g.key == CONNECTED_BRANCH_GENE_KEY)
    got = match.encoded_copy_string.strip().removesuffix("$")
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
