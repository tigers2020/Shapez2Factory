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
import os
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = _REPO / "var" / "experiments" / "golden_loop"


@dataclass(frozen=True, slots=True)
class GoldenLoopRunConfig:
    throughput_target_percent: int
    budget_ms: int
    speed_tier: int = 1


def _gene_seeds_entry_count(seeds: object) -> int:
    entries = getattr(seeds, "entries", None)
    if isinstance(entries, (list, tuple)):
        return len(entries)
    return 0


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


def _eval_record_dict(result: object) -> dict[str, object]:
    payload = asdict(result)
    payload["diagnostics"] = list(result.diagnostics)
    return payload


def _load_genetic_sample_seeds_for_loop(
    gene_seeds_source: str,
    *,
    gene_seeds_db_scope: str = "admin",
) -> tuple[object, dict[str, object] | None]:
    if gene_seeds_source == "fixture":
        from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures import (
            load_genetic_sample_seeds,
        )

        return load_genetic_sample_seeds(), None

    if gene_seeds_source != "db":
        msg = f"unsupported gene_seeds_source={gene_seeds_source!r} (fixture|db)"
        raise ValueError(msg)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()

    from django_apps.asteroid_lab.services.gene_seed_l3_catalog import (
        GeneSeedCatalogScope,
        build_genetic_sample_seed_snapshot_from_db,
    )
    from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
        GeneticSampleSeedSnapshot,
    )

    scope: GeneSeedCatalogScope = "all" if gene_seeds_db_scope == "all" else "admin"
    payload = build_genetic_sample_seed_snapshot_from_db(scope=scope)
    return GeneticSampleSeedSnapshot.from_payload(payload), payload


def run_golden_loop(
    *,
    out_dir: Path | str = DEFAULT_OUT,
    configs: tuple[GoldenLoopRunConfig, ...] | None = None,
    write_snapshots: bool = False,
    write_best_copy: bool = False,
    gene_seeds_source: str = "fixture",
    gene_seeds_db_scope: str = "admin",
    now_fn: Callable[[], datetime] | None = None,
) -> dict[str, object]:
    """Run the golden fixture loop and write JSON artifacts under ``out_dir``."""

    sys.path.insert(0, str(_REPO))

    from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_eval import (
        evaluate_against_golden,
    )
    from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures import (
        load_empty_copy,
        load_game_data_rules,
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
    seeds, seed_payload = _load_genetic_sample_seeds_for_loop(
        gene_seeds_source,
        gene_seeds_db_scope=gene_seeds_db_scope,
    )
    golden_oracle = build_golden_oracle(decode_copy_string(golden_copy).root)

    if seed_payload is not None:
        (out / "genetic_sample_seeds.json").write_text(
            json.dumps(seed_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if write_snapshots:
        write_decoded_snapshots(
            empty_copy=empty_copy,
            golden_copy=golden_copy,
            out_dir=out / "snapshots",
        )

    runs_path = out / "runs.jsonl"
    failure_patterns: dict[str, int] = {}
    best_valid_score = float("-inf")
    best_valid_record: dict[str, object] | None = None
    best_valid_artifacts: object | None = None
    best_any_score = float("-inf")
    best_any_record: dict[str, object] | None = None
    run_records: list[dict[str, object]] = []

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
                best_valid_artifacts = artifacts

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
        "gene_seeds_source": gene_seeds_source,
        "gene_seeds_db_scope": gene_seeds_db_scope if gene_seeds_source == "db" else None,
        "gene_seeds_entry_count": _gene_seeds_entry_count(seeds),
    }
    diagnostics_path.write_text(
        json.dumps(diagnostics_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    best_copy_path: Path | None = None
    if write_best_copy and best_valid_artifacts is not None:
        from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_assembler import (
            encode_candidate_copy_string,
        )

        best_copy_path = out / "best_result.shapez.txt"
        copy_out = encode_candidate_copy_string(
            artifacts=best_valid_artifacts,
            empty_copy=empty_copy,
        )
        best_copy_path.write_text(copy_out + "\n", encoding="utf-8")

    return {
        "out_dir": str(out),
        "runs_path": str(runs_path),
        "best_config_path": str(best_config_path),
        "diagnostics_path": str(diagnostics_path),
        "best_copy_path": str(best_copy_path) if best_copy_path is not None else None,
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
    parser.add_argument(
        "--write-best-copy",
        action="store_true",
        help="Write best_result.shapez.txt from best valid solver artifacts",
    )
    parser.add_argument(
        "--gene-seeds",
        choices=("fixture", "db"),
        default="fixture",
        help="genetic_sample_seeds source: frozen fixture (CI) or live GeneSeed DB",
    )
    parser.add_argument(
        "--gene-seeds-db-scope",
        choices=("admin", "all"),
        default="admin",
        help="When --gene-seeds=db: admin=GeneSeed admin catalog; all=GeneSeed.objects.all()",
    )
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
        write_best_copy=args.write_best_copy,
        gene_seeds_source=args.gene_seeds,
        gene_seeds_db_scope=args.gene_seeds_db_scope,
    )
    print(f"wrote {summary['out_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
