# PR-CLI-0 — Artifact Spec + ADR + AST Gate Skeleton

**Type:** documentation change · contract change
**Depends on:** none
**Enables:** all subsequent PRs
**Branch (suggested):** `feat/asteroid-cli-first-spec`

---

## Goal

Author the normative artifact contract, ADR, and failing/skeleton architecture gates so every later PR
has a single source of truth. No solver code moves in this PR.

## Behavior contract

- Define artifact directory layout, `manifest.json` schema, `replay_core.jsonl` line schema, run lifecycle enum.
- Define BA-1…BA-8 as normative rules.
- Define subprocess invocation + typed exit-code mapping table.
- Define `game_data_snapshot.json` schema + fail-closed rules.

## Non-goals

- No `src/shapez2_factory/` package code.
- No moving reconstruction/layers.
- No Django runtime changes.

---

## File map

| Action | Path | Why |
|--------|------|-----|
| Create | `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md` | Normative contract |
| Create | `docs/adr/ADR-006-asteroid-lab-cli-first-artifact.md` | Decision record (confirm next free ADR number at authoring) |
| Modify | [`structure.md`](../../../../structure.md) | Add `var/runs/`, CLI entry, `src/shapez2_factory` solver-core role |
| Modify | [`documents/ai/current_plan.md`](../../../../documents/ai/current_plan.md) | New ACTIVE queue row |
| Modify | [`documents/index/document_inventory.md`](../../../../documents/index/document_inventory.md) | Register spec + plan set |
| Create | `tests/unit/architecture/test_shapez2_factory_core_purity.py` | BA-1 gate skeleton (xfail/empty-dir tolerant) |

---

## Spec required sections (normative)

1. **Artifact directory** — `var/runs/<run_key>/` final; `var/runs/.tmp/<run_key>/` staging.
2. **manifest.json schema** — fields:
   `schema_version`, `run_key`, `lifecycle_status`, `created_at_utc`, `core_build_id`,
   `content_hashes` (map relpath → sha256), `paths`, `game_data_provenance`, `error_code`.
   - **`content_hashes` excludes `manifest.json` itself** (manifest is the last write; it cannot hash
     itself). It covers **all artifact payload files written before manifest finalization**.
   - If a manifest integrity digest is needed, `manifest_sha256` is computed **externally** by the
     validator / DB ingest and is **not** stored inside `content_hashes`.
3. **replay_core.jsonl** — one JSON object per line; deterministic ordering; `frame_index` monotonic;
   output-only; no web/template fields. **Reuse event-type semantics by copying/relocating the pure enum
   definitions into core** when needed. **Core MUST NOT import
   `django_apps.asteroid_lab.replay.event_types`** (or any `django_apps` module). The current
   [`replay/event_types.py`](../../../../django_apps/asteroid_lab/replay/event_types.py) is a reference for
   values only.
4. **Run lifecycle enum:** `QUEUED | RUNNING | ARTIFACT_WRITING | ARTIFACT_WRITTEN | INDEXED | SUCCEEDED | FAILED`.
   - **Authority split (normative):** `manifest.lifecycle_status` is the **artifact** lifecycle and stays at
     `ARTIFACT_WRITTEN` after atomic finalize — it is **immutable** thereafter. `INDEXED` / `SUCCEEDED` /
     `FAILED` are **DB/`SolverRun`** lifecycle states only. **Django ingest must never rewrite
     `manifest.json`.** `validate-artifact` therefore only ever expects `ARTIFACT_WRITTEN` in the manifest.
5. **Atomic write protocol (BA-5)** — temp → hash → manifest last → rename → ingest.
6. **Subprocess contract (BA-7)** — `shell=False`, list args, `sys.executable`, fixed cwd, timeout,
   stdout/stderr → `logs/subprocess.log`, path-traversal guard, exit-code → `SolverRuntimeEntryErrorCode` table
   (align with [`solver_runtime_types.py`](../../../../django_apps/asteroid_lab/services/solver_runtime_types.py)).
7. **game_data_snapshot.json (BA-8)** — schema + fail-closed (missing / unsupported version / hash mismatch).
8. **BA-1 core purity** — forbidden import prefixes list.
9. **BA-4 replay boundary** — core vs viewer responsibility table.
10. **BA-6 manifest reader** — Option 1 location and no-core-import rule.

## Exit-code mapping table (spec)

| Exit | Meaning | error_code |
|------|---------|------------|
| 0 | success | none |
| 2 | validation failed | `VALIDATION_FAILED` |
| 3 | timeout fail-closed | `SOLVER_TIME_BUDGET_EXCEEDED` |
| 4 | snapshot missing/invalid | `GAME_DATA_SNAPSHOT_INVALID` (new enum value) |
| 5 | decode failed | `DECODE_FAILED` |
| 1 | unexpected | `SOLVER_INTERNAL_ERROR` |

> New enum values are added in the PR that implements them (CLI-3 / CLI-4), not here; spec only declares them.

---

## Tasks

- [ ] **Step 1:** Write spec with all 10 sections; cite invariants from [`.cursor/rules/asteroid-lab-invariants.mdc`](../../../../.cursor/rules/asteroid-lab-invariants.mdc).
- [ ] **Step 2:** Write ADR-006 (context, decision, consequences, alternatives = Option 2 neutral package rejected for now).
- [ ] **Step 3:** Update `structure.md` (var/runs, CLI entry path) + `current_plan.md` ACTIVE row + `document_inventory.md`.
- [ ] **Step 4:** Add `test_shapez2_factory_core_purity.py` — AST scan; tolerate empty `src/shapez2_factory` package (no asteroid modules yet) so test is green but active.

## Architecture gate skeleton

```python
# tests/unit/architecture/test_shapez2_factory_core_purity.py
import ast
from pathlib import Path

FORBIDDEN_PREFIXES = ("django", "django_apps", "config")

def test_shapez2_factory_has_no_forbidden_imports() -> None:
    root = Path("src/shapez2_factory")
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            mods: list[str] = []
            if isinstance(node, ast.ImportFrom) and node.module:
                mods.append(node.module)
            if isinstance(node, ast.Import):
                mods.extend(a.name for a in node.names)
            for mod in mods:
                top = mod.split(".")[0]
                assert top not in FORBIDDEN_PREFIXES, f"{path} imports {mod}"
                assert "django_apps" not in mod, f"{path} imports {mod}"
```

---

## Tests / verification

```powershell
python -m pytest tests/unit/architecture/test_shapez2_factory_core_purity.py -v
python -m ruff check tests/unit/architecture/test_shapez2_factory_core_purity.py
```

Docs change only otherwise (pytest not required for prose).

## Risks

- `uncertain:` ADR number collision — verify highest existing ADR before writing.
- Spec drift if later PRs deviate — each PR restates the BA it touches.

## Done criteria

- Spec + ADR merged-ready; structure/inventory/current_plan updated; purity gate present and green.
