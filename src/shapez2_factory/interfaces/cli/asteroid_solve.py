"""``asteroid_solve`` CLI for pure-core artifact validation and solver runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from enum import IntEnum
from io import StringIO
from pathlib import Path

from shapez2_factory.adapters.asteroid_lab.artifact_manifest import (
    MANIFEST_FILENAME,
    MANIFEST_SCHEMA_VERSION,
    ArtifactManifest,
    ManifestSchemaVersionError,
    parse_manifest_checked,
)
from shapez2_factory.adapters.asteroid_lab.artifact_writer import (
    ArtifactWriterError,
    AtomicArtifactWriter,
)
from shapez2_factory.adapters.asteroid_lab.cli_console import (
    emit_cli_line,
    verbose_logging_enabled,
)
from shapez2_factory.adapters.asteroid_lab.json_snapshot_rules import (
    GameDataSnapshotInvalid,
    JsonSnapshotGameDataRulesAdapter,
)
from shapez2_factory.adapters.asteroid_lab.run_key_safety import (
    ArtifactPathError,
    resolve_artifact_dir,
)
from shapez2_factory.adapters.asteroid_lab.run_status import RunLifecycleStatus
from shapez2_factory.application.asteroid_lab.replay_core import write_replay_core_jsonl
from shapez2_factory.application.asteroid_lab.run_stack import RunStackUseCase

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
        help="Run the solver and write a finalized artifact directory.",
    )
    run.add_argument("--artifact-root", dest="artifact_root", type=Path, required=True)
    run.add_argument("--run-key", dest="run_key", type=str, required=True)
    run.add_argument("--copy-file", dest="copy_file", type=Path, required=True)
    run.add_argument("--snapshot", dest="snapshot", type=Path, required=True)
    run.add_argument("--expected-snapshot-hash", dest="expected_snapshot_hash", default=None)
    run.add_argument(
        "--throughput-target-percent",
        dest="throughput_target_percent",
        type=int,
        default=80,
    )
    run.add_argument("--budget-ms", dest="budget_ms", type=int, default=60_000)
    run.add_argument("--verbose", dest="verbose", action="store_true")
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
    """Fail-closed validation of a finalized artifact directory."""

    manifest_path = artifact_dir / MANIFEST_FILENAME
    if not manifest_path.is_file():
        print(f"error: manifest not found: {manifest_path}", file=sys.stderr)
        return int(ExitCode.VALIDATION_FAILED)

    try:
        text = manifest_path.read_text(encoding="utf-8")
        manifest = parse_manifest_checked(text)
    except ManifestSchemaVersionError as exc:
        print(f"error: invalid manifest schema: {exc}", file=sys.stderr)
        return int(ExitCode.VALIDATION_FAILED)
    except (ValueError, KeyError, OSError) as exc:
        print(f"error: unreadable or malformed manifest: {exc!r}", file=sys.stderr)
        return int(ExitCode.VALIDATION_FAILED)

    if manifest.lifecycle_status != RunLifecycleStatus.ARTIFACT_WRITTEN:
        print(
            f"error: artifact not finalized: lifecycle_status="
            f"{manifest.lifecycle_status.value!r} "
            f"(expected {RunLifecycleStatus.ARTIFACT_WRITTEN.value!r})",
            file=sys.stderr,
        )
        return int(ExitCode.VALIDATION_FAILED)

    artifact_root = artifact_dir.resolve()
    for relpath, expected_hash in manifest.content_hashes.items():
        payload_path = (artifact_dir / relpath).resolve()
        try:
            payload_path.relative_to(artifact_root)
        except ValueError:
            print(
                f"error: payload path escapes artifact dir: {relpath}",
                file=sys.stderr,
            )
            return int(ExitCode.VALIDATION_FAILED)
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
        f"ok: artifact '{manifest.run_key}' verified ({len(manifest.content_hashes)} files)",
        file=sys.stdout,
    )
    return int(ExitCode.OK)


def _json_bytes(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def _read_text_file(path: Path, *, label: str) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return path.read_text(encoding="utf-8")


def _read_copy_file(path: Path) -> str:
    text = _read_text_file(path, label="copy file")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    raise ValueError(f"copy file is empty: {path}")


def _run_artifact(
    artifact_root: Path,
    run_key: str,
    allowed_root: Path,
    replace_existing: bool,
    copy_file: Path,
    snapshot_path: Path,
    expected_snapshot_hash: str | None,
    throughput_target_percent: int,
    budget_ms: int,
    verbose: bool,
) -> int:
    """Execute the pure stack and write a finalized artifact directory."""

    resolve_artifact_dir(allowed_root, artifact_root, run_key)
    copy_text = _read_copy_file(copy_file)
    snapshot_text = _read_text_file(snapshot_path, label="game_data_snapshot")
    snapshot_payload = json.loads(snapshot_text)
    rules = JsonSnapshotGameDataRulesAdapter.from_payload(
        snapshot_payload,
        expected_hash=expected_snapshot_hash,
    )
    result = RunStackUseCase(game_data_rules=rules).run(
        copy_text=copy_text,
        throughput_target_percent=throughput_target_percent,
        budget_ms=budget_ms,
    )
    if verbose or verbose_logging_enabled():
        for record in result.solver_summary.get("layer_summaries", []):
            if not isinstance(record, dict):
                continue
            emit_cli_line(
                "layer_done",
                layer_slug=record.get("layer_slug"),
                elapsed_ms=record.get("elapsed_ms"),
            )

    replay_stream = StringIO()
    write_replay_core_jsonl(replay_stream, result.replay_core_lines, run_key=run_key)

    writer = AtomicArtifactWriter(
        artifact_root,
        run_key,
        replace_existing=replace_existing,
    )
    writer.open_staging()
    writer.write_output("input/copy.txt", copy_text.encode("utf-8"))
    writer.write_output("input/game_data_snapshot.json", snapshot_text.encode("utf-8"))
    writer.write_output("output/layer01_complete_map.json", _json_bytes(result.complete_map_json))
    writer.write_output("output/stack_result.json", _json_bytes(result.stack_result_json))
    writer.write_output("output/solver_summary.json", _json_bytes(result.solver_summary))
    writer.write_output("output/replay_core.jsonl", replay_stream.getvalue().encode("utf-8"))
    manifest = ArtifactManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        run_key=run_key,
        lifecycle_status=RunLifecycleStatus.ARTIFACT_WRITTEN,
        created_at_utc=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        core_build_id="local",
        paths={
            "copy": "input/copy.txt",
            "game_data_snapshot": "input/game_data_snapshot.json",
            "layer01_complete_map": "output/layer01_complete_map.json",
            "stack_result": "output/stack_result.json",
            "solver_summary": "output/solver_summary.json",
            "replay_core": "output/replay_core.jsonl",
        },
        game_data_provenance={"source": "cli_snapshot_file"},
        error_code=result.error_code,
    )
    final_dir = writer.finalize(manifest)
    print(f"ok: artifact written: {final_dir}", file=sys.stdout)
    return int(ExitCode.OK if result.ok else ExitCode.STACK_UNAVAILABLE)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate-artifact":
        emit_cli_line("validate-artifact start")
        started = time.monotonic()
        code = validate_artifact(args.dir)
        elapsed_ms = int((time.monotonic() - started) * 1000)
        emit_cli_line(
            "validate-artifact end",
            exit=code,
            elapsed_ms=elapsed_ms,
            ok=code == int(ExitCode.OK),
        )
        return code

    if args.command == "run":
        emit_cli_line("run start", run_key=args.run_key)
        started = time.monotonic()
        try:
            code = _run_artifact(
                args.artifact_root,
                args.run_key,
                args.allowed_root,
                args.replace_existing,
                args.copy_file,
                args.snapshot,
                args.expected_snapshot_hash,
                args.throughput_target_percent,
                args.budget_ms,
                args.verbose,
            )
        except ArtifactPathError as exc:
            print(f"error: {exc}", file=sys.stderr)
            code = int(ExitCode.VALIDATION_FAILED)
        except (
            ArtifactWriterError,
            FileNotFoundError,
            GameDataSnapshotInvalid,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            print(f"error: {exc}", file=sys.stderr)
            code = int(ExitCode.VALIDATION_FAILED)
        elapsed_ms = int((time.monotonic() - started) * 1000)
        emit_cli_line(
            "run end",
            run_key=args.run_key,
            exit=code,
            elapsed_ms=elapsed_ms,
            ok=code == int(ExitCode.OK),
        )
        return code

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
