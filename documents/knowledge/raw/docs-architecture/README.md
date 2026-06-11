# Architecture

This document is the human-friendly version of `.cursor/rules/architecture.mdc`. It normatively describes layer responsibilities and dependency direction.

## Layer structure

```
src/{{package_name}}/
├── domain/          # Pure business rules, value objects, policies (no I/O)
├── application/
│   ├── ports/       # Port abstractions (Protocol / ABC)
│   └── use_cases/   # Use case orchestration
├── adapters/        # Port implementations, external system integration, DTO mapping
├── interfaces/      # UI screens, user state, widget composition
└── bootstrap/       # Dependency assembly (DI wiring)
```

## Dependency direction

```
interfaces ──► application (use_cases, ports)
adapters   ──► application (ports)
application──► domain
bootstrap  ──► adapters, interfaces, application
domain     ──► (none — no external dependencies)
```

## Responsibilities by layer

### domain

- Entities, value objects, domain events, policies
- Absolutely no I/O, UI, DB, or external API calls
- Owner: Dominic

### application

- Use case = receive input → call domain → return output
- Abstract external dependencies via ports (Protocol/ABC)
- Do not import concrete adapter implementations directly
- Owner: Yuri

### adapters

- Implement port contracts
- Map external responses to application DTOs
- Must not contain business policy
- Owner: Ada

### interfaces

- UI screens, user state management
- Depend only on use cases or application DTOs
- Do not know concrete adapter implementations directly
- Owner: Gina

### bootstrap

- Wire concrete adapters with UI/use cases
- Framework initialization, configuration loading
- Owner: Simon

## Port design guidelines

1. Define in `application/ports/` as Protocol or ABC.
2. Use cases depend only on port types (not concrete classes).
3. Adapters provide concrete implementations that satisfy port contracts.
4. In tests, replace ports with fake (stub/mock) implementations.

## References

- [Domain Manual](../domain/README.md)
- [ADR](../adr/README.md)
- [architecture.mdc](../../.cursor/rules/architecture.mdc)
