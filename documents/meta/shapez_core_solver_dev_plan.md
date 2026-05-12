# Shapez Solver Core Development Plan

## 0. Architecture Correction

This feature must **not** be modeled as a gallery feature.

The shape code data, official shape/color definitions, parser, validator, normalized representation, and solver-facing data model are **core domain assets**. A gallery or visual page may exist later, but it should only consume core data.

## 1. Final Architecture Decision

### Correct ownership

| Concern | Owner | Reason |
|---|---|---|
| Official shape codes | `shapez_core` | Solver depends on these definitions |
| Official color codes | `shapez_core` | Solver and renderers both require canonical colors |
| Shape code parser | `shapez_core` | Must be reusable by solver, admin, tests, and API |
| Shape code validator | `shapez_core` | Invalid codes must be rejected before solving |
| Normalized pattern model | `shapez_core` | Solver should not parse raw strings repeatedly |
| MySQL master data | `shapez_core` | Persistent canonical reference data |
| Django Admin management | `shapez_core.admin` | Admin edits core data, but does not own the domain |
| Three.js glTF viewer | `web/static` | Browser rendering concern |
| Solver algorithms | `shapez_solver` | Uses normalized core pattern data |
| Gallery / viewer page | `web` | Optional presentation layer only |

## 2. Recommended Django App Split

```text
django_apps/
  shapez_core/
    __init__.py
    models.py
    admin.py
    apps.py

    domain/
      __init__.py
      constants.py
      dataclasses.py
      grammar.py

    services/
      __init__.py
      parser.py
      validator.py
      normalizer.py
      serializers.py
      render_scene_serializer.py

    management/
      commands/
        seed_shapez_masterdata.py

    tests/
      test_parser.py
      test_validator.py
      test_masterdata.py

  shapez_solver/
    __init__.py
    models.py
    admin.py
    apps.py

    services/
      __init__.py
      solver.py
      operation_graph.py
      cost_model.py
      recipe_search.py

    tests/
      test_solver_inputs.py
      test_operation_graph.py

  web/
    views.py
    urls.py
    templates/
      web/
        pattern_inspector.html
        solve_detail.html
    static/
      web/
        js/
          shape3d.js
```

## 3. Core Domain Scope

`shapez_core` is responsible for converting official Shapez shape codes into solver-ready data.

### Core input

```text
[SuSuSuSu]
[RuRuRuRu, WrCrRgSy]
RuRuRuRu:WrCrRgSy
```

### Core output

```json
{
  "patterns": [
    {
      "patternIndex": 0,
      "layers": [
        {
          "layerIndex": 0,
          "quadrants": [
            {
              "quadrantIndex": 0,
              "position": "NE",
              "shapeCode": "S",
              "shapeName": "Star",
              "colorCode": "u",
              "colorName": "Uncolored",
              "rawToken": "Su"
            }
          ]
        }
      ]
    }
  ]
}
```

The solver must consume this normalized object, not raw shape code strings.

## 4. Official Shape Master Data

### ShapePartType

| Field | Type | Purpose |
|---|---|---|
| `code` | `CharField(unique=True)` | Official shape code |
| `name` | `CharField` | Canonical name |
| `display_name` | `CharField` | UI label |
| `is_colorable` | `BooleanField` | Whether color code is allowed |
| `is_empty` | `BooleanField` | Whether this represents empty quadrant |
| `is_quad_supported` | `BooleanField` | Whether usable in quadrant shape code |
| `is_hex_supported` | `BooleanField` | Whether usable in hex shape code |
| `three_mesh_kind` | `CharField` | Renderer mesh mapping |
| `solver_kind` | `CharField` | Solver primitive mapping |
| `sort_order` | `PositiveSmallIntegerField` | Admin ordering |
| `is_active` | `BooleanField` | Enable/disable without deleting |

Recommended initial rows:

| Code | Name | Solver Kind |
|---|---|---|
| `C` | Circle | `circle` |
| `R` | Rectangle / Square | `rectangle` |
| `S` | Star / Spike | `spike` |
| `W` | Diamond | `diamond` |
| `c` | Crystal | `crystal` |
| `P` | Pin | `pin` |
| `-` | Empty | `empty` |

### ShapeColor

| Field | Type | Purpose |
|---|---|---|
| `code` | `CharField(unique=True)` | Official color code |
| `name` | `CharField` | Canonical color name |
| `hex_color` | `CharField(max_length=7)` | UI/rendering color |
| `solver_color` | `CharField` | Solver color enum |
| `is_empty` | `BooleanField` | Represents no color |
| `sort_order` | `PositiveSmallIntegerField` | Admin ordering |
| `is_active` | `BooleanField` | Enable/disable without deleting |

