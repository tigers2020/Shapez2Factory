# UI UX Pro Max — Theme Mapping (shapez2 Factory Planner)

> **Created:** 2026-06-13  
> **Authority:** `DESIGN.md` wins over skill recommendations  
> **Skill CLI:** `.cursor/skills/ui-ux-pro-max/scripts/search.py`

---

## Summary

| Skill domain | Project decision |
|--------------|------------------|
| Styles | Use **Dark Mode (OLED)**, **Motion-Driven**, **Minimal Dark Dashboard** patterns; adapt accent to `#22D3EE` |
| Colors | Map **Developer Tool / IDE** palette to `DESIGN.md`; reject light SaaS palettes |
| Typography | **Google Sans Code** (canon) — ignore skill JetBrains/IBM Plex unless user approves |
| Components | Global `pro-max-*` in `assets/css/ui-ux-pro-max-themes.css`; lab-specific stays `lab-*` in `input.css` |

---

## Style mapping

### Compatible (use with project tokens)

| Skill style | Fit | Project adaptation |
|-------------|-----|-------------------|
| Dark Mode (OLED) | High | bg `#020617` (not pure `#000000`); accent `#22D3EE`; minimal glow only |
| Motion-Driven | Medium | 150–300ms transitions; respect `prefers-reduced-motion` |
| Aurora UI (dark) | Medium | Subtle gradient borders; no light glass cards |
| Vibrant & Block-based (dark variant) | Medium | Large sections OK; colors from DESIGN.md only |
| Cyberpunk UI | Low–Medium | Cyan accent only; skip matrix green / glitch unless scoped |

### Reject or HITL-only

| Skill style | Reason |
|-------------|--------|
| Glassmorphism (light) | Light `bg-white/10` breaks OLED dashboard |
| Neumorphism | Light shadows clash with dark console |
| Light SaaS landing | Background `#F8FAFC` conflicts with `#020617` |
| Bento / horizontal scroll marketing | Marketing layout, not factory console |

---

## Color palette mapping

Skill **Developer Tool / IDE** → `DESIGN.md`:

| Skill field | Skill hex | Project token | Project hex |
|-------------|-----------|---------------|-------------|
| Background | `#0F172A` | surface | `#0F172A` ✓ |
| Primary | `#1E293B` | secondary | `#1E293B` ✓ |
| Secondary | `#334155` | — | use `#1E293B` + border opacity |
| CTA | `#22C55E` | success (lab CTA) | `#34D399` / lab `--lab-cta` `#22c55e` |
| Text | `#F8FAFC` | on-surface | `#F1F5F9` |
| Accent (skill N/A) | — | border-accent | `#22D3EE` |

**Conflicts logged:**

| Skill recommendation | Conflict | Resolution |
|---------------------|----------|------------|
| `--design-system` typography: JetBrains Mono / IBM Plex Sans | `DESIGN.md` mandates Google Sans Code | Keep Google Sans Code; Fira Code for mono blocks |
| Micro SaaS palette `#F5F3FF` bg | Light background | Reject |
| CTA green `#22C55E` vs success `#34D399` | Lab uses both intentionally | Lab buttons: `--lab-cta`; global success: `#34D399` |

---

## Typography mapping

| Role | Canon (`DESIGN.md`) | Skill alternative | Decision |
|------|---------------------|-------------------|----------|
| Headline / body / label | Google Sans Code | IBM Plex Sans | **Canon** |
| Code / mono | Fira Code | JetBrains Mono | **Canon** (Fira Code) |
| Lab UI sans fallback | Fira Sans (in `#lab-root`) | — | Keep for lab readability |

---

## CSS component strategy

| Prefix | Scope | File |
|--------|-------|------|
| `lab-*` | Asteroid Lab (`#lab-root`) | `assets/css/input.css` (existing) |
| `pro-max-*` | Global Django templates / new UI | `assets/css/ui-ux-pro-max-themes.css` (new) |

Agents: prefer `pro-max-*` for new non-lab pages; never rename existing `lab-*` classes.

---

Persisted overlay: `design-system/shapez2-factory-planner/MASTER.md` (DESIGN.md overrides in § Project overrides).

## Verification queries (repeatable)

```bash
python .cursor/skills/ui-ux-pro-max/scripts/search.py "factory dashboard dark OLED developer tools" --design-system --stack html-tailwind -p "shapez2 Factory Planner"
python .cursor/skills/ui-ux-pro-max/scripts/search.py "dark dashboard developer tools OLED" --domain style -n 8
python .cursor/skills/ui-ux-pro-max/scripts/search.py "developer tools saas dark" --domain color -n 5
```
