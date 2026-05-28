# Miner Seed Difficulty Rank Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic intrinsic difficulty metadata (`difficulty_score`, `difficulty_rank`, `difficulty_tier`, `rank_reason`) to miner seed v2 ingest while keeping `seed_rank` as stable catalog order.

**Architecture:** Extract equipment parent-tree helpers → pure intrinsic scorer (`int` score, `compactness_approx` float in `rank_reason`) → global rank assignment over 18 bootstrap patterns → `seed_miner_patterns` writes metadata; Admin displays difficulty columns; `search_priority_rank` stays `null` until Phase 5.

**Tech Stack:** Django 5.2, pytest, ruff, mypy (`django_apps config src`), `scripts/test_fast.ps1`.

**Spec:** [`../specs/2026-05-28-miner-seed-difficulty-rank-design.md`](../specs/2026-05-28-miner-seed-difficulty-rank-design.md)

**Branch (recommended):** `feat/miner-seed-difficulty-rank` from latest `master` (or current miner seed v2 branch).

---

## File map

| File | Action |
|------|--------|
| `django_apps/asteroid_lab/genetic_sample/miner_seed_parent_tree.py` | **Create** — public `equipment_nodes`, `parent_edges_bfs` |
| `django_apps/asteroid_lab/genetic_sample/miner_seed_equivalence.py` | **Modify** — import parent tree from shared module |
| `django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py` | **Create** — score, tier, `assign_difficulty_ranks` |
| `django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py` | **Modify** — `EXPECTED_DIFFICULTY_RANK_ORDER` golden tuple |
| `django_apps/asteroid_lab/management/commands/seed_miner_patterns.py` | **Modify** — two-pass ingest, dry-run table, `--strict-rank-ambiguity` |
| `django_apps/asteroid_lab/admin.py` | **Modify** — catalog vs difficulty columns |
| `tests/unit/asteroid_lab/test_miner_seed_parent_tree.py` | **Create** (optional thin) or covered by equivalence tests |
| `tests/unit/asteroid_lab/test_miner_seed_intrinsic_difficulty.py` | **Create** — scorer + golden §3.6 |
| `tests/unit/asteroid_lab/test_seed_miner_patterns_command.py` | **Modify** — metadata contract tests |
| `tests/unit/asteroid_lab/test_miner_seed_equivalence.py` | **Modify** — only if import paths change (should stay green) |
| `docs/superpowers/specs/2026-05-28-miner-seed-difficulty-rank-design.md` | Already approved |

---

## Golden contract (lock in tests)

```python
EXPECTED_DIFFICULTY_RANK_ORDER: tuple[str, ...] = (
    "m0e_01",
    "m1e_01",
    "m2e_01",
    "m2e_02",
    "m2e_04",
    "m2e_03",
    "m3e_01",
    "m3e_02",
    "m3e_04",
    "m3e_03",
    "m3e_07",
    "m3e_09",
    "m3e_06",
    "m3e_13",
    "m3e_05",
    "m3e_11",
    "m3e_12",
    "m3e_08",
)
```

`difficulty_rank` for `pattern_id` = `EXPECTED_DIFFICULTY_RANK_ORDER.index(pattern_id) + 1`.

---

### Task 1: Shared parent-tree module

**Files:**
- Create: `django_apps/asteroid_lab/genetic_sample/miner_seed_parent_tree.py`
- Modify: `django_apps/asteroid_lab/genetic_sample/miner_seed_equivalence.py`
- Test: `tests/unit/asteroid_lab/test_miner_seed_equivalence.py` (regression)

- [ ] **Step 1: Run equivalence tests (baseline)**

```bash
python -m pytest tests/unit/asteroid_lab/test_miner_seed_equivalence.py -v
```

Expected: PASS

- [ ] **Step 2: Create `miner_seed_parent_tree.py`**

Move (no logic change) from equivalence:

