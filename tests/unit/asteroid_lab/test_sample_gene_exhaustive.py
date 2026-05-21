"""Exhaustive sample-gene generator and seed command (contract tests)."""

from __future__ import annotations

import copy
from typing import Any

import pytest
from django.core.management import call_command

from django_apps.asteroid_lab.adapters.blueprint_canonical_export import to_official_island_root
from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.models import GeneticSample
from django_apps.asteroid_lab.services.sample_gene_exhaustive_generator import (
    DELTA_NWS,
    OUTPUT_TRANSPORT_GRID,
    abstract_grid_to_raw_xy,
    assert_blueprint_entries_raw_x_nonzero,
    build_layout_root,
    generate_exhaustive_sample_genes,
)
from django_apps.asteroid_lab.snapshots.server_coords import attach_server_coords_to_decoded_json

pytestmark = pytest.mark.slow


def test_assert_blueprint_entries_raw_x_nonzero_raises() -> None:
    with pytest.raises(ValueError, match="raw X==0"):
        assert_blueprint_entries_raw_x_nonzero(
            [{"X": 0, "Y": 0, "R": 0, "T": "Layout_ShapeMiner"}],
        )

    for gx in range(-5, 6):
        rx, _ = abstract_grid_to_raw_xy(gx, 0)
        assert rx != 0


def test_exhaustive_generator_all_layout_entries_raw_x_nonzero() -> None:
    genes, _stats = generate_exhaustive_sample_genes(max_extensions=3)
    for g in genes:
        for row in g.layout_json["BP"]["Entries"]:
            assert row["X"] != 0


def _official_export_occupied_server_x_contiguous(layout_root: dict[str, Any]) -> bool:
    """Lab layout → official island XY → attach_server_coords; no holes in server_x columns."""

    official = to_official_island_root(copy.deepcopy(layout_root))
    d = copy.deepcopy(official)
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


def test_exhaustive_generator_official_export_server_x_always_contiguous() -> None:
    """Dense-delta export_x: west branches must not leave a gap in bbox server_x columns."""

    genes, _stats = generate_exhaustive_sample_genes(max_extensions=3)
    for g in genes:
        assert _official_export_occupied_server_x_contiguous(g.layout_json)


def test_abstract_grid_to_raw_xy_skips_x_zero_column() -> None:
    assert abstract_grid_to_raw_xy(0, 0) == (1, 0)
    assert abstract_grid_to_raw_xy(1, 0) == (2, 0)
    assert abstract_grid_to_raw_xy(-1, 0) == (-1, 0)
    assert abstract_grid_to_raw_xy(0, 1) == (1, 1)
    rx, _ry = abstract_grid_to_raw_xy(0, 0)
    assert rx != 0


def test_exhaustive_generator_includes_extractor_solo() -> None:
    genes, _stats = generate_exhaustive_sample_genes(max_extensions=0)
    solos = [g for g in genes if g.extension_count == 0]
    assert len(solos) == 2
    kinds = {g.transport_kind for g in solos}
    assert kinds == {"belt", "pipe"}
    for g in solos:
        assert len(g.nodes) == 1
        assert g.nodes[0].kind == "extractor"


def test_exhaustive_generator_generates_belt_and_pipe_variants() -> None:
    genes, _stats = generate_exhaustive_sample_genes(max_extensions=3)
    assert {g.transport_kind for g in genes} == {"belt", "pipe"}


def test_exhaustive_generator_extension_count_0_to_3() -> None:
    genes, stats = generate_exhaustive_sample_genes(max_extensions=3)
    by_ec: dict[int, int] = {}
    for g in genes:
        by_ec[g.extension_count] = by_ec.get(g.extension_count, 0) + 1
    assert by_ec == stats.by_extension_count
    assert set(by_ec) == {0, 1, 2, 3}
    assert by_ec[0] == 2


def test_exhaustive_generator_never_attaches_extension_to_r() -> None:
    genes, _stats = generate_exhaustive_sample_genes(max_extensions=3)
    for g in genes:
        for n in g.nodes:
            if n.kind == "extension":
                assert n.attach_dir in DELTA_NWS
                assert n.attach_dir is not None


