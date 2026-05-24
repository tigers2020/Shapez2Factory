# Operation: Stacker / Combiner

## shapez 1 Wiki-Style Summary

- Combines two input shapes.
- If both can sit **side by side in the same layer**, they **fuse/merge** on that layer.
- Otherwise one shape is **stacked on top of** the other.
- Descriptions say **at most 4 layers** are kept and excess layers are **dropped** (reconfirm on game board/patch).

## Solver Signature (Conceptual)

```text
stack(bottom, top) -> combined_shape
```

## Shapez 2 Role Names

Shapez 2 often uses **bottom / top** for inputs. Modeling as **left/right** in solver/graph can misalign wiring and demand — prefer **bottom·top** ([shapez2_stacker_inputs.md](shapez2_stacker_inputs.md)).

## Example: Same-Layer Merge (Empty Quadrants)

```text
A = Rc------     # NE only
B = --Cu----     # SE only

stack(A, B) -> RcCu----   # merge on same layer
```

## Example: Layer Increase on Quadrant Collision

```text
A = Rc------
B = Cu------

stack(A, B) -> Rc------:Cu------   # same quadrant collision → upper layer
```

## Sources and Trust

- shapez 1 Stacker wiki: **Medium–High**.
- Details like "drop excess layers" may vary by **version/game** — tests needed.
