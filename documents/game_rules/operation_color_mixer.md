# Operation: Color Mixer (Liquid Mixing)

## General Rules (Conceptual)

Combines color liquids to produce new colors. Examples:

```text
red + green = yellow
red + blue = magenta
green + blue = cyan
red + green + blue = white
```

## Solver Design Recommendation

Do not mix with layer/quadrant shape operations; prefer separating as **paint resource dependency**:

- Shape transform function: `Shape -> Shape`
- Color liquid pipes: separate graph/quantity model for **which base/intermediate colors and how many units**

This keeps boundaries clear between "shape solver" and "ink supply solver".

## Sources and Trust

- Color mix tables are commonly cited in community guides, but **exact in-game recipes** should be verified by play or data extraction.
