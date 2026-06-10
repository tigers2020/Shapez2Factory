# src/shapez2_factory/application/asteroid_lab AGENTS.md

## Scope

Django-free Asteroid Lab application core: stack runner, layer orchestration, ports, contracts, and experiments.

## Authority

- Current code, current tests, current canon/spec/ADR.
- Deleted Layer 3 greedy plans and archived solver docs are historical only.

## Rules

- Preserve layer order and explicit contracts between reconstruction, exterior transport, placement, routing, fill, and commit validation.
- Stack runner may orchestrate; layer modules own layer-local behavior.
- Ports define boundaries; do not import Django or persistence adapters here.
- Keep seeded/stable randomness only. No unseeded `random` or `uuid4`.
- Do not use replay, metrics, logs, or artifacts as algorithm input.
- Diagnostic output must explain failed source, route, capacity, or invariant cause without repairing state.

## Verify

- `python -m pytest tests/unit/asteroid_lab/layers/ tests/unit/shapez2_factory/`
- Add golden or invariant tests when layer contracts change.
