"""Narrow untrusted wire JSON scalars (strict-mypy safe, no loose typing)."""

from __future__ import annotations


def wire_int(val: object, *, default: int = 0) -> int:
    if val is None:
        return default
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return int(val)
    if isinstance(val, str):
        try:
            return int(val, 10)
        except ValueError:
            return default
    return default


def wire_str(val: object, *, default: str = "") -> str:
    if val is None:
        return default
    if isinstance(val, str):
        return val
    return str(val)


def wire_optional_str(val: object) -> str | None:
    if val is None:
        return None
    return wire_str(val)


def wire_float(val: object, *, default: float = 0.0) -> float:
    if val is None:
        return default
    if isinstance(val, bool):
        return float(val)
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except ValueError:
            return default
    return default


def wire_optional_float(val: object) -> float | None:
    if val is None:
        return None
    if isinstance(val, bool):
        return float(val)
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except ValueError:
            return None
    return None


def wire_dict(val: object, *, field: str = "") -> dict[str, object]:
    if isinstance(val, dict):
        return val
    label = f"{field} " if field else ""
    msg = f"{label}must be a dict"
    raise TypeError(msg)


def wire_list(val: object, *, field: str = "") -> list[object]:
    if isinstance(val, list):
        return val
    if isinstance(val, tuple):
        return list(val)
    label = f"{field} " if field else ""
    msg = f"{label}must be a list"
    raise TypeError(msg)


__all__ = [
    "wire_dict",
    "wire_float",
    "wire_int",
    "wire_list",
    "wire_optional_float",
    "wire_optional_str",
    "wire_str",
]
