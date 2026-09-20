# SAM Exploration — What Helped, What Failed

> Session 2, Section 3. A no-code evaluation of Segment Anything as a labelling
> accelerator for this class contract.

## What was tried

SAM was used through Roboflow's Smart Polygon / auto-label path rather than a local
install — the no-code route in the session — on a sample of façade images spanning the
five classes, including several of the boundary cases from
[`class_definitions.md`](class_definitions.md).

## What helped

**Large, high-contrast, convex elements.** `curtain_wall` zones and `door` openings are
exactly what SAM is good at: a big region whose boundary is a strong, continuous edge. A
click near the centre returned a mask that needed no adjustment. For these two classes
the time saving over drawing a box by hand was real and worth having.

**Balconies, with one caveat.** SAM segments the balustrade cleanly because it is a
distinct texture against the façade. It reliably returns the balustrade *only* — which
happens to be close to this contract's box definition, so the result needed a small
extension downward rather than a redraw.

**Consistency of edges.** Where SAM worked, it was more consistent than a human at
finding the true frame edge. Hand-drawn boxes drift a few pixels; SAM's did not. Given
that this project's headline metric is IoU-strict, that consistency is not cosmetic — it
directly reduces the localization-error floor baked into the labels.

## What failed

**The `window` / `curtain_wall` boundary — the decisive failure.** SAM has no concept of
this contract. Asked to segment a glazed area it returns *a glazed area*: sometimes one
pane, sometimes one bay, sometimes the whole façade plane, and the choice varies with
click position. The distinction the contract turns on — whether the glass is interrupted
by opaque material — is a semantic rule about buildings, not a visual boundary SAM can
see. Every glazed region still needed a human decision about which class it was and where
one instance ended. This is precisely the "Kryptonite check" the session warns about.

**Mirror-glass spandrel panels.** SAM segments them beautifully, because they *are* a
clean visual region. It has no way of knowing they are opaque and must not be labelled.
Auto-labelling would have silently created the single most expensive false positive in
this project's taxonomy, at scale, with tight boxes and high apparent quality. Reviewing
these out by hand cost more time than drawing the correct boxes would have.

**Small and thin elements.** Clerestory strips and slim louvre blades fell below SAM's
useful resolution: returned masks either merged them with the surrounding wall or missed
them. These are already this project's hardest instances; SAM made them no easier.

**The geometry tax.** SAM returns masks; YOLO detection consumes axis-aligned boxes. The
mask→box conversion is lossy in a specific and relevant way: on an oblique elevation, a
window is a parallelogram, and its axis-aligned bounding box includes a wedge of wall.
The tighter the mask, the more obviously wrong the box. Since box area feeds the cost
index, this inflates quantities on exactly the oblique images where they are hardest to
sanity-check. The tax is paid at conversion and SAM cannot avoid it.

## Verdict

**Use SAM as an accelerator for `curtain_wall`, `door` and `balcony`. Do not use it for
`window` or `louvre_screen`, and never accept its output unreviewed.**

The net saving across the sample was real but modest — perhaps 25–30 % of annotation time
on the classes where it worked — and it was conditional on a human reviewing every mask.
The moment review was skipped, decoy panels entered the dataset as confident, tight,
wrong labels. A wrong label with a tight box is worse than no label: it teaches the model
the error and it looks like quality while doing so.

The session's framing holds. SAM does not know your class contract. It knows edges. The
part of annotation that is expensive is not drawing the box — it is deciding what the box
means, and that decision is the contract, which stays human.

## What this changed in the project

1. `curtain_wall`, `door` and `balcony` were annotated SAM-first, human-reviewed.
2. `window` and `louvre_screen` were annotated entirely by hand.
3. The unbroken-glass test in the class contract was written *because* SAM exposed how
   ambiguous the boundary was — the failure produced a better contract. That is the
   useful outcome of the exploration, more than the time saved.
