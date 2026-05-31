# PR-CLI-6 — `subprocess_only` Default + Viewer Import Gate

**Type:** contract change
**Depends on:** PR-CLI-5 (and ideally PR-CLI-2e for full purity)
**Enables:** target end state
**Branch (suggested):** `feat/asteroid-cli-first-viewer-only`

---

## Goal

Set `ASTEROID_LAB_SOLVER_MODE=subprocess_only`, **fully remove in-process core import from the Django
request path**, and add the AST gate forbidding `shapez2_factory` import in viewer services. Django is now
an artifact viewer; DB is index/cache only.

> **Structural amendment (2026-05-30) — Option A chosen:** The previous draft kept a "legacy `in_process`
> still selectable" escape hatch, which contradicted the viewer import gate (in-process requires Django to
> import core). Option A removes in-process from the request path entirely. No `legacy_in_process_runner`
> allowlist. The only viewer-side reference to core is the subprocess runner, which names the CLI as a
> **module string** (`"shapez2_factory.interfaces.cli.asteroid_solve"`), never an `import`.

## Behavior contract

- `run-solver` only spawns the CLI subprocess; there is no in-process solve path in the request flow.
- `django_apps/asteroid_lab/{services,replay,views}/**` must not import `shapez2_factory` (sole exception:
  `solver_subprocess_runner.py`, which references the CLI by module string, not import).
- Local/dev pure solving is done by invoking the CLI directly (`python -m shapez2_factory...`), not via Django.

## Non-goals

- No deletion of ORM models.
- No in-process Django solve path retained (removed — Option A).

---

## File map

| Action | Path | Why |
|--------|------|-----|
| Modify | [`config/settings.py`](../../../../config/settings.py) | `ASTEROID_LAB_SOLVER_MODE="subprocess_only"` (only mode in request path) |
| Modify | [`services/solver_runtime_entry.py`](../../../../django_apps/asteroid_lab/services/solver_runtime_entry.py) | remove in-process core import entirely; subprocess dispatch only |
| Delete/retire | `django_apps/asteroid_lab/services/solver_runtime_layer02.py` | completed: deleted; request path no longer imports core |
| Create | `tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py` | viewer must not import core |
| Modify | [`documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md`](../../../../documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md) | final CLI-first wiring |
| Modify | [`documents/ai/current_plan.md`](../../../../documents/ai/current_plan.md) | mark initiative reaching target state |
| Modify | [`structure.md`](../../../../structure.md) | Django role = viewer; `python -m shapez2_factory...` canonical |

---

## Viewer import gate

```python
# tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py
import ast
from pathlib import Path

VIEWER_ROOTS = [
    "django_apps/asteroid_lab/services",
    "django_apps/asteroid_lab/replay",
    "django_apps/asteroid_lab/views",
]
# Allowance: solver_subprocess_runner references CLI as a module STRING only (no import).
ALLOWLIST = {"django_apps/asteroid_lab/services/solver_subprocess_runner.py"}

def test_viewer_does_not_import_solver_core() -> None:
    for root in VIEWER_ROOTS:
        for path in Path(root).rglob("*.py"):
            if str(path).replace("\\", "/") in ALLOWLIST:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            for node in ast.walk(tree):
                mods = []
                if isinstance(node, ast.ImportFrom) and node.module:
                    mods.append(node.module)
                if isinstance(node, ast.Import):
                    mods.extend(a.name for a in node.names)
                for mod in mods:
                    assert not mod.startswith("shapez2_factory"), f"{path} imports {mod}"
```

## Tasks

- [x] **Step 1:** Set `subprocess_only`; remove `in_process`/`subprocess` branch selection from request path (subprocess is the only path).
- [x] **Step 2:** Remove all core imports from `solver_runtime_entry`; ensure subprocess runner references CLI by module string only.
- [x] **Step 3 (TDD):** Add viewer import gate; make it green (move/remove any stray core imports).
- [ ] **Step 4:** Update docs (`structure.md`, runtime wiring, current_plan).
- [ ] **Step 5:** Full gate: ruff + black + mypy + pytest.

## Tests / verification

```powershell
python -m pytest tests/unit/architecture/test_asteroid_lab_viewer_no_core_import.py tests/unit/architecture/test_shapez2_factory_core_purity.py -v
python -m pytest tests/integration/web/test_asteroid_miner_layout_solver.py -v
powershell -File scripts/test_full.ps1
python -m ruff check .
python -m mypy django_apps config src
python -m black --check .
```

## Risks

- Hidden in-process dependency surfacing at runtime — integration test in subprocess_only mode catches it.
- `assumption:` subprocess perf acceptable vs in-process for UX; measure with [`lab_perf_trace`](../../../../django_apps/asteroid_lab/observability/lab_perf_trace.py). If unacceptable, optimization is artifact caching, **not** re-adding in-process import.
- Removing in-process entirely means CI/tests that solved in-process must switch to CLI/subprocess fixtures.

## Done criteria

- `subprocess_only` only path; no core import in request flow; viewer import gate green; docs updated; full gate green; Django = artifact viewer.
