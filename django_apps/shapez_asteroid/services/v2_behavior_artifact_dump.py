"""Write v2 copy-preview behavior artifact JSON files (development-only, output-only)."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_JSON_SUFFIX = "_behavior_artifact.json"
_BEHAVIOR_ARTIFACT_MAX_STEMS = 10


def _prune_behavior_artifact_dir(root: Path) -> None:
    stems: dict[str, int] = {}
    try:
        for path in root.glob(f"*{_JSON_SUFFIX}"):
            if not path.is_file():
                continue
            name = path.name
            if not name.endswith(_JSON_SUFFIX):
                continue
            stem = name[: -len(_JSON_SUFFIX)]
            try:
                mtime_ns = path.stat().st_mtime_ns
            except OSError:
                continue
            prev = stems.get(stem)
            if prev is None or mtime_ns > prev:
                stems[stem] = mtime_ns
    except OSError as exc:
        logger.warning("v2 behavior artifact: prune scan failed dir=%s: %s", root, exc)
        return

    if len(stems) <= _BEHAVIOR_ARTIFACT_MAX_STEMS:
        return
    ordered = sorted(stems.items(), key=lambda kv: (kv[1], kv[0]))
    for stem, _ in ordered[: len(stems) - _BEHAVIOR_ARTIFACT_MAX_STEMS]:
        path = root / f"{stem}{_JSON_SUFFIX}"
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("v2 behavior artifact: prune unlink failed path=%s: %s", path, exc)


def dump_v2_behavior_artifact_json(payload: dict[str, Any], dump_dir: str | Path) -> None:
    """Write one JSON file under ``dump_dir``. Failures are logged and swallowed."""

    root = Path(dump_dir)
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.warning("v2 behavior artifact: cannot mkdir %s: %s", root, exc)
        return

    digest = str(payload.get("input_digest_prefix") or "unknown")[:32]
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ")
    stem = f"v2_behavior_artifact_{stamp}_{digest}"
    json_path = root / f"{stem}{_JSON_SUFFIX}"

    try:
        json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except OSError as exc:
        logger.warning("v2 behavior artifact: cannot write %s: %s", json_path, exc)
        return
    except (TypeError, ValueError) as exc:
        logger.warning("v2 behavior artifact: JSON serialize failed path=%s: %s", json_path, exc)
        return

    _prune_behavior_artifact_dir(root)


def input_digest_prefix_from_code(code: str) -> str:
    """Short SHA-256 prefix for artifact correlation (not the raw copy string)."""

    return hashlib.sha256(code.encode("utf-8", errors="surrogatepass")).hexdigest()[:16]


__all__ = [
    "dump_v2_behavior_artifact_json",
    "input_digest_prefix_from_code",
]
