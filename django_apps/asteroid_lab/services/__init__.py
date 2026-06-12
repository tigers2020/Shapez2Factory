"""Asteroid Lab application services (persistence/cache/UI); solver remains DTO-driven."""

from __future__ import annotations

from importlib import import_module

from django_apps.asteroid_lab.services.dto import ReplayFrameDTO

__all__ = [
    "ReplayFrameDTO",
    "append_replay_frame",
    "create_project_from_copy_code",
    "create_solver_run",
    "ensure_default_replay_track",
    "get_replay_track_payload",
    "get_topology_modal_payload",
    "update_playback_session",
]

_EXPORT_MODULES = {
    "append_replay_frame": "django_apps.asteroid_lab.services.replay_service",
    "create_project_from_copy_code": "django_apps.asteroid_lab.services.project_service",
    "create_solver_run": "django_apps.asteroid_lab.services.experiment_service",
    "ensure_default_replay_track": "django_apps.asteroid_lab.services.experiment_service",
    "get_replay_track_payload": "django_apps.asteroid_lab.services.replay_service",
    "get_topology_modal_payload": "django_apps.asteroid_lab.services.topology_service",
    "update_playback_session": "django_apps.asteroid_lab.services.replay_service",
}


def __getattr__(name: str) -> object:
    if name in _EXPORT_MODULES:
        module = import_module(_EXPORT_MODULES[name])
        return getattr(module, name)
    raise AttributeError(name)
