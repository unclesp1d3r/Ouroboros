# Ouroboros UI Style Guide

**Version:** 1.0
**Last Reviewed:** 2025-05-16

This document defines the visual design and behavior standards for the Ouroboros frontend. It ensures consistency across pages, components, and themes, while staying fully offline-capable and budget-friendly.

---

## 🎨 Color & Theme

### 🎨 Macchiato Palette Reference

| Role              | Token      | Hex       | Preview                                                                                                      |
| ----------------- | ---------- | --------- | ------------------------------------------------------------------------------------------------------------ |
| Text              | `text`     | `#cad3f5` | <span style="display:inline-block;width:1.5em;height:1.5em;background:#cad3f5;border:1px solid #ccc"></span> |
| Subtext           | `subtext0` | `#a5adcb` | <span style="display:inline-block;width:1.5em;height:1.5em;background:#a5adcb;border:1px solid #ccc"></span> |
| Surface           | `surface0` | `#363a4f` | <span style="display:inline-block;width:1.5em;height:1.5em;background:#363a4f;border:1px solid #ccc"></span> |
| Base              | `base`     | `#24273a` | <span style="display:inline-block;width:1.5em;height:1.5em;background:#24273a;border:1px solid #ccc"></span> |
| Crust             | `crust`    | `#181926` | <span style="display:inline-block;width:1.5em;height:1.5em;background:#181926;border:1px solid #ccc"></span> |
| Overlay           | `overlay1` | `#5b6078` | <span style="display:inline-block;width:1.5em;height:1.5em;background:#5b6078;border:1px solid #ccc"></span> |
| Accent (lavender) | `lavender` | `#b7bdf8` | <span style="display:inline-block;width:1.5em;height:1.5em;background:#b7bdf8;border:1px solid #ccc"></span> |
| Accent (custom)   | `accent`   | `#9400D3` | <span style="display:inline-block;width:1.5em;height:1.5em;background:#9400D3;border:1px solid #ccc"></span> |

- **Base Theme**: Catppuccin **Macchiato**

  - Integrated via `@catppuccin/tailwindcss`
  - Tailwind `defaultFlavor` set to `macchiato`

- **Accent Color**: `DarkViolet` (`#9400D3`)

  - Used as `accent` throughout UI (buttons, toggles, highlights)
  - Aliased in Tailwind via `theme.extend.colors.accent`

- **Surface Colors**:

  - Backgrounds: `surface0`, `crust`
  - Foreground: `text`, `subtext0`

> Avoid true black. Ensure contrast for accessibility.

---

## 📐 Layout & Spacing

