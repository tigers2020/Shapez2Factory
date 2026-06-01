# Position — Adapter Owner

## Lens

`src/shapez2_factory/adapters/` — port implementations, external I/O isolation, DTO mapping.

## Responsibility

- Implement `application/ports/` contracts.
- Map external responses to application DTOs — **no business policy**.

## Authority

- **May:** edit adapters · integration tests · adapter unit tests with fakes.
- **Must not:** encode business rules; mutate domain objects directly; import use cases (ports only).

## Primary paths

- `src/shapez2_factory/adapters/`
- `tests/integration/`

## Stop conditions

- Business branching added to adapter
- Port contract change without spec + tests

## Verification habit

```bash
python -m pytest tests/integration/…
python -m pytest tests/unit/…<adapter path>…
```
