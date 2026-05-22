"""Unit tests for stratified sampling helpers (no Django DB)."""

from __future__ import annotations

from tests.unit.game_data._stratified import merge_unique_paths, pick_stratified_by_key


def test_pick_stratified_by_key_head_mid_tail() -> None:
    items = [f"node-{i:03d}" for i in range(30)]
    picked = pick_stratified_by_key(items, n=5, key=lambda s: s)
    assert len(picked) == 15
    assert picked[0] == "node-000"
    assert picked[-1] == "node-029"
    assert "node-015" in picked or "node-014" in picked


def test_pick_stratified_small_list_returns_all() -> None:
    items = ["a", "b", "c"]
    assert pick_stratified_by_key(items, n=5, key=lambda s: s) == ["a", "b", "c"]


def test_merge_unique_paths_skips_missing_and_dedupes() -> None:
    merged = merge_unique_paths(
        ["b", "b", "c"],
        ["a", "b"],
        available={"a", "b", "c"},
    )
    assert merged == ["b", "c", "a"]
