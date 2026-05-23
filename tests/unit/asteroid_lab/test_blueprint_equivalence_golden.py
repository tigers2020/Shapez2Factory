"""Layout equivalence: connected branch (good) vs spread bug (historical bad export)."""

from __future__ import annotations

from pathlib import Path

from django_apps.asteroid_lab.adapters.blueprint_canonical_export import (
    encode_official_copy_string,
    to_official_island_root,
)
from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.genetic_sample.exhaustive_generator import build_layout_root
from django_apps.asteroid_lab.snapshots.blueprint_equivalence import decoded_json_layout_equivalent


def _line(fname: str) -> str:
    p = Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab" / fname
    return p.read_text(encoding="utf-8").splitlines()[0].strip()


def test_spread_bug_and_connected_fixture_copies_not_layout_equivalent() -> None:
    bad = decode_copy_string(_line("spread_branch_fluid_pipe_bug.txt")).root
    good = decode_copy_string(_line("connected_branch_fluid_pipe.txt")).root
    assert not decoded_json_layout_equivalent(bad, good, include_transport=True)


def test_south_chain_official_encode_dense_contiguous() -> None:
    exts = [
        {"id": "E1", "coord": (0, 1), "parent_id": "E0", "parent_coord": (0, 0), "attach_dir": "S"},
        {"id": "E2", "coord": (0, 2), "parent_id": "E1", "parent_coord": (0, 1), "attach_dir": "S"},
        {"id": "E3", "coord": (0, 3), "parent_id": "E2", "parent_coord": (0, 2), "attach_dir": "S"},
    ]
    lab = build_layout_root(transport_kind="pipe", exts=exts)
    got = encode_official_copy_string(to_official_island_root(lab))
    assert got.startswith("SHAPEZ2-4-")
    decode_copy_string(got)
