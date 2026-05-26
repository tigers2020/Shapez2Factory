"""RTTP core recovery evidence schema (output-only; never solver algorithm input)."""

from __future__ import annotations

EVIDENCE_SCHEMA_VERSION = "rttp.core_recovery_evidence.v1"

RTTP_CORE_RECOVERY_TEST_MAP_SLUG = "rttp-core-recovery-test-map"
RTTP_CORE_RECOVERY_TEST_MAP_FIXTURE = "tests/fixtures/asteroid_lab/test_map.txt"

GATE_A_PRIMARY_SLUGS: frozenset[str] = frozenset(
    {
        RTTP_CORE_RECOVERY_TEST_MAP_SLUG,
        "rttp-cert-candidate-recon-l0",
    }
)

__all__ = [
    "EVIDENCE_SCHEMA_VERSION",
    "GATE_A_PRIMARY_SLUGS",
    "RTTP_CORE_RECOVERY_TEST_MAP_FIXTURE",
    "RTTP_CORE_RECOVERY_TEST_MAP_SLUG",
]
