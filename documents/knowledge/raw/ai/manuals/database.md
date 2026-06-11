# Manual: Database · Migrations

## Prerequisites

Schema changes · data migrations may fall under **do not proceed without explicit approval** in [`AGENTS.md`](../../../AGENTS.md). Check the project plan · approval gates first.

## Django models

Per-app `models.py` and migrations follow each Django app directory convention. Do not introduce layer-violating imports ([`architecture.mdc`](../../../.cursor/rules/architecture.mdc)).

## After changes

- If migration file generation is included, assume it is **subject to review**.
- Record integration/staging seed · data issues in [`documents/ai/context_notes.md`](../../context_notes.md).

## Related

- Django app structure: [`django.md`](django.md)
- Layered schema · ETL · data validation: [`django.md`](django.md) and [`.cursor/skills/shapez2-workflow/SKILL.md`](../../../.cursor/skills/shapez2-workflow/SKILL.md) (`@shapez2-workflow`)
