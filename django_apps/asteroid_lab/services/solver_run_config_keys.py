"""Stable ``SolverRun.config_json`` keys (wire contract; no free-form strings)."""

from __future__ import annotations

SOLVER_RUN_CONFIG_GENE_TEMPLATE_SOURCE_KEY = "gene_template_source"
SOLVER_RUN_CONFIG_SERVER_XY_PARAMS_KEY = "server_xy_params"
SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY = "solver_summary"
SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY = "solver_runtime_replay_frames"

__all__ = [
    "SOLVER_RUN_CONFIG_GENE_TEMPLATE_SOURCE_KEY",
    "SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY",
    "SOLVER_RUN_CONFIG_SERVER_XY_PARAMS_KEY",
    "SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY",
]
