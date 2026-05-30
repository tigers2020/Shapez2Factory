"""Guard C — run_key + artifact-root safety (pure stdlib).

This module validates a caller-supplied ``run_key`` and ensures the resolved
artifact directory truly nests under an allowed root. It is part of the pure
core (``src/shapez2_factory/**``) and must never import Django.

Containment is verified with :meth:`pathlib.Path.relative_to`, never with
``str.startswith``. A prefix string check is unsafe: ``"/var/runs2"`` would
falsely match the prefix ``"/var/runs"`` even though it is a sibling, not a
child. ``relative_to`` raises ``ValueError`` for non-nested paths, giving us a
correct containment test.
"""

from __future__ import annotations

import re
from pathlib import Path

__all__ = ["ArtifactPathError", "resolve_artifact_dir"]

_RUN_KEY_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class ArtifactPathError(Exception):
    """Raised when a run_key is unsafe or escapes the allowed artifact root."""

    def __init__(self, run_key: str) -> None:
        super().__init__(f"unsafe or out-of-root run_key: {run_key!r}")
        self.run_key = run_key


def resolve_artifact_dir(allowed_root: Path, artifact_root: Path, run_key: str) -> Path:
    """Resolve ``artifact_root / run_key`` and assert it nests under ``allowed_root``.

    Raises :class:`ArtifactPathError` when ``run_key`` contains path separators,
    is a relative-navigation token (``.`` / ``..``), uses characters outside
    ``[A-Za-z0-9._-]``, or resolves to a path that is not contained within
    ``allowed_root``.
    """
    if run_key in (".", "..") or "/" in run_key or "\\" in run_key:
        raise ArtifactPathError(run_key)
    if not _RUN_KEY_RE.fullmatch(run_key):
        raise ArtifactPathError(run_key)
    root = allowed_root.resolve()
    final = (artifact_root / run_key).resolve()
    # Do NOT use str.startswith — "/var/runs2" would falsely match prefix "/var/runs".
    try:
        final.relative_to(root)
    except ValueError as exc:
        raise ArtifactPathError(run_key) from exc
    return final
