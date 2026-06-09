"""Golden fixture experiments package (PR-1 loader; PR-2 fixtures; PR-3/4 solver eval)."""

from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_assembler import (
    assemble_candidate_blueprint,
    encode_candidate_copy_string,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_eval import (
    GoldenEvalResult,
    evaluate_against_golden,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures import (
    golden_fixture_dir,
    load_game_data_rules,
    load_genetic_sample_seeds,
    load_genetic_sample_seeds_payload,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_loader import (
    GoldenOracle,
    build_golden_oracle,
    load_golden_fixture_summary,
    load_shapez_copy_string,
    summarize_blueprint,
    write_decoded_snapshots,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_solver_run import (
    GoldenSolverArtifacts,
    GoldenSolverConfig,
    run_golden_solver,
)

__all__ = [
    "GoldenEvalResult",
    "GoldenOracle",
    "GoldenSolverArtifacts",
    "GoldenSolverConfig",
    "assemble_candidate_blueprint",
    "build_golden_oracle",
    "encode_candidate_copy_string",
    "evaluate_against_golden",
    "golden_fixture_dir",
    "load_game_data_rules",
    "load_genetic_sample_seeds",
    "load_genetic_sample_seeds_payload",
    "load_golden_fixture_summary",
    "load_shapez_copy_string",
    "run_golden_solver",
    "summarize_blueprint",
    "write_decoded_snapshots",
]
