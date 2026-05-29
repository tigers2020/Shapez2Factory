"""Layer 04 rim bundle provisional placement."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = ["run_layer_04_rim_bundle_placement"]


def __getattr__(name: str) -> Any:
    if name == "run_layer_04_rim_bundle_placement":
        run_module = import_module(
            "django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run"
        )
        return getattr(run_module, name)
    raise AttributeError(name)
