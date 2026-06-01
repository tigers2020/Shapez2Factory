# Position — Application / Use Case Owner

## Lens

`src/shapez2_factory/application/` — use cases, DTOs, ports (Protocol/ABC).

## Responsibility

- Orchestrate flows through **ports only** (no concrete adapters).
- Contract review lens: scope vs spec · layer boundaries.
- Port changes → coordinate adapter + test updates in PR plan.

## Authority

- **May:** edit application layer · port fakes in unit tests.
- **Must not:** import concrete adapters; put UI/HTTP in use cases; redefine domain invariants here.

## Primary paths

- `src/shapez2_factory/application/`
- `tests/unit/` (use case + port fake)

## Stop conditions

- Business policy in adapter instead of domain/application split
- Contract change without spec

## Verification habit

```bash
python -m pytest tests/unit/…<application path>…
```
