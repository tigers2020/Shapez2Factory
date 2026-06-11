# Recipe Graph Path Bottleneck Report

Written: 2026-05-04  
Scope: paths that validate and recompute `graph_document` (`recompute_graph_document`) and staff API/views that call them.  
Evidence: static code analysis, `cProfile` hotspots (large chain document, many operations scenario), call-site tracing.

---

## 1. Summary

| Priority | Area | Nature |
|----------|------|------|
| High | `validate_graph_document` → `copy.deepcopy` | full document deep copy on every `recompute` and many API calls |
| High | **Double validation** in staff recompute API | `validate_graph_document` then `recompute_graph_document` validates again internally → 2× `deepcopy` |
| High | `apply_operation` → `parse_shape` → `shapez_core` parser | per-operation input `shape_code` string parsing (duplicate when same code repeats) |
| Medium | repeated `OperationEngine()` creation in `operation_semantics` | new engine instance per branch for `rotate`/`cut`/`swap` etc. |
| Medium | `assert_recipe_graph_edge_topology` | per-edge node lookup and rule checks `O(E)` (included in validation) |
| Medium | `_operation_dep_pairs_from_shape_links` | per-shape producer×consumer transpose (can explode `O(P×C)` with large fan-in/fan-out) |
| Low–medium | `validate_recipe_graph_context` | node walk + per-target family alignment (`explain_pattern_family_mismatch`, etc.) |
| Low | `macro_pattern_staff_api_recipe_graph_recompute` response assembly | `serialize_macro_recipe_visual` may **re-call** inside `enrich_react_flow_with_macro_visual_previews` |
| Low | `graph_cost_hint_from_document` / `try_linear_operation_sequence` | linear node-list scan level |

---

## 2. Items confirmed by measurement (recompute loop)

Running `cProfile` (cumtime) on many repetitions of `recompute_graph_document` against a linear chain `graph_document` with ~120 operations, **before optimization** showed at top:

- `index_recipe_graph_nodes_by_id` (duplicate calls per operation and input sort)
- `_sorted_input_codes_for_operation` + full edge scan
- `_output_edges_for_operation` (full edge scan per operation)

→ mitigated in `recipe_graph_recompute.py` via **edge adjacency list and `node_by_id` reuse**.

**After optimization**, same scenario still dominated by:

- `deepcopy` on `validate_graph_document` path
- `apply_operation` → `parse_shape` / `shape_code_parser`

---

## 3. Path details

### 3.1 Inside `recompute_graph_document`

File: `django_apps/shapez_solver/services/recipe_graph_recompute.py`

1. **`validate_graph_document(doc)`** (always once)  
   - `copy.deepcopy(raw)`: time and memory `O(|nodes|+|edges|)` proportional to document size.  
   - node/edge format checks, `assert_recipe_graph_edge_topology`, `assert_delivery_targets_unique`.

2. **`index_recipe_graph_nodes_by_id(nodes)`**  
   - `O(N)`. no longer repeated per operation inside recompute loop.

3. **`_operation_dependency_edges`**  
   - one edge pass + `_operation_dep_pairs_from_shape_links`.  
   - dependency pair count can grow on irregular graphs with many producers/consumers on same intermediate.

4. **`_topological_operation_order`**  
   - typically `O(|ops| + |dep_pairs|)`.

5. **`_edge_adjacency`**  
   - `O(E)` once.

6. **Operation loop**  
   - input code sort: proportional to that operation’s input edge count (removed per-op full `E` scan).  
   - output edge sort: proportional to that operation’s output edge count.  
   - **`_apply_recomputed_operation` → `apply_operation`**: bottleneck candidate (see 3.3).

7. **`_apply_delivery_edges`**  
   - linear in delivery edge count. duplicate indexing removed via `node_by_id` argument.

### 3.2 HTTP: staff graph recompute API

File: `django_apps/web/views.py` — `macro_pattern_staff_api_recipe_graph_recompute`

Flow summary:

