"""Default Asteroid Lab core assembly (no Django).

Concrete adapters are injected by the caller (CLI in PR-CLI-3a/3b). This module only assembles pure
core objects and never imports Django.
"""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.ports.copy_decode import CopyDecodePort
from shapez2_factory.application.asteroid_lab.ports.game_data_rules import GameDataRulesPort
from shapez2_factory.application.asteroid_lab.run_stack import RunStackUseCase


def build_run_stack_use_case(
    *,
    game_data_rules: GameDataRulesPort,
    copy_decode: CopyDecodePort,
) -> RunStackUseCase:
    return RunStackUseCase(game_data_rules=game_data_rules, copy_decode=copy_decode)


__all__ = ["build_run_stack_use_case"]
