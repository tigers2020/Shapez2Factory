"""Diagnostic snapshots must not be resumable stack inputs."""

from __future__ import annotations

import inspect

import django_apps.asteroid_lab.layers.stack_runner as stack_runner_mod


def test_stack_runner_has_no_resume_public_api() -> None:
    forbidden = ("resume", "from_diagnostic", "run_from_layer")
    for name in dir(stack_runner_mod):
        if name.startswith("_"):
            continue
        for token in forbidden:
            assert token not in name.lower(), f"public API {name!r} suggests resumable stack"

    source = inspect.getsource(stack_runner_mod)
    for token in forbidden:
        assert token not in source, f"stack_runner source mentions {token!r}"
