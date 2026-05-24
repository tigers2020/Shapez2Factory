# Repository Map Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `structure.md` the sole repository-map SoT, slim `AGENTS.md` to routing only, and enforce drift prevention with an architecture test.

**Architecture:** Parse `structure.md` for registered paths; compare to filesystem; lint `AGENTS.md` for forbidden duplicate map tables. No YAML manifest.

**Tech Stack:** Python 3, pytest, markdown in repo root

**Spec:** [`../specs/2026-05-24-repo-map-governance-design.md`](../specs/2026-05-24-repo-map-governance-design.md)

---

### Task 1: Failing governance test

**Files:**
- Create: `tests/unit/architecture/test_repo_map_governance.py`

- [ ] **Step 1:** Add tests for django_apps parity, structure link in AGENTS, AGENTS duplicate-table ban.
- [ ] **Step 2:** Run `python -m pytest tests/unit/architecture/test_repo_map_governance.py` — expect fail on current AGENTS/structure drift.

### Task 2: Repair structure.md (SoT)

**Files:**
- Modify: `structure.md`

- [ ] Add `django_apps/game_data/` to Top-level layout; fix `shapez_core` row.
- [ ] Add `docs/superpowers/`, `tests/fixtures|golden|support`, `harness/validators/` where missing.
- [ ] English for map-related sections; Documentation layers: AGENTS = router, structure = map SoT.

### Task 3: Slim AGENTS.md

**Files:**
- Modify: `AGENTS.md`

- [ ] Replace `## Repository map` subsections with `## Repository routing` (SoT link + work-type table only).

### Task 4: doc-update skill

**Files:**
- Modify: `.cursor/skills/doc-update/SKILL.md`

- [ ] structure.md first on layout changes; AGENTS routing check only.

### Task 5: Verify

- [ ] `python -m pytest tests/unit/architecture/test_repo_map_governance.py`
- [ ] `ruff check tests/unit/architecture/test_repo_map_governance.py`
