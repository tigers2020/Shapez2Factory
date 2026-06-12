---
name: typing-zero-loop
description: >-
  Inventory-driven typing-zero chain on a single PR until typing.Any is 0.
  Dynamic loop: finish one slice, immediately start the next. Local gates only
  until Any=0; then run test_full + CI + Bugbot once. Use when the user says
  typing-zero loop, Any zero, typing debt loop, /typing-zero-loop, or
  /loop typing-zero.
disable-model-invocation: false
metadata:
  owner: project
  risk: normal
  requires_validation: true
---

# Typing-Zero Loop

**Role:** Typing / boundary contract worker on one PR until `typing.Any` count is 0.

**Invoke:** `/typing-zero-loop` · `@typing-zero-loop` · `/loop typing-zero` (dynamic, no interval)

**Authority:** [`documents/ai/manuals/typing_boundary_layers.md`](../../../documents/ai/manuals/typing_boundary_layers.md) · [`typing_contracts.md`](../../../documents/ai/manuals/typing_contracts.md) · PR **#284** · branch `typing-zero/phase-5-persistent-exterior-overlay`

---

## Goal

```text
Any removal → raw JsonValue/object + validator → wire TypedDict → domain dataclass
```

**Not:** convert every dict to dataclass. **Not:** run `test_full` or wait for Bugbot on every slice.

---

## Single PR rule

All commits go to **one PR** (#284) on `typing-zero/phase-5-persistent-exterior-overlay`. Do not open new PRs per slice.

---

## One slice (while Any > 0)

1. `python scripts/typing_debt_inventory.py`
2. Pick smallest safe bucket (manual checklist: wire→TypedDict, domain→dataclass, raw→validator)
3. Implement typing-only change (no behavior drift)
4. **Local gates only:**
   - `ruff check` / `black --check` on touched paths
   - `mypy` on touched packages
   - targeted `pytest` when replay/service touched
   - `python scripts/check_typing_debt.py` (non-increase baseline)
5. `git commit` + `git push` to same branch
6. **Immediately** start next slice (no CI wait, no `test_full`, no Bugbot)

---

## Final slice (when Any == 0)

Run **once**:

```text
python manage.py check
powershell -File scripts/test_full.ps1
mypy django_apps config src
ruff check .
black --check .
python scripts/check_typing_debt.py  # set zero baseline
```

Then push if needed; wait for **CI + Bugbot once**. Stop slicing.

---

## Dynamic `/loop` re-arm

After each slice (or when starting the chain), emit the next wake **once**:

```powershell
powershell -NoProfile -File .cursor/arm-typing-zero-loop.ps1
```

Optional: run in background with monitored output on `^AGENT_LOOP_WAKE_typing_zero`.

**Do not** poll CI between slices. **Do not** use fixed 1m sleep loops.

Wake payload is printed by `scripts/typing_zero_next_wake.py` (includes `any_remaining` + `manual` path).

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/typing_debt_inventory.py` | Bucketed Any/object inventory |
| `scripts/check_typing_debt.py` | Non-increase guard (→ zero at end) |
| `scripts/typing_zero_next_wake.py` | Print `AGENT_LOOP_WAKE_typing_zero` JSON |
| `.cursor/arm-typing-zero-loop.ps1` | Agent re-arm entrypoint |

---

## Stop conditions

Stop and report `BLOCKED:` when:

- public contract ambiguity needs human design approval
- third-party/stub makes zero Any unsafe
- fix requires behavior change, not typing refactor

---

## Resume

1. `git checkout typing-zero/phase-5-persistent-exterior-overlay`
2. `python scripts/typing_debt_inventory.py`
3. `python scripts/check_typing_debt.py`
4. Continue next slice or FINAL if Any=0
