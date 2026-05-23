"""AST/text gates for raw-island coordinate migration."""

from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_FORBIDDEN_COORD_TOKENS = tuple(
    "_".join(parts)
    for parts in (
        ("server", "x"),
        ("server", "y"),
        ("server", "xy"),
        ("server", "coord"),
        ("server", "coords"),
        ("attach", "server"),
        ("raw", "x", "to", "dense"),
        ("map", "bbox", "dense"),
    )
) + ("Serv" + "erCoord",)


def test_product_python_has_no_derived_coordinate_tokens() -> None:
    roots = (_REPO / "django_apps", _REPO / "src")
    violations: list[str] = []
    for root in roots:
        for path in sorted(root.rglob("*.py")):
            rel = path.relative_to(_REPO).as_posix()
            text = path.read_text(encoding="utf-8")
            for token in _FORBIDDEN_COORD_TOKENS:
                if token in text:
                    violations.append(f"{rel}: {token}")
    assert not violations
