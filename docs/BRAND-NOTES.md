# Brand notes

Usage rules for the mark, the lockup and the system as a whole. Read this before putting the logo on anything.

## Ownership — read this first

The **Zigurat** name and the ziggurat mark belong to **Zigurat Global Institute of Technology**. Group 02 does not own them.

They appear in this repository for one reason: we are producing a Final Master's Project *for* the MAICEN programme, and our deliverables need to identify the programme they belong to. That is academic use in context.

What this means in practice:

- **Do** use the mark to identify the programme on FMP deliverables — report covers, slide masters, the project dashboard.
- **Do not** present anything in this repository as official Zigurat communication, or imply the institute authored, endorsed or reviewed it.
- **Do not** reuse these assets for anything outside the FMP — a personal portfolio site, a commercial product, a different course — without asking the programme first.
- **Do not** redistribute the asset files as if they were an official brand kit.

The `fmp-group02-lockup.svg` is a different thing: it is **our team's** lockup. It pairs the mark with *Group 02* set in this system's own typefaces, which makes it clearly a team signature rather than institutional branding. Prefer it over the bare mark wherever the audience might otherwise mistake our work for the institute's.

If the programme supplies an official brand book, it supersedes this file entirely. Replace the assets and the two font declarations, and the rest of the system keeps working unchanged.

## Where the assets came from

The team supplied one bitmap: `assets/logo/zigurat-logo.jpg`, 200 × 200 px.

Everything else was derived from it:

- **Colours.** `#1C60F3` and `#41CF97` are the dominant non-white pixel values in that file — exact samples, not approximations.
- **Vectors.** `zigurat-mark.svg` was traced by pixel analysis: two stacked isometric steps on a true 2:1 axonometric slope, each split into a blue left face and a green right face. The trace matches the source bitmap on **98.8%** of pixels; the residual is antialiasing along the diagonals.

Prefer the SVGs over the JPG everywhere. The JPG is 200 px and has compression artefacts around the edges; it is kept only as the provenance record for the trace.

## Which file to use

| File | Use it for |
|---|---|
| `zigurat-mark.svg` | Default. Any light or charcoal background. |
| `zigurat-mark-mono.svg` | One-ink printing, watermarks, embossing, busy photographic backgrounds. Inherits `currentColor` — set `color` on the parent. |
| `fmp-group02-lockup.svg` | Title slides, report covers, the repository README. Anywhere the team should be named. |
| `zigurat-logo.jpg` | Nothing. Provenance only. |

## Clear space and minimum size

**Clear space:** keep at least one step-height — 16 units in the mark's own coordinate system, which is ⅛ of the mark's width — clear on all four sides. Nothing else sits inside that margin: no text, no rule, no image edge.

**Minimum size:**

- Mark alone: 24 px on screen, 8 mm in print. The two steps stop reading as separate planes below that.
- Lockup: 180 px on screen, 45 mm in print. Below that, drop the signature and use the mark alone.

## Backgrounds

The full-colour mark needs a background that lets both faces read. It is approved on:

- White `#FFFFFF` and off-white `#F7F9FA`
- Charcoal `#1B1F23` and graphite `#2D3339`

On anything else — a photograph, a mid-tone, a coloured panel, a gradient — use `zigurat-mark-mono.svg` in white or charcoal, whichever gives more contrast. Never place the full-colour mark on electric blue or mint green; the matching face disappears.

## Don't

- Don't stretch, squash or rotate the mark. Scale it proportionally.
- Don't recolour it. The two-tone version is blue/green; the mono version is one ink. There is no third option.
- Don't add effects — no drop shadow, glow, bevel, outline or gradient fill.
- Don't rebuild it in a slide tool from rectangles. Import the SVG.
- Don't crop it, box it, or put it inside a circle.
- Don't set the lockup's signature in a different typeface, or retype it as live text next to the mark.
- Don't place it closer than the clear space to anything, including the slide edge.

## Applying the system elsewhere

**Slides.** Build one master carrying the lockup, the type scale and the palette, then have everyone work from it. Poppins for titles, Inter for body. Do not introduce a sixth heading size because one slide felt crowded — cut the words instead.

**Diagrams and figures.** Vector wherever possible. Use `--series-1` … `--series-6` in order so the same variable is the same colour in every figure. Name files `fig-NN-short-slug.svg`.

**Notebooks.** Set the matplotlib `prop_cycle` and font family once at the top, as shown in the README. Never paste a hex inline.

**The written report.** Charcoal body text, slate captions, blue for links and cross-references. Keep the measure around 68 characters — `--content-max` in the token file — so long passages stay readable.

## Changing the system

The palette and type scale are deliberately small. That is the point: five people producing work in parallel converge only if the shared vocabulary is short enough to hold in your head.

If you genuinely need something new, add it properly — token file, CSS, contrast check, style guide, PR — rather than inlining a one-off value in your own deliverable. A one-off value is invisible to everyone else and becomes the inconsistency someone notices in the final review.
