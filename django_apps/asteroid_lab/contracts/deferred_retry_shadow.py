"""Deferred commit retry shadow contracts (PR-1 observe-only)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

PRIMARY_INCREMENTAL_COMMIT_PHASE: Literal["primary_incremental_commit"] = (
    "primary_incremental_commit"
)


@dataclass(frozen=True, slots=True)
class DeferredRetryShadowConfig:
    """Runtime shadow policy; wired from SolverRun.config_json in PR-2."""

    enabled: bool = True
    observe_only: bool = True
    max_retry_rounds: int = 1
    max_candidates: int | None = None
    route_probe_max_expansions: int = 500


@dataclass(frozen=True, slots=True)
class DeferredRetryShadowBudget:
    max_retry_rounds: int
    max_candidates: int
    route_probe_max_expansions: int


@dataclass(frozen=True, slots=True)
class DeferredRetryShadowCandidate:
    candidate_id: str
    conflict_reason: str
    original_commit_order: int
    transport_kind: str
    domain_snapshot_index: int
    retry_round: int


@dataclass(frozen=True, slots=True)
class DeferredRetryShadowSummary:
    enabled: bool
    observe_only: bool
    source_phase: Literal["primary_incremental_commit"]
    candidate_count: int
    candidates: tuple[DeferredRetryShadowCandidate, ...]
    budget: DeferredRetryShadowBudget
    domain_context: Mapping[str, Any]
    ineligible_conflict_count: int


__all__ = [
    "PRIMARY_INCREMENTAL_COMMIT_PHASE",
    "DeferredRetryShadowBudget",
    "DeferredRetryShadowCandidate",
    "DeferredRetryShadowConfig",
    "DeferredRetryShadowSummary",
]
