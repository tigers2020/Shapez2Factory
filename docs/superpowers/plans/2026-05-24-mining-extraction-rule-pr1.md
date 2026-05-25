# Mining Extraction Rule PR-1 Implementation Plan

**Status:** APPROVED (2026-05-24 plan review — 3 mandatory corrections applied below)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended). Execute task-by-task with review between tasks. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `game_data.MiningExtractionRule` as a queryable **CANON_MANUAL** mirror of L1 extraction rates (shape 30/min, fluid 300 L/min, mini-unit ladder 4→16), with helpers and tests — **no RTTP wiring**.

### Review corrections (mandatory)

| # | Fix |
|---|-----|
| 1 | `test_unique_active_rule_per_resource`: expect `IntegrityError` on second active row (seed already has active shape); add `test_inactive_duplicate_rule_allowed` |
| 2 | Seed `update_or_create(resource_kind=..., is_active=True, defaults={...})` — `is_active` in lookup, not only in defaults |
| 3 | Task 7 `git add` includes audit, spec, roadmap (do not rely on optional docs-only commit) |

**Architecture:** New `mining.py` model (no `import_batch` FK), `RunPython` seed via historical models, pure service in `game_data/services/mining_extraction_rules.py`. Authority docs (audit + spec) ship in the same PR. Admin is view-only.

**Tech Stack:** Django 5.x ORM, `Decimal`, pytest-django, ruff, black, mypy `django_apps config src`

**Spec:** [`docs/superpowers/specs/2026-05-24-mining-extraction-rule-design.md`](../specs/2026-05-24-mining-extraction-rule-design.md)

**Audit:** [`documents/game_data/extraction_rate_authority_audit.md`](../../documents/game_data/extraction_rate_authority_audit.md)

**Branch:** `feat/rttp-mining-extraction-rule-pr1` (worktree recommended)

