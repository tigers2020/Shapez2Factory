"""Miner seed equivalence_signature and strict layout validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import EXPECTED_PATTERN_IDS
from django_apps.asteroid_lab.snapshots.copy_json_coords import entry_island_raw_coord
from django_apps.asteroid_lab.genetic_sample.miner_seed_equivalence import (
    MinerSeedLayoutValidationError,
    assert_miner_seed_layout_strict,
    equivalence_signature_from_decoded_root,
)

_BOOTSTRAP = Path("var/default_miner_pattern.txt")


@pytest.fixture(scope="module")
def bootstrap_lines() -> list[str]:
    return [ln.strip() for ln in _BOOTSTRAP.read_text(encoding="utf-8").splitlines() if ln.strip()]


def test_bootstrap_nineteen_lines(bootstrap_lines: list[str]) -> None:
    assert len(bootstrap_lines) == 19


def test_equivalence_signatures_count_among_bootstrap(bootstrap_lines: list[str]) -> None:
    sigs: list[str] = []
    for line in bootstrap_lines:
        root = decode_copy_string(line).root
        assert_miner_seed_layout_strict(root)
        sigs.append(equivalence_signature_from_decoded_root(root))
    assert len(sigs) == 19
    assert len(set(sigs)) == 18
    assert sigs.count(sigs[14]) == 2


def test_m3e_09_and_m3e_10_share_equivalence_signature(bootstrap_lines: list[str]) -> None:
    roots = [decode_copy_string(bootstrap_lines[i]).root for i in (14, 15)]
    assert equivalence_signature_from_decoded_root(roots[0]) == equivalence_signature_from_decoded_root(
        roots[1],
    )


def test_d4_rotation_preserves_equivalence_signature(bootstrap_lines: list[str]) -> None:
    """Rotate island coords 90° CCW; parent-tree equivalence must match."""

    root = decode_copy_string(bootstrap_lines[0]).root
    base_sig = equivalence_signature_from_decoded_root(root)

    def rot_xy(x: int, y: int) -> tuple[int, int]:
        return (-y, x)

    entries = root["BP"]["Entries"]
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if "X" in entry or "Y" in entry:
            coord = entry_island_raw_coord(entry)
            rx, ry = rot_xy(coord.x, coord.y)
            entry["X"] = rx
            entry["Y"] = ry
        if "R" in entry and str(entry.get("T", "")).startswith("Layout_"):
            entry["R"] = (int(entry["R"]) + 1) % 4

    assert equivalence_signature_from_decoded_root(root) == base_sig


def test_belt_position_does_not_change_equivalence_signature(bootstrap_lines: list[str]) -> None:
    root = decode_copy_string(bootstrap_lines[-1]).root
    base_sig = equivalence_signature_from_decoded_root(root)
    for entry in root["BP"]["Entries"]:
        if isinstance(entry, dict) and entry.get("T") == "SpaceBelt_Forward":
            entry["X"] = int(entry.get("X", 0)) + 99
            entry["Y"] = int(entry.get("Y", 0)) - 42
    assert equivalence_signature_from_decoded_root(root) == base_sig


def test_wrong_miner_r_raises(bootstrap_lines: list[str]) -> None:
    root = decode_copy_string(bootstrap_lines[0]).root
    for entry in root["BP"]["Entries"]:
        if isinstance(entry, dict) and entry.get("T") == "Layout_ShapeMiner":
            entry["R"] = 2
    with pytest.raises(MinerSeedLayoutValidationError, match="miner R must be 0"):
        assert_miner_seed_layout_strict(root)


def test_m0e_and_m3e_bootstrap_decode_strict(bootstrap_lines: list[str]) -> None:
    for pattern_id in ("m0e_01", "m3e_01", "m3e_13"):
        idx = EXPECTED_PATTERN_IDS.index(pattern_id)
        root = decode_copy_string(bootstrap_lines[idx]).root
        assert_miner_seed_layout_strict(root)
