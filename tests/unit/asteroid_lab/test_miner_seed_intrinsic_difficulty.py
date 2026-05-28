"""Intrinsic difficulty scoring for miner seed catalog patterns."""

from __future__ import annotations

from pathlib import Path

from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import (
    EXPECTED_DIFFICULTY_RANK_ORDER,
    EXPECTED_INTRINSIC_PRIORITY_RANK_ORDER,
    EXPECTED_PATTERN_IDS,
)
from django_apps.asteroid_lab.genetic_sample.miner_seed_equivalence import (
    assert_miner_seed_layout_strict,
)
from django_apps.asteroid_lab.genetic_sample.miner_seed_intrinsic_difficulty import (
    IntrinsicDifficultyResult,
    assign_difficulty_ranks,
    assign_intrinsic_priority_ranks,
    intrinsic_difficulty_from_root,
    intrinsic_priority_score,
)

_BOOTSTRAP = Path("var/default_miner_pattern.txt")

_GOLDEN_SCORES: dict[str, int] = {
    "m0e_01": 8,
    "m1e_01": 105,
    "m2e_01": 221,
    "m2e_02": 233,
    "m2e_04": 261,
    "m2e_03": 263,
    "m3e_01": 337,
    "m3e_02": 354,
    "m3e_04": 354,
    "m3e_03": 364,
    "m3e_07": 377,
    "m3e_09": 381,
    "m3e_06": 384,
    "m3e_13": 384,
    "m3e_05": 394,
    "m3e_11": 394,
    "m3e_12": 394,
    "m3e_08": 404,
}


def test_golden_difficulty_rank_order() -> None:
    lines = [ln.strip() for ln in _BOOTSTRAP.read_text(encoding="utf-8").splitlines() if ln.strip()]
    scored: list[tuple[str, IntrinsicDifficultyResult]] = []
    for pattern_id, line in zip(EXPECTED_PATTERN_IDS, lines, strict=True):
        root = decode_copy_string(line).root
        assert_miner_seed_layout_strict(root)
        scored.append((pattern_id, intrinsic_difficulty_from_root(root)))
    ranked = assign_difficulty_ranks(scored)
    order = [pid for pid, _result, _rank in ranked]
    assert order == list(EXPECTED_DIFFICULTY_RANK_ORDER)
    for pid, result, rank in ranked:
        assert rank == EXPECTED_DIFFICULTY_RANK_ORDER.index(pid) + 1
        assert result.score == _GOLDEN_SCORES[pid]


def test_difficulty_score_is_int_for_m0e() -> None:
    line = _BOOTSTRAP.read_text(encoding="utf-8").splitlines()[0].strip()
    root = decode_copy_string(line).root
    assert_miner_seed_layout_strict(root)
    result = intrinsic_difficulty_from_root(root)
    assert isinstance(result.score, int)
    assert result.score == 8
    assert result.tier == 0
    assert result.reason["compactness_approx"] == 1.0
    assert "coverage_approx" not in result.reason


_GOLDEN_PRIORITY_SCORES: dict[str, int] = {
    "m3e_01": 211,
    "m3e_02": 221,
    "m3e_04": 221,
    "m2e_01": 224,
    "m3e_03": 228,
    "m2e_02": 234,
    "m3e_07": 236,
    "m3e_09": 238,
    "m3e_06": 240,
    "m3e_13": 240,
    "m3e_05": 246,
    "m3e_11": 246,
    "m3e_12": 246,
    "m3e_08": 252,
    "m2e_04": 258,
    "m2e_03": 259,
    "m1e_01": 351,
    "m0e_01": 420,
}


def _score_all_patterns() -> list[tuple[str, IntrinsicDifficultyResult]]:
    lines = [ln.strip() for ln in _BOOTSTRAP.read_text(encoding="utf-8").splitlines() if ln.strip()]
    scored: list[tuple[str, IntrinsicDifficultyResult]] = []
    for pattern_id, line in zip(EXPECTED_PATTERN_IDS, lines, strict=True):
        root = decode_copy_string(line).root
        assert_miner_seed_layout_strict(root)
        scored.append((pattern_id, intrinsic_difficulty_from_root(root)))
    return scored


def test_golden_intrinsic_priority_rank_order() -> None:
    scored = _score_all_patterns()
    ranked = assign_intrinsic_priority_ranks(scored)
    order = [pid for pid, _result, _rank in ranked]
    assert order == list(EXPECTED_INTRINSIC_PRIORITY_RANK_ORDER)
    for pid, result, rank in ranked:
        assert rank == EXPECTED_INTRINSIC_PRIORITY_RANK_ORDER.index(pid) + 1
        assert intrinsic_priority_score(result) == _GOLDEN_PRIORITY_SCORES[pid]


def test_m1e_does_not_precede_simple_m3e_for_priority() -> None:
    scored = dict(_score_all_patterns())
    priority_ranked = assign_intrinsic_priority_ranks(list(scored.items()))
    by_id = {pid: rank for pid, _result, rank in priority_ranked}
    assert by_id["m3e_01"] < by_id["m1e_01"]


def test_intrinsic_priority_rank_is_not_search_priority_rank() -> None:
    """Map-aware search_priority_rank stays null until Phase 5."""

    scored = _score_all_patterns()
    priority_ranked = assign_intrinsic_priority_ranks(scored)
    assert all(rank >= 1 for _pid, _result, rank in priority_ranked)


def test_difficulty_rank_remains_curriculum_order() -> None:
    scored = _score_all_patterns()
    difficulty_ranked = assign_difficulty_ranks(scored)
    order = [pid for pid, _result, _rank in difficulty_ranked]
    assert order == list(EXPECTED_DIFFICULTY_RANK_ORDER)
    assert order[0] == "m0e_01"
    assert order[1] == "m1e_01"


def test_linear_m3e_01_tier_four() -> None:
    lines = [ln.strip() for ln in _BOOTSTRAP.read_text(encoding="utf-8").splitlines() if ln.strip()]
    idx = EXPECTED_PATTERN_IDS.index("m3e_01")
    root = decode_copy_string(lines[idx]).root
    assert_miner_seed_layout_strict(root)
    result = intrinsic_difficulty_from_root(root)
    assert result.tier == 4
    assert result.reason["branch_count"] == 0
    assert result.reason["linear_chain_bonus"] == 15
