"""``AtomicArtifactWriter`` — BA-5 atomic artifact write protocol (spec §5).

Protocol: staging ``var/runs/.tmp/<run_key>`` → write payloads → hash payloads → write
``manifest.json`` last → atomic rename to final ``var/runs/<run_key>``. The final directory never
exists in a partial state. Collisions fail closed unless ``replace_existing`` is set.
"""

from __future__ import annotations

import dataclasses
import hashlib
import os
import shutil
from pathlib import Path

from shapez2_factory.adapters.asteroid_lab.artifact_manifest import (
    MANIFEST_FILENAME,
    ArtifactManifest,
)
from shapez2_factory.adapters.asteroid_lab.run_status import RunLifecycleStatus

_STAGING_DIRNAME = ".tmp"


class ArtifactWriterError(Exception):
    """Base error for the atomic artifact writer."""


class InvalidRunKeyError(ArtifactWriterError):
    """``run_key`` failed the writer-level safety guard."""


class ArtifactExistsError(ArtifactWriterError):
    """Final artifact directory already exists and ``replace_existing`` is False."""


class StagingExistsError(ArtifactWriterError):
    """Staging directory already exists and ``replace_existing`` is False."""


def _validate_run_key(run_key: str) -> None:
    if not run_key or run_key in {".", ".."}:
        raise InvalidRunKeyError(f"invalid run_key: {run_key!r}")
    if "/" in run_key or "\\" in run_key:
        raise InvalidRunKeyError(f"run_key must not contain path separators: {run_key!r}")
    if any(ord(ch) < 32 for ch in run_key):
        raise InvalidRunKeyError(f"run_key must not contain control characters: {run_key!r}")


def _normalize_relpath(relpath: str) -> str:
    parts = [seg for seg in relpath.replace("\\", "/").split("/") if seg not in ("", ".")]
    if not parts:
        raise ArtifactWriterError(f"empty output relpath: {relpath!r}")
    if any(seg == ".." for seg in parts):
        raise ArtifactWriterError(f"output relpath must not traverse: {relpath!r}")
    return "/".join(parts)


class AtomicArtifactWriter:
    def __init__(
        self,
        artifact_root: Path,
        run_key: str,
        *,
        replace_existing: bool = False,
    ) -> None:
        _validate_run_key(run_key)
        self._artifact_root = Path(artifact_root)
        self.run_key = run_key
        self._replace_existing = replace_existing
        self._staging_dir = self._artifact_root / _STAGING_DIRNAME / run_key
        self._final_dir = self._artifact_root / run_key
        self._written: list[str] = []
        self._staging_open = False

    @property
    def staging_dir(self) -> Path:
        return self._staging_dir

    @property
    def final_dir(self) -> Path:
        return self._final_dir

    def open_staging(self) -> Path:
        if self._staging_dir.exists():
            if not self._replace_existing:
                raise StagingExistsError(f"staging already exists: {self._staging_dir}")
            shutil.rmtree(self._staging_dir)
        self._staging_dir.mkdir(parents=True, exist_ok=False)
        self._staging_open = True
        return self._staging_dir

    def write_output(self, relpath: str, data: bytes) -> None:
        if not self._staging_open:
            raise ArtifactWriterError("open_staging() must be called before write_output()")
        rel = _normalize_relpath(relpath)
        if rel == MANIFEST_FILENAME:
            raise ArtifactWriterError("manifest.json is written by finalize(), not write_output()")
        target = self._staging_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        if rel not in self._written:
            self._written.append(rel)

    def finalize(self, manifest: ArtifactManifest) -> Path:
        if not self._staging_open:
            raise ArtifactWriterError("open_staging() must be called before finalize()")
        if self._final_dir.exists() and not self._replace_existing:
            raise ArtifactExistsError(f"final artifact already exists: {self._final_dir}")

        final_manifest = dataclasses.replace(
            manifest,
            content_hashes=self._hash_payloads(),
            lifecycle_status=RunLifecycleStatus.ARTIFACT_WRITTEN,
        )
        manifest_path = self._staging_dir / MANIFEST_FILENAME
        manifest_path.write_text(final_manifest.to_json(), encoding="utf-8")

        if self._final_dir.exists():
            shutil.rmtree(self._final_dir)
        self._final_dir.parent.mkdir(parents=True, exist_ok=True)
        os.replace(self._staging_dir, self._final_dir)
        self._staging_open = False
        return self._final_dir

    def _hash_payloads(self) -> dict[str, str]:
        hashes: dict[str, str] = {}
        for path in sorted(self._staging_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(self._staging_dir).as_posix()
            if rel == MANIFEST_FILENAME:
                continue
            hashes[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        return hashes


__all__ = [
    "ArtifactExistsError",
    "ArtifactWriterError",
    "AtomicArtifactWriter",
    "InvalidRunKeyError",
    "StagingExistsError",
]
