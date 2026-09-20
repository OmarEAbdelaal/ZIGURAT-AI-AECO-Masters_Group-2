# Class Definitions — The Labelling Contract

> Session 1, Section 4: *"Why projects die here."* The class list is not a list of words.
> It is a contract between whoever draws the boxes and whoever consumes the model.
> If two annotators read this document and disagree on an image, the document is wrong.

**Contract version:** 1.0 · **Classes:** 5 · **Order is load-bearing** — class ids are
positional in every `.txt` label file. Append only; never reorder. `src/dataset.py`
refuses to train if the dataset's class order disagrees with `src/config.py`.

| id | class | one-line definition |
|---|---|---|
| 0 | `window` | A discrete glazed opening set within an opaque wall plane |
| 1 | `curtain_wall` | A continuous glazed zone with no opaque interruption across its width |
| 2 | `door` | A ground-level pedestrian entrance or egress opening |
| 3 | `balcony` | A projecting or recessed occupiable slab with a balustrade |
| 4 | `louvre_screen` | A fixed slatted element for solar shading or plant screening |

---

## 0 · `window`

**Include** — a glazed opening bounded on all four sides by opaque wall; punched windows,
ribbon windows (each structural bay boxed separately), clerestory strips, glazed sections
of a shopfront that sit between solid piers.

**Exclude** — glazing that is continuous past its neighbours with no opaque return
(that is `curtain_wall`); a glazed door at ground level (that is `door`); reflections of
windows in another surface; windows on a building that is not the subject of the image.

**Box** — the outer edge of the visible frame, including the frame, excluding the
surrounding reveal or sill. Frame-inclusive is the convention because the frame is part of
the purchased unit and therefore part of the cost.

**Occlusion** — box only the visible part. A window half behind a tree gets a box around
the visible half. This matches LS3's *"teach the model that a 'floating head' is still a
person"* — the partially visible instance is the normal case on a real street, not an
exception.

**Minimum size** — 8 × 8 px. Below that there is not enough signal for the convolution
and the label teaches noise. Clerestory strips as thin as 4 px in height are labelled
**if** the full width is legible, because they are a genuine and recurring hard case.

---

## 1 · `curtain_wall`

**Include** — a glazed zone that runs continuously across two or more structural bays
with no opaque interruption; a fully glazed façade plane; a glazed atrium wall. Mullions
and transoms inside the zone do **not** break it — they are part of the system.

**Exclude** — a row of separate punched windows that merely look adjacent; there is wall
between them, so each is a `window`. A single-bay glazed panel isolated in masonry is a
`window`, however large.

**Box** — one box per continuous glazed zone, not one per pane. Where a curtain wall runs
across several floors uninterrupted, that is one box spanning them.

**The discriminating question** — *can I trace an unbroken line of glass from one side of
this element to the other without crossing opaque material?* Yes → `curtain_wall`.
No → one or more `window`.

> This is the boundary that generates almost all class confusion in this project, and
> it is the one an annotator must be able to apply without hesitating. The test above is
> phrased as a yes/no procedure for exactly that reason.

---

## 2 · `door`

**Include** — the primary pedestrian entrance; secondary and service doors at ground
level; revolving doors (box the whole drum); glazed entrance doors within a shopfront.

**Exclude** — vehicle and loading-bay shutters (not in this contract; leave unlabelled);
internal doors visible through glazing; balcony doors above ground level — those are
`window`, because in cost terms they are a glazed unit in a façade, not an entrance.

**Box** — the full door leaf plus its frame. For a paired or revolving entrance, one box
around the whole assembly.

---

## 3 · `balcony`

**Include** — projecting balconies; inset/recessed balconies and loggias; French
balconies where a balustrade sits directly against the façade.

**Exclude** — a parapet at roof level with no occupiable slab behind it; a window guard
rail less than ~400 mm deep; a walkway that is part of scaffolding rather than the
building.

**Box** — the balustrade plus the visible edge of the slab. The occupiable area behind
it is not boxed, because from a frontal elevation it is not visible and boxing it would
mean guessing depth — and a guessed box is a wrong quantity.

---

## 4 · `louvre_screen`

**Include** — fixed horizontal or vertical solar shading; brise-soleil; perforated or
slatted screens over plant and mechanical zones; slatted car-park ventilation screens.

**Exclude** — operable blinds or shutters behind glazing (they are a fit-out item, not an
envelope item); decorative grilles smaller than ~0.5 m²; scaffolding mesh and debris
netting, which look very similar and are temporary — this exclusion matters, because a
scaffolded building will otherwise be read as heavily screened.

**Box** — the extent of the slatted zone.

---

## The three standing rules

Session 2's homework asks for three project-specific rules written down before labelling
begins. These are ours, and they are the tie-breakers when this document is silent:

1. **I will NOT label reflections.** A window reflected in a neighbouring glass façade is
   not a window on the subject building. Labelling it double-counts the envelope.
2. **I will NOT label elements on a background or neighbouring building.** One subject
   building per image. If two buildings are equally prominent, the image is ambiguous —
   crop it or discard it, do not guess.
3. **I WILL label partial and occluded elements**, boxing only the visible extent, down to
   the 8 px minimum. A façade seen from the street is occluded; a model trained only on
   clean instances will fail on every real photograph.

## Boundary cases — the "rogues gallery" (LS2, Section 4)

Session 2 requires at least five boundary cases: things that look like a class and are
not. These are this project's kryptonite, collected deliberately:

| # | Boundary case | Correct label | Why it is hard |
|---|---|---|---|
| 1 | **Mirror-glass spandrel panel** | *unlabelled* | Opaque panel that reflects sky exactly like glazing. The single most expensive error available to this model: it inflates WWR and the cost index simultaneously. |
| 2 | **Dark ground-floor signage panel** | *unlabelled* | Same aspect ratio, tone and position as an entrance door. |
| 3 | **Scaffold debris netting over a bay** | *unlabelled* | Visually near-identical to a `louvre_screen`, but temporary and not part of the envelope. |
| 4 | **Ribbon window across bays with slim piers** | `window` × n | Sits on the exact boundary with `curtain_wall`. Resolved by the unbroken-glass test above. |
| 5 | **Window reflected in an adjacent glass tower** | *unlabelled* | Rule 1. Geometrically perfect, contextually wrong. |
| 6 | **Deep reveal in strong sun** | `window` | Half the opening is in black shadow; the visible glazing is a fraction of the true opening, so the box is drawn to the frame, not to the lit part. |
| 7 | **Clerestory strip, ~4 px tall** | `window` | Legitimate instance below the comfortable detection scale. LS3: *"software cannot invent pixels that aren't there"* — kept in as a known, documented limit. |

Cases 1, 2 and 3 are planted deliberately in the verification dataset
(`src/synthetic_facades.py`) as unlabelled decoys, which is why the error analysis finds
real false positives rather than a clean diagonal.

## Changing this contract

Adding or redefining a class invalidates every existing label for that class. If it must
happen: bump the contract version above, record what changed and why, re-export a new
Roboflow dataset version, and re-train. Never edit a definition in place and leave the
old labels in the dataset — that is how a dataset quietly becomes noise.
