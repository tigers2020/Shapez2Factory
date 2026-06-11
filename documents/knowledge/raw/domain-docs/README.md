# Domain Manual

**Owner**: Dominic (`persona/dominic.md`)

This directory holds the project's core domain knowledge. It is the "single source of truth" for both AI and humans.

## Role

- Formalizes domain terminology, invariants, and policies.
- Code in `src/{{package_name}}/domain/` follows this documentation.
- When code and docs conflict, update this documentation first, then align the code.

## Domain terminology (placeholder — fill in at project start)

| Term | Description | Reference |
|---|---|---|
| {{TERM_1}} | {{TERM_1_DESC}} | — |
| {{TERM_2}} | {{TERM_2_DESC}} | — |
| {{TERM_3}} | {{TERM_3_DESC}} | — |

## Invariants (placeholder)

> Record conditions the system must always satisfy here.

- INV-1: (description)
- INV-2: (description)

## Table of contents

| Document | Concept |
|------|------|
| [`asteroid_game_data_snapshot.md`](asteroid_game_data_snapshot.md) | Asteroid Lab `game_data` consumer snapshot — ordering, `SnapshotMeta`, `content_hash`, fail-fast |
| [`asteroid_coord_transform_spec.md`](asteroid_coord_transform_spec.md) | Canonical E → server rotation — `rotate_offset`, anchor placement, footprint adapter rule |
| [`game_data_coverage.md`](game_data_coverage.md) | Domain-complete import — A vs B, manifest dispositions, provenance, Phase 2 audit pending |

## File organization rules

- One file covers one concept (entity / value object / policy) only.
- File names use the format `<concept_name>.md`.
- When adding a new file, update the table of contents in this README.

## References

- [Architecture](../architecture/README.md)
- [ADR](../adr/README.md)
