"""Optional filesystem dump of copy code + decoded JSON (debugging)."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_CODE_SUFFIX = "_encrypt_code.txt"
_JSON_SUFFIX = "_decoded.json"
# stem(한 번의 덤프 = txt+json 한 쌍) 기준으로 아래 상한만 남기고 오래된 것부터 삭제한다.
_COPY_PREVIEW_DEBUG_MAX_STEMS = 10


def _copy_preview_stem_from_name(name: str) -> str | None:
    if name.endswith(_CODE_SUFFIX):
        return name[: -len(_CODE_SUFFIX)]
    if name.endswith(_JSON_SUFFIX):
        return name[: -len(_JSON_SUFFIX)]
    return None


def _copy_preview_stem_mtime_ns(path: Path) -> tuple[str, int] | None:
    if not path.is_file():
        return None
    stem = _copy_preview_stem_from_name(path.name)
    if stem is None:
        return None
    try:
        mtime_ns = path.stat().st_mtime_ns
    except OSError:
        return None
    return stem, mtime_ns


def _scan_copy_preview_stems(root: Path) -> dict[str, int] | None:
    stems: dict[str, int] = {}
    try:
        for path in root.glob("copy_preview_*"):
            pair = _copy_preview_stem_mtime_ns(path)
            if pair is None:
                continue
            stem, mtime_ns = pair
            prev = stems.get(stem)
            if prev is None or mtime_ns > prev:
                stems[stem] = mtime_ns
    except OSError as exc:
        logger.warning("shapez copy debug dump: prune scan failed dir=%s: %s", root, exc)
        return None
    return stems


def _unlink_copy_preview_stem_files(root: Path, stem: str) -> None:
    for suffix in (_CODE_SUFFIX, _JSON_SUFFIX):
        path = root / f"{stem}{suffix}"
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("shapez copy debug dump: prune unlink failed path=%s: %s", path, exc)


def _prune_copy_preview_debug_dir(root: Path) -> None:
    """``copy_preview_*`` stem 수가 `_COPY_PREVIEW_DEBUG_MAX_STEMS`를 넘으면
    mtime 오래된 stem부터 삭제한다.
    """

    stems = _scan_copy_preview_stems(root)
    if stems is None:
        return

    max_stems = _COPY_PREVIEW_DEBUG_MAX_STEMS
    if len(stems) <= max_stems:
        return
    ordered = sorted(stems.items(), key=lambda kv: (kv[1], kv[0]))
    for stem, _ in ordered[: len(stems) - max_stems]:
        _unlink_copy_preview_stem_files(root, stem)


def dump_copy_preview_debug(code: str, decoded: dict[str, Any], dump_dir: str | Path) -> None:
    """Write ``*_encrypt_code.txt`` and ``*_decoded.json`` under ``dump_dir``.

    성공 후 stem(한 쌍)이 `_COPY_PREVIEW_DEBUG_MAX_STEMS`를 넘으면 mtime이 오래된 stem부터 삭제한다.

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
        return

    _prune_copy_preview_debug_dir(root)
