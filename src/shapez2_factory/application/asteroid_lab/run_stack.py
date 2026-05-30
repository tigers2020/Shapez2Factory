"""``RunStackUseCase`` — stub (real decode→stack→artifact impl lands in PR-CLI-3b)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shapez2_factory.application.asteroid_lab.ports.copy_decode import CopyDecodePort
from shapez2_factory.application.asteroid_lab.ports.game_data_rules import GameDataRulesPort

STACK_NOT_IMPLEMENTED = "STACK_NOT_IMPLEMENTED"


@dataclass(frozen=True, slots=True)
class StackRunResult:
    ok: bool = False
    error_code: str | None = None
    replay_core_lines: tuple[dict[str, Any], ...] = ()
    solver_summary: dict[str, Any] = field(default_factory=dict)


class RunStackUseCase:
    """Wires the ports; ``run`` returns an empty result until PR-CLI-3b implements the stack."""

    def __init__(
        self,
        *,
        game_data_rules: GameDataRulesPort,
        copy_decode: CopyDecodePort,
    ) -> None:
        self._game_data_rules = game_data_rules
        self._copy_decode = copy_decode

    def run(self, *, copy_text: str) -> StackRunResult:
        del copy_text  # not consumed until the real stack lands (PR-CLI-3b)
        return StackRunResult(ok=False, error_code=STACK_NOT_IMPLEMENTED)


__all__ = ["STACK_NOT_IMPLEMENTED", "RunStackUseCase", "StackRunResult"]
