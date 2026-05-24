# Repository Map Governance — AGENTS vs structure.md

**Status:** APPROVED  
**Date:** 2026-05-24  
**Scope:** Documentation governance + architecture test (no runtime code)

---

## 1. Problem

`AGENTS.md` **Repository map** and `structure.md` duplicated path tables. With no single SoT, drift appeared (e.g. `django_apps/game_data/` missing from `structure.md` Top-level table; `shapez_core` row conflated with game data).

## 2. Decision (Option C)

| Document | Role |
|----------|------|
| [`structure.md`](../../../structure.md) | **SoT** — paths, Django apps, URLs, tests, document trees, commands |
| [`AGENTS.md`](../../../AGENTS.md) | **Router** — triggers, gates, manual routing, thin work-type → entry hints; links to structure.md |

**Precedence:** On conflict, **structure.md wins**.

## 3. structure.md SoT scope

**In scope (canonical):**

- Documentation layers
- Top-level layout table
- Django app ownership (per-app subdirs and responsibilities)
- URL ownership
- Test layout (`tests/unit`, `integration`, fixtures, golden, support, `harness/`)
- Documents map
- Common commands

**Out of scope (remain elsewhere):**

- Agent triggers, validation gates, PR checklist → `AGENTS.md`
- Domain invariants → `docs/domain/`
- Per-topic Asteroid Lab authority → `document_inventory.md`

## 4. AGENTS.md minimal routing

Rename `## Repository map` → `## Repository routing`.

**Keep:** SoT link, work-type → persona → code/doc entry (one table), session entry (`START_HERE.md`), hex pointer to `docs/architecture/README.md`.

**Remove:** All duplicate subsection tables (Runtime, Hexagonal, Frontend, Tests, Documentation layers, Agent workflow tooling path tables).

Manual routing table stays unchanged.

## 5. Sync validation (Option B)

`tests/unit/architecture/test_repo_map_governance.py`:

1. Parse `structure.md` for registered `django_apps/<app>/` paths (Top-level table + `### django_apps/...` headers).
2. Assert set equals on-disk `django_apps/*` app directories (exclude `__pycache__`).
3. Assert each Top-level `` `path` `` in the layout table exists on disk or is a documented non-dir exception.
4. Assert `AGENTS.md` contains a link to `structure.md`.
5. Assert `AGENTS.md` has **no** duplicate repo-map tables: at most **zero** markdown table rows whose first cell is a backtick path under `django_apps/`, `tests/`, `frontend/`, `docs/`, `documents/` (work-type routing table uses prose paths, not full map tables).

Update [`.cursor/skills/doc-update/SKILL.md`](../../../.cursor/skills/doc-update/SKILL.md): structural changes → edit `structure.md` first; then verify `AGENTS.md` routing only.

## 6. Acceptance criteria

- [x] `structure.md` Top-level lists all five Django apps including `game_data`; `shapez_core` description does not claim game data ownership.
- [x] `structure.md` map-related sections in English; Documentation layers states AGENTS = router, structure = map SoT.
- [x] `AGENTS.md` has no duplicate path tables; `## Repository routing` with SoT link.
- [x] `test_repo_map_governance.py` passes.
- [x] `doc-update` skill references structure-first workflow.

## 7. Non-goals

- No change to `document_inventory` / contamination policy
- No YAML manifest SoT
- No `src/shapez2_factory` filesystem gate (stub)
- No bulk Korean→English for all of `documents/`
- No directory moves or app renames

## 8. Implementation plan

[`../plans/2026-05-24-repo-map-governance.md`](../plans/2026-05-24-repo-map-governance.md)
