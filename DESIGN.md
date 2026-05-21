---
version: alpha
name: shapez2 Factory Planner
description: Dark factory-console UI for shape solver, pattern lab, asteroid mining lab, and staff recipe graph tools. YAML tokens are the design contract; Tailwind CSS v4 utility classes in Django templates are the primary implementation.
colors:
  primary: "#020617"
  secondary: "#1E293B"
  tertiary: "#06B6D4"
  neutral: "#F1F5F9"
  surface: "#0F172A"
  on-surface: "#F1F5F9"
  on-surface-muted: "#94A3B8"
  border-default: "#1E293B"
  border-accent: "#22D3EE"
  error: "#FB7185"
  success: "#34D399"
  warning: "#F59E0B"
  semantic-violet: "#A78BFA"
  semantic-violet-deep: "#4C1D95"
  semantic-amber: "#F59E0B"
  semantic-lime: "#84CC16"
  semantic-emerald: "#6EE7B7"
  semantic-rose: "#FB7185"
  staff-amber: "#FCD34D"
  graph-canvas: "#141414"
  graph-node: "#1E1E1E"
typography:
  headline-lg:
    fontFamily: "Google Sans Code"
    fontSize: 36px
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: -0.02em
  headline-md:
    fontFamily: "Google Sans Code"
    fontSize: 24px
    fontWeight: 600
    lineHeight: 1.2
  body-md:
    fontFamily: "Google Sans Code"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
  body-sm:
    fontFamily: "Google Sans Code"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  label-md:
    fontFamily: "Google Sans Code"
    fontSize: 12px
    fontWeight: 600
    lineHeight: 1
    letterSpacing: 0.1em
  label-sm:
    fontFamily: "Google Sans Code"
    fontSize: 10px
    fontWeight: 600
    lineHeight: 1
    letterSpacing: 0.05em
  mono-code:
    fontFamily: "Google Sans Code"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  caption:
    fontFamily: "Google Sans Code"
    fontSize: 11px
    fontWeight: 400
    lineHeight: 1.4
spacing:
  base: 16px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 24px
  margin-page: 32px
  lab-cell-gap: 4px
  nav-py: 12px
  card-pad: 20px
  modal-pad: 20px
rounded:
  none: 0px
  sm: 4px
  md: 8px
  lg: 12px
  xl: 16px
  xxl: 24px
  full: 9999px
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.primary}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.lg}"
    padding: 12px
  button-primary-hover:
    backgroundColor: "#22D3EE"
    textColor: "{colors.primary}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.lg}"
    padding: 12px
  button-ghost-accent:
    backgroundColor: "#06B6D41A"
    textColor: "#A5F3FC"
    rounded: "{rounded.lg}"
    padding: 12px
  button-danger:
    backgroundColor: "#F43F5E26"
    textColor: "#FFE4E6"
    rounded: "{rounded.lg}"
    padding: 10px
  nav-link:
    textColor: "{colors.on-surface-muted}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.md}"
    padding: 8px
  nav-link-active:
    textColor: "#A5F3FC"
  card-feature:
    backgroundColor: "#0F172ACC"
    rounded: "{rounded.xl}"
    padding: 20px
  card-panel:
    backgroundColor: "#020617B3"
    rounded: "{rounded.xl}"
    padding: 16px
  input-text:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.mono-code}"
    rounded: "{rounded.lg}"
    padding: 12px
  modal-shell:
    backgroundColor: "{colors.primary}"
    rounded: "{rounded.xxl}"
    padding: 20px
  modal-scrim:
    backgroundColor: "#000000B3"
  lab-decode-cell:
    backgroundColor: "#4C1D9580"
    rounded: "{rounded.sm}"
  lab-route-goal:
    textColor: "{colors.semantic-violet}"
  lab-route-probe:
    textColor: "{colors.semantic-amber}"
  lab-route-confirmed:
    textColor: "{colors.semantic-lime}"
  lab-timeline-scrub:
    backgroundColor: "{colors.tertiary}"
    rounded: "{rounded.full}"
    height: 28px
  lab-topology-trigger:
    backgroundColor: "#8B5CF61A"
    textColor: "#C4B5FD"
    rounded: "{rounded.xl}"
    padding: 10px
  graph-status:
    textColor: "#FDE68AE6"
    typography: "{typography.body-sm}"
  staff-banner-label:
    textColor: "{colors.staff-amber}"
    typography: "{typography.label-md}"
---

# shapez2 Factory Planner — DESIGN.md