- Base layout follows Flowbite’s [Sidebar + Navbar Shell](https://flowbite.com/blocks/application/shells/)

- Default spacing:

  - Padding: `p-4` for containers
  - Grid: `grid-cols-6` for dashboard lists

- Modals:

  - Max width: `max-w-2xl`
  - Use `hx-target="#modal-body"` for content

---

## 🖋 Typography

- Font: system default stack (no external fonts)

  - Use Tailwind’s `font-sans` only

- Headings:

  - `text-xl` = section title
  - `text-lg` = card title or modal heading

- Paragraph/text:

  - `text-base` for body
  - `text-sm` for meta/help text

---

## 🧱 Components

### 🧭 Tooltip & Validation States

| Context        | Style Tokens                                                 | Notes                                                    |
| -------------- | ------------------------------------------------------------ | -------------------------------------------------------- |
| Tooltip (info) | `bg-surface0 text-subtext0 text-sm px-2 py-1 rounded shadow` | Use for hover-based rule previews, complexity dots, etc. |
| Input (error)  | `border-red-500 text-red-500`                                | Applies on invalid fields; include error message below.  |
| Toast (error)  | `bg-red-600 text-white`                                      | Used for system errors or failed actions                 |
| Toast (info)   | `bg-blue-600 text-white`                                     | Used for cracked hashes, import/export confirmations     |

Use Flowbite tooltip behavior for any inline rule help or config explanations.

### 🎛️ Button & Badge Color Reference

| Element Type | State     | Class Tokens                | Color (Hex) | Preview                                                                                                       |
| ------------ | --------- | --------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------- |
| Button       | Primary   | `bg-accent text-white`      | `#9400D3`   | <span style="display:inline-block;width:1.5em;height:1.5em;background:#9400D3;border:1px solid #ccc"></span>  |
| Button       | Secondary | `border-accent text-accent` | `#9400D3`   | <span style="display:inline-block;width:1.5em;height:1.5em;background:white;border:2px solid #9400D3"></span> |
| Badge        | Success   | `bg-green-500 text-white`   | `#22c55e`   | <span style="display:inline-block;width:1.5em;height:1.5em;background:#22c55e;border:1px solid #ccc"></span>  |
| Badge        | Warning   | `bg-yellow-400 text-black`  | `#facc15`   | <span style="display:inline-block;width:1.5em;height:1.5em;background:#facc15;border:1px solid #ccc"></span>  |
| Badge        | Error     | `bg-red-600 text-white`     | `#dc2626`   | <span style="display:inline-block;width:1.5em;height:1.5em;background:#dc2626;border:1px solid #ccc"></span>  |
| Badge        | Info      | `bg-blue-500 text-white`    | `#3b82f6`   | <span style="display:inline-block;width:1.5em;height:1.5em;background:#3b82f6;border:1px solid #ccc"></span>  |

All UI elements should use Flowbite or native Tailwind components.

- **Buttons**:

  - Primary: `btn bg-accent text-white`
  - Secondary: `btn-outline border-accent text-accent`

- **Modals**:

  - Use Flowbite modal layout
  - Always insert into `#modal`

- **Toasts**:

  - Persistent container in `base.html`
  - Rendered via Flowbite toast class

- **Tables**:

  - Use Flowbite’s table with alternating row color
  - Add icon column for state or action

---

## 🧠 Behavioral Expectations

- Use `hx-get` and `hx-post` for fragment-based flows
- Use `hx-trigger="change, input delay:300ms"` for live estimation
- Modal form actions must submit via HTMX and return partial to update UI
- SSE updates must trigger targeted data refreshes using Svelte stores

---

## 🐝 Branding Motif

- Hexagons may be used as:

  - Low-opacity background overlays
  - Card or modal decoration

- Should not be bright yellow or overwhelming

- Must be inline SVG or local asset — no external fetch

---

### 🛠 Attack Type Icon Mapping (Lucide Icons)

| Attack Type               | Icon Name (Lucide)   | Rationale                           |
| ------------------------- | -------------------- | ----------------------------------- |
| Dictionary                | `book-open`          | Implies a wordlist or data set      |
| Mask (Manual)             | `command`            | Symbolizes pattern-based input      |
| Brute Force (Incremental) | `hash`               | Represents raw cryptographic attack |
| Previous Passwords        | `rotate-ccw`         | Visual shorthand for reuse/history  |
| Hybrid (Dict + Mask)      | `merge`              | Conveys two strategies joined       |
| Rule-based only           | `sliders-horizontal` | Represents configurable modifiers   |
| Toggleable Modifiers      | `puzzle`             | Abstracts modifiers as rule pieces  |

> All icons should be outline-style SVGs sourced from [Lucide Icons](https://lucide.dev/icons/), stored locally in `app/assets/icons/attacks/`, and themed using `fill="currentColor"` or Tailwind `text-accent`.

---

## 🖥️ Viewport & Small Window Considerations

Ouroboros is not designed for mobile-first usage but must remain usable in constrained browser windows (e.g., side-by-side dev consoles or dashboards).

- Minimum target resolution: 768px width

- Avoid horizontal scroll on core views like Campaign Detail and Agent List

- Overflowing tables or charts must:

  - Scroll horizontally inside a `div.overflow-x-auto`
  - Provide pinned headers or key columns if feasible

- Toasts and modals must anchor to the viewport rather than parent containers

- Responsive sidebars should collapse below `lg` breakpoint via Flowbite’s toggle pattern

---

## 📱 Responsive & Layout Guidance

- All views must be usable on a minimum screen width of 768px (tablet)
- Campaign and agent views should gracefully wrap or scroll
- Avoid fixed widths unless needed for modal max-widths
- Use `sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3` patterns where applicable
- Don’t use pixel units — use Tailwind spacing (`px-4`, `gap-2`, etc.)
- Sidebar must collapse below `lg` breakpoint (standard Flowbite pattern)

---

## 🧾 Max Width & Wrapping Conventions

- Modals: max width `max-w-2xl`; centered with backdrop
- Toasts: width `max-w-sm`; pinned bottom right or top right
- Tables: should never break layout — wrap in `overflow-x-auto`
- Sidebar: fixed width `w-64` on `lg+`, collapses to `w-16` or hidden on `md`
- Cards/blocks: prefer `max-w-4xl` or container-based layout to avoid full-width stretch
- Never hard-code pixel widths for primary layout regions — use Tailwind utilities

---

## 📦 Offline & Zero-Budget Constraints

- All fonts, icons, and assets must work offline
- Use system fonts and local SVG assets
- Do **not** rely on Google Fonts, CDN icons, or paid icon libraries
- Recommend: [Lucide Icons](https://lucide.dev/icons/) (MIT licensed, installable as SVG)

---

## ✅ Implementation Status

> This style guide will evolve throughout Phase 3-5. For current implementation notes, refer to [Phase 3: Web UI Foundation](../v2_rewrite_implementation_plan/phase-3-web-ui-foundation.md).
