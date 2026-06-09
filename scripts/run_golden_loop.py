#!/usr/bin/env python
"""Batch golden fixture solver configs and write experiment outputs.

Outputs under ``var/experiments/golden_loop/``::

    runs.jsonl
    best_config.json
    diagnostics.json

Optional ``--write-snapshots`` writes decoded JSON under ``snapshots/``.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = _REPO / "var" / "experiments" / "golden_loop"


@dataclass(frozen=True, slots=True)
class GoldenLoopRunConfig:
    throughput_target_percent: int
    budget_ms: int
    speed_tier: int = 1


def build_config_grid(
    *,
    throughput_targets: tuple[int, ...] = (70, 80, 90),
    budget_ms: int = 60_000,
    speed_tiers: tuple[int, ...] = (1,),
) -> tuple[GoldenLoopRunConfig, ...]:
    return tuple(
        GoldenLoopRunConfig(
            throughput_target_percent=target,
            budget_ms=budget_ms,
            speed_tier=speed_tier,
        )
        for target in throughput_targets
        for speed_tier in speed_tiers
    )


def _eval_record_dict(result: Any) -> dict[str, Any]:
    payload = asdict(result)
    payload["diagnostics"] = list(result.diagnostics)
    return payload


def run_golden_loop(
    *,
    out_dir: Path | str = DEFAULT_OUT,
    configs: tuple[GoldenLoopRunConfig, ...] | None = None,
    write_snapshots: bool = False,
    now_fn: Callable[[], datetime] | None = None,
) -> dict[str, Any]:
    """Run the golden fixture loop and write JSON artifacts under ``out_dir``."""

    sys.path.insert(0, str(_REPO))

    from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_eval import (
        evaluate_against_golden,
    )
    from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures import (
        load_empty_copy,
        load_game_data_rules,
        load_genetic_sample_seeds,
        load_golden_copy,
    )
    from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_loader import (
        build_golden_oracle,
        write_decoded_snapshots,
    )
    from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_solver_run import (
        GoldenSolverConfig,
        run_golden_solver,
    )
    from shapez2_factory.domain.asteroid_lab.copy_decode import decode_copy_string

    grid = configs or build_config_grid()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    clock = now_fn or (lambda: datetime.now(UTC))

    empty_copy = load_empty_copy()
    golden_copy = load_golden_copy()
    rules = load_game_data_rules()
    seeds = load_genetic_sample_seeds()
    golden_oracle = build_golden_oracle(decode_copy_string(golden_copy).root)

    if write_snapshots:
        write_decoded_snapshots(
            empty_copy=empty_copy,
            golden_copy=golden_copy,
            out_dir=out / "snapshots",
        )

    runs_path = out / "runs.jsonl"
    failure_patterns: dict[str, int] = {}
    best_valid_score = float("-inf")
    best_valid_record: dict[str, Any] | None = None
    best_any_score = float("-inf")
    best_any_record: dict[str, Any] | None = None
    run_records: list[dict[str, Any]] = []

    with runs_path.open("w", encoding="utf-8") as runs_file:
        for loop_config in grid:
            solver_config = GoldenSolverConfig(
                throughput_target_percent=loop_config.throughput_target_percent,
                budget_ms=loop_config.budget_ms,
                speed_tier=loop_config.speed_tier,
            )
            artifacts = run_golden_solver(
                copy_text=empty_copy,
                game_data_rules=rules,
                genetic_sample_seeds=seeds,
                config=solver_config,
            )
            result = evaluate_against_golden(artifacts, golden_oracle)
            record = {
                "timestamp": clock().isoformat(),
                "config": asdict(loop_config),
                "result": _eval_record_dict(result),
            }
            runs_file.write(json.dumps(record, sort_keys=True) + "\n")
            run_records.append(record)

            if not result.valid:
                for diag in result.diagnostics:
                    failure_patterns[diag] = failure_patterns.get(diag, 0) + 1

            if result.score > best_any_score:
                best_any_score = result.score
                best_any_record = record
            if result.valid and result.score > best_valid_score:
                best_valid_score = result.score
                best_valid_record = record

    best_record = best_valid_record or best_any_record
    best_config_path = out / "best_config.json"
    best_config_path.write_text(
        json.dumps(best_record or {}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    diagnostics_path = out / "diagnostics.json"
    diagnostics_payload = {
        "failure_patterns": failure_patterns,
        "run_count": len(grid),
        "best_score": best_valid_score if best_valid_record is not None else None,
        "best_valid": best_valid_record is not None,
        "best_any_score": best_any_score if best_any_record is not None else None,
    }
    diagnostics_path.write_text(
        json.dumps(diagnostics_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "out_dir": str(out),
        "runs_path": str(runs_path),
        "best_config_path": str(best_config_path),
        "diagnostics_path": str(diagnostics_path),
        "run_count": len(run_records),
        "best_valid": best_valid_record is not None,
        "best_score": best_valid_score if best_valid_record is not None else None,
    }


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Golden fixture optimization loop")
    parser.add_argument(
        "--throughput-targets",
        default="70,80,90",
        help="Comma-separated throughput_target_percent values",
    )
    parser.add_argument("--budget-ms", type=int, default=60_000)
    parser.add_argument(
        "--speed-tiers",
        default="1",
        help="Comma-separated speed_tier values",
    )
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUT),
        help="Output directory for runs.jsonl and summary JSON files",
    )
    parser.add_argument("--write-snapshots", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    targets = tuple(int(x.strip()) for x in args.throughput_targets.split(",") if x.strip())
    speed_tiers = tuple(int(x.strip()) for x in args.speed_tiers.split(",") if x.strip())
    summary = run_golden_loop(
        out_dir=Path(args.out_dir),
        configs=build_config_grid(
            throughput_targets=targets,
            budget_ms=args.budget_ms,
            speed_tiers=speed_tiers,
        ),
        write_snapshots=args.write_snapshots,
    )
    print(f"wrote {summary['out_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
