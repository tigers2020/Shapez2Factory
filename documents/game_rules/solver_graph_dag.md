# Solver Graph: Shape Is a DAG, Not a Tree

## Why

The same **intermediate shape** can feed multiple operation inputs.

```text
RcRcRcRc
   ├─ rotate
   ├─ cut
   └─ swap
```

## Recommended Graph Form

```text
Source -> Operation -> Intermediate -> Operation -> Target
```

Intermediate nodes carry an **identifiable shape code** (or normalized hash).

## Alignment with Project Rules

- Project rule: operation outputs do not **directly splice** into other operation inputs; they go through **intermediate shape nodes** ([architecture.mdc](../../.cursor/rules/architecture.mdc)).
- Do not confuse **visualization graph** with **physical/domain graph** terminology when applying this DAG concept.