Recommended initial rows:

| Code | Name |
|---|---|
| `u` | Uncolored |
| `r` | Red |
| `g` | Green |
| `b` | Blue |
| `c` | Cyan |
| `m` | Magenta |
| `y` | Yellow |
| `w` | White |
| `-` | Empty |

## 5. Core Pattern Data Model

### ShapePattern

This should be a **core pattern entity**, not a gallery card.

| Field | Type | Purpose |
|---|---|---|
| `title` | `CharField` | Human-readable name |
| `code` | `CharField` | Raw user/input code |
| `normalized_code` | `CharField` | Canonical code after normalization |
| `description` | `TextField` | Notes |
| `source` | `CharField(choices=...)` | Manual, wiki, game, generated, solver |
| `parsed_json` | `JSONField` | Cached normalized representation |
| `parse_error` | `TextField` | Last parser/validator error |
| `is_solver_available` | `BooleanField` | Can be used as solver input |
| `created_at` | `DateTimeField` | Audit |
| `updated_at` | `DateTimeField` | Audit |

### ShapePatternPart

This is the normalized relational form used by solver queries.

| Field | Type | Purpose |
|---|---|---|
| `pattern` | `ForeignKey(ShapePattern)` | Parent pattern |
| `pattern_index` | `PositiveSmallIntegerField` | Index inside bracket list |
| `layer_index` | `PositiveSmallIntegerField` | Bottom-to-top layer order |
| `quadrant_index` | `PositiveSmallIntegerField` | NE/SE/SW/NW order |
| `position` | `CharField(choices=...)` | `NE`, `SE`, `SW`, `NW` |
| `part_type` | `ForeignKey(ShapePartType)` | Canonical shape primitive |
| `color` | `ForeignKey(ShapeColor)` | Canonical color |
| `raw_token` | `CharField(max_length=2)` | Original token |

Recommended unique constraint:

```python
unique_together = [
    ("pattern", "pattern_index", "layer_index", "quadrant_index"),
]
```

## 6. Parser / Validator Rules

### Grammar

```text
shape_code_list := "["? shape_pattern ("," shape_pattern)* "]"?
shape_pattern   := shape_layer (":" shape_layer)*
shape_layer     := token token token token
token           := shape_code color_code
```

### Quadrant order

```text
SW -> NW -> NE -> SE
```

### Layer order

```text
bottom -> top
```

### Recommended semantics

| Syntax | Meaning |
|---|---|
| `[SuSuSuSu]` | One pattern |
| `[RuRuRuRu, WrCrRgSy]` | Two independent patterns |
| `RuRuRuRu:WrCrRgSy` | One stacked multi-layer pattern |
| `--` | Empty quadrant |

### Hard validation

| Case | Result |
|---|---|
| Unknown shape code such as `A` | Reject |
| Unknown color code | Reject |
| Non-empty shape with empty color `-` | Reject |
| Empty shape `-` with non-empty color | Reject |
| Wrong layer length | Reject |
| Empty input | Reject |
| Mixed invalid bracket syntax | Reject |

## 7. Solver Integration

The solver must receive normalized `ShapePattern` or `ShapePatternPart` data.

### Solver-facing DTO

```python
@dataclass(frozen=True)
class SolverQuadrant:
    position: str
    shape_kind: str
    color_kind: str

@dataclass(frozen=True)
class SolverLayer:
    index: int
    quadrants: tuple[SolverQuadrant, ...]

@dataclass(frozen=True)
class SolverPattern:
    code: str
    layers: tuple[SolverLayer, ...]
```

### Solver service entrypoint

```python
def solve_target_pattern(pattern: ShapePattern) -> SolveResult:
    solver_pattern = build_solver_pattern(pattern)
    return solver.solve(solver_pattern)
```

### Solver should not do this

```python
# Bad
solve("RuRuRuRu:WrCrRgSy")
```

### Solver should do this

```python
# Good
pattern = ShapePattern.objects.get(...)
solve_target_pattern(pattern)
```

## 8. Admin Usage Plan

Admin should be treated as the main internal control panel.

### ShapePartTypeAdmin

Features:

```text
[ ] List shape codes
[ ] Edit display name
[ ] Edit renderer mesh kind
[ ] Edit solver kind
[ ] Enable/disable shape code
[ ] Search by code/name
[ ] Filter by active/colorable/empty
```

### ShapeColorAdmin

Features:

