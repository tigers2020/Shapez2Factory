# Architecture Decision Records (ADR)

This directory records important architectural decisions for the project.

## Purpose

- Explain to future team members why a decision was made.
- Track decisions that are irreversible or costly to reverse.
- Leave a record of alternatives considered.

## When to write an ADR

Write an ADR when one or more of the following apply:

- A decision changes layer boundaries or dependency direction
- Introducing or replacing an external library/framework
- Changing data storage or serialization format
- Structural changes to testing strategy or validation approach
- Decisions with performance/stability trade-offs

## File naming

```
ADR-NNNN-<short-title>.md
```

Example: `ADR-0001-port-protocol-over-abc.md`

## Status list

| Number | Title | Status |
|---|---|---|
| 0000 | Template | — |

## Status values

- `proposed` — Under review
- `accepted` — Adopted
- `deprecated` — No longer valid
- `superseded` — Replaced by another ADR

## References

- [ADR template](ADR-0000-template.md)
- [Architecture](../architecture/README.md)
