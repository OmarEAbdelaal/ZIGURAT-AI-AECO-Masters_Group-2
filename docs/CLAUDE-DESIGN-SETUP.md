# Filling in the Claude Design "Set up your design system" form

Copy each block below into the matching field. Nothing here needs editing except the GitHub URL once the repo exists.

---

## 1. Company name and blurb (or name of design system)

> Group 02 FMP Design System — ZIGURAT AI-AECO Master (MAICEN 0526, Module 10). The shared visual system for our Final Master's Project, "AI-Powered BIM Value Engineering Assistant with Continuous Design-Stage Feedback". Built on the Zigurat brand mark: electric blue #1C60F3 and mint green #41CF97, both sampled pixel-exact from the official logo. Five team members produce slides, notebooks, diagrams and a written report in parallel, so this system exists to make all of it read as one project.

*(Your current entry, "ZIGURAT AI-AECO Master' - Group 2", also has a stray apostrophe worth removing.)*

---

## 2. Link code from GitHub

```
https://github.com/OmarEAbdelaal/ZIGURAT-AI-AECO-Masters_Group-2
```

The repo is **private**, so Claude Design can only read it if your GitHub account is connected with access to private repositories. If it can't reach it, the folder attachment in field 3 covers the same content — you don't need both.

---

## 3. Link code from your computer

You currently have the whole `01_FMP_PROJECT ⭐` folder attached. **Remove it and attach `01_FMP_PROJECT ⭐/fmp-design-system` instead.**

The form itself recommends a focused subfolder over a large codebase, and the parent folder is mostly `.docx`, `.pdf` and meeting notes — none of which tell Claude anything about your visual system, while the noise makes the signal harder to find. The `fmp-design-system` folder is nothing but tokens, CSS, logos and the style guide.

---

## 4. Upload a .fig file

Skip — the team isn't working in Figma. Nothing is lost: `colors.json` and `typography.json` carry the same information in W3C token format.

---

## 5. Add fonts, logos and assets

You already have `colors.json`, `tokens.css`, `typography.json` and `zigurat-logo.jpg` attached. Add these four, all from `fmp-design-system/`:

| File | Why it matters |
|---|---|
| `assets/logo/zigurat-mark.svg` | The vector mark. Scales cleanly; the JPG is 200 px with compression artefacts. |
| `assets/logo/fmp-group02-lockup.svg` | The team lockup — mark plus signature. |
| `css/components.css` | Shows how the tokens are actually consumed: buttons, cards, badges, callouts, tables. |
| `docs/style-guide.html` | The whole system rendered in one page, including the contrast table. |

You can also drop `zigurat-logo.jpg`, since the SVGs supersede it — but leaving it costs nothing.

**Fonts:** don't upload font files. Poppins, Inter and JetBrains Mono are Google Fonts and load from a URL; `tokens.css` documents the exact import string.

---

## 6. Any other notes?

> **Brand basis.** Both brand colours are pixel-exact samples from the official Zigurat logo, not approximations: electric blue #1C60F3 (left face) and mint green #41CF97 (right face). The mark is two stacked isometric steps — a ziggurat — on a true 2:1 axonometric slope. Our SVG rebuild matches the source bitmap on 98.8% of pixels.
>
> **Tone.** Engineered, precise, calm. Flat colour, no gradients, no drop shadows beyond the two defined elevation levels. Generous whitespace on an 8px spacing rhythm. The subject is BIM and value engineering for a technical academic audience — clarity beats decoration every time.
>
> **Type.** Poppins for headings (geometric, echoes the mark's flat planes), Inter for body and dense tables, JetBrains Mono for BIM parameters, IFC classes and GUIDs. All Google Fonts. Zigurat publishes no official typeface, so this pairing is a documented stand-in — if that changes, only the three font tokens need to move.
>
> **Critical colour rule.** Mint green #41CF97 is **fill only**. It is 1.98:1 on white and must never carry text. Use #1E7A57 when green has to be read. Same for amber #D69E2E (fill) vs #8C651C (text).
>
> **Accessibility is a hard constraint, not a preference.** Every foreground/background pair in the system clears WCAG AA 4.5:1 in both light and dark themes; the ratios are computed and documented in `docs/style-guide.html`. Colour never carries meaning alone — always pair it with a label, icon or dot. Keep the shared `:focus-visible` ring.
>
> **Use the semantic tokens, never raw hexes.** Write `var(--color-primary)`, not `#1C60F3`. The semantic layer is what re-points itself in dark theme. Both themes are already defined in `tokens.css` and must keep working.
>
> **Project-specific patterns to preserve:** a 0–100 *value score* with a delta indicator; a four-step *value-risk* scale (low / moderate / high / critical) used on badges and card spines; and data tables where numeric and BIM-parameter columns are set in mono, right-aligned, with tabular numerals.
>
> **Brand ownership.** The Zigurat name and mark belong to Zigurat Global Institute of Technology and appear here for academic use within our Final Master's Project. Do not generate anything that presents itself as official Zigurat communication — team-level "Group 02" branding only.

---

## Before you hit "Continue to generation"

- [ ] Blurb replaced (and the stray apostrophe gone)
- [ ] Folder attachment switched to `fmp-design-system`
- [ ] The four extra assets added
- [ ] GitHub URL pasted
- [ ] Notes pasted