```python
"""Equipment parent-tree helpers for miner seed catalog (island-local)."""

from __future__ import annotations

from collections import deque
from typing import Any

from django_apps.asteroid_lab.snapshots.copy_json_coords import entry_island_raw_coord

_MINER_T = frozenset({"Layout_ShapeMiner", "Layout_FluidMiner"})
_EXT_T = frozenset({"Layout_ShapeMinerExtension", "Layout_FluidMinerExtension"})
_BELT_T = frozenset({"SpaceBelt_Forward", "SpacePipe_Forward"})
_ISLAND_DIRS: tuple[tuple[str, int, int], ...] = (
    ("n", 0, -1),
    ("e", 1, 0),
    ("s", 0, 1),
    ("w", -1, 0),
)


def entries(root: dict[str, Any]) -> list[dict[str, Any]]:
    bp = root.get("BP")
    if not isinstance(bp, dict):
        return []
    raw = bp.get("Entries")
    return [e for e in raw if isinstance(e, dict)] if isinstance(raw, list) else []


def equipment_nodes(root: dict[str, Any]) -> tuple[tuple[int, int], dict[tuple[int, int], dict[str, Any]]]:
    """Return (miner_xy, nodes) for miner + extensions; belts excluded."""

    miner_xy: tuple[int, int] | None = None
    nodes: dict[tuple[int, int], dict[str, Any]] = {}
    for entry in entries(root):
        tile = str(entry.get("T", ""))
        if tile in _BELT_T:
            continue
        if tile not in _MINER_T and tile not in _EXT_T:
            continue
        coord = entry_island_raw_coord(entry)
        xy = (coord.x, coord.y)
        if tile in _MINER_T:
            if miner_xy is not None:
                msg = "multiple miner entries"
                raise ValueError(msg)
            miner_xy = xy
        nodes[xy] = entry
    if miner_xy is None:
        msg = "miner entry required"
        raise ValueError(msg)
    return miner_xy, nodes


def parent_edges_bfs(
    miner_xy: tuple[int, int],
    nodes: dict[tuple[int, int], dict[str, Any]],
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Directed child→parent edges on 4-connected equipment tree."""

    visited: set[tuple[int, int]] = {miner_xy}
    parent_of: dict[tuple[int, int], tuple[int, int]] = {}
    queue: deque[tuple[int, int]] = deque([miner_xy])
    while queue:
        current = queue.popleft()
        cx, cy = current
        for _d, dx, dy in _ISLAND_DIRS:
            nb = (cx + dx, cy + dy)
            if nb not in nodes or nb in visited:
                continue
            visited.add(nb)
            parent_of[nb] = current
            queue.append(nb)
    ext_keys = [xy for xy in nodes if xy != miner_xy]
    if len(visited) != len(nodes):
        msg = "extension cells must be 4-connected to miner"
        raise ValueError(msg)
    edges = [(child, parent_of[child]) for child in ext_keys]
    if len(edges) != len(ext_keys):
        msg = "extension parent tree incomplete"
        raise ValueError(msg)
    return edges
```

- [ ] **Step 3: Update `miner_seed_equivalence.py`**

Replace local `_equipment_nodes` / `_parent_edges_bfs` with imports; map `MinerSeedLayoutValidationError` on connectivity failures from `parent_edges_bfs` (wrap `ValueError` if needed).

- [ ] **Step 4: Run regression tests**

```bash
python -m pytest tests/unit/asteroid_lab/test_miner_seed_equivalence.py -v
python -m ruff check django_apps/asteroid_lab/genetic_sample/miner_seed_parent_tree.py django_apps/asteroid_lab/genetic_sample/miner_seed_equivalence.py
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/genetic_sample/miner_seed_parent_tree.py django_apps/asteroid_lab/genetic_sample/miner_seed_equivalence.py
git commit -m "refactor(asteroid_lab): extract miner seed parent-tree helpers"
```

---