1. `validate_graph_document(...)` (client payload) → **`deepcopy` once**
2. `recompute_graph_document(validated)` → internally **`validate_graph_document` again** → **2nd `deepcopy`** (same logical document back-to-back)

Additionally in same request roughly:

- `serialize_macro_recipe_visual(doc)`
- `validate_recipe_graph_context(...)`
- `graph_cost_hint_from_document(doc)` / `try_linear_operation_sequence(doc)`
- `domain_graph_to_react_flow(doc)`
- `enrich_react_flow_with_macro_visual_previews(react_flow, doc)` → internally **`serialize_macro_recipe_visual(graph_doc)` again**

→ validation, visualization, and serialization can overlap in one UI response.

### 3.3 `apply_operation` / `OperationEngine` instantiation

File: `django_apps/shapez_solver/services/operation_semantics.py`

- most branches call `parse_shape(shape_code)` for string → `Shape` conversion.
- **`OperationEngine()` created fresh** on each call for `rotate`, `cut`, `swap`, `stack`, etc.  
  - allocation/init cost accumulates across operation count×calls (one reason rotate stood out in profiles).

Parser/domain logic: `django_apps/shapez_core/services/shape_code_parser.py`, `shape_codec.py`, etc.

### 3.4 Validation & topology

File: `django_apps/shapez_solver/services/recipe_graph_topology.py`

- `assert_recipe_graph_edge_topology`: one node index + edges `O(E)`.
- `assert_delivery_targets_unique`: delivery edges `O(E)`.

### 3.5 Pattern macro step extraction

`try_pattern_macro_step_rows_from_graph_document`:  
one `validate_graph_document` (or prior validation on macro path) + similar topo/adjacency build. linear in edge/node scale.

### 3.6 Other `validate_graph_document` call sites

- on `macro_recipe_staff_catalog` save  
- `macro_recipe_graph_visual` (`document_to_solver_graph`, etc.)  
- GET graph page: `macro_pattern_graph` runs `validate_graph_document` + `domain_graph_to_react_flow` + `enrich_...`

Each can incur `deepcopy` cost.

---

## 4. Already mitigated bottlenecks (reference)

- removed **full edge iteration** in operation loop (`_edge_adjacency`, `_sorted_output_edges_for_operation`).
- removed **rebuilding `index_recipe_graph_nodes_by_id` per operation** in `_sorted_input_codes_for_operation`.
- removed **unnecessary node index rebuild** in `_apply_delivery_edges`.

---

## 5. Recommended follow-ups (priority)

1. **`recompute_graph_document` entry**: overload or “skip copy” option accepting dict already passed `validate_graph_document` (design with call contract, security, tamper prevention).  
2. **Staff API**: adjust call order so `validate` runs once only (internal-only `recompute` path).  
3. **Parse cache**: within one `recompute` call, cache `shape_code` → parse result (or canonical).  
4. **`OperationEngine`**: module-level singleton or reuse (after thread-safety check).  
5. **Response assembly**: pass `serialize_macro_recipe_visual` result into `enrich_*` to avoid duplicate work.  
6. **Rare worst case**: revisit domain constraints or algorithm for `_operation_dep_pairs_from_shape_links` explosion graphs.

---

## 6. Related file list

| File | Role |
|------|------|
| `django_apps/shapez_solver/services/recipe_graph_recompute.py` | validation, recompute, pattern step extraction |
| `django_apps/shapez_solver/services/recipe_graph_topology.py` | edge topology, indexing |
| `django_apps/shapez_solver/services/operation_semantics.py` | `apply_operation`, parsing, engine calls |
| `django_apps/shapez_core/services/shape_code_parser.py` | shape code parsing |
| `django_apps/web/views.py` | staff graph API, pages |
| `django_apps/shapez_solver/services/macro_recipe_graph_visual.py` | visual graph, React Flow enrichment |
| `django_apps/shapez_solver/services/recipe_graph_recipe_validation.py` | family context validation |

---

End of document.