Living design contract for humans and AI agents building UI in this repository.

- **DESIGN.md YAML tokens** — what color, type, and spacing *mean* (portable across tools).
- **Tailwind CSS v4** — how the app *implements* those choices (utility classes in templates).
- **`assets/css/input.css`** — Tailwind entry, Flowbite plugin, and lab-only `@layer components` that cannot be expressed as utilities alone.

When tokens and Tailwind drift, fix both in the same change: adjust classes in templates first, then sync hex values here.

**Spec:** [DESIGN.md format](https://stitch.withgoogle.com/docs/design-md/overview) · [github.com/google-labs-code/design.md](https://github.com/google-labs-code/design.md).

## Tailwind CSS (implementation)

This project styles the Django web app with **Tailwind CSS v4**, not hand-written global CSS pages.

| Piece | Path / command |
|-------|----------------|
| Source entry | `assets/css/input.css` (`@import "tailwindcss"`) |
| Built CSS (committed / served) | `django_apps/web/static/web/css/app.css` |
| Build | `npm run build:css` |
| Watch during UI work | `npm run watch:css` |
| Template scan | `@source "../../django_apps/web/templates"` in `input.css` |
| Components plugin | Flowbite `@plugin "flowbite/plugin"` + `flowbite/src/themes/mono` |
| Loaded in HTML | `web/base.html` → `{% static 'web/css/app.css' %}` |

**Recipe graph editor** bundles its own Tailwind scan via `frontend/recipe_graph_editor` → `recipe-graph-editor.css` (React Flow overrides at bottom of that file). Staff graph pages still use the global `app.css` for shell/nav.

### Token → Tailwind mapping (default palette)

Use these utilities in templates unless this file defines a custom `@layer` class. Opacity modifiers (`/20`, `/80`) are idiomatic Tailwind—keep them when matching existing screens.

| DESIGN token | Tailwind utilities (examples) |
|--------------|----------------------------------|
| `colors.primary` | `bg-slate-950`, `text-slate-950` |
| `colors.surface` | `bg-slate-900`, `bg-slate-900/80` |
| `colors.secondary` | `border-slate-800`, `bg-slate-800` |
| `colors.tertiary` | `bg-cyan-500`, `text-cyan-500`, `accent-cyan-500`, `ring-cyan-500/50` |
| `colors.on-surface` | `text-slate-100` |
| `colors.on-surface-muted` | `text-slate-400`, `text-slate-500` |
| `colors.border-accent` | `border-cyan-400/20`, `border-cyan-400/45` |
| `colors.semantic-violet` | `text-violet-300`, `border-violet-500/30`, `bg-violet-500/10` |
| `colors.semantic-amber` | `text-amber-200`, `text-amber-300/90`, `border-amber-500/40` |
| `colors.semantic-lime` | route glow in CSS (see `lab-route-confirmed-tone`) |
| `colors.semantic-emerald` | `text-emerald-300`, `bg-emerald-400/10` |
| `colors.error` | `text-rose-300`, `border-rose-500/40`, `bg-rose-500/10` |
| `typography.*` | `text-sm`, `text-2xl`, `font-semibold`, `tracking-[0.22em]`, `font-mono` |
| `spacing.md` | `p-4`, `gap-4`, `px-4` |
| `spacing.lg` | `p-6`, `gap-6`, `py-6` |
| `rounded.lg` | `rounded-xl` |
| `rounded.xl` | `rounded-2xl` |
| `rounded.xxl` | `rounded-3xl` |

**Prefer utilities in templates** (`class="..."`). Add rules in `input.css` only when:

- JS toggles a fixed class (lab replay: `.lab-decode-cell-tone`, `.lab-route-*-tone`, `#lab-replay-grid`),
- Flowbite/allauth needs a shared component hook (`account-allauth-primary-btn`),
- or Tailwind cannot express the effect (inset gap bridges, `touch-action` on viewport).

Do not add new global `.css` files under `static/` for product UI—extend `input.css` or template classes.

After changing template class names or `@source` paths, run `npm run build:css` so `app.css` includes the utilities (CI and static serving use the built file).

## Overview

shapez2 Factory Planner presents as a **dark factory console**: precise, technical, and calm—not playful consumer SaaS. The audience is players and staff optimizing shapez2 factories, solvers, and asteroid layouts.

- **Emotional tone:** Trustworthy instrumentation (readouts, grids, monospace codes) with a single energetic accent (cyan) for navigation and primary actions.
- **Density:** Marketing pages breathe (`max-w-7xl`, hero grids); **lab and graph workspaces** are denser (multi-column grids, smaller labels, live status lines).
- **Dark-first:** `<html class="dark">` on all pages; do not introduce a light theme without updating this document and contrast checks.
- **Domain color lanes:** Cyan = product chrome & primary CTA. Violet = topology / decode / graph-adjacent semantics. Amber = staff tools, warnings, probes. Emerald/lime = success, confirmed routes, MVP badges. Rose = errors and destructive actions.
- **Game fidelity:** Shape previews and lab sprites use game assets; UI chrome stays in the slate/cyan system so content reads clearly on `#020617` canvases.

## Colors

Palette is **slate neutrals + cyan interaction + fixed semantic accents** for solver/lab overlays.

- **Primary (`#020617`):** Page canvas (`bg-slate-950`). Headlines on marketing sections may use pure white for emphasis.
- **Surface (`#0F172A`):** Cards, inputs, side panels (`bg-slate-900` / `bg-slate-900/80`).
- **Secondary (`#1E293B`):** Borders and dividers (`border-slate-800`, `border-slate-700`).
- **Tertiary (`#06B6D4`):** Primary buttons, timeline scrub accent, focus rings (`ring-cyan-500/50`, `accent-cyan-500`).
- **Neutral (`#F1F5F9`):** Default body text (`text-slate-100`).
- **On-surface muted (`#94A3B8`):** Captions, metadata (`text-slate-400`, `text-slate-500`).
- **Semantic violet (`#A78BFA`):** Decode cells, bundle rules, replay event types, production planner headings. Deep fill `#4C1D95` at 50% for `.lab-decode-cell-tone`.
- **Semantic amber (`#F59E0B`):** Staff sections, macro graph status, route probes, miner demo metrics.
- **Semantic lime (`#84CC16`):** Confirmed solver routes (`lab-route-confirmed-tone` glow).
- **Semantic emerald (`#6EE7B7`):** Success flashes, MVP chips, graph editor links.
- **Error (`#FB7185`):** Validation and alert text (`text-rose-300`).

**Alpha borders:** Prefer `border-cyan-400/20` on feature cards and `border-cyan-400/45` on primary ghost buttons—not solid bright outlines everywhere.

**Hero grid:** Optional 48×48px cyan grid at 8% opacity (`rgba(34,211,238,0.08)`) on marketing heroes only.

## Typography

**Google Sans Code** is the sole UI family (loaded in `assets/css/input.css`). It signals “terminal / planner” and matches shape codes in inputs.

- **Headlines:** `headline-lg` / `headline-md` — semibold, tight tracking on page titles (e.g. lab h1 `text-2xl font-semibold tracking-tight`).
- **Body:** `body-md` / `body-sm` for paragraphs and nav; relaxed leading on explanatory copy (`leading-relaxed`).
- **Labels:** `label-md` — uppercase with wide tracking (`tracking-[0.22em]`) for section kicker lines (Solver, Staff, Shape solver).
- **Mono codes:** `mono-code` on shape codes, blueprint paste areas, addresses (`font-mono text-sm`).
- **Captions:** `caption` / `text-xs` for helper text under inputs and KPI sublabels (`text-xs uppercase tracking-wide text-slate-500` in lab stat cards).

Do not mix additional display fonts on product pages. Auth pages may reuse the same scale with slightly larger hero strips.

## Layout

- **Page shell:** `min-h-screen bg-slate-950 text-slate-100`; primary content width `max-w-7xl` with `px-4 sm:px-6 lg:px-8` (graph editor staff view uses `max-w-[1600px]`).
- **Spacing scale:** 4px base unit — `xs` 4, `sm` 8, `md` 16, `lg` 24, `xl` 32. Card internal padding typically `p-4`–`p-6` (16–24px).
- **Navigation:** Sticky header `border-b border-slate-800 bg-slate-950/95 backdrop-blur`; nav links `rounded-lg px-3 py-2`.
- **Marketing grid:** Two-column `lg:grid-cols-[1.05fr_0.95fr]` on home/solver; feature cards in three-column `md:grid-cols-3` on home roadmap strip.
- **Asteroid lab workspace:** `xl:grid-cols-[320px_1fr_360px]` — left constraints, center replay/map, right metrics. Stat KPI row `grid-cols-2 lg:grid-cols-5`.
- **Lab replay grid:** Cell gap `--lab-cell-gap: 0.25rem` (4px); cell radius `--lab-cell-radius: 4px`. Viewport uses `contain: layout paint` and disables browser zoom gestures on the grid.
- **Modals:** Centered `fixed inset-0 z-[100+]`, scrim `bg-black/70`, panel `max-w-xl` or `max-w-sm`, `rounded-3xl`.

## Elevation & Depth

Depth is **tonal layering**, not Material-style floating cards.

- Background: flat `slate-950`.
- Content: `slate-900/80` panels with `border-slate-800` or `border-cyan-400/20`.
- Emphasis: soft colored shadows — `shadow-2xl shadow-cyan-950/40` on hero quick-solver card, `shadow-lg shadow-cyan-950/30` on previews.
- Modals: `shadow-2xl` on `slate-950` panels; scrim darkens to 70% black.
- Lab route overlays: **glow** via `box-shadow` (violet/amber/lime) on cells, not elevation lift.
- Recipe graph: React Flow `.dark` canvas `#141414`; editor overrides controls/minimap to `#0f172a` family in `recipe-graph-editor.css`.

Avoid large blurred drop shadows on dense lab UI; they reduce grid readability.

## Shapes

- **Default radius:** `rounded-xl` (12px) for buttons, inputs, side panels.
- **Marketing / modals:** `rounded-2xl` cards, `rounded-3xl` modals and preview wells.
- **Pills / chips:** `rounded-full` for MVP badge, solver CTA chips, language switcher active ring.
- **Lab cells:** `4px` (`rounded.sm`) — engineered, grid-aligned; matches `--lab-cell-radius`.
- **Logo mark:** `rounded-xl` with `border-cyan-400/30` on `slate-950` background.
- **Corners:** Do not mix `rounded-md` buttons with `rounded-3xl` cards in the same toolbar row; pick one tier per component group.

## Components

### Buttons

| Variant | Use | Implementation hint |
|---------|-----|---------------------|
| Primary solid | Single main action per toolbar (Run Solver) | `bg-cyan-500 text-slate-950 rounded-xl` |
| Secondary outline | Reset, dismiss, save draft | `border-slate-700 bg-slate-900` |
| Ghost accent | Apply shape code, open solver | `border-cyan-500/40 bg-cyan-500/10 text-cyan-200` |
| Danger | Delete recipe, auth danger | `border-rose-500/40 bg-rose-500/15 text-rose-100` |
| Link | Secondary navigation in forms | `text-cyan-200 no-underline hover:text-cyan-100` |
| Staff amber | Staff-only create actions | `border-amber-500/40 bg-amber-500/10 text-amber-100` |

Primary width on auth: `account-allauth-primary-btn` caps at `12rem` centered.

### Navigation

- Inactive: `text-slate-400`, hover `text-cyan-300`.
- Active page: `text-cyan-200` (optional `aria-current="page"`).
- Logo hover: `hover:text-cyan-200`.

### Cards & panels

- **Feature card:** `rounded-2xl border border-cyan-400/20 bg-slate-900/80 p-5 sm:p-6` + optional cyan shadow.
- **Lab panel:** `rounded-2xl border border-slate-800 bg-slate-950/70 shadow-sm` with `p-4` body.
- **Stat tile:** uppercase micro-label `text-slate-500`, value `text-2xl font-semibold text-slate-100`.

### Inputs

- Text / textarea: `rounded-xl border border-slate-700 bg-slate-900`, focus `border-cyan-500` or `ring-cyan-500/50`.
- Placeholder: `text-slate-600`.
- Shape code fields: always `font-mono`.

### Chips & badges

- MVP / OK: `rounded-full` with `bg-emerald-400/10 text-emerald-300`.
- Section kicker: uppercase amber or cyan at 90% opacity for staff vs public.

### Tooltips & status

- Live regions: `aria-live="polite"` on `#macro-graph-status`, `#macro-meta-status`, lab replay HUD lines.
- Status warning: `text-amber-200/90`; errors `text-rose-300`.

### Checkboxes / radio

Use Flowbite patterns from mono theme when adding form controls; match slate-900 surfaces and cyan focus.

### Asteroid lab (domain)

- **Decode cell:** class `lab-decode-cell-tone` — inset violet ring, translucent violet fill (see `assets/css/input.css`).
- **Route overlays:** `lab-route-goal-tone`, `lab-route-probe-tone`, `lab-route-confirmed-tone` — glow only, no layout shift.
- **Timeline:** `#lab-timeline-scrub` — full width, `accent-color` cyan, `touch-action: manipulation` on `#lab-timeline-controls`.
- **Topology modal:** violet section label `text-violet-300`; trigger button violet tinted square `border-violet-500/30 bg-violet-500/10`.
- **Bundle bridges:** `.lab-bundle-bridge` — 3px arms in cell gap; color from JS, not CSS tokens.

### Recipe graph editor (staff)

- Mount: `#macro-graph-editor-root` inside `max-w-[1600px]` shell.
- Canvas: React Flow dark theme; custom `--xy-*` overrides for slate controls.
- Status line above canvas: amber `text-amber-200/90`.
- Do not restyle graph nodes to cyan; keep React Flow node `#1e1e1e` / border `#3c3c3c` unless this file is updated.

### Auth & messages

Flash messages: error rose, success emerald, warning amber, default info cyan — all `rounded-xl border` + 10% tint backgrounds (`base_auth.html`).

## Iconography

- **Stroke icons:** Heroicons-style SVG inline in templates — `stroke="currentColor"`, `stroke-width="2"`, size `h-4 w-4` or `h-5 w-5`, inherit text color (cyan-300 in lab headers, slate-500 decorative).
- **Branding:** PNG logo `web/img/branding/logo-3.png` in nav; header art on home.
- **Game sprites:** Lab `lab-cell-sprite` — `object-fit: contain`, `image-rendering: auto` for SVG assets.
- **Stage icons:** Asteroid pipeline stages via `asteroid_mining_lab_stage_icon.html` partial — tone from server `tone_class`, do not hardcode new colors in partial.

## Data visualization

- **Shape preview:** Dark well `rounded-2xl border border-slate-800 bg-slate-950` with optional `ring-cyan-400/20`; GLTF viewer module for 3D previews.
- **Lab replay grid:** Absolute-positioned cells; pan/zoom on `#lab-replay-grid-stage`; optimization overlay `pointer-events: none`.
- **Demo metrics:** Amber numerals for throughput; violet step badges `bg-violet-500/20 text-violet-200`.
- **Graph edges:** Default React Flow stroke `#3e3e3e`; selection `#727272` in dark mode — do not override to cyan (reserved for chrome).
- **Minimap:** Background `#0f172aeb`, nodes `#475569` per `.rf-editor-canvas .react-flow` overrides.

## Do's and Don'ts

**Do**

- Use cyan for the **one** primary solid CTA per major toolbar (e.g. Run Solver, not every button).
- Keep shape codes and blueprint paste areas in **monospace** at `body-sm` or larger.
- Preserve lab semantic colors (violet decode, amber probe, lime confirmed) when adding overlay types.
- Use `aria-live` for async solver/graph status text.
- Run `npx design.md lint DESIGN.md` when changing tokens.
- Implement layout and color with **Tailwind utilities**; copy patterns from sibling templates (`site_nav.html`, `home.html`, `asteroid_miner_layout_solver.html`).
- Run `npm run build:css` after template or `input.css` changes that affect class names.
- Match new screens to existing Tailwind recipes before inventing new hues.

**Don't**

- Add a light theme or white page background without revising tokens and WCAG checks.
- Use cyan glow on graph nodes (conflicts with route/lab semantics).
- Mix `rounded-md` and `rounded-3xl` on adjacent controls in the same bar.
- Use more than **two font weights** on a single dense panel (e.g. lab side column).
- Replace semantic lab colors with generic “brand cyan” for state indication.
- Edit generated bundles (`django_apps/web/static/web/js/*.js` from esbuild) or committed `app.css` by hand — change `assets/css/input.css` / templates, then `npm run build:css`.
- Add one-off `<style>` blocks in templates when Tailwind utilities suffice.
- Set `failure_reason` or status copy as free-form color names in code — use design tokens / Tailwind classes from this file.

**Accessibility**

- Target WCAG AA for `text-slate-400` on `slate-950` and `text-cyan-200` on `slate-900` (lint with `@google/design.md`).
- Focus: visible `focus-visible:ring-2 focus-visible:ring-cyan-500/50` on inputs; do not remove focus rings on lab timeline controls.
- Modals: `role="dialog"`, `aria-modal="true"`, labelled titles (`aria-labelledby`).

---

**Maintenance:** After visual changes to `django_apps/web/templates/` or `assets/css/input.css`, update YAML tokens if hex values shifted. Optional CI: `npx design.md lint DESIGN.md`.
