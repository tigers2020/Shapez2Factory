"""Parse simulation_systems source_type_name CLR strings into domain fields."""

from __future__ import annotations

import re
from dataclasses import dataclass

_GENERIC_RE = re.compile(
    r"^(?P<family>[A-Za-z0-9_.]+)`\d+\[\[(?P<sim>[^,\]]+)",
    re.DOTALL,
)
_STATE_RE = re.compile(r",\s*\[(?P<state>[^,\]]+)")


@dataclass(frozen=True)
class ParsedSimulationClr:
    family: str
    simulation_class: str | None
    state_class: str | None
    is_standalone: bool


def _short_type_name(qualified: str) -> str:
    name = (qualified or "").strip()
    if not name:
        return ""
    return name.rsplit(".", maxsplit=1)[-1].split(",", maxsplit=1)[0].strip()


def parse_simulation_clr(source_type_name: str) -> ParsedSimulationClr:
    raw = (source_type_name or "").strip()
    if not raw:
        return ParsedSimulationClr(
            family="unknown",
            simulation_class=None,
            state_class=None,
            is_standalone=False,
        )

    match = _GENERIC_RE.match(raw)
    if match:
        state_match = _STATE_RE.search(raw)
        return ParsedSimulationClr(
            family=_short_type_name(match.group("family")),
            simulation_class=_short_type_name(match.group("sim")),
            state_class=_short_type_name(state_match.group("state")) if state_match else None,
            is_standalone=False,
        )

    short = _short_type_name(raw)
    return ParsedSimulationClr(
        family=short,
        simulation_class=short,
        state_class=None,
        is_standalone=True,
    )
