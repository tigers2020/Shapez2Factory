# Manual: Typing Boundary Layers (Any · object · TypedDict · dataclass)

Process authority: [`AGENTS.md`](../../../AGENTS.md).  
Companion: [`typing_contracts.md`](typing_contracts.md) · [`docs/superpowers/specs/2026-06-11-any-boundary-typing-design.md`](../../../docs/superpowers/specs/2026-06-11-any-boundary-typing-design.md).

**Canon path:** `documents/ai/manuals/typing_boundary_layers.md`

Use this manual during the **typing-zero** loop (`scripts/typing_zero_next_wake.py`, PR `#284`).

---

## Goal (not “everything becomes dataclass”)

```text
Any removal
  → raw object / JsonValue at decode
  → validator / converter narrowing
  → wire = TypedDict
  → domain = frozen dataclass
```

**Not:** convert every dict payload into a dataclass.

---

## Three layers

| Layer | Preferred types | Why |
|-------|-----------------|-----|
| **Raw JSON / decode** | `object`, `JsonValue`, `JsonObject` | Untrusted until validated |
| **Wire / API / replay payload** | named `TypedDict` | Runtime shape is `dict`; matches JSON consumers |
| **Domain / semantic model** | frozen `dataclass` | Meaning, invariants, methods, strong mypy |

```text
dataclass  = semantic authority
TypedDict  = wire authority
converter  = boundary authority
```

---

## `Any` vs `object`

### `typing.Any`

- Mypy **disables** checking on that value.
- `dict[str, Any]` allows silent misuse:

```python
row: Mapping[str, Any]
x: int = row["x"]  # mypy OK even if runtime type is wrong
```

**Policy:** remove from production boundaries (typing-zero KPI).

### `object`

- Every value is an `object`, but **use requires narrowing**.
- Intermediate step, not the final contract:

```python
row: Mapping[str, object]
x: int = row["x"]  # mypy ERROR — must narrow first
```

**Policy:** allowed only as a **short-lived** input to a named validator/converter.

---

## Where each type belongs

### frozen `dataclass` (semantic)

Use for in-process authority:

- solver runtime state (domain)
- placement bundle, route reservation, complete map
- `EffectiveCellView`, `ReplayOverlayCell`, timeline DTOs
- any model that carries **behavior** or **invariants**

### `TypedDict` (wire)

Use when data **enters or leaves** as JSON/dict:

- `ReplayOverlayCellWire`, `EffectiveCellWire`, `PersistentConnectorOverlayWire`
- replay frame rows, metrics payloads, cache wire shapes

Pattern:

```python
@dataclass(frozen=True)
class EffectiveCellView:
    ...

class EffectiveCellWire(TypedDict):
    ...

def effective_cell_to_wire(view: EffectiveCellView) -> EffectiveCellWire:
    return {"x": view.x, ...}
```

### `object` / `JsonValue` (raw)

**Allowed:**

- immediately after `json.loads`
- validator **input**
- legacy migration input
- unknown external payloads

**Forbidden as long-lived contract:**

- domain objects kept across layers
- replay frame **output**
- service response output
- persisted cache schema
- internal APIs that pass `dict[str, object]` through multiple modules

Bad:

```python
def build_frame(cell: dict[str, object]) -> dict[str, object]:
    ...
```

Good:

```python
def parse_overlay_cell(raw: Mapping[str, object]) -> ReplayOverlayCellWire:
    ...
```

Better:

```python
def parse_overlay_cell(raw: Mapping[str, object]) -> ReplayOverlayCellView:
    ...

def overlay_cell_to_wire(view: ReplayOverlayCellView) -> ReplayOverlayCellWire:
    ...
```

---

## Slice decision checklist

| Situation | Choose |
|-----------|--------|
| External JSON just decoded | `object` / `JsonValue` |
| Generic JSON object tree | `JsonObject` (`Mapping[str, JsonValue]`) |
| Named wire payload shape | `TypedDict` + converter |
| Internal semantic model | frozen `dataclass` |
| Behavior / invariants | `dataclass` |
| Closed string tokens | `Literal` or `Enum` |
| Structural interface | `Protocol` |
| Temporary migration shim | `Mapping[str, object]` + validator (name removal slice) |
| Long-lived internal contract | **no** bare `dict[str, object]` |

---

## Typing-zero loop rules

**Single PR:** `typing-zero/phase-5-persistent-exterior-overlay` (#284) until `Any` count is 0.

**Per slice (while `Any` > 0):**

1. `python scripts/typing_debt_inventory.py`
2. Pick smallest bucket; apply checklist above
3. Local gates only: `ruff` / `black` on touched paths, `mypy` on touched packages, targeted pytest, `python scripts/check_typing_debt.py`
4. Commit + push to same PR
5. **Do not** run `scripts/test_full.ps1` or wait for Bugbot

**Final (when `Any` == 0):**

- Run full validation **once:** `manage.py check`, `test_full.ps1`, repo `mypy` / `ruff` / `black`, CI + Bugbot

**Re-arm chain:** `powershell -NoProfile -File .cursor/typing-zero-loop.ps1`

---

## One-line summary

```text
Any = remove.
object = force narrowing before use; not a final contract.
domain = frozen dataclass.
wire = TypedDict.
raw decode = JsonValue / Mapping[str, object] → converter.
```
