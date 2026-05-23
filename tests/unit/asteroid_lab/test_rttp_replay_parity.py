"""RTTP v0.2 — replay on/off parity (G8) and sink contracts."""

from __future__ import annotations

import inspect

from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import incremental_commit
from django_apps.asteroid_lab.optimization.commit.local_lns import run_local_lns
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.pipeline import PipelineResult, run_rttp_pipeline
from django_apps.asteroid_lab.optimization.replay_sink import (
    InMemoryRttpReplaySink,
    NullRttpReplaySink,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import select_genome
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.dto import SnapshotEventDTO


def _pipeline_results_equal(a: PipelineResult, b: PipelineResult) -> bool:
    return (
        a == b
        and a.commit_result.committed_ids == b.commit_result.committed_ids
        and a.genome.commit_order == b.genome.commit_order
        and a.validation_passed == b.validation_passed
        and a.normal_count == b.normal_count
    )


def test_pipeline_records_four_milestone_events(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    sink = InMemoryRttpReplaySink()
    run_rttp_pipeline(greenfield_optimization_input, replay_sink=sink)
    types = [event.event_type for event in sink.events]
    assert types == [
        et.EVENT_TYPE_ROUTING_PROBE_STARTED,
        et.EVENT_TYPE_CANDIDATE_GENERATED,
        et.EVENT_TYPE_GA_BEST_UPDATED,
        et.EVENT_TYPE_ROUTING_COMMITTED,
    ]
    final = sink.events[-1]
    assert final.metrics_json["validation_passed"] is True
    assert final.metrics_json["committed_ids"]
    assert final.metrics_json["commit_order"]


def test_rttp_replay_on_off_parity(greenfield_optimization_input: OptimizationInput) -> None:
    off = run_rttp_pipeline(
        greenfield_optimization_input,
        replay_sink=NullRttpReplaySink(),
    )
    mem = InMemoryRttpReplaySink()
    on = run_rttp_pipeline(greenfield_optimization_input, replay_sink=mem)
    assert mem.events
    assert _pipeline_results_equal(off, on)


class WeirdSink:
    def record(self, event: SnapshotEventDTO) -> dict[str, object]:
        del event
        return {"try_to_influence_solver": True}


def test_rttp_replay_sink_return_value_is_ignored(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    baseline = run_rttp_pipeline(
        greenfield_optimization_input,
        replay_sink=NullRttpReplaySink(),
    )
    weird = run_rttp_pipeline(
        greenfield_optimization_input,
        replay_sink=WeirdSink(),
    )
    assert baseline == weird


def test_rttp_layer_functions_do_not_accept_replay_sink() -> None:
    targets = [
        generate_candidates,
        select_genome,
        incremental_commit,
        run_local_lns,
    ]
    for fn in targets:
        sig = inspect.signature(fn)
        assert "replay_sink" not in sig.parameters, (
            f"{fn.__qualname__} must not take replay_sink"
        )
