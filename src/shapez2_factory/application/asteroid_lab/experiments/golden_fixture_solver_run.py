"""Run golden-map solver stack and capture L2–L5 artifacts (Django-free)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import Any

from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
    GeneticSampleSeedSnapshot,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.inner_fill_strategy import (
    InnerFillStrategy,
    parse_inner_fill_strategy,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    Layer04InnerFillResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
    Layer05RoutePlan,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_post_summary import (
    LayerPostSummaryRecord,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
    LAYER_06_COMMIT_VALIDATE,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    IntegratedRimGreedyResult,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.run import (
    run_layer_02_exterior_transport,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.run import (
    run_layer_05_transport_routing,
)
from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill.run import (
    run_layer_04_inner_pattern_fill,
)
from shapez2_factory.application.asteroid_lab.layers.layer_06_commit_validate.run import (
    run_layer_06_commit_validate,
)
from shapez2_factory.application.asteroid_lab.ports.game_data_rules import GameDataRulesPort
from shapez2_factory.application.asteroid_lab.run_stack import _capacity_envelope
from shapez2_factory.application.asteroid_lab.stack_runner import (
    LAYER_STACK_BUDGET_MS,
    CoreStackRunResult,
    _LayerStackRunner,
    run_layers_02_to_06,
)
from shapez2_factory.domain.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
    build_reconstruction_complete_map,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.pipeline import (
    run_topology_reconstruction,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
)


@dataclass(frozen=True, slots=True)
class GoldenSolverConfig:
    throughput_target_percent: int = 80
    budget_ms: int = LAYER_STACK_BUDGET_MS
    speed_tier: int = 1
    inner_fill_strategy: InnerFillStrategy | str = InnerFillStrategy.GREEDY


@dataclass(frozen=True, slots=True)
class GoldenSolverArtifacts:
    core_result: CoreStackRunResult
    complete_map: ReconstructionCompleteMap
    exterior_plan: ExteriorConnectionPlan | None
    rim_result: IntegratedRimGreedyResult | None
    inner_fill: Layer04InnerFillResult | None
    route_plan: Layer05RoutePlan | None
    layer_summaries: tuple[LayerPostSummaryRecord, ...]


@dataclass
class _LayerArtifactCapture:
    exterior_plan: ExteriorConnectionPlan | None = None
    rim_result: IntegratedRimGreedyResult | None = None
    inner_fill: Layer04InnerFillResult | None = None
    route_plan: Layer05RoutePlan | None = None


def _capture_layer_run(
    run: Callable[..., Any],
    capture: _LayerArtifactCapture,
    field_name: str,
) -> Callable[..., Any]:
    def wrapped(**kwargs: Any) -> Any:
        result = run(**kwargs)
        setattr(capture, field_name, result)
        return result

    return wrapped


def _build_runners(
    *,
    game_data_rules: GameDataRulesPort,
    capacity_envelope: dict[str, Any],
    cfg: GoldenSolverConfig,
    capture: _LayerArtifactCapture,
) -> tuple[_LayerStackRunner, ...]:
    return (
        _LayerStackRunner(
            LAYER_02_EXTERIOR_TRANSPORT,
            _capture_layer_run(
                partial(
                    run_layer_02_exterior_transport,
                    capacity_envelope=capacity_envelope,
                    throughput_target_percent=cfg.throughput_target_percent,
                    speed_tier=cfg.speed_tier,
                    rules=game_data_rules,
                ),
                capture,
                "exterior_plan",
            ),
        ),
        _LayerStackRunner(
            LAYER_03_RIM_GREEDY_PLACEMENT,
            _capture_layer_run(
                run_layer_03_rim_greedy_placement,
                capture,
                "rim_result",
            ),
        ),
        _LayerStackRunner(
            LAYER_04_INNER_PATTERN_FILL,
            _capture_layer_run(
                partial(
                    run_layer_04_inner_pattern_fill,
                    inner_fill_strategy=parse_inner_fill_strategy(cfg.inner_fill_strategy),
                ),
                capture,
                "inner_fill",
            ),
        ),
        _LayerStackRunner(
            LAYER_05_TRANSPORT_ROUTING,
            _capture_layer_run(
                run_layer_05_transport_routing,
                capture,
                "route_plan",
            ),
        ),
        _LayerStackRunner(LAYER_06_COMMIT_VALIDATE, run_layer_06_commit_validate),
    )


def run_golden_solver(
    *,
    copy_text: str,
    game_data_rules: GameDataRulesPort,
    genetic_sample_seeds: GeneticSampleSeedSnapshot | None = None,
    config: GoldenSolverConfig | None = None,
) -> GoldenSolverArtifacts:
    """Decode, reconstruct, and run L2–L6; return captured layer artifacts."""

    cfg = config or GoldenSolverConfig()
    snapshot = decode_shapez_copy_string(copy_text)
    cleanup = deconstruct_snapshot(snapshot)
    recon = run_topology_reconstruction(cleanup)
    complete_map = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    capacity_envelope = _capacity_envelope(complete_map=complete_map, rules=game_data_rules)
    capture = _LayerArtifactCapture()
    runners = _build_runners(
        game_data_rules=game_data_rules,
        capacity_envelope=capacity_envelope,
        cfg=cfg,
        capture=capture,
    )
    core_result = run_layers_02_to_06(
        complete_map=complete_map,
        budget_ctx=LayerBudgetContext.from_budget_ms(cfg.budget_ms),
        runners=runners,
        genetic_sample_seeds=genetic_sample_seeds,
        capacity_envelope=capacity_envelope,
        throughput_target_percent=cfg.throughput_target_percent,
    )
    return GoldenSolverArtifacts(
        core_result=core_result,
        complete_map=complete_map,
        exterior_plan=capture.exterior_plan,
        rim_result=capture.rim_result,
        inner_fill=capture.inner_fill,
        route_plan=capture.route_plan,
        layer_summaries=core_result.layer_summaries,
    )


__all__ = [
    "GoldenSolverArtifacts",
    "GoldenSolverConfig",
    "run_golden_solver",
]
