# {{PROJECT_NAME}} Architecture

## Layers

| Layer | Path | Owner | Principles |
|---|---|---|---|
| domain | `src/{{package_name}}/domain/` | Dominic | Pure rules, value objects, policies |
| application | `src/{{package_name}}/application/` | Yuri | use cases, DTOs, port abstractions |
| adapters | `src/{{package_name}}/adapters/` | Ada | External system implementations, response→DTO mapping |
| interfaces | `src/{{package_name}}/interfaces/` | Gina | UI screens, user state, widget composition |
| bootstrap | `src/{{package_name}}/bootstrap/` | Simon | Assembly, dependency wiring |
| tests | `tests/` | Tess | unit/integration/golden |

## Dependency direction

- `domain` must not import other layers.
- `application` depends on `domain` and `application.ports`.
- `adapters` implement `application.ports` and hide external library details.
- `interfaces` depend on use cases or application DTOs but must not know adapter implementation details directly.
- `bootstrap` wires concrete adapters with UI and use cases.

## Port rules

- Place ports under `src/{{package_name}}/application/ports/`.
- Use cases depend on port protocols or abstract interfaces, not concrete classes.
- Adapters satisfy port contracts and map external responses to application DTOs.
- Port changes are owned by Yuri; adapter implementation changes by Ada; domain rule changes by Dominic.

## Test placement

- Domain rules: prefer `tests/unit/`.
- Use case flows: prefer unit tests with port fakes.
- Adapters/DB/FS: `tests/integration/` when needed.

## References

- [Dominic card](mdc:persona/dominic.md)
- [Yuri card](mdc:persona/yuri.md)
- [Ada card](mdc:persona/ada.md)
