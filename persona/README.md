# Position Lenses (Domain Routing)

This directory holds **position cards** — domain routing hints for agents. They are **not** mandatory roleplay personas.

## How to use

1. Pick work type in [`AGENTS.md`](../AGENTS.md) domain routing table.
2. Open the matching card for **primary lens · paths · DO/DON'T · verification habits**.
3. Scope each task with **Position · Mission · Authority · Acceptance** ([`documents/ai/templates/pr-plan.md`](../documents/ai/templates/pr-plan.md)).

Abstract labels like "senior engineer" add noise. **Scope + acceptance** control behavior.

## Position cards

| Lens | Card | Primary ownership |
|---|---|---|
| Coordinator | [simon.md](simon.md) | Scope split · handoff · close report structure |
| Domain rules | [dominic.md](dominic.md) | `domain/`, pure policy |
| Application | [yuri.md](yuri.md) | `application/`, use cases, ports |
| Adapters | [ada.md](ada.md) | `adapters/`, DTO mapping (no business-rule changes) |
| Tests | [tess.md](tess.md) | `tests/`, contract/regression/golden tests |
| Harness | [rex.md](rex.md) | pytest → ruff → mypy → black chain |
| UI | [gina-gui.md](gina-gui.md) | `interfaces/`, templates, frontend |
| Django runtime | [denny.md](denny.md) | `django_apps/`, `config/` |

## Layer dependency (hexagonal `src/shapez2_factory/`)

```text
interfaces → application → domain
adapters   → application.ports
domain     → (none)
```

**Django-first runtime** (`django_apps/`, `config/`): see [denny.md](denny.md) and [`documents/ai/manuals/django.md`](../documents/ai/manuals/django.md).

## Retired pattern

Multi-character `[Name]` dialogue scripts and mandatory 3-stage briefing before every edit are **retired**. Use contract brief + PR plan instead ([`protocols/README.md`](../protocols/README.md)).