### Task 2: Intrinsic difficulty scorer (TDD)

**Files:**
- Create: `django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py`
- Create: `tests/unit/asteroid_lab/test_miner_seed_intrinsic_difficulty.py`

- [ ] **Step 1: Write failing golden-order test**

```python
from pathlib import Path

import pytest

from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import (
    EXPECTED_DIFFICULTY_RANK_ORDER,
    EXPECTED_PATTERN_IDS,
)
from django_apps.asteroid_lab.genetic_sample.miner_seed_equivalence import (
    assert_miner_seed_layout_strict,
)
from django_apps.asteroid_lab.genetic_sample.miner_seed_intrinsic_difficulty import (
    assign_difficulty_ranks,
    intrinsic_difficulty_from_root,
)

_BOOTSTRAP = Path("var/default_miner_pattern.txt")


def test_golden_difficulty_rank_order() -> None:
    lines = [ln.strip() for ln in _BOOTSTRAP.read_text(encoding="utf-8").splitlines() if ln.strip()]
    scored: list[tuple[str, object]] = []
    for pattern_id, line in zip(EXPECTED_PATTERN_IDS, lines, strict=True):
        root = decode_copy_string(line).root
        assert_miner_seed_layout_strict(root)
        scored.append((pattern_id, intrinsic_difficulty_from_root(root)))
    ranked = assign_difficulty_ranks(scored)
    order = [pid for pid, _ in ranked]
    assert order == list(EXPECTED_DIFFICULTY_RANK_ORDER)


def test_difficulty_score_is_int_for_m0e() -> None:
    line = _BOOTSTRAP.read_text(encoding="utf-8").splitlines()[0].strip()
    root = decode_copy_string(line).root
    assert_miner_seed_layout_strict(root)
    result = intrinsic_difficulty_from_root(root)
    assert isinstance(result.score, int)
    assert result.score == 8
    assert result.reason["compactness_approx"] == 1.0
```

Add `EXPECTED_DIFFICULTY_RANK_ORDER` to `miner_seed_constants.py` in Step 3 if test imports it.

- [ ] **Step 2: Run test (red)**

```bash
python -m pytest tests/unit/asteroid_lab/test_miner_seed_intrinsic_difficulty.py -v
```

Expected: FAIL — `ModuleNotFoundError` or missing functions

- [ ] **Step 3: Implement scorer**

`miner_seed_intrinsic_difficulty.py` (core types):

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django_apps.asteroid_lab.genetic_sample.miner_seed_parent_tree import (
    equipment_nodes,
    parent_edges_bfs,
)
from django_apps.asteroid_lab.genetic_sample.miner_seed_topology import (
    count_extensions,
    throughput_factor_for_extension_count,
)
from django_apps.asteroid_lab.snapshots.island_bbox import island_bbox_from_xy_dicts


@dataclass(frozen=True)
class IntrinsicDifficultyResult:
    score: int
    tier: int
    reason: dict[str, Any]


def intrinsic_difficulty_from_root(root: dict[str, Any]) -> IntrinsicDifficultyResult:
    miner_xy, nodes = equipment_nodes(root)
    edges = parent_edges_bfs(miner_xy, nodes)
    ext = count_extensions(root)
    # ... branch_count, turn_count, bbox, compactness_approx, tier, int score per spec §3
    ...


def assign_difficulty_ranks(
    items: list[tuple[str, IntrinsicDifficultyResult]],
) -> list[tuple[str, IntrinsicDifficultyResult, int]]:
    """Return (pattern_id, result, difficulty_rank) sorted; ranks 1..N."""

    def sort_key(item: tuple[str, IntrinsicDifficultyResult]) -> tuple:
        pid, r = item
        return (
            r.tier,
            r.score,
            -float(r.reason["compactness_approx"]),
            int(r.reason["throughput_factor"]),
            pid,
        )

    ordered = sorted(items, key=sort_key)
    return [(pid, r, i) for i, (pid, r) in enumerate(ordered, start=1)]
