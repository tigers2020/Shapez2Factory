# Solver Quantity: Needed on Edges and Plans, Not Just Nodes

## Common Mismatch Symptom

```text
Demand summary says 1:1:2 but graph shows 1:1:1
```

## Typical Causes

1. Source node quantity changed but **edge demand** not updated
2. Operation output **multiplicity** not reflected in graph
3. `target_count` etc. reset to 1 during **materialized graph generation**
4. **Shape identity** aggregation and **quantity aggregation** not separated

## Recommended Model Sketch

```python
# Conceptual example — align field names with project DTOs
Node:
    shape_code
    node_type
    display_quantity

Edge:
    quantity
    throughput   # or per-time throughput, etc.
    role: input | output | top | bottom | east | west   # building/port semantics
```

## Related

- Avoid confusing graph UI with summary numbers: [documents/ai/manuals/graph_ui.md](../ai/manuals/graph_ui.md)
- [solver_graph_dag.md](solver_graph_dag.md)
