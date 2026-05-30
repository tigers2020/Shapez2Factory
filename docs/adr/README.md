# Architecture Decision Records (ADR)

This directory records current architectural decisions for the project.

## Purpose

- Explain why a decision was made.
- Track decisions that are irreversible or costly to reverse.
- Keep current accepted decisions easy to find.

## When To Write An ADR

Write an ADR when a decision changes layer boundaries, dependency direction,
storage format, serialization format, testing strategy, or performance and
stability trade-offs.

## File Naming

```text
ADR-NNNN-<short-title>.md
```

Example: `ADR-0001-port-protocol-over-abc.md`

## Status Values

- `proposed`: under review
- `accepted`: adopted and current

Outdated ADRs are deleted instead of retained locally.

## References

- [ADR template](ADR-0000-template.md)
- [Architecture](../architecture/README.md)
