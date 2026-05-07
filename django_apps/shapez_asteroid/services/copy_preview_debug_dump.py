"""Optional filesystem dump of copy code + decoded JSON (debugging)."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def dump_copy_preview_debug(code: str, decoded: dict[str, Any], dump_dir: str | Path) -> None:
    """Write ``*_encrypt_code.txt`` and ``*_decoded.json`` under ``dump_dir``.

    Failures are logged and swallowed so the HTTP handler keeps returning 200.
    """

    root = Path(dump_dir)
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.warning("shapez copy debug dump: cannot mkdir %s: %s", root, exc)
        return

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ")
    digest = hashlib.sha256(code.encode("utf-8", errors="surrogatepass")).hexdigest()[:10]
    stem = f"copy_preview_{stamp}_{digest}"
    code_path = root / f"{stem}_encrypt_code.txt"
    json_path = root / f"{stem}_decoded.json"

    try:
        code_path.write_text(code, encoding="utf-8", newline="\n")
    except OSError as exc:
        logger.warning("shapez copy debug dump: cannot write %s: %s", code_path, exc)
        return

    try:
        json_path.write_text(
            json.dumps(decoded, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except OSError as exc:
        logger.warning("shapez copy debug dump: cannot write %s: %s", json_path, exc)
