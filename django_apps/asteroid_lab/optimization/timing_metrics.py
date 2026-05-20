"""Solver runtime wall-clock metrics (output-only observability)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _percentile_ms(samples_ms: list[float], pct: float) -> float:
    if not samples_ms:
        return 0.0
    ordered = sorted(samples_ms)
    idx = min(len(ordered) - 1, max(0, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return ordered[idx]


@dataclass
class CandidateGenerationTiming:
    """Timing collected during ``generate_gene_candidates``."""

    candidate_generation_ms: float = 0.0
    route_probe_total_ms: float = 0.0
    route_probe_count: int = 0
    route_probe_avg_ms: float = 0.0
    route_probe_p95_ms: float = 0.0
    route_probe_expanded_nodes_total: int = 0
    route_domain_build_total_ms: float = 0.0
    route_domain_build_count: int = 0
    _probe_samples_ms: list[float] = field(default_factory=list, repr=False)

    def record_probe(self, *, elapsed_ms: float, expanded_nodes: int) -> None:
        self.route_probe_count += 1
        self.route_probe_total_ms += elapsed_ms
        self._probe_samples_ms.append(elapsed_ms)
        self.route_probe_expanded_nodes_total += expanded_nodes

    def record_domain_build(self, *, elapsed_ms: float) -> None:
        self.route_domain_build_count += 1
        self.route_domain_build_total_ms += elapsed_ms

    def finalize(self, *, total_ms: float) -> None:
        self.candidate_generation_ms = total_ms
        if self.route_probe_count:
            self.route_probe_avg_ms = self.route_probe_total_ms / self.route_probe_count
        self.route_probe_p95_ms = _percentile_ms(self._probe_samples_ms, 95.0)


@dataclass
class CommitTiming:
    commit_reprobe_ms: float = 0.0
    route_probe_count: int = 0
    route_probe_expanded_nodes_total: int = 0


@dataclass
class SolverRuntimeTimingMetrics:
    """Aggregated pipeline timing for ``solver_summary['timing']``."""

    total_ms: float = 0.0
    candidate_generation_ms: float = 0.0
    route_probe_total_ms: float = 0.0
    route_probe_count: int = 0
    route_probe_avg_ms: float = 0.0
    route_probe_p95_ms: float = 0.0
    route_probe_expanded_nodes_total: int = 0
    route_domain_build_total_ms: float = 0.0
    route_domain_build_count: int = 0
    evolution_ms: float = 0.0
    commit_reprobe_ms: float = 0.0
    validation_ms: float = 0.0
    replay_build_ms: float = 0.0
    json_serialize_ms: float = 0.0

    def absorb_candidate_generation(self, timing: CandidateGenerationTiming) -> None:
        self.candidate_generation_ms = timing.candidate_generation_ms
        self.route_probe_total_ms += timing.route_probe_total_ms
        self.route_probe_count += timing.route_probe_count
        self.route_probe_expanded_nodes_total += timing.route_probe_expanded_nodes_total
        self.route_domain_build_total_ms += timing.route_domain_build_total_ms
        self.route_domain_build_count += timing.route_domain_build_count
        if timing.route_probe_count:
            gen_avg = timing.route_probe_avg_ms
            if self.route_probe_count == timing.route_probe_count:
                self.route_probe_avg_ms = gen_avg
                self.route_probe_p95_ms = timing.route_probe_p95_ms
            else:
                self._recompute_probe_avg_p95()

    def absorb_commit(self, timing: CommitTiming) -> None:
        self.commit_reprobe_ms = timing.commit_reprobe_ms
        self.route_probe_total_ms += timing.commit_reprobe_ms
        self.route_probe_count += timing.route_probe_count
        self.route_probe_expanded_nodes_total += timing.route_probe_expanded_nodes_total
        self._recompute_probe_avg_p95()

    def _recompute_probe_avg_p95(self) -> None:
        if self.route_probe_count and self.route_probe_total_ms:
            self.route_probe_avg_ms = self.route_probe_total_ms / self.route_probe_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_ms": round(self.total_ms, 3),
            "candidate_generation_ms": round(self.candidate_generation_ms, 3),
            "route_probe_total_ms": round(self.route_probe_total_ms, 3),
            "route_probe_count": self.route_probe_count,
            "route_probe_avg_ms": round(self.route_probe_avg_ms, 3),
            "route_probe_p95_ms": round(self.route_probe_p95_ms, 3),
            "route_probe_expanded_nodes_total": self.route_probe_expanded_nodes_total,
            "route_domain_build_total_ms": round(self.route_domain_build_total_ms, 3),
            "route_domain_build_count": self.route_domain_build_count,
            "evolution_ms": round(self.evolution_ms, 3),
            "commit_reprobe_ms": round(self.commit_reprobe_ms, 3),
            "validation_ms": round(self.validation_ms, 3),
            "replay_build_ms": round(self.replay_build_ms, 3),
            "json_serialize_ms": round(self.json_serialize_ms, 3),
        }
