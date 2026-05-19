"""Phase 9 pre-9B — ReplayEventType adapter coverage matrix."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.unified_enums import ReplayEventType
from django_apps.asteroid_lab.replay.unified_event_coverage import (
    DEFERRED_POST_9B,
    SUPPORTED_BY_9B_LAB_ADAPTER,
    SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER,
    replay_event_type_coverage_partitions,
)


def test_unified_replay_event_type_adapter_coverage_matrix_is_explicit() -> None:
    lab, opt, post = replay_event_type_coverage_partitions()
    assert lab is SUPPORTED_BY_9B_LAB_ADAPTER
    assert opt is SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER
    assert post is DEFERRED_POST_9B

    all_members = frozenset(ReplayEventType)
    union = lab | opt | post
    assert union == all_members
    assert not (lab & opt)
    assert not (lab & post)
    assert not (opt & post)

    assert lab == frozenset(
        {
            ReplayEventType.DECODE_STARTED,
            ReplayEventType.DECODE_COMPLETED,
            ReplayEventType.RECONSTRUCTION_STARTED,
            ReplayEventType.RECONSTRUCTION_COMPLETED,
        }
    )
    assert len(opt) == len(all_members) - len(lab)
    assert len(post) == 0


def test_unified_replay_event_type_every_enum_accounted_for() -> None:
    accounted = (
        SUPPORTED_BY_9B_LAB_ADAPTER | SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER | DEFERRED_POST_9B
    )
    assert len(accounted) == len(ReplayEventType)
    for member in ReplayEventType:
        assert member in accounted


def test_optimization_replay_event_types_match_unified_9c_set() -> None:
    """Every OptimizationReplayEventType wire value must map to a ReplayEventType
    that is covered by the 9C optimization adapter set.  If this fails, a new
    OptimizationReplayEventType was added without updating unified_enums.py /
    unified_event_coverage.py — or vice versa.
    """
    from django_apps.asteroid_lab.optimization.enums import OptimizationReplayEventType
    from django_apps.asteroid_lab.replay.unified_serialization import parse_replay_event_type

    for member in OptimizationReplayEventType:
        unified = parse_replay_event_type(member.value)
        assert unified in SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER, (
            f"OptimizationReplayEventType.{member.name} ({member.value!r}) is not in "
            "SUPPORTED_BY_9C_OPTIMIZATION_ADAPTER — add it to unified_event_coverage.py"
        )
