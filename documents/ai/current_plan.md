# Current Plan

## Active Baseline

Asteroid Lab currently owns reconstruction, cleanup, replay, snapshot contracts,
and the fail-closed runtime entry. Deleted solver plans and archive material are
not implementation context.

Runtime authority:

```text
decode -> cleanup -> reconstruction -> ReconstructionCompleteMap -> persist -> replay
```

`shapez_solver` is a separate factory graph domain and is out of scope for
Asteroid Lab runtime decisions.

## Authority Precedence

1. Code under `django_apps/asteroid_lab/reconstruction/`, `cleanup/`, `replay/`,
   `contracts/`, and `services/solver_runtime_entry.py`
2. This file for current queue and standing gates
3. [`documents/index/document_inventory.md`](../index/document_inventory.md)
4. Current `documents/Algorithm/asteroid_lab_*.md` files
5. Current tests

Deleted document content is not authority.

## Active Code Paths

```text
django_apps/asteroid_lab/reconstruction/
django_apps/asteroid_lab/cleanup/
django_apps/asteroid_lab/replay/
django_apps/asteroid_lab/contracts/
django_apps/asteroid_lab/genetic_sample/
django_apps/asteroid_lab/services/solver_runtime_entry.py
```

## Verification

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
powershell -File scripts/test_capacity_sot.ps1
```

Full gate: see [`AGENTS.md`](../../AGENTS.md).

## Next Focus

Open new work from current code, current tests, and
[`document_inventory.md`](../index/document_inventory.md). Add or update current
plans only when the task needs a written implementation plan.
