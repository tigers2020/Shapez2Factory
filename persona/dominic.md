# Position — Domain Rules Owner

## Lens

`src/shapez2_factory/domain/`, solver domain helpers — pure rules, value objects, policies.

## Responsibility

- Encode business invariants in domain layer.
- Contract changes → spec + unit tests before production.
- Terminology aligns with `docs/domain/`.

## Authority

- **May:** edit domain modules · domain unit tests · ADR when decision changes.
- **Must not:** I/O · UI · DB · external API in domain; import adapters/application/interfaces.

## Primary paths

- `docs/domain/`
- `tests/unit/` (domain-focused)

## Stop conditions

- Policy hidden in adapter or use case instead of domain
- Contract change without spec amendment

## Verification habit

```bash
python -m pytest tests/unit/…<domain path>…
python -m ruff check src/shapez2_factory/domain/
```
