"""Runtime ``trace_events`` must not pull serialization, preview, or django."""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_V2_ROOT = _REPO_ROOT / "django_apps" / "shapez_asteroid" / "services" / "asteroid_mining_layout_v2"
_RUNTIME_TRACE_EVENTS = _V2_ROOT / "runtime" / "trace_events.py"


def _forbidden_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    bad: list[str] = []
    forbidden_prefixes = (
        "django",
        "django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.serialization",
        "django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.preview_reconstruction_timeline",
        "django_apps.shapez_asteroid.services.behavior_artifact_collector",
        "django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.replay",
        "django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                n = alias.name
                if n == "django" or n.startswith("django."):
                    bad.append(f"{path}: import {n}")
                if any(n == p or n.startswith(p + ".") for p in forbidden_prefixes if "." in n):
                    bad.append(f"{path}: import {n}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            m = node.module
            if m == "django" or m.startswith("django."):
                bad.append(f"{path}: from {m}")
            for p in forbidden_prefixes:
                if m == p or m.startswith(p + "."):
                    bad.append(f"{path}: from {m}")
    return bad


def test_runtime_trace_events_module_has_no_forbidden_imports() -> None:
    offenders = _forbidden_imports(_RUNTIME_TRACE_EVENTS)
    assert not offenders, "\n".join(offenders)


def test_trace_event_single_identity_across_dto_and_runtime_modules() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import dto as dto_mod
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime import (
        trace_events as rt_mod,
    )

    assert dto_mod.TraceEvent is rt_mod.TraceEvent
