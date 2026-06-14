# Manual: Typing Contracts · Wire Boundaries

Process authority: [`AGENTS.md`](../../../AGENTS.md).  
Design spec: [`documents/superpowers/specs/2026-06-11-any-boundary-typing-design.md`](../../../documents/superpowers/specs/2026-06-11-any-boundary-typing-design.md).

**Canon path for this manual:** `documents/ai/manuals/typing_contracts.md` (not `documents/knowledge/raw/...`).

**Layer guide (Any vs object vs TypedDict vs dataclass):** [`typing_boundary_layers.md`](typing_boundary_layers.md)

Related (legacy mirror paths until migrated):

- [`django.md`](../../knowledge/raw/ai/manuals/django.md) — Django app ownership
- [`solver.md`](../../knowledge/raw/ai/manuals/solver.md) — solver layer boundaries
- [`2026-06-10-solver-runtime-wires-replay-projection-design.md`](../../knowledge/raw/docs-superpowers/specs/2026-06-10-solver-runtime-wires-replay-projection-design.md) — runtime wire authority

---

## Purpose

This manual defines **where `typing.Any` is allowed**, **how wire JSON is typed**, and **who owns schema authority** at serialization boundaries.

The repo’s `Any` problem is primarily **wire contract drift**, not missing hints in solver core logic.

---

## Core rules

```text
Semantic authority is frozen dataclass.
Wire authority is named TypedDict.
Raw dict[str, Any] is allowed only at explicit decode/import boundaries.
Converters are the only legal path between semantic DTOs and wire dictionaries.
```

---

## Shared types

Module: `django_apps/asteroid_lab/typing_boundary.py`

```python
type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]

# typing_contracts: validated generic JSON object after json.loads narrow
type RawJsonObject = JsonObject
```

Implementation may use Python 3.12 `type` alias syntax where ruff UP040 prefers it over `TypeAlias`.

| Alias | Meaning |
|-------|---------|
| `RawJsonObject` | Unvalidated input immediately after `json.loads` or game-data import |
| `JsonValue` | Validated generic JSON tree (no named schema yet) |
| Named `TypedDict` | Named wire contract for a specific payload |
| `frozen dataclass` | In-process semantic authority |

Promote aliases to `shapez2_factory/` only when multiple packages share them.

---

## Allowed `Any`

Use **only** with an explicit comment referencing this manual:

```python
# typing_contracts: raw game-data JSON before schema normalization
def load_raw_manifest(data: RawJsonObject) -> GameDataManifestWire:
    ...
```

| Case | Example |
|------|---------|
| Raw JSON decode before normalization | Importers, `json.loads` entry |
| Third-party untyped boundary | Django admin hooks, ORM edge cases |
| Temporary migration shim | Must name removal slice in PR |
| Tests — intentionally loose fixtures | `tests/` only; annotate in test module |

---

## Forbidden `Any`

After validation or at public contract surfaces:

| Surface | Required type |
|---------|---------------|
| Replay wire after validation | Named `TypedDict` + converter |
| DTO public fields (`service_dtos`, `timeline_dtos`) | `frozen dataclass`; wire fields use named `*Wire` types |
| Solver-facing input | Strict domain/application DTOs (`src/` mypy strict) |
| Artifact persistence contract | Named wire types in serialize/deserialize modules |
| UI effective-cell read model | `EffectiveCellView` + `EffectiveCellWire` |

---

## Boundary schema style

### In-process (semantic)

- Use `@dataclass(frozen=True, slots=True)` for replay, service, and UI read models.
- Semantic field renames happen here first, with contract tests.

### Wire (JSON projection)

- Use **named** `TypedDict` types (`ReplayOverlayCellWire`, `EffectiveCellWire`, …).
- TypedDict is **not** a second domain model — projection contract only.

### TypedDict optional fields

```text
TypedDict must be total=True by default.
Use NotRequired[...] for optional wire keys.
Use total=False only for explicitly documented extension/patch payloads.
```

### Converters

All dataclass ↔ wire conversions pass through **named functions** in converter modules (`*_serialization.py`, `overlay_wire_contract.py`, etc.).

```python
# REQUIRED
wire = overlay_cell_to_wire_dict(cell)

# FORBIDDEN at call sites
wire = {"x": cell.x, "y": cell.y, "kind": cell.kind}
```

---

## Authority map (Asteroid Lab replay)

| Component | Owns |
|-----------|------|
| `timeline_dtos.py` | Semantic replay frame types |
| `timeline_serialization.py` | Wire TypedDict + deserialize validation |
| `overlay_wire_contract.py` | Overlay occupancy vs `output_transport_kind` |
| `lab_timeline_adapter.py` | Assembler projection (no hand-built wire dicts) |
| `effective_cell_view.py` | UI merged cell read model |
| `runtime_wires/serialize|deserialize` | Solver output wire (replay-projection-only) |
| `solver_run_config_keys.py` | Stable `config_json` key names |

Runtime wire is **forbidden** as algorithm input (placement, routing, validation, recovery).

---

## Migration patterns

### Adding a new wire type

1. Add `FooWire` TypedDict in `*_wire.py` or next to converter.
2. Add `foo_to_wire(dto) -> FooWire` and `foo_from_wire(raw) -> FooDTO`.
3. Replace `dict[str, Any]` return/params at module boundary.
4. Add round-trip or reject-invalid unit tests.

### Deprecating inline wire builders

Example: `EffectiveCellView.to_wire()` → external converter.

```text
1. Add effective_cell_to_wire(view) -> EffectiveCellWire
2. Migrate call sites
3. Remove to_wire() in a follow-up slice
```

---

## mypy rollout (phased)

Full command (target): `mypy django_apps config src`

Current phased order:

```text
src/                              strict (existing)
django_apps/asteroid_lab/replay/  strict (first expansion)
wire-related services modules     strict (second)
remaining django_apps/, config/   report-only until green
```

Do not expand CI hard gate until boundary modules pass strict checks. See SHA-20.

---

## Review checklist (PR)

- [ ] No new `dict[str, Any]` on forbidden surfaces without manual exception comment
- [ ] Wire shapes use named TypedDict, not bare dict
- [ ] Converters are the only dataclass ↔ wire path
- [ ] TypedDict uses `total=True` unless extension payload is documented
- [ ] Tests cover deserialize reject + round-trip where wire changed
- [ ] Success judged by contract safety, not `Any` count delta

---

## Ban-test scope (when enabled)

Exact paths verified in Phase 0 inventory (2026-06-11):

```text
django_apps/asteroid_lab/replay/          (package; converter modules exempt)
django_apps/asteroid_lab/replay/effective_cell_view.py
django_apps/asteroid_lab/services/        (replay compose / timeline paths only)
django_apps/web/services/replay_frame_cell_lookup.py
```

Replay overlay wire uses `x` / `y` and optional `layer` (height). No `z` key.

**Allow:**

```text
tests/, tests/support/
raw JSON decode/import modules (annotated exception)
typing_boundary.py
*_serialization.py and named converter modules
```
