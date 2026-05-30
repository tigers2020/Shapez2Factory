"""Run lifecycle status enum (spec §4).

Authority split: ``manifest.lifecycle_status`` is the *artifact* lifecycle and is immutable at
``ARTIFACT_WRITTEN`` after atomic finalize. ``QUEUED``/``RUNNING``/``ARTIFACT_WRITING`` are
pre-finalize orchestration/DB states; ``INDEXED``/``SUCCEEDED``/``FAILED`` are DB/``SolverRun``
states only. Django ingest MUST NEVER rewrite ``manifest.json``.
"""

from __future__ import annotations

from enum import StrEnum


class RunLifecycleStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    ARTIFACT_WRITING = "artifact_writing"
    ARTIFACT_WRITTEN = "artifact_written"
    INDEXED = "indexed"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


__all__ = ["RunLifecycleStatus"]
