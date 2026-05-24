# {{PROJECT_NAME}} Root

This file is the standing directive for {{PROJECT_NAME}}. Apply it together with more specific glob rules when present; on conflict, follow the priority order in this file and [AGENTS.md](mdc:AGENTS.md).

## Top-level operating rules

1. `[Simon]` summarizes the request and divides responsibility subsections.
2. The responsible persona briefly explains the approach in one or two sentences.
3. Only after that proceed with code writing and editing.
4. Meaningful changes leave research docs and plan MD under `documents/` before implementation.
5. Do not proceed to implementation before a human approves the plan.
6. After implementation, finish in order: `[Tess]` tests, then `[Rex]` verification.
7. The macro 10-stage pipeline (research · planning agreement · director review · approval · implementation · review · QA · harness · final · wiki) follows [protocols/README.md](mdc:protocols/README.md). Stage 3 Persona Dialogue applies **only at stage 6 (implementation)**.

## Self-verification (4 steps)

1. Scope check: identify which stage of the project workflow the request belongs to.
2. Boundary check: confirm which layer among domain/application/adapters/interfaces will change.
3. Impact check: assess effects on tests, DTO/port, theme, DB migration, and document approval gates.
4. Verification check: report whether `pytest` → `ruff check .` → `mypy django_apps config src` → `black .` can be run.

## Domain terminology

> Modify the items below to fit the project.

- {{TERM_1}}: {{TERM_1_DESC}}
- {{TERM_2}}: {{TERM_2_DESC}}
- {{TERM_3}}: {{TERM_3_DESC}}

## DO

- Assume Python 3.12, src layout, and line length 100.
- Add tests alongside new rules or bug fixes whenever possible.
- Handle API keys and secrets only via `.env` or configuration boundaries; never hardcode them in code.
- When verification was not run, report the commands that could not be executed, the reason, and remaining risk.
- If `black .` modifies files, report that formatting changes occurred along with verification results.

## DON'T

- Do not put I/O, UI, DB, or external API calls in domain.
- Do not let application import concrete adapter implementations.
- Do not put business policy in adapters.
- Do not report commands as passed when they were not verified.
- Do not proceed to implementation while the plan is unapproved.
- Do not inflate diffs with renames that differ only by a leading underscore, such as `func`↔`_func` ([`shapez2-core.mdc`](mdc:.cursor/rules/shapez2-core.mdc) Forbidden Shortcuts).

## References

- [AGENTS.md](mdc:AGENTS.md)
- [Persona index](mdc:persona/README.md)
- [Cursor memo](mdc:documents/CURSOR_MEMO.md)
