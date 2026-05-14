"""copy-preview 개발용: 타임라인·리플레이 요약 Markdown (``var/`` 덮어쓰기).

솔버 입력으로 사용하지 않는다. 레거시 v1(``asteroid_mining_layout`` / zip 추출본)의
``solver_trace.trace_event`` / ``debug_log_event`` NDJSON은 별도 계약이며,
zip 동봉본 갱신 시 ``documents/Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md``
단계와 경계 로깅을 재점검한다.
"""

from __future__ import annotations

import logging
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SOLVER_ENV_PREFIXES = ("SHAPEZ_SOLVER_", "SHAPEZ_DEV_ASTEROID_")


def resolve_dev_report_md_path(*, base_dir: Path, override: str) -> Path:
    raw = (override or "").strip()
    if raw:
        p = Path(raw)
        return p if p.is_absolute() else (base_dir / p)
    return base_dir / "var" / "asteroid_optimizer_dev_report.md"


def format_asteroid_optimizer_dev_report_md(
    *,
    map_timeline: list[dict[str, Any]],
    root_summary: dict[str, Any],
    reconstruction_summary: dict[str, Any] | None,
    mining_layout_engine: str | None,
    include_solver_overlay: bool,
    include_solver_replay: bool,
    solver_timeline: list[dict[str, Any]] | None,
    solver_replay: dict[str, Any] | None,
    solver_layout_package_unavailable: bool,
    mining_layout_runtime_flags: dict[str, Any] | None,
    preview_schema_version: int | None,
    code_fingerprint: str | None,
) -> str:
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = [
        "# Asteroid optimizer — dev step / replay report",
        "",
        f"- **generated_utc**: `{now}`",
        f"- **preview_schema_version**: `{preview_schema_version}`",
        f"- **mining_layout_engine**: `{mining_layout_engine}`",
        f"- **include_solver_overlay**: `{include_solver_overlay}`",
        f"- **include_solver_replay**: `{include_solver_replay}`",
        f"- **solver_layout_package_unavailable**: `{solver_layout_package_unavailable}`",
    ]
    if code_fingerprint:
        lines.append(f"- **code_sha256_prefix**: `{code_fingerprint}`")
    lines.append("")

    lines.append("## Root summary (last frame)")
    lines.append("")
    lines.append("```json")
    lines.append(_short_json(root_summary))
    lines.append("```")
    lines.append("")

    if reconstruction_summary is not None:
        lines.append("## Reconstruction summary")
        lines.append("")
        lines.append("```json")
        lines.append(_short_json(reconstruction_summary))
        lines.append("```")
        lines.append("")

    if mining_layout_runtime_flags:
        lines.append("## Mining layout runtime flags (response)")
        lines.append("")
        lines.append("```json")
        lines.append(_short_json(mining_layout_runtime_flags))
        lines.append("```")
        lines.append("")

    lines.append("## Map timeline (`map_timeline`)")
    lines.append("")
    lines.append("| idx | id | entry_count | phase | preview_placeholder |")
    lines.append("| --- | --- | ---: | --- | --- |")
    for i, fr in enumerate(map_timeline):
        if not isinstance(fr, dict):
            lines.append(f"| {i} | (non-dict) | | | |")
            continue
        fid = fr.get("id", "")
        summ_raw = fr.get("summary")
        summ: dict[str, Any] = summ_raw if isinstance(summ_raw, dict) else {}
        ec = summ.get("entry_count", "")
        ph = summ.get("phase", "")
        pph = summ.get("preview_placeholder", "")
        lines.append(f"| {i} | `{fid}` | {ec} | `{ph}` | `{pph}` |")
    lines.append("")

    lines.append("## Solver timeline (`solver_timeline`)")
    lines.append("")
    if not solver_timeline:
        lines.append("_(absent or empty)_")
    else:
        lines.append("| idx | id |")
        lines.append("| --- | --- |")
        for i, fr in enumerate(solver_timeline):
            if isinstance(fr, dict) and isinstance(fr.get("id"), str):
                lines.append(f"| {i} | `{fr['id']}` |")
            else:
                lines.append(f"| {i} | _(invalid row)_ |")
    lines.append("")

    lines.append("## Solver replay (`solver_replay`)")
    lines.append("")
    if not isinstance(solver_replay, dict):
        lines.append("_(absent)_")
    else:
        ev = solver_replay.get("events")
        contract = solver_replay.get("contractVersion", solver_replay.get("contract_version"))
        lines.append(f"- **contractVersion**: `{contract}`")
        if isinstance(ev, list):
            lines.append(f"- **events_len**: {len(ev)}")
            kinds = Counter(
                str(e["kind"]) for e in ev if isinstance(e, dict) and e.get("kind") is not None
            )
            if kinds:
                lines.append("")
                lines.append("### Event kinds (count)")
                lines.append("")
                lines.append("| kind | count |")
                lines.append("| --- | ---: |")
                for k, c in kinds.most_common():
                    lines.append(f"| `{k}` | {c} |")
        else:
            lines.append("- **events**: _(missing or not a list)_")
    lines.append("")

    lines.append("## Process env (NDJSON / dev; non-secret keys only)")
    lines.append("")
    rows = sorted(
        (k, v)
        for k, v in os.environ.items()
        if any(k.startswith(p) for p in _SOLVER_ENV_PREFIXES) and v != ""
    )
    if not rows:
        lines.append("_(no matching env vars set)_")
    else:
        lines.append("| variable | value |")
        lines.append("| --- | --- |")
        for k, v in rows:
            lines.append(f"| `{k}` | `{v}` |")
    lines.append("")

    return "\n".join(lines) + "\n"


def write_asteroid_optimizer_dev_report(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    except OSError as exc:
        logger.warning("asteroid dev report: write failed path=%s: %s", path, exc)


def _short_json(obj: Any, *, limit: int = 8000) -> str:
    import json

    raw = json.dumps(obj, indent=2, ensure_ascii=False, default=str)
    if len(raw) > limit:
        return raw[: limit - 20] + "\n…(truncated)…\n"
    return raw


__all__ = [
    "format_asteroid_optimizer_dev_report_md",
    "resolve_dev_report_md_path",
    "write_asteroid_optimizer_dev_report",
]