def test_exhaustive_generator_all_extensions_connected_to_extractor_tree() -> None:
    genes, _stats = generate_exhaustive_sample_genes(max_extensions=3)
    for g in genes:
        by_id = {n.node_id: n for n in g.nodes}
        for n in g.nodes:
            if n.kind == "extension":
                assert n.parent_id is not None
                walk = n.parent_id
                seen = 0
                while walk != "E0" and seen < 10:
                    assert walk in by_id
                    walk = by_id[walk].parent_id or "E0"
                    seen += 1
                assert walk == "E0"


def test_exhaustive_generator_all_coords_unique() -> None:
    genes, _stats = generate_exhaustive_sample_genes(max_extensions=3)
    for g in genes:
        coords = [n.coord for n in g.nodes] + [OUTPUT_TRANSPORT_GRID]
        assert len(coords) == len(set(coords))


def test_exhaustive_generator_output_transport_required_at_r() -> None:
    genes, _stats = generate_exhaustive_sample_genes(max_extensions=3)
    for g in genes:
        assert g.transport_cells == (OUTPUT_TRANSPORT_GRID,)
        entries = g.layout_json["BP"]["Entries"]
        raw_transport = abstract_grid_to_raw_xy(*OUTPUT_TRANSPORT_GRID)
        matches = [e for e in entries if (e["X"], e["Y"]) == raw_transport]
        assert len(matches) == 1
        t = matches[0]["T"]
        assert "Belt" in t or "Pipe" in t


def test_exhaustive_generator_transport_not_occupied() -> None:
    genes, _stats = generate_exhaustive_sample_genes(max_extensions=3)
    for g in genes:
        ext_coords = {n.coord for n in g.nodes if n.kind == "extension"}
        assert OUTPUT_TRANSPORT_GRID not in ext_coords


def test_exhaustive_generator_canonical_keys_unique() -> None:
    genes, _stats = generate_exhaustive_sample_genes(max_extensions=3)
    keys = [g.key for g in genes]
    assert len(keys) == len(set(keys))


def test_exhaustive_generator_names_have_no_spaces() -> None:
    genes, _stats = generate_exhaustive_sample_genes(max_extensions=3)
    for g in genes:
        assert " " not in g.name


def test_exhaustive_generator_copy_string_roundtrip(
    exhaustive_genes_ext3: tuple[list, object],
) -> None:
    genes, _stats = exhaustive_genes_ext3
    for g in genes[:5]:
        assert g.encoded_copy_string.startswith("SHAPEZ2-4-")
        assert g.encoded_copy_string.endswith("$")
        dto = decode_copy_string(g.encoded_copy_string.strip().removesuffix("$"))
        assert dto.root.get("V") == 1137


@pytest.mark.django_db
def test_seed_exhaustive_sample_genes_dry_run_no_write() -> None:
    before = GeneticSample.objects.count()
    call_command(
        "seed_exhaustive_sample_genes",
        "--dry-run",
        verbosity=0,
    )
    after = GeneticSample.objects.count()
    assert after == before


@pytest.mark.django_db
def test_seed_exhaustive_sample_genes_idempotent_update_or_create() -> None:
    def _seeded() -> int:
        return GeneticSample.objects.filter(
            metadata_json__generator="exhaustive_sample_gene_v1",
        ).count()

    call_command("seed_exhaustive_sample_genes", verbosity=0)
    n1 = _seeded()
    call_command("seed_exhaustive_sample_genes", verbosity=0)
    n2 = _seeded()
    assert n1 == n2 == 102


@pytest.mark.django_db
def test_seed_exhaustive_sample_genes_overwrites_stale_decoded_json() -> None:
    call_command("seed_exhaustive_sample_genes", verbosity=0)
    sample = GeneticSample.objects.filter(gene_key__isnull=False).first()
    assert sample is not None
    GeneticSample.objects.filter(pk=sample.pk).update(decoded_json={"stale_marker": True})
    call_command("seed_exhaustive_sample_genes", verbosity=0)
    sample.refresh_from_db()
    assert "stale_marker" not in sample.decoded_json
    assert "_asteroid_lab_summary" in sample.decoded_json


