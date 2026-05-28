"""Miner seed topology signature contract tests (audit-only; not catalog dedupe)."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.genetic_sample.miner_seed_topology import (
    count_extensions,
    throughput_factor_for_extension_count,
    topology_signature_from_decoded_root,
)

_BOOTSTRAP = Path("var/default_miner_pattern.txt")


@pytest.fixture(scope="module")
def bootstrap_lines() -> list[str]:
    return [ln.strip() for ln in _BOOTSTRAP.read_text(encoding="utf-8").splitlines() if ln.strip()]


def test_bootstrap_has_eighteen_lines(bootstrap_lines: list[str]) -> None:
    assert len(bootstrap_lines) == 18


def test_topology_signatures_present_for_all_bootstrap(bootstrap_lines: list[str]) -> None:
    sigs: list[str] = []
    for line in bootstrap_lines:
        dto = decode_copy_string(line)
        sigs.append(topology_signature_from_decoded_root(dto.root))
    assert len(sigs) == 18


def test_extension_count_distribution(bootstrap_lines: list[str]) -> None:
    counts = [count_extensions(decode_copy_string(line).root) for line in bootstrap_lines]
    assert counts.count(3) == 12
    assert counts.count(2) == 4
    assert counts.count(1) == 1
    assert counts.count(0) == 1


def test_throughput_factor_table() -> None:
    assert throughput_factor_for_extension_count(0) == 4
    assert throughput_factor_for_extension_count(3) == 16
