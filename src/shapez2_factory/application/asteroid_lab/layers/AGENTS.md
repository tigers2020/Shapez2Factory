# src/shapez2_factory/application/asteroid_lab/layers AGENTS.md

## Scope

Layer contracts and implementations for reconstruction, exterior transport, placement, transport routing, inner fill, and commit validation.

## Rules

- Contract files are the boundary. Do not smuggle extra state through ad-hoc dicts.
- L3/L4/L5 numbering and names are unstable unless current specs say otherwise; prefer contract names over old plan names.
- Placement, routing, fill, and validation are separate responsibilities.
- Validation is read-only. It may report failures; it must not repair placement, topology, or routes.
- Commit must re-probe latest route domain and preserve deterministic diagnostics.
- No relaxed/skipped tests to force green.

## Verify

- `python -m pytest tests/unit/asteroid_lab/layers/`
- Golden loop tests when throughput, capacity, or routeability changes.