@pytest.mark.django_db
def test_seed_exhaustive_sample_genes_stale_delete_respects_generator() -> None:
    call_command("seed_exhaustive_sample_genes", verbosity=0)
    genes, _ = generate_exhaustive_sample_genes(max_extensions=0)
    assert len(genes) == 2
    orphan = GeneticSample.objects.create(
        gene_key="stale_test_only_key",
        name="stale",
        code=genes[0].encoded_copy_string,
        metadata_json={"generator": "exhaustive_sample_gene_v1"},
    )
    call_command("seed_exhaustive_sample_genes", "--delete-stale-generated", verbosity=0)
    assert not GeneticSample.objects.filter(pk=orphan.pk).exists()


def test_build_layout_minimal_entries_order_deterministic() -> None:
    root = build_layout_root(transport_kind="belt", exts=[])
    entries = root["BP"]["Entries"]
    assert len(entries) == 2
    types = {e["T"] for e in entries}
    assert "Layout_ShapeMiner" in types and "SpaceBelt_Forward" in types


def test_extension_rotations_ports_compatible_with_parent() -> None:
    """Each extension ``R`` must link to parent (equipment_bundles port contract)."""

    from django_apps.asteroid_lab.services.sample_gene_exhaustive_generator import (
        compute_extension_rotations_by_parent,
    )
    from django_apps.asteroid_lab.snapshots.equipment_bundles import (
        direction_from_a_to_b,
        ports_compatible,
    )

    for tk in ("belt", "pipe"):
        child_ck = "shape_miner_extension" if tk == "belt" else "fluid_miner_extension"
        parent_ck = "shape_miner" if tk == "belt" else "fluid_miner"
        for ad, ccoord in (("N", (0, -1)), ("W", (-1, 0)), ("S", (0, 1))):
            exts = [
                {
                    "id": "E1",
                    "coord": ccoord,
                    "parent_id": "E0",
                    "parent_coord": (0, 0),
                    "attach_dir": ad,
                }
            ]
            r = compute_extension_rotations_by_parent(exts, transport_kind=tk)["E1"]
            cx, cy = abstract_grid_to_raw_xy(*ccoord)
            px, py = abstract_grid_to_raw_xy(0, 0)
            d = direction_from_a_to_b(cx, cy, px, py)
            assert d is not None
            assert ports_compatible(child_ck, r, parent_ck, 0, d)

    # chain: E2 south of E1, E1 north of extractor
    exts_chain = [
        {
            "id": "E1",
            "coord": (0, -1),
            "parent_id": "E0",
            "parent_coord": (0, 0),
            "attach_dir": "N",
        },
        {
            "id": "E2",
            "coord": (0, -2),
            "parent_id": "E1",
            "parent_coord": (0, -1),
            "attach_dir": "N",
        },
    ]
    for tk in ("belt", "pipe"):
        child_ck = "shape_miner_extension" if tk == "belt" else "fluid_miner_extension"
        parent_ck = "shape_miner" if tk == "belt" else "fluid_miner"
        rots = compute_extension_rotations_by_parent(exts_chain, transport_kind=tk)
        c1x, c1y = abstract_grid_to_raw_xy(0, -1)
        p1x, p1y = abstract_grid_to_raw_xy(0, 0)
        d1 = direction_from_a_to_b(c1x, c1y, p1x, p1y)
        assert d1 is not None
        assert ports_compatible(child_ck, rots["E1"], parent_ck, 0, d1)
        c2x, c2y = abstract_grid_to_raw_xy(0, -2)
        p2x, p2y = abstract_grid_to_raw_xy(0, -1)
        d2 = direction_from_a_to_b(c2x, c2y, p2x, p2y)
        assert d2 is not None
        assert ports_compatible(child_ck, rots["E2"], child_ck, rots["E1"], d2)