```

Implement branch/turn/tier exactly per spec §3.3–§3.4. Store `compactness_approx` (not `coverage_approx`) in `rank_reason`.

- [ ] **Step 4: Add `EXPECTED_DIFFICULTY_RANK_ORDER` to constants**

```python
EXPECTED_DIFFICULTY_RANK_ORDER: tuple[str, ...] = (
    "m0e_01",
    "m1e_01",
    # ... full list from plan header
)
```

- [ ] **Step 5: Run tests (green) + ruff + mypy**

```bash
python -m pytest tests/unit/asteroid_lab/test_miner_seed_intrinsic_difficulty.py -v
python -m ruff check django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
python -m mypy django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add django_apps/asteroid_lab/genetic_sample/miner_seed_intrinsic_difficulty.py django_apps/asteroid_lab/genetic_sample/miner_seed_constants.py tests/unit/asteroid_lab/test_miner_seed_intrinsic_difficulty.py
git commit -m "feat(asteroid_lab): add miner seed intrinsic difficulty scorer"
```

---

### Task 3: `seed_miner_patterns` ingest + dry-run

**Files:**
- Modify: `django_apps/asteroid_lab/management/commands/seed_miner_patterns.py`
- Modify: `tests/unit/asteroid_lab/test_seed_miner_patterns_command.py`

- [ ] **Step 1: Write failing ingest metadata test**

```python
@pytest.mark.django_db
def test_seed_miner_patterns_writes_difficulty_metadata() -> None:
    call_command("seed_miner_patterns")
    row = GeneticSample.objects.get(gene_key="miner_seed_m3e_01")
    meta = row.metadata_json
    assert meta["difficulty_rank"] == 7
    assert meta["difficulty_score"] == 337
    assert isinstance(meta["difficulty_score"], int)
    assert meta["difficulty_tier"] == 4
    assert meta["search_priority_rank"] is None
    assert meta["search_priority_source"] == "deferred_phase5"
    assert "compactness_approx" in meta["rank_reason"]
    assert "coverage_approx" not in meta["rank_reason"]
    assert meta["seed_rank"] == EXPECTED_PATTERN_IDS.index("m3e_01") + 1


@pytest.mark.django_db
def test_difficulty_ranks_are_permutation_1_to_18() -> None:
    call_command("seed_miner_patterns")
    ranks = list(
        GeneticSample.objects.filter(metadata_json__is_seed=True).values_list(
            "metadata_json__difficulty_rank",
            flat=True,
        ),
    )
    assert sorted(ranks) == list(range(1, 19))
```

- [ ] **Step 2: Run test (red)**

```bash
python -m pytest tests/unit/asteroid_lab/test_seed_miner_patterns_command.py::test_seed_miner_patterns_writes_difficulty_metadata -v
```

- [ ] **Step 3: Implement two-pass ingest**

Pass 1 (existing loop): decode, strict validate, collect `(pattern_id, root, code, signatures, ext, ...)`.

Pass 2: `assign_difficulty_ranks([(pid, intrinsic_difficulty_from_root(root)) ...])` → merge into `metadata_json`.

Add CLI flags:

```python
parser.add_argument(
    "--strict-rank-ambiguity",
    action="store_true",
    help="Fail if pre-pattern_id sort keys collide across two pattern_ids.",
)
```

`_check_rank_ambiguity(ranked_items)` — compare keys `(tier, score, compactness_approx, throughput_factor)`; raise `CommandError` only when flag set.

Dry-run: after validation, print table:

```text
difficulty_rank  pattern_id  tier  score  catalog_rank(seed_rank)
```

Do not fail on duplicate scores by default.

- [ ] **Step 4: Run command tests (green)**

```bash
python -m pytest tests/unit/asteroid_lab/test_seed_miner_patterns_command.py -v
```

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/management/commands/seed_miner_patterns.py tests/unit/asteroid_lab/test_seed_miner_patterns_command.py
git commit -m "feat(asteroid_lab): persist miner seed difficulty metadata on ingest"
```

