"""Asteroid Lab algorithm layer stack exports."""

from __future__ import annotations

from importlib import import_module

from django_apps.asteroid_lab.layers.contracts import (
    DiagnosticLayerSnapshot,
    LayerBudgetContext,
    StackRunResult,
    StackRunStatus,
)

__all__ = [
    "DiagnosticLayerSnapshot",
    "LAYER_STACK_BUDGET_MS",
    "LayerBudgetContext",
    "StackRunResult",
    "StackRunStatus",
    "run_full_from_cleanup_recon",
    "run_layers_02_to_05",
    "run_layers_02_to_06",
]


def __getattr__(name: str) -> object:
    if name in {
        "LAYER_STACK_BUDGET_MS",
        "run_full_from_cleanup_recon",
        "run_layers_02_to_05",
        "run_layers_02_to_06",
    }:
        stack_runner = import_module("django_apps.asteroid_lab.layers.stack_runner")
        return getattr(stack_runner, name)
    raise AttributeError(name)
