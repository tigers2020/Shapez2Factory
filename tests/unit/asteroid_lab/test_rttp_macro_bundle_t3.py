"""RTTP v1 MacroBundleT3 compiler + probe gates — RTTP-G9, RTTP-G10 (PR-B)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflict,
    CommitConflictReason,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.commit.incremental_macro_commit import (
    incremental_commit_macro,
)
from django_apps.asteroid_lab.optimization.input_contracts import RttpPipelineConfig
from django_apps.asteroid_lab.optimization.macros import (
    MacroCompileConfig,
    MacroRejectReason,
    compile_macros,
    probe_macro_shared_lift,
)
from django_apps.asteroid_lab.optimization.macros.macro_compiler import (
    _derive_shared_lift_stub_plan,
    _derive_shared_ring_port_intent,
)
from django_apps.asteroid_lab.optimization.macros.macro_dtos import (
    MacroBundleCandidate,
    SharedLiftStubPlan,
)
from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import (
    build_route_domain_from_skeleton,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.selection.macro_equivalence import dedupe_macros
from django_apps.asteroid_lab.optimization.selection.macro_greedy_regret import (
    assert_macro_only_commit_order,
    select_macro_genome,
)
from django_apps.asteroid_lab.optimization.validation.final_validation import validate_macro_layout
from tests.support.macro_triple_greenfield_fixture import (
    build_macro_triple_greenfield_fixture,
    build_overlapping_macro_triple_candidates,
    build_unreachable_shared_trunk_skeleton,
)


def test_macro_compiler_emits_one_candidate_for_valid_triple() -> None:
    """RTTP-G9: valid triple → one MacroBundleCandidate in macro_normal."""

    fixture = build_macro_triple_greenfield_fixture()
    result = compile_macros(fixture.valid_triple, fixture.skeleton, fixture.inp)

    assert len(result.macro_normal) == 1
    macro_row = result.macro_normal[0]
    assert macro_row.reachable is True
    assert macro_row.macro_id == macro_row.macro.macro_id
    child_ids = {c.candidate_id for c in fixture.valid_triple}
    macro_child_ids = {
        macro_row.macro.child_a_id,
        macro_row.macro.child_b_id,
        macro_row.macro.child_c_id,
    }
    assert macro_child_ids == child_ids
    assert result.macro_rejected == ()


def test_macro_compiler_rejects_overlap() -> None:
    """RTTP-G9: overlapping child footprints → CHILD_OCCUPANCY_OVERLAP."""

    fixture = build_macro_triple_greenfield_fixture()
    overlapping = build_overlapping_macro_triple_candidates()
    result = compile_macros(overlapping, fixture.skeleton, fixture.inp)

    assert result.macro_normal == ()
    assert len(result.macro_rejected) == 1
    assert (
        result.macro_rejected[0].rejection_reason is MacroRejectReason.CHILD_OCCUPANCY_OVERLAP
    )


def test_macro_probe_rejects_unreachable_shared_trunk() -> None:
    """RTTP-G10: shared lift plan cannot reach trunk → SHARED_LIFT_UNREACHABLE."""

    fixture = build_macro_triple_greenfield_fixture()
    broken_skeleton = build_unreachable_shared_trunk_skeleton(fixture)
    domain = build_route_domain_from_skeleton(broken_skeleton, fixture.inp)

    shared_lift = SharedLiftStubPlan(
        lift_column_coords=frozenset({(99, 99), (99, 98)}),
        trunk_entry_coord=(99, 98),
        reserved_route_cells=frozenset({(99, 99), (99, 98)}),
    )
    probe = probe_macro_shared_lift(domain, shared_lift, max_expansions=500)
    assert probe.reachable is False

    result = compile_macros(fixture.valid_triple, broken_skeleton, fixture.inp)
    assert result.macro_normal == ()
    assert len(result.macro_rejected) == 1
    assert (
        result.macro_rejected[0].rejection_reason is MacroRejectReason.SHARED_LIFT_UNREACHABLE
    )


def test_macro_compiler_rejects_existing_shared_lift_when_probe_unreachable() -> None:
    """RTTP-G10: derived shared lift plan exists but probe fails → probe rejection branch."""

    fixture = build_macro_triple_greenfield_fixture()
    assert fixture.skeleton.lift_columns
    assert fixture.skeleton.ring_ports

    shared_lift = _derive_shared_lift_stub_plan(fixture.skeleton)
    shared_ring = _derive_shared_ring_port_intent(fixture.skeleton)
    assert shared_lift is not None
    assert shared_ring is not None

    domain = build_route_domain_from_skeleton(fixture.skeleton, fixture.inp)
    probe = probe_macro_shared_lift(domain, shared_lift, max_expansions=0)
    assert probe.reachable is False

    config = MacroCompileConfig(max_probe_expansions=0)
    result = compile_macros(
        fixture.valid_triple,
        fixture.skeleton,
        fixture.inp,
        config=config,
    )

    assert result.macro_normal == ()
    assert len(result.macro_rejected) == 1
    rejected = result.macro_rejected[0]
    assert rejected.rejection_reason is MacroRejectReason.SHARED_LIFT_UNREACHABLE
    assert rejected.route_probe_cost is not None


def test_macro_equivalence_dedupe_deterministic() -> None:
    """RTTP-G11: equivalent macros collapse; lowest macro_id wins."""

    fixture = build_macro_triple_greenfield_fixture()
    compiled = compile_macros(fixture.valid_triple, fixture.skeleton, fixture.inp)
    assert len(compiled.macro_normal) == 1
    base_row = compiled.macro_normal[0]

    low_macro = replace(base_row.macro, macro_id="a" * 64)
    high_macro = replace(base_row.macro, macro_id="f" * 64)
    low_row = MacroBundleCandidate(
        macro_id=low_macro.macro_id,
        macro=low_macro,
        route_probe_cost=base_row.route_probe_cost,
        reachable=True,
    )
    high_row = MacroBundleCandidate(
        macro_id=high_macro.macro_id,
        macro=high_macro,
        route_probe_cost=base_row.route_probe_cost,
        reachable=True,
    )

    deduped = dedupe_macros((high_row, low_row, high_row))
    assert len(deduped) == 1
    assert deduped[0].macro_id == low_row.macro_id

    permuted_pool = fixture.valid_triple[1:] + fixture.valid_triple[:1]
    permuted = compile_macros(permuted_pool, fixture.skeleton, fixture.inp)
    assert len(permuted.macro_normal) == 1
    assert permuted.macro_normal[0].macro_id == base_row.macro_id


def test_macro_regret_commit_order_uses_macro_ids_only() -> None:
    """RTTP-G12: genome slots are macro_id strings only."""

    fixture = build_macro_triple_greenfield_fixture()
    compiled = compile_macros(fixture.valid_triple, fixture.skeleton, fixture.inp)
    macro_normal = dedupe_macros(compiled.macro_normal)
    config = RttpPipelineConfig(macro_only_mode=True, allow_singleton_genome_slots=False)

    genome = select_macro_genome(
        macro_normal,
        fixture.skeleton,
        fixture.inp,
        pipeline_config=config,
    )

    assert genome.commit_order
    macro_ids = {row.macro_id for row in macro_normal}
    assert all(slot_id in macro_ids for slot_id in genome.commit_order)
    child_ids = {c.candidate_id for row in macro_normal for c in row.macro.children}
    assert not any(slot_id in child_ids for slot_id in genome.commit_order)


def test_macro_genome_rejects_singleton_slot_injection() -> None:
    fixture = build_macro_triple_greenfield_fixture()
    compiled = compile_macros(fixture.valid_triple, fixture.skeleton, fixture.inp)
    macro_normal = dedupe_macros(compiled.macro_normal)
    child_id = macro_normal[0].macro.children[0].candidate_id
    config = RttpPipelineConfig(allow_singleton_genome_slots=False)

    try:
        assert_macro_only_commit_order(
            PlacementGenome(commit_order=(child_id,)),
            macro_normal,
            pipeline_config=config,
        )
    except ValueError as exc:
        assert "singleton" in str(exc)
    else:
        raise AssertionError("expected singleton injection guard to raise")


def test_macro_commit_all_or_nothing_success() -> None:
    """RTTP-G13: successful macro commits all three child ids."""

    from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
        ExtractorPlacementPolicy,
    )
    from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
        generate_candidates,
    )

    fixture = build_macro_triple_greenfield_fixture()
    generation = generate_candidates(
        fixture.inp,
        fixture.skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    compiled = compile_macros(generation.normal_candidates, fixture.skeleton, fixture.inp)
    macro_normal = dedupe_macros(compiled.macro_normal)
    assert macro_normal
    genome = select_macro_genome(macro_normal, fixture.skeleton, fixture.inp)
    candidates_by_id = {c.candidate_id: c for c in generation.normal_candidates}
    macros_by_id = {row.macro_id: row for row in macro_normal}
    domain = initial_commit_domain(fixture.skeleton, fixture.inp)

    result = incremental_commit_macro(
        genome,
        macros_by_id,
        candidates_by_id,
        fixture.inp,
        fixture.skeleton,
        domain=domain,
    )

    assert genome.commit_order
    assert result.committed_macro_ids == genome.commit_order
    assert len(result.committed_child_ids) == 3
    macro_row = macros_by_id[genome.commit_order[0]]
    assert set(result.committed_child_ids) == {
        child.candidate_id for child in macro_row.macro.children
    }
    assert result.conflicts == ()


def test_macro_commit_reprobe_failure_rolls_back() -> None:
    """RTTP-G13: mid-macro reprobe failure commits zero children for that slot."""

    from unittest.mock import patch

    from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
        ExtractorPlacementPolicy,
    )
    from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
        generate_candidates,
    )
    from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
        CommitResult,
        incremental_commit,
    )

    fixture = build_macro_triple_greenfield_fixture()
    generation = generate_candidates(
        fixture.inp,
        fixture.skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    )
    compiled = compile_macros(generation.normal_candidates, fixture.skeleton, fixture.inp)
    macro_normal = dedupe_macros(compiled.macro_normal)
    assert macro_normal
    genome = select_macro_genome(macro_normal, fixture.skeleton, fixture.inp)
    candidates_by_id = {c.candidate_id: c for c in generation.normal_candidates}
    macros_by_id = {row.macro_id: row for row in macro_normal}
    domain = initial_commit_domain(fixture.skeleton, fixture.inp)
    attempts = {"n": 0}

    def flaky_commit(genome_slot, candidates_by_id_arg, inp, skeleton, *, domain):
        attempts["n"] += 1
        if attempts["n"] == 2:
            return CommitResult(
                committed_ids=(),
                reserved_route_cells=domain.committed_route_cells,
                domain_version=domain.version,
                conflicts=(
                    CommitConflict(
                        candidate_id=genome_slot.commit_order[0],
                        reason=CommitConflictReason.REPROBE_FAILED,
                    ),
                ),
            )
        return incremental_commit(
            genome_slot,
            candidates_by_id_arg,
            inp,
            skeleton,
            domain=domain,
        )

    with patch(
        "django_apps.asteroid_lab.optimization.commit.incremental_macro_commit.incremental_commit",
        side_effect=flaky_commit,
    ):
        result = incremental_commit_macro(
            genome,
            macros_by_id,
            candidates_by_id,
            fixture.inp,
            fixture.skeleton,
            domain=domain,
        )

    assert result.committed_macro_ids == ()
    assert result.committed_child_ids == ()
    assert result.conflicts
    assert result.conflicts[0].reason is CommitConflictReason.REPROBE_FAILED


def test_macro_compiler_caps_enumeration_at_max_macro_candidates() -> None:
    fixture = build_macro_triple_greenfield_fixture()
    config = MacroCompileConfig(max_macro_candidates=0)
    result = compile_macros(fixture.valid_triple, fixture.skeleton, fixture.inp, config=config)

    assert result.macro_normal == ()
    assert len(result.macro_rejected) == 1
    assert (
        result.macro_rejected[0].rejection_reason
        is MacroRejectReason.EXCEEDS_MAX_MACRO_CANDIDATES
    )


def test_validate_macro_layout_rejects_disjoint_violation() -> None:
    fixture = build_macro_triple_greenfield_fixture()
    compiled = compile_macros(fixture.valid_triple, fixture.skeleton, fixture.inp)
    macro_normal = dedupe_macros(compiled.macro_normal)
    row = macro_normal[0]
    candidates_by_id = {c.candidate_id: c for c in fixture.valid_triple}
    macros_by_id = {row.macro_id: row}

    assert not validate_macro_layout(
        (row.macro_id,),
        (fixture.valid_triple[0].candidate_id, fixture.valid_triple[0].candidate_id),
        frozenset(),
        macros_by_id,
        candidates_by_id,
        fixture.inp,
    )


def test_optimization_import_boundary_no_lab_compose() -> None:
    """RTTP-G16: optimization package must not import Lab compose modules."""

    root = Path("django_apps/asteroid_lab/optimization")
    forbidden = "lab_rttp_snapshot_compose"
    hits: list[str] = []
    for path in root.rglob("*.py"):
        if forbidden in path.read_text(encoding="utf-8"):
            hits.append(str(path))
    assert hits == []