---

### Task 4: Admin display

**Files:**
- Modify: `django_apps/asteroid_lab/admin.py`

- [ ] **Step 1: Update `GeneticSampleAdmin.list_display`**

Add after `seed_rank_display`:

```python
@admin.display(description="Catalog rank", ordering="metadata_json__seed_rank")
def seed_rank_display(self, obj: m.GeneticSample) -> str:
    ...

@admin.display(description="Difficulty", ordering="metadata_json__difficulty_rank")
def difficulty_rank_display(self, obj: m.GeneticSample) -> str:
    meta = obj.metadata_json if isinstance(obj.metadata_json, dict) else {}
    rank = meta.get("difficulty_rank")
    tier = meta.get("difficulty_tier")
    if isinstance(rank, int) and isinstance(tier, int):
        return f"{rank} (T{tier})"
    return "-"
```

Include `difficulty_rank_display` in `list_display`; keep default queryset ordering by `seed_rank` (catalog).

- [ ] **Step 2: Manual smoke (optional)**

```bash
python manage.py seed_miner_patterns
python manage.py runserver
```

Open GeneticSample changelist — verify Catalog rank vs Difficulty columns.

- [ ] **Step 3: Run admin unit test if present**

```bash
python -m pytest tests/unit/asteroid_lab/test_genetic_sample_admin_seed.py -v
```

- [ ] **Step 4: Commit**

```bash
git add django_apps/asteroid_lab/admin.py
git commit -m "feat(asteroid_lab): show miner seed difficulty rank in admin"
```

---

### Task 5: Full gate + docs

**Files:**
- Modify: `documents/ai/current_plan.md` (CLOSED entry when merged)

- [ ] **Step 1: Narrow pytest**

```bash
python -m pytest tests/unit/asteroid_lab/test_miner_seed_intrinsic_difficulty.py tests/unit/asteroid_lab/test_miner_seed_equivalence.py tests/unit/asteroid_lab/test_seed_miner_patterns_command.py -v
```

- [ ] **Step 2: Ruff + mypy**

```bash
python -m ruff check django_apps/asteroid_lab/genetic_sample/ django_apps/asteroid_lab/management/commands/seed_miner_patterns.py django_apps/asteroid_lab/admin.py
python -m mypy django_apps config src
```

- [ ] **Step 3: PR full gate (when ready to merge)**

```bash
powershell -File scripts/test_full.ps1
```

- [ ] **Step 4: Plan CLOSED in `documents/ai/current_plan.md`**

Link spec + plan; date stamp.

- [ ] **Step 5: Commit docs**

```bash
git add documents/ai/current_plan.md
git commit -m "docs: close miner seed difficulty rank plan"
```

---

## Spec self-review (plan vs spec)

| Spec section | Task |
|--------------|------|
| §2 `seed_rank` = catalog | Task 3 — `seed_rank` unchanged |
| §2 `difficulty_score: int` | Task 2–3 tests assert `int` |
| §2 `compactness_approx` | Task 2 `rank_reason` key |
| §3 formula + tier | Task 2 |
| §3.6 golden order | Task 2 `EXPECTED_DIFFICULTY_RANK_ORDER` |
| §4.1 dry-run table | Task 3 |
| §4.1 `--strict-rank-ambiguity` | Task 3 |
| §4.2 Admin | Task 4 |
| §4.3 deferred `search_priority_rank` | Task 3 metadata |
| §5 tests | Tasks 2–3 |
| PR-D3 Phase 5 | Out of scope |

No placeholders remain in task steps.

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-28-miner-seed-difficulty-rank.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — run tasks in this session with executing-plans checkpoints  

Which approach do you want?
