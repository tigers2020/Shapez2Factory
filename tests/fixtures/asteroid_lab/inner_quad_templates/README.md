# Inner quad template fixtures

Frozen `SHAPEZ2-4-*` island blueprints for Asteroid Lab **inner placement canon** (cycle N: doc + decode only).

| File | Family | Role |
| --- | --- | --- |
| `T1.shapez.txt` | T | solo miner + lift |
| `T2.shapez.txt` | T | 3 miners + triple merger + lift |
| `T3.shapez.txt` | T | 2 miners + left merger + lift |
| `T4.shapez.txt` | T | 2 miners + Y merger + lift |
| `Q1.shapez.txt` | Q | minimal quad tile |
| `Q2.shapez.txt` | Q | small quad tile |
| `Q3.shapez.txt` | Q | medium quad tile |
| `Q4.shapez.txt` | Q | large quad tile |

Contract: [`documents/game_rules/shapez2_asteroid_inner_quad_templates.md`](../../../../documents/game_rules/shapez2_asteroid_inner_quad_templates.md)

Regression: `tests/unit/asteroid_lab/test_inner_quad_template_decode.py`

**Not** golden oracle input. **Not** wired into L5 solver until a later cycle.
