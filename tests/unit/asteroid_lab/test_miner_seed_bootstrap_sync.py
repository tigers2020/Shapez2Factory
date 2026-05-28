"""Audit markdown copy strings must match var/default_miner_pattern.txt (19-line SoT)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_AUDIT_MD = Path("var/miner_seed_belt_ignored_canonical_parent_r_patterns.md")
_BOOTSTRAP_TXT = Path("var/default_miner_pattern.txt")


def _copy_strings_from_audit_md(text: str) -> list[str]:
    sections = re.split(r"^## (m\d+e_\d+)\b", text, flags=re.MULTILINE)
    if len(sections) < 2:
        msg = "no miner seed sections found in audit markdown"
        raise ValueError(msg)
    ordered: list[str] = []
    for i in range(1, len(sections), 2):
        body = sections[i + 1]
        match = re.search(
            r"Copy string:\s*\n```[^\n]*\n(SHAPEZ2-[^\n`]+)",
            body,
            flags=re.IGNORECASE,
        )
        if not match:
            msg = f"Copy string block missing for section {sections[i]!r}"
            raise ValueError(msg)
        ordered.append(match.group(1).strip())
    return ordered


def test_bootstrap_md_txt_sync() -> None:
    md_text = _AUDIT_MD.read_text(encoding="utf-8")
    from_md = _copy_strings_from_audit_md(md_text)
    from_txt = [
        ln.strip() for ln in _BOOTSTRAP_TXT.read_text(encoding="utf-8").splitlines() if ln.strip()
    ]
    assert len(from_md) == 19
    assert len(from_txt) == 19
    normalized_md = [s if s.endswith("$") else f"{s}$" for s in from_md]
    normalized_txt = [s if s.endswith("$") else f"{s}$" for s in from_txt]
    assert normalized_md == normalized_txt
    assert all(line.endswith("$") for line in from_txt)