**Out of scope:** `django_apps/asteroid_lab/**` RTTP pipeline, UI, `capacity_goals` changes

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `documents/game_data/extraction_rate_authority_audit.md` | L1–L5 authority audit (done in planning; verify in PR) |
| Create | `docs/superpowers/specs/2026-05-24-mining-extraction-rule-design.md` | PR-1..3 contract (done in planning; verify in PR) |
| Create | `django_apps/game_data/models/mining.py` | `MiningExtractionRule` model |
| Modify | `django_apps/game_data/models/__init__.py` | Export model |
| Create | `django_apps/game_data/services/mining_extraction_rules.py` | Pure helpers |
| Create | `django_apps/game_data/migrations/0026_mining_extraction_rule.py` | Schema + seed |
| Modify | `django_apps/game_data/admin.py` | Read-only admin |
| Create | `tests/unit/game_data/test_mining_extraction_rules.py` | PR-1 tests |
| Modify | `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | PR-1 row (optional, one line) |

---

### Task 0: Branch and baseline

**Files:** none

- [ ] **Step 1: Create worktree/branch**

```powershell
git checkout master
git pull
git checkout -b feat/rttp-mining-extraction-rule-pr1
```

- [ ] **Step 2: Narrow game_data gate**

```powershell
python -m pytest tests/unit/game_data/ -v --tb=short
```

Expected: PASS (fix unrelated reds before PR-1 work).

- [ ] **Step 3: Confirm docs present**

Verify `documents/game_data/extraction_rate_authority_audit.md` and `docs/superpowers/specs/2026-05-24-mining-extraction-rule-design.md` exist and match approved ladder/forbidden list.

---

### Task 1: Authority docs commit checkpoint

**Files:**
- `documents/game_data/extraction_rate_authority_audit.md`
- `docs/superpowers/specs/2026-05-24-mining-extraction-rule-design.md`

- [ ] **Step 1: Review audit links**

Ensure audit references `game_data_backup/game_data_dump.json` `runtime_reflection` and simulation speed-only promote finding.

- [ ] **Step 2: Docs-only commit (optional)**

If skipping a separate docs commit, **Task 7 must stage audit + spec** (see Task 7 `git add`).

---

### Task 2: Model + meta tests (TDD)

**Files:**
- Create: `django_apps/game_data/models/mining.py`
- Modify: `django_apps/game_data/models/__init__.py`
- Test: `tests/unit/game_data/test_mining_extraction_rules.py`

- [ ] **Step 1: Write failing model contract tests**

Create `tests/unit/game_data/test_mining_extraction_rules.py`:

```python
"""PR-1 — MiningExtractionRule CANON_MANUAL seed and helpers."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.db import IntegrityError

from django_apps.game_data.models.mining import MiningExtractionRule


@pytest.mark.django_db
def test_seed_has_shape_and_fluid_active_rules() -> None:
    assert MiningExtractionRule.objects.filter(resource_kind="shape", is_active=True).count() == 1
    assert MiningExtractionRule.objects.filter(resource_kind="fluid", is_active=True).count() == 1


def test_no_import_batch_field_on_rule_model() -> None:
    names = {f.name for f in MiningExtractionRule._meta.get_fields()}
    assert "import_batch" not in names


def test_no_fluid_pipe_capacity_field_on_rule_model() -> None:
    names = {f.name for f in MiningExtractionRule._meta.get_fields()}
    assert "fluid_pipe_capacity" not in names
    assert "fluid_pipe_capacity_per_min" not in names


@pytest.mark.django_db
def test_unique_active_rule_per_resource() -> None:
    """Seed already inserted active shape; second active row violates partial unique."""
    with pytest.raises(IntegrityError):
        MiningExtractionRule.objects.create(
            resource_kind=MiningExtractionRule.ResourceKind.SHAPE,
            transport_kind="shape_belt",
            mini_unit_output_per_min=Decimal("30"),
            output_unit="shapes_per_min",
            is_active=True,
        )


@pytest.mark.django_db
def test_inactive_duplicate_rule_allowed() -> None:
    row = MiningExtractionRule.objects.create(
        resource_kind=MiningExtractionRule.ResourceKind.SHAPE,
        transport_kind="shape_belt",
        mini_unit_output_per_min=Decimal("30"),
        output_unit="shapes_per_min",
        is_active=False,
    )
    assert row.pk is not None
```

- [ ] **Step 2: Run tests — expect FAIL (no model / no table)**

```powershell
python -m pytest tests/unit/game_data/test_mining_extraction_rules.py -v --tb=short
```

Expected: FAIL (`ImportError` or `no such table`).

- [ ] **Step 3: Implement model**

Create `django_apps/game_data/models/mining.py` with approved schema (`ResourceKind`, `SourceKind`, `UniqueConstraint` with `condition=Q(is_active=True)`). Set:

```python
class Meta:
    verbose_name = "mining extraction rule"
    verbose_name_plural = "⑦ Mining · Extraction rules"
```

Update `django_apps/game_data/models/__init__.py` — import and add to `__all__`.

- [ ] **Step 4: Generate migration (schema only first)**

```powershell
python manage.py makemigrations game_data --name mining_extraction_rule
```

Rename to `0026_mining_extraction_rule.py` if Django picks another number; depend on `0025_alter_artifactchecksum_options_and_more`.

- [ ] **Step 5: Apply migration (schema only — seed in Task 3)**

Temporarily comment `RunPython` if generated together; apply:

```powershell
python manage.py migrate game_data
```

- [ ] **Step 6: Re-run model tests — still fail on seed tests**

Expected: `test_no_*_field` PASS; seed tests FAIL until Task 3.

---

### Task 3: Data migration seed

**Files:**
- Modify: `django_apps/game_data/migrations/0026_mining_extraction_rule.py`

- [ ] **Step 1: Add RunPython seed (historical model)**

In the same migration file:

```python
from decimal import Decimal

from django.db import migrations, models


def seed_mining_extraction_rules(apps, schema_editor):
    Rule = apps.get_model("game_data", "MiningExtractionRule")
    rows = (
        {
            "resource_kind": "shape",
            "transport_kind": "shape_belt",
            "mini_unit_output_per_min": Decimal("30.0000"),
            "output_unit": "shapes_per_min",
            "base_mini_units_per_miner": 4,
            "mini_units_per_extension": 4,
            "max_extension_count": 3,
            "source_kind": "CANON_MANUAL",
            "source_note": (
                "Queryable mirror of L1 CANON: "
                "documents/game_rules/shapez2_asteroid_space_transport_throughput.md"
            ),
            "is_active": True,
        },
        {
            "resource_kind": "fluid",
            "transport_kind": "fluid_pipe",
            "mini_unit_output_per_min": Decimal("300.0000"),
            "output_unit": "liters_per_min",
            "base_mini_units_per_miner": 4,
            "mini_units_per_extension": 4,
            "max_extension_count": 3,
            "source_kind": "CANON_MANUAL",
            "source_note": (
                "Queryable mirror of L1 CANON: "
                "documents/game_rules/shapez2_asteroid_space_transport_throughput.md"
            ),
            "is_active": True,
        },
    )
    for row in rows:
        resource_kind = row["resource_kind"]
        Rule.objects.update_or_create(
            resource_kind=resource_kind,
            is_active=True,
            defaults={
                "transport_kind": row["transport_kind"],
                "mini_unit_output_per_min": row["mini_unit_output_per_min"],
                "output_unit": row["output_unit"],
                "base_mini_units_per_miner": row["base_mini_units_per_miner"],
                "mini_units_per_extension": row["mini_units_per_extension"],
                "max_extension_count": row["max_extension_count"],
                "source_kind": row["source_kind"],
                "source_note": row["source_note"],
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("game_data", "0025_alter_artifactchecksum_options_and_more"),
    ]
    operations = [
        # CreateModel ... (from makemigrations),
        migrations.RunPython(seed_mining_extraction_rules, migrations.RunPython.noop),
    ]
```

Lookup `(resource_kind, is_active=True)` so inactive revision rows never collide. Re-run is idempotent.

- [ ] **Step 2: Migrate**

```powershell
python manage.py migrate game_data
```

- [ ] **Step 3: Run seed tests**

```powershell
python -m pytest tests/unit/game_data/test_mining_extraction_rules.py::test_seed_has_shape_and_fluid_active_rules tests/unit/game_data/test_mining_extraction_rules.py::test_unique_active_rule_per_resource tests/unit/game_data/test_mining_extraction_rules.py::test_inactive_duplicate_rule_allowed -v --tb=short
```

Expected: PASS.

- [ ] **Step 4: Refresh admin taxonomy (optional)**

```powershell
python manage.py seed_game_data_taxonomy
```

Expected: new section under namespace `⑦ Mining`.

---

### Task 4: Helper service (TDD)

**Files:**
- Create: `django_apps/game_data/services/mining_extraction_rules.py`
- Test: `tests/unit/game_data/test_mining_extraction_rules.py`

- [ ] **Step 1: Write failing helper tests**

Append to `tests/unit/game_data/test_mining_extraction_rules.py`:

```python
from django_apps.game_data.services.mining_extraction_rules import (
    VALID_THROUGHPUT_FACTORS,
    assert_throughput_factor_matches_extensions,
    effective_mini_units,
    get_active_rule,
    max_output_per_miner,
    output_per_min,
)


@pytest.mark.django_db
def test_shape_max_output_is_480() -> None:
    rule = get_active_rule("shape")
    assert max_output_per_miner(rule) == Decimal("480.0000")


@pytest.mark.django_db
def test_fluid_max_output_is_4800() -> None:
    rule = get_active_rule("fluid")
    assert max_output_per_miner(rule) == Decimal("4800.0000")


def test_effective_mini_units_0_to_3() -> None:
    assert effective_mini_units(0) == 4
    assert effective_mini_units(1) == 8
    assert effective_mini_units(2) == 12
    assert effective_mini_units(3) == 16


def test_effective_mini_units_rejects_out_of_range() -> None:
    with pytest.raises(ValueError):
        effective_mini_units(4)


@pytest.mark.django_db
def test_output_per_min_uses_decimal() -> None:
    rule = get_active_rule("shape")
    assert output_per_min(rule, 8) == Decimal("240.0000")


def test_assert_throughput_factor_matches_extensions() -> None:
    assert_throughput_factor_matches_extensions(12, 2)


def test_valid_throughput_factors_match_pattern_library() -> None:
    assert VALID_THROUGHPUT_FACTORS == frozenset({4, 8, 12, 16})
```

- [ ] **Step 2: Run tests — FAIL**

```powershell
python -m pytest tests/unit/game_data/test_mining_extraction_rules.py -v --tb=short
```

- [ ] **Step 3: Implement helpers**

```python
"""Queryable CANON extraction rates (L1b). No RTTP imports."""

from __future__ import annotations

from decimal import Decimal

from django_apps.game_data.models.mining import MiningExtractionRule

VALID_THROUGHPUT_FACTORS: frozenset[int] = frozenset({4, 8, 12, 16})


def get_active_rule(resource_kind: str) -> MiningExtractionRule:
    row = MiningExtractionRule.objects.filter(
        resource_kind=resource_kind,
        is_active=True,
    ).first()
    if row is None:
        msg = f"no active MiningExtractionRule for resource_kind={resource_kind!r}"
        raise LookupError(msg)
    return row


def effective_mini_units(extension_count: int) -> int:
    if extension_count < 0 or extension_count > 3:
        msg = "extension_count must be in 0..3"
        raise ValueError(msg)
    return 4 + 4 * extension_count


def output_per_min(rule: MiningExtractionRule, throughput_factor: int) -> Decimal:
    if throughput_factor not in VALID_THROUGHPUT_FACTORS:
        msg = f"throughput_factor must be one of {sorted(VALID_THROUGHPUT_FACTORS)}"
        raise ValueError(msg)
    return rule.mini_unit_output_per_min * Decimal(throughput_factor)


def max_output_per_miner(rule: MiningExtractionRule) -> Decimal:
    factor = effective_mini_units(int(rule.max_extension_count))
    return output_per_min(rule, factor)


def assert_throughput_factor_matches_extensions(
    throughput_factor: int,
    extension_count: int,
) -> None:
    if throughput_factor != effective_mini_units(extension_count):
        msg = (
            f"throughput_factor {throughput_factor} != "
            f"effective_mini_units({extension_count})"
        )
        raise ValueError(msg)
```

- [ ] **Step 4: Run full test file — PASS**

```powershell
python -m pytest tests/unit/game_data/test_mining_extraction_rules.py -v --tb=short
```

- [ ] **Step 5: Add PR-1 scope guard test (after service file exists)**

Append to `tests/unit/game_data/test_mining_extraction_rules.py`:

```python
def test_service_has_no_rttp_imports() -> None:
    import ast
    from pathlib import Path

    tree = ast.parse(
        Path("django_apps/game_data/services/mining_extraction_rules.py").read_text(
            encoding="utf-8"
        )
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "asteroid_lab" not in node.module
            assert "shapez_asteroid" not in node.module
```

```powershell
python -m pytest tests/unit/game_data/test_mining_extraction_rules.py::test_service_has_no_rttp_imports -v --tb=short
```

Expected: PASS.

---

### Task 5: Admin (read-only)

**Files:**
- Modify: `django_apps/game_data/admin.py`

- [ ] **Step 1: Register admin**

```python
@admin.register(m.MiningExtractionRule)
class MiningExtractionRuleAdmin(admin.ModelAdmin):
    list_display = (
        "resource_kind",
        "transport_kind",
        "mini_unit_output_per_min",
        "output_unit",
        "max_extension_count",
        "source_kind",
        "is_active",
    )
    list_filter = ("resource_kind", "source_kind", "is_active")
    search_fields = ("resource_kind", "transport_kind", "source_note")

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_view_permission(self, request, obj=None) -> bool:
        return bool(request.user.is_active and request.user.is_staff)
```

Do **not** use `GameDataReadOnlyAdminMixin` if it allows staff edit — CANON rows are migration-only. View-only for staff; mutations via migration only.

- [ ] **Step 2: Smoke**

```powershell
python manage.py check
```

---

### Task 6: Lint, types, full gate slice

**Files:** all touched

- [ ] **Step 1: Ruff**

```powershell
python -m ruff check django_apps/game_data/models/mining.py django_apps/game_data/services/mining_extraction_rules.py django_apps/game_data/admin.py tests/unit/game_data/test_mining_extraction_rules.py
```

- [ ] **Step 2: Mypy**

```powershell
python -m mypy django_apps/game_data/models/mining.py django_apps/game_data/services/mining_extraction_rules.py
```

- [ ] **Step 3: Black check**

```powershell
python -m black --check django_apps/game_data/models/mining.py django_apps/game_data/services/mining_extraction_rules.py tests/unit/game_data/test_mining_extraction_rules.py
```

- [ ] **Step 4: Broader game_data tests**

```powershell
python -m pytest tests/unit/game_data/ -v --tb=short
```

---

### Task 7: PR package

**Files:** roadmap optional

- [ ] **Step 1: Update roadmap (one row)**

In `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md`, add under open/next:

```text
Mining extraction rule PR-1 (CANON_MANUAL L1b) — in flight
```

- [ ] **Step 2: Commit implementation**

```powershell
git add `
  django_apps/game_data/ `
  tests/unit/game_data/ `
  documents/game_data/extraction_rate_authority_audit.md `
  docs/superpowers/specs/2026-05-24-mining-extraction-rule-design.md `
  docs/superpowers/plans/2026-05-24-mining-extraction-rule-pr1.md `
  docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md
git commit -m "feat(game_data): add MiningExtractionRule CANON_MANUAL seed and helpers"
```

- [ ] **Step 3: Push and open PR**

PR title: `feat(game_data): MiningExtractionRule CANON_MANUAL (PR-1)`

Body must include:

- Summary: L1b queryable mirror; not dump import
- Test plan: `pytest tests/unit/game_data/test_mining_extraction_rules.py`
- Explicit: **no RTTP changes**

---

## Plan self-review

| Spec requirement | Task |
|------------------|------|
| L1b model, no import_batch | Task 2 tests + model |
| No fluid pipe capacity field | Task 2 test |
| CANON_MANUAL seed shape/fluid | Task 3 |
| Helpers, no RTTP | Task 4 + `test_service_has_no_rttp_imports` |
| Partial unique test (post-seed) | Task 2–3 `IntegrityError` + inactive allowed |
| Seed lookup `is_active=True` | Task 3 |
| Audit + spec (C) | Task 0–1 + Task 7 `git add` |
| Admin browse | Task 5 |
| PR-2/3 out of scope | Header |

No placeholders remain in task steps.

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-24-mining-extraction-rule-pr1.md`.

**Approved execution mode: Subagent-Driven** — model + migration + helper + admin + docs; task-level self-review before PR.

When starting implementation: `git checkout -b feat/rttp-mining-extraction-rule-pr1` (worktree optional per `using-git-worktrees`).
