"""Pre-reconstruction cleanup: strip buildings and compute topology walls."""

from django_apps.asteroid_lab.cleanup.result import CleanupResult


def __getattr__(name: str) -> object:
    if name == "deconstruct_snapshot":
        from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot

        return deconstruct_snapshot
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["CleanupResult", "deconstruct_snapshot"]
