# UI Design — shapez2 Factory Planner

Use with `/ui-ux-pro-max` skill and `.cursor/rules/ui-ux-pro-max-skill.mdc`.

## Before coding

1. Read `DESIGN.md` — YAML tokens are the design contract.
2. Run design-system search (required):

```bash
python .cursor/skills/ui-ux-pro-max/scripts/search.py "<page or feature> dark OLED factory dashboard developer tools" --design-system --stack html-tailwind -p "shapez2 Factory Planner"
```

Persisted overlay (reference): `design-system/shapez2-factory-planner/MASTER.md` — **DESIGN.md overrides** per § Project overrides in that file.

3. Optional domain supplements:

```bash
python .cursor/skills/ui-ux-pro-max/scripts/search.py "animation accessibility focus" --domain ux
python .cursor/skills/ui-ux-pro-max/scripts/search.py "dashboard data grid" --stack html-tailwind
```

## Project design contract

**Theme:** Dark OLED factory-console dashboard. No light backgrounds.

| Token | Hex / font |
|-------|------------|
| primary (bg) | `#020617` |
| secondary | `#1E293B` |
| surface | `#0F172A` |
| border-default | `#1E293B` |
| border-accent / accent | `#22D3EE` |
| tertiary | `#06B6D4` |
| success | `#34D399` |
| warning | `#F59E0B` |
| error | `#FB7185` |
| on-surface | `#F1F5F9` |
| on-surface-muted | `#94A3B8` |
| headline / body / label | `Google Sans Code` |
| code / mono | `Fira Code` |

**Stack:** Django templates + Tailwind CSS v4 + Flowbite (mono theme). Entry: `assets/css/input.css`.

## Generation rules

1. **Canon wins** — skill palette/style suggestions must map to `DESIGN.md`; do not invent new brand colors.
2. **Dark only** — reject light-mode-first skill styles unless explicitly scoped.
3. **Tailwind utilities** in templates; shared patterns in `@layer components` inside `input.css` or `pro-max-*` in `assets/css/ui-ux-pro-max-themes.css`.
4. **`lab-*` prefix** — preserve existing asteroid lab classes; extend, do not rename in place.
5. **No emoji icons** — SVG (Heroicons/Lucide). `cursor-pointer` on clickables; 150–300ms transitions.
6. **No layout shift** on hover — color/opacity/shadow only.
7. **Accessibility** — labels, focus rings, keyboard path, `prefers-reduced-motion`.
8. **No business logic** in templates, CSS, or JS — presentation only.

## Skill DB usage (reference only)

Installed at `.cursor/skills/ui-ux-pro-max/` (67 styles, 96 palettes, 57 font pairings).

Prefer dark-compatible styles: Aurora UI, Motion-Driven, minimal dark dashboards.
Avoid blindly applying: Glassmorphism, Neumorphism, light SaaS landing patterns.

Font pairings: only those compatible with **Google Sans Code** as primary.

## Verification before done

```bash
npm run build:css
python manage.py check
```

Manual: asteroid lab layout unchanged unless task explicitly targets it.
Visible changes: `/playwright` snapshot when practical.

## Conflict reporting

If skill `--design-system` output conflicts with `DESIGN.md`, list:

- conflicting field (color / font / style)
- skill recommendation
- chosen project token

Do not merge conflicting values without user approval.
