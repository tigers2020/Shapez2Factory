"""Repository map governance: structure.md SoT vs AGENTS.md router (see spec 2026-05-24)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_STRUCTURE_MD = _REPO_ROOT / "structure.md"
_AGENTS_MD = _REPO_ROOT / "AGENTS.md"
_DJANGO_APPS = _REPO_ROOT / "django_apps"

_BACKTICK_PATH = re.compile(r"`([^`]+)`")
_TABLE_ROW_DJANGO = re.compile(r"^\|\s*`django_apps/")
_TABLE_ROW_REPO_PATH = re.compile(
    r"^\|\s*`(?:django_apps|tests|frontend|docs|documents|harness|assets|locale|scripts|var)/"
)
_SECTION = re.compile(r"^## (.+)$")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    """Return body text under ## heading until the next ##."""
    lines = text.splitlines()
    out: list[str] = []
    in_section = False
    for line in lines:
        m = _SECTION.match(line)
        if m:
            if in_section:
                break
            in_section = m.group(1).strip() == heading
            continue
        if in_section:
            out.append(line)
    return "\n".join(out)


def _django_apps_on_disk() -> set[str]:
    return {
        p.name
        for p in _DJANGO_APPS.iterdir()
        if p.is_dir() and not p.name.startswith("_") and p.name != "__pycache__"
    }


def _django_apps_in_structure(text: str) -> set[str]:
    apps: set[str] = set()
    for match in _BACKTICK_PATH.finditer(text):
        path = match.group(1)
        if path.startswith("django_apps/"):
            rest = path.removeprefix("django_apps/").strip("/")
            app = rest.split("/")[0]
            if app:
                apps.add(app)
    return apps


def _top_level_paths(structure_text: str) -> list[str]:
    block = _section(structure_text, "Top-level layout")
    paths: list[str] = []
    for line in block.splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells:
            continue
        first = cells[0]
        for match in _BACKTICK_PATH.finditer(first):
            paths.append(match.group(1).rstrip("/"))
    return paths


@pytest.mark.unit
def test_structure_md_lists_every_django_app_on_disk() -> None:
    structure = _read(_STRUCTURE_MD)
    on_disk = _django_apps_on_disk()
    in_doc = _django_apps_in_structure(structure)
    assert on_disk <= in_doc, (
        f"django_apps on disk missing from structure.md: {sorted(on_disk - in_doc)}"
    )
    assert in_doc <= on_disk, (
        f"structure.md references unknown django_apps: {sorted(in_doc - on_disk)}"
    )


@pytest.mark.unit
def test_structure_md_top_level_paths_exist() -> None:
    structure = _read(_STRUCTURE_MD)
    missing: list[str] = []
    for path in _top_level_paths(structure):
        target = _REPO_ROOT / path
        if not target.exists():
            missing.append(path)
    assert not missing, f"Top-level layout paths missing on disk: {missing}"


@pytest.mark.unit
def test_agents_md_links_structure_sot() -> None:
    agents = _read(_AGENTS_MD)
    assert "structure.md" in agents
    assert "Repository routing" in agents


@pytest.mark.unit
def test_agents_md_has_no_duplicate_repo_map_tables() -> None:
    """AGENTS must not duplicate structure.md path tables (router only)."""
    agents = _read(_AGENTS_MD)
    duplicate_rows = [
        line
        for line in agents.splitlines()
        if _TABLE_ROW_REPO_PATH.match(line) and "Work type" not in line
    ]
    assert not duplicate_rows, (
        "AGENTS.md must not contain repo-map table rows; use structure.md SoT. "
        f"Found {len(duplicate_rows)} row(s), e.g. {duplicate_rows[:3]}"
    )


@pytest.mark.unit
def test_agents_md_no_repository_map_subsections() -> None:
    agents = _read(_AGENTS_MD)
    forbidden = (
        "### Runtime",
        "### Hexagonal extraction",
        "### Frontend & assets",
        "### Tests (",
        "### Documentation layers",
        "### Agent workflow & tooling",
    )
    found = [h for h in forbidden if h in agents]
    assert not found, f"Remove duplicate map subsections from AGENTS.md: {found}"
