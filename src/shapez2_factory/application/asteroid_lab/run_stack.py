"""Pure Asteroid Lab run-stack use case for the CLI-first artifact path."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from functools import partial
from typing import Any

from shapez2_factory.adapters.asteroid_lab.complete_map_serializer import serialize_complete_map
from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
    GeneticSampleSeedSnapshot,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_05_INNER_PATTERN_FILL,
    LAYER_06_COMMIT_VALIDATE,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.run import (
    run_layer_02_exterior_transport,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill.run import (
    run_layer_05_inner_pattern_fill,
)
from shapez2_factory.application.asteroid_lab.layers.layer_06_commit_validate.run import (
    run_layer_06_commit_validate,
)
from shapez2_factory.application.asteroid_lab.ports.game_data_rules import GameDataRulesPort
from shapez2_factory.application.asteroid_lab.reconstruction_capacity import (
    build_terrain_capacity_summary_row,
)
from shapez2_factory.application.asteroid_lab.stack_runner import (
    LAYER_STACK_BUDGET_MS,
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
from shapez2_factory.domain.asteroid_lab.reconstruction.resource_kinds import (
    detect_present_resource_kinds,
    detect_primary_resource_kind,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
)


@dataclass(frozen=True, slots=True)
class StackRunResult:
    ok: bool = False
    error_code: str | None = None
    replay_core_lines: tuple[dict[str, Any], ...] = ()
    solver_summary: dict[str, Any] = field(default_factory=dict)
    complete_map_json: dict[str, Any] = field(default_factory=dict)
    stack_result_json: dict[str, Any] = field(default_factory=dict)


def _decimal_str(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.0001")), "f")


def _capacity_summary(
    *,
    resource_kind: str,
    platform_count: int,
    rules: GameDataRulesPort,
) -> dict[str, Any]:
    rule = rules.mining_extraction_rule(resource_kind=resource_kind)
    return build_terrain_capacity_summary_row(
        resource_kind=resource_kind,
        platform_count=platform_count,
        mini_unit_output_per_min=rule.mini_unit_output_per_min,
        output_unit=rule.output_unit,
        max_extension_count=rule.max_extension_count,
        source_kind=rule.source_kind,
        authority="game_data_snapshot",
    )


def _capacity_envelope(
    *,
    complete_map: ReconstructionCompleteMap,
    rules: GameDataRulesPort,
) -> dict[str, Any]:
    shape_field_cell_count = complete_map.shape_field_cell_count
    fluid_field_cell_count = complete_map.fluid_field_cell_count
    primary = detect_primary_resource_kind(complete_map)
    present = detect_present_resource_kinds(complete_map)
    return {
        "capacity_basis": "terrain_upper_bound",
        "primary_resource_kind": primary,
        "present_resource_kinds": list(present),
        "confirmed_platforms_by_resource": {
            "shape": shape_field_cell_count,
            "fluid": fluid_field_cell_count,
        },
        "by_resource": {
            "shape": _capacity_summary(
                resource_kind="shape",
                platform_count=shape_field_cell_count,
                rules=rules,
            ),
            "fluid": _capacity_summary(
                resource_kind="fluid",
                platform_count=fluid_field_cell_count,
                rules=rules,
            ),
        },
    }


def _stack_result_to_json(stack_result: Any) -> dict[str, Any]:
    diagnostic = stack_result.diagnostic_snapshot
    return {
        "status": stack_result.status.value,
        "completed_layer_slugs": list(stack_result.completed_layer_slugs),
        "failed_layer_slug": stack_result.failed_layer_slug,
        "diagnostic_snapshot": (
            None
            if diagnostic is None
            else {
                "layer_slug": diagnostic.layer_slug,
                "layer_index": diagnostic.layer_index,
                "payload": dict(diagnostic.payload),
            }
        ),
    }


def _layer_summary_to_json(record: Any) -> dict[str, Any]:
    return {
        "layer_slug": record.layer_slug,
        "layer_index": record.layer_index,
        "outcome": record.outcome.value,
        "elapsed_ms": record.elapsed_ms,
        "remaining_budget_ms": record.remaining_budget_ms,
        "metrics": dict(record.metrics),
    }


class RunStackUseCase:
    """Execute the pure decode, reconstruction, stack, and artifact-summary path."""

    def __init__(
        self,
        *,
        game_data_rules: GameDataRulesPort,
    ) -> None:
        self._game_data_rules = game_data_rules

    def run(
        self,
        *,
        copy_text: str,
        throughput_target_percent: int = 80,
        budget_ms: int = LAYER_STACK_BUDGET_MS,
        speed_tier: int = 1,
        genetic_sample_seeds: GeneticSampleSeedSnapshot | None = None,
    ) -> StackRunResult:
        snapshot = decode_shapez_copy_string(copy_text)
        cleanup = deconstruct_snapshot(snapshot)
        recon = run_topology_reconstruction(cleanup)
        complete_map = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
        capacity_envelope = _capacity_envelope(
            complete_map=complete_map,
            rules=self._game_data_rules,
        )
        runners = (
            _LayerStackRunner(
                LAYER_02_EXTERIOR_TRANSPORT,
                partial(
                    run_layer_02_exterior_transport,
                    capacity_envelope=capacity_envelope,
                    throughput_target_percent=throughput_target_percent,
                    speed_tier=speed_tier,
                    rules=self._game_data_rules,
                ),
            ),
            _LayerStackRunner(LAYER_03_RIM_GREEDY_PLACEMENT, run_layer_03_rim_greedy_placement),
            _LayerStackRunner(LAYER_05_INNER_PATTERN_FILL, run_layer_05_inner_pattern_fill),
            _LayerStackRunner(LAYER_06_COMMIT_VALIDATE, run_layer_06_commit_validate),
        )
        core_result = run_layers_02_to_06(
            complete_map=complete_map,
            budget_ctx=LayerBudgetContext.from_budget_ms(budget_ms),
            runners=runners,
            genetic_sample_seeds=genetic_sample_seeds,
        )
        stack_result_json = _stack_result_to_json(core_result.stack_result)
        layer_summaries = [_layer_summary_to_json(record) for record in core_result.layer_summaries]
        run_ok = core_result.stack_result.failed_layer_slug is None
        solver_summary = {
            "run_success": run_ok,
            "validation_passed": run_ok,
            "stack_run_status": core_result.stack_result.status.value,
            "completed_layer_slugs": list(core_result.stack_result.completed_layer_slugs),
            "failed_layer_slug": core_result.stack_result.failed_layer_slug,
            "throughput_target_percent": throughput_target_percent,
            "reconstruction_capacity": capacity_envelope,
            "layer_summaries": layer_summaries,
        }
        replay_core_lines = tuple(
            {
                "frame_index": index,
                "event": "layer_done",
                "layer_slug": record["layer_slug"],
                "outcome": record["outcome"],
                "elapsed_ms": record["elapsed_ms"],
            }
            for index, record in enumerate(layer_summaries)
        )
        return StackRunResult(
            ok=core_result.stack_result.failed_layer_slug is None,
            error_code=None,
            replay_core_lines=replay_core_lines,
            solver_summary=solver_summary,
            complete_map_json=serialize_complete_map(complete_map),
            stack_result_json=stack_result_json,
        )


__all__ = ["RunStackUseCase", "StackRunResult"]
