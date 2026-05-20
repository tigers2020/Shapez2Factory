"""Parse generation caps from ``SolverRun.config_json`` (12E stub)."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from django_apps.asteroid_lab.optimization.candidate_dtos import CandidateGenerationConfig
from django_apps.asteroid_lab.optimization.candidate_generator import default_generation_config
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_MAX_CANDIDATES_KEY,
    SOLVER_RUN_CONFIG_PROBE_BUDGET_FACTOR_KEY,
    SOLVER_RUN_CONFIG_ROUTE_PROBE_MAX_EXPANSIONS_KEY,
)


def generation_config_from_run_config(
    run_config: dict[str, Any] | None,
) -> CandidateGenerationConfig:
    """Merge optional numeric caps from run config onto v0 defaults."""

    base = default_generation_config()
    if not run_config:
        return base

    max_candidates = run_config.get(SOLVER_RUN_CONFIG_MAX_CANDIDATES_KEY)
    max_expansions = run_config.get(SOLVER_RUN_CONFIG_ROUTE_PROBE_MAX_EXPANSIONS_KEY)
    probe_budget_factor = run_config.get(SOLVER_RUN_CONFIG_PROBE_BUDGET_FACTOR_KEY)

    kwargs: dict[str, int | None] = {}
    if isinstance(max_candidates, int) and max_candidates > 0:
        kwargs["max_candidates"] = max_candidates
    if isinstance(max_expansions, int) and max_expansions > 0:
        kwargs["route_probe_max_expansions"] = max_expansions
    if isinstance(probe_budget_factor, int) and probe_budget_factor > 0:
        kwargs["probe_budget_factor"] = probe_budget_factor

    if not kwargs:
        return base
    return replace(base, **kwargs)
