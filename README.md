<div align="center">
  <img src="assets/logo/fmp-group02-lockup.svg" alt="Group 02 — AI-Powered BIM Value Engineering Assistant" width="420">
</div>

# Group 02 — FMP Design System

Brand assets, design tokens and a shared component layer for **Group 02**'s Final Master's Project on the **ZIGURAT AI-AECO Master** (MAICEN 0526, Module 10).

**Project:** AI-Powered BIM Value Engineering Assistant with Continuous Design-Stage Feedback.

Five people are producing slides, notebooks, diagrams and a written report in parallel. This repository exists so that all of it looks like one project rather than five — one palette, one type scale, one spacing rhythm, defined once and imported everywhere.

---

## Coursework in this repository

| Unit | Deliverable | |
|---|---|---|
| **M4U3 — Computer Vision** | **Façade Element Detection for Continuous Value Engineering** — a YOLOv8 detector that reads envelope elements from photographs and rendered elevations, feeding the FMP's Value Engineering loop with Window-to-Wall Ratio and envelope indicators for buildings with no BIM model. | [**→ open**](m4u3-facade-ve-vision/) |

Each coursework folder is self-contained: its own README, licence, notebooks, source and
results, with no path reaching outside it. The design system below is shared across all of
them.

---

## What's in here

```
fmp-design-system/
├── design-tokens/
│   ├── colors.json        # Brand, neutral, semantic, value-risk and tint colours (W3C token format)
│   ├── typography.json    # Font families, weights, and the full type scale
│   └── tokens.css         # Every token as a CSS custom property, light + dark theme
├── css/
│   └── components.css     # Buttons, cards, badges, callouts, tables, value score, utilities
├── assets/
│   └── logo/
│       ├── zigurat-mark.svg          # Vector mark, full colour
│       ├── zigurat-mark-mono.svg     # Single colour, inherits currentColor
│       ├── fmp-group02-lockup.svg    # Team lockup: mark + signature
│       └── zigurat-logo.jpg          # The original bitmap the vectors were traced from
├── docs/
│   ├── style-guide.html   # ← Open this first. The whole system, rendered.
│   └── BRAND-NOTES.md     # Usage rules, clear space, and the brand-ownership position
└── README.md
```

**Start here:** open [`docs/style-guide.html`](docs/style-guide.html) in a browser. It renders every colour, type step, component and contrast ratio in the system, and it is built from the same token files you'll be importing — so if it looks right there, it will look right in your deliverable.

---

## Using it

### In an HTML or web deliverable

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap">
<link rel="stylesheet" href="design-tokens/tokens.css">
<link rel="stylesheet" href="css/components.css">
```

Then write `var(--color-primary)`, `var(--font-heading)`, `var(--space-4)` — never a raw hex, font name or arbitrary pixel gap. The semantic tokens are what re-point themselves in dark theme; a hard-coded hex will not, and that is the thing that breaks the night before submission.

### In Python plots (matplotlib, plotly)

Read the tokens rather than retyping them, so a palette change propagates:

```python
import json
colors = json.load(open("design-tokens/colors.json"))["color"]
SERIES = ["#1C60F3", "#41CF97", "#7B4FE0", "#DD6B20", "#4A5568", "#17A2B8"]

import matplotlib as mpl
mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=SERIES)
mpl.rcParams["font.family"]     = "Inter"
mpl.rcParams["text.color"]      = colors["neutral"]["charcoal"]["value"]
```

Use `--series-1` … `--series-6` **in order**, so the same variable is the same colour in every chart anyone produces.

### In Figma or a design tool

Import `colors.json` and `typography.json` — most token plugins read this W3C format directly.

### In slides and documents

Take the hex values from `colors.json`. Set headings in Poppins, body in Inter. If a colour isn't in the file, it isn't in the project.

---

## The palette in one table

| Token | Hex | Role |
|---|---|---|
| `electric-blue` | `#1C60F3` | Primary — actions, links, first chart series |
| `mint-green` | `#41CF97` | Accent — **fill only**, never text on light |
| `mint-green-text` | `#1E7A57` | The green to use when green must be read |
| `charcoal` | `#1B1F23` | Body text on light, page background on dark |
| `slate` | `#4A5568` | Secondary text, captions, axis labels |
| `silver` | `#E2E8F0` | Borders, dividers, table rules |
| `off-white` | `#F7F9FA` | Page background on light |

Both brand colours are **pixel-exact samples** from the supplied logo file — `#1C60F3` and `#41CF97` are the dominant non-white pixels in `assets/logo/zigurat-logo.jpg`. Nothing was eyeballed.

## Type

Zigurat's public materials do not name a licensed typeface, so this pairing is a deliberate stand-in: geometric headings that echo the mark's flat planes, a highly legible body face for dense tables, and a mono for BIM parameters and IFC identifiers. All three are open Google Fonts, so every team member can install them without a licence.

| Role | Family | Used for |
|---|---|---|
| Heading | **Poppins** 600/700 | H1–H4, slide titles, section headers |
| Body | **Inter** 400/500/600 | Body copy, UI, documentation, tables |
| Mono | **JetBrains Mono** 400 | Code, IFC classes, BIM parameters, GUIDs |

If the programme later publishes an official typeface, change the three `fontFamilies` values in `typography.json` and the three `--font-*` tokens in `tokens.css`. Nothing else names a font directly — that is the entire migration.

## Accessibility

Every foreground/background pair this system recommends was computed against the WCAG 2.1 relative-luminance formula and clears **4.5:1** (AA at any text size), in both light and dark themes. The full table is in the style guide.

Three colours are explicitly **fill-only** and must never carry text:

- `#41CF97` mint green — 1.98:1 on white
- `#D69E2E` amber — 2.39:1 on white
- `#8A94A6` steel — 3.06:1 on white (large text and non-text UI only)

Each has a darkened text-safe counterpart (`mint-green-text`, `warning-text`, `slate`). Beyond contrast: colour never carries meaning alone — pair it with a label, icon or dot; the shared `:focus-visible` ring is defined once in `components.css`, so never write `outline: none` without a replacement; and `prefers-reduced-motion` is already handled in the token file.

## Brand ownership

The **Zigurat** name and mark belong to Zigurat Global Institute of Technology. They are reproduced here for academic use within our Final Master's Project. The `fmp-group02-lockup.svg` names *Group 02* in this system's own typefaces and is **our team's** lockup — it must never be presented as official institutional branding. See [`docs/BRAND-NOTES.md`](docs/BRAND-NOTES.md) before using any of it outside the FMP.

## Team

**Group 02** — MAICEN 0526, Module 10

| Member | Role on the FMP |
|---|---|
| Omar Elsayed | AI Architect — overall AI architecture, RAG/recommendation pipeline, BIM integration |
| Silvana Abou Shakra | BIM Automation & Dynamo — parameter, room and material schedule extraction |
| Ahmed Elbasyouni | BIM Developer & Standards — VE rules, risk taxonomy, ISO 19650 alignment |
| Asiya Begum | BIM Strategy & Automation — workflow analysis, research, use-case validation |
| Valentina Vötter | Advanced AI & Civil BIM — recommendation/classification models, RAG component |

## Contributing

Adding a colour, a type step or a spacing value is a **team decision**, not an individual one — the value of this repository is entirely in everyone using the same small set. If you need something that isn't here:

1. Add the token to `colors.json` / `typography.json` **and** `tokens.css` (they are kept in sync by hand).
2. If it is a text colour, check it clears 4.5:1 on every background it will sit on, and record the ratio in the comment.
3. Add it to the style guide so the next person can find it.
4. Open a PR rather than pushing to `main`.