```text
[ ] List color codes
[ ] Show color swatch
[ ] Edit hex color
[ ] Edit solver color mapping
[ ] Enable/disable color
[ ] Search by code/name
```

### ShapePatternAdmin

Features:

```text
[ ] Create/edit raw shape code
[ ] Auto-parse on save
[ ] Store normalized code
[ ] Store parsed JSON
[ ] Store relational parts
[ ] Display parse errors
[ ] Inline ShapePatternPart view
[ ] Action: rebuild selected patterns
[ ] Action: mark solver-available
[ ] Action: mark solver-disabled
[ ] Three.js glTF preview
```

## 9. MySQL Plan

### Database

```text
database: shapez_solver
charset: utf8mb4
collation: utf8mb4_unicode_ci
```

### Django settings

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "shapez_solver",
        "USER": "shapez_user",
        "PASSWORD": "your_password",
        "HOST": "127.0.0.1",
        "PORT": "3306",
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}
```

### Recommended package

```bash
pip install mysqlclient
```

## 10. Rendering Layer

Rendering must not own the domain model.

### Three.js glTF Viewer

Recommended owner:

```text
django_apps/web/static/web/js/shape_gltf_viewer.js
```

Purpose:

```text
[ ] Interactive browser preview
[ ] Mouse rotation
[ ] Zoom
[ ] Pan
[ ] Debug solver target shape visually
```

The 3D viewer consumes JSON generated from core data.

It must not parse official shape code by itself.

## 11. Web Pages

Rename the previous “gallery” concept.

Recommended page names:

| Old | New | Reason |
|---|---|---|
| Gallery | Pattern Inspector | This is a solver data inspection tool |
| Gallery Detail | Pattern Detail | Shows canonical pattern data |
| 3D Gallery Viewer | Pattern 3D Preview | Debug/preview purpose |
| Gallery Notes | Pattern Metadata | Domain-focused terminology |

### Suggested URLs

```python
urlpatterns = [
    path("patterns/", views.pattern_list, name="pattern_list"),
    path("patterns/<int:pk>/", views.pattern_detail, name="pattern_detail"),
    path("solve/", views.solve_index, name="solve_index"),
    path("solve/<int:pattern_id>/", views.solve_pattern, name="solve_pattern"),
]
```

## 12. Flowbite / Tailwind Position

Flowbite is still acceptable, but only as a UI utility.

It should not influence domain structure.

### Keep

```css
@plugin "flowbite/plugin";
@source "../../node_modules/flowbite";
```

### Avoid for now

```css
@import "flowbite/src/themes/default";
```

Reason:

```text
[ ] Existing slate/cyan UI stays stable
[ ] Admin/domain functionality is more important than redesign
[ ] Flowbite JS can support accordion/modal/dropdown only
```

## 13. Testing Plan

### Core tests

```text
[ ] Valid code parses
[ ] Invalid shape code `A` rejects
[ ] Invalid color rejects
[ ] Layer length validation
[ ] Empty quadrant validation
[ ] Multi-layer parsing
[ ] Pattern-list parsing
[ ] Normalized code output
[ ] ShapePatternPart rebuild
[ ] Seed command creates master data
```

### Solver integration tests

```text
[ ] Solver receives normalized pattern
[ ] Solver rejects pattern with parse_error
[ ] Solver does not parse raw string directly
[ ] Solver handles multiple layers
[ ] Solver handles empty quadrant
```

### Admin smoke tests

```text
[ ] ShapePartType admin loads
[ ] ShapeColor admin loads
[ ] ShapePattern admin loads
[ ] Pattern save triggers parse
[ ] Invalid pattern stores parse_error
[ ] Rebuild admin action works
```

### Web tests

```text
[ ] Pattern inspector page loads
[ ] Pattern detail page includes normalized data
[ ] 3D viewer JSON exists
[ ] Flowbite JS loads if used
```

## 14. Phase Plan

### Phase 1 — Core foundation

```text
[ ] Create shapez_core app
[ ] Add ShapePartType model
[ ] Add ShapeColor model
[ ] Add ShapePattern model
[ ] Add ShapePatternPart model
[ ] Add migrations
[ ] Add MySQL settings
[ ] Add seed_shapez_masterdata command
[ ] Register admin pages
```

Exit criteria:

```text
[ ] MySQL tables created
[ ] Master data seeded
[ ] Admin can view/edit shape and color definitions
```

### Phase 2 — Parser and validator

```text
[ ] Implement grammar parser
[ ] Implement DB-backed validation
[ ] Implement normalized code output
[ ] Implement parsed JSON output
[ ] Implement ShapePatternPart rebuild service
[ ] Auto-parse on admin save
```

Exit criteria:

```text
[ ] `A` is rejected
[ ] `[SuSuSuSu]` parses
[ ] `[RuRuRuRu, WrCrRgSy]` parses
[ ] `RuRuRuRu:WrCrRgSy` parses as stacked layer pattern
```

### Phase 3 — Solver interface

```text
[ ] Add solver DTOs
[ ] Add build_solver_pattern service
[ ] Add solve_target_pattern entrypoint
[ ] Add placeholder SolveResult model or dataclass
[ ] Add tests proving solver consumes normalized data
```

Exit criteria:

```text
[ ] Solver can receive core pattern object
[ ] Solver no longer depends on raw code parsing
```

### Phase 4 — Preview and inspection

```text
[ ] Add Pattern Inspector page
[ ] Add Pattern Detail page
[ ] Add viewer JSON endpoint or template JSON
[ ] Add Three.js glTF viewer
[ ] Add OrbitControls rotation
```

Exit criteria:

```text
[ ] Admin or web page can preview pattern visually
[ ] 3D viewer rotates with mouse
[ ] Viewer consumes normalized JSON from core
```

### Phase 5 — Solver workflow

```text
[ ] Add solve page
[ ] Select target ShapePattern from DB
[ ] Run solver
[ ] Display operation result
[ ] Display cost/steps
[ ] Link result back to pattern detail
```

Exit criteria:

```text
[ ] User can choose a pattern and run solve
[ ] Result is tied to canonical core pattern data
```

## 15. Task Breakdown

| ID | Task | Owner Layer | Priority |
|---|---|---:|---:|
| CORE-001 | Create `shapez_core` app | Core | P0 |
| CORE-002 | Add master data models | Core | P0 |
| CORE-003 | Add pattern models | Core | P0 |
| CORE-004 | Add seed command | Core | P0 |
| CORE-005 | Add DB-backed parser | Core | P0 |
| CORE-006 | Add validator | Core | P0 |
| CORE-007 | Add normalization service | Core | P0 |
| CORE-008 | Add `ShapePatternPart` rebuild service | Core | P0 |
| ADMIN-001 | Register shape/color admin | Admin | P0 |
| ADMIN-002 | Register pattern admin | Admin | P0 |
| ADMIN-003 | Add rebuild admin action | Admin | P1 |
| SOLVER-001 | Define solver DTOs | Solver | P0 |
| SOLVER-002 | Add solver input builder | Solver | P0 |
| SOLVER-003 | Add placeholder solver service | Solver | P1 |
| RENDER-001 | Add ShapeRenderScene contract | Rendering | P1 |
| RENDER-002 | Add Three.js glTF viewer | Web | P1 |
| WEB-001 | Rename gallery to pattern inspector | Web | P0 |
| WEB-002 | Add pattern detail page | Web | P1 |
| TEST-001 | Parser tests | Test | P0 |
| TEST-002 | Admin smoke tests | Test | P1 |
| TEST-003 | Solver input tests | Test | P0 |

## 16. MVP Acceptance Criteria

```text
[ ] Official shape/color codes live in MySQL
[ ] Admin can manage shape/color master data
[ ] Admin can create ShapePattern
[ ] ShapePattern save validates code
[ ] Invalid `A` code is rejected or stored as parse_error
[ ] Valid pattern creates ShapePatternPart rows
[ ] Solver receives normalized pattern object
[ ] Web page can inspect pattern
[ ] 2D preview works
[ ] 3D preview can rotate with mouse
```

## 17. Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Shapez code grammar changes | Parser breaks | Keep master data seed versioned |
| Solver parses raw strings directly | Duplication and bugs | Enforce DTO boundary |
| Web viewer owns parsing logic | Domain drift | JS consumes normalized JSON only |
| Admin edits break official data | Invalid solver behavior | Add validation and active flags |
| Flowbite theme changes UI unexpectedly | Visual regression | Do not import global Flowbite theme yet |
| MySQL migration friction | Setup delay | Keep SQLite-compatible tests where possible |

## 18. Final Recommendation

The previous “gallery” framing should be replaced.

Correct naming:

```text
shapez_core = official data + parser + validator + normalized pattern
shapez_solver = solving logic
web = pattern inspector / preview UI
admin = management surface for core data
```

The data is solver-critical. Therefore, it belongs in `shapez_core`, not `web/gallery`.

The gallery concept can still exist later, but only as a read-only or user-facing view over core pattern data.
