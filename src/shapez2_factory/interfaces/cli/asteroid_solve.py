"""``asteroid_solve`` CLI — pure-core shell + ``validate-artifact`` command.

PR-CLI-3a. This module is part of the pure core (``src/shapez2_factory/**``) and
must never import Django (BA-1): stdlib only.

Subcommands:

* ``validate-artifact`` — fail-closed verification of a finalized artifact
  directory (manifest schema, lifecycle status, payload content hashes).
* ``run`` — stub. Enforces Guard C (``run_key`` / artifact-root safety) then
  reports that the full solver stack is unavailable until PR-CLI-3b.

Errors are printed to ``stderr``; success lines to ``stdout``. Exit codes are
typed via :class:`ExitCode` (argparse reserves ``2`` for usage errors, so it is
deliberately unused here).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from enum import IntEnum
from pathlib import Path

from shapez2_factory.adapters.asteroid_lab.artifact_manifest import (
    MANIFEST_FILENAME,
    ManifestSchemaVersionError,
    parse_manifest_checked,
)
from shapez2_factory.adapters.asteroid_lab.run_key_safety import (
    ArtifactPathError,
    resolve_artifact_dir,
)
from shapez2_factory.adapters.asteroid_lab.run_status import RunLifecycleStatus

_PROG = "asteroid_solve"


class ExitCode(IntEnum):
    """Typed process exit codes for the ``asteroid_solve`` CLI."""

    OK = 0
    VALIDATION_FAILED = 10
    STACK_UNAVAILABLE = 20


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_PROG,
        description="Asteroid Lab CLI-first solver shell (pure core, no Django).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser(
        "validate-artifact",
        help="Verify a finalized artifact directory (manifest + content hashes).",
    )
    validate.add_argument(
        "--dir",
        dest="dir",
        type=Path,
        required=True,
        help="Artifact directory containing manifest.json.",
    )

    run = subparsers.add_parser(
        "run",
        help="Run the solver and write an artifact (stub until PR-CLI-3b).",
    )
    run.add_argument("--artifact-root", dest="artifact_root", type=Path, required=True)
    run.add_argument("--run-key", dest="run_key", type=str, required=True)
    run.add_argument(
        "--allowed-root",
        dest="allowed_root",
        type=Path,
        default=Path("var/runs"),
        help="Configured sandbox root that artifacts must nest under (Guard C).",
    )
    run.add_argument("--replace-existing", dest="replace_existing", action="store_true")

    return parser


def validate_artifact(artifact_dir: Path) -> int:
    """Fail-closed validation of a finalized artifact directory.

    Returns :attr:`ExitCode.OK` only when the manifest parses at the supported
    schema version, declares ``ARTIFACT_WRITTEN`` lifecycle, and every payload in
    ``content_hashes`` exists with a matching sha256. Any failure prints a typed
    error to ``stderr`` and returns :attr:`ExitCode.VALIDATION_FAILED`.
    """
    manifest_path = artifact_dir / MANIFEST_FILENAME
    if not manifest_path.is_file():
        print(f"error: manifest not found: {manifest_path}", file=sys.stderr)
        return int(ExitCode.VALIDATION_FAILED)

    text = manifest_path.read_text(encoding="utf-8")
    try:
        manifest = parse_manifest_checked(text)
    except ManifestSchemaVersionError as exc:
        print(f"error: invalid manifest schema: {exc}", file=sys.stderr)
        return int(ExitCode.VALIDATION_FAILED)
    except json.JSONDecodeError as exc:
        print(f"error: malformed manifest JSON: {exc}", file=sys.stderr)
        return int(ExitCode.VALIDATION_FAILED)

    if manifest.lifecycle_status != RunLifecycleStatus.ARTIFACT_WRITTEN:
        print(
            f"error: artifact not finalized: lifecycle_status="
            f"{manifest.lifecycle_status.value!r} "
            f"(expected {RunLifecycleStatus.ARTIFACT_WRITTEN.value!r})",
            file=sys.stderr,
        )
        return int(ExitCode.VALIDATION_FAILED)

    for relpath, expected_hash in manifest.content_hashes.items():
        payload_path = artifact_dir / relpath
        if not payload_path.is_file():
            print(f"error: missing payload file: {relpath}", file=sys.stderr)
            return int(ExitCode.VALIDATION_FAILED)
        actual_hash = hashlib.sha256(payload_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            print(
                f"error: content hash mismatch for {relpath}: "
                f"expected {expected_hash}, got {actual_hash}",
                file=sys.stderr,
            )
            return int(ExitCode.VALIDATION_FAILED)

    print(
        f"ok: artifact '{manifest.run_key}' verified " f"({len(manifest.content_hashes)} files)",
        file=sys.stdout,
    )
    return int(ExitCode.OK)


def _run_stub(
    artifact_root: Path,
    run_key: str,
    allowed_root: Path,
    replace_existing: bool,
) -> int:
    """Stub ``run`` handler — enforces Guard C, then reports stack unavailable.

    Guard C is wired now so unsafe ``run_key`` values and out-of-sandbox
    ``artifact_root`` values fail fast even though the full solver stack does not
    land until PR-CLI-3b. ``allowed_root`` is the configured sandbox (Guard C
    threat-2 containment) and the resolved artifact dir must nest under it.
    """
    resolve_artifact_dir(allowed_root, artifact_root, run_key)
    print(
        "error: the full solver stack is not available until PR-CLI-3b; "
        "'run' cannot produce an artifact yet",
        file=sys.stderr,
    )
    return int(ExitCode.STACK_UNAVAILABLE)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate-artifact":
        return validate_artifact(args.dir)

    if args.command == "run":
        try:
            return _run_stub(
                args.artifact_root,
                args.run_key,
                args.allowed_root,
                args.replace_existing,
            )
        except ArtifactPathError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return int(ExitCode.VALIDATION_FAILED)

    parser.error(f"unknown command: {args.command!r}")
    return int(ExitCode.VALIDATION_FAILED)  # pragma: no cover - parser.error exits


__all__ = [
    "ExitCode",
    "build_parser",
    "main",
    "validate_artifact",
]


if __name__ == "__main__":
    raise SystemExit(main())
