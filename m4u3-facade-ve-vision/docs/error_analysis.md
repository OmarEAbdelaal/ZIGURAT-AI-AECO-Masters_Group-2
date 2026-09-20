# Error Analysis & Iteration Plan

> Session 4: *"I will give more points for a well-explained failure than a fake success."*

**Run analysed:** `results/metrics/error_analysis.json` · weights `results/weights/best.pt`
· confidence ≥ 0.35 · match IoU 0.50 · 24 validation images · 491 ground-truth instances.

> ⚠️ **This analysis is of the VERIFICATION run** on the procedural dataset
> (`src/synthetic_facades.py`). The failure *mechanisms* below are real and transfer
> directly to photographic data — scale, class imbalance, thin-element drift and
> reflective decoys behave the same way on a real façade. The *rates* do not: synthetic
> imagery is far easier than a photograph, so every count here is optimistic. Re-run
> notebook 03 against the Roboflow dataset and this file regenerates from real evidence.

Every case below was found by `src/error_analysis.py`, which classifies every prediction
in the validation split against Session 3's four-way taxonomy and ranks the failures.
Nothing here was chosen by scrolling until something looked bad.

---

## 1 · The tally

| Error type | Count | % of all errors | AECO cost |
|---|---:|---:|---|
| True positive | 459 | — | — |
| **False negative** | **23** | 56.1 % | Understated envelope — **silent** |
| **False positive** | **9** | 22.0 % | Phantom glazed area → inflated WWR |
| **Localization error** | **6** | 14.6 % | Wrong quantity, *invisible to mAP50* |
| **Class confusion** | **3** | 7.3 % | Wrong unit rate applied |

**By class:**

| | window | curtain_wall | door | balcony | louvre_screen |
|---|---:|---:|---:|---:|---:|
| Val instances | 316 | 37 | 24 | 66 | 48 |
| False negatives | 16 | 0 | 4 | 2 | 1 |
| False positives | 7 | 0 | 2 | 0 | 0 |
| Recall | 0.951 | **1.000** | **0.830** | 0.970 | 0.979 |
| mAP50 | 0.985 | 0.995 | **0.821** | 0.965 | 0.971 |
| mAP50-95 | 0.951 | 0.976 | 0.809 | 0.897 | **0.764** |

Two numbers in that table are the whole story:

- **`door` recall 0.830** — the model misses one door in six, on the class with the fewest
  training instances.
- **`louvre_screen` mAP50 0.971 → mAP50-95 0.764**, a 21-point collapse. The model finds
  virtually every louvre screen and boxes almost none of them tightly. A project reporting
  only mAP50 would record this class as its second-best result. It is its worst.

---

## 2 · Three false positives

### FP-1 · Confident duplicate on a ground-floor opening
`results/evidence/errors/fp_01_facade_valid_0118.jpg` — predicted `door`, **conf 0.980**,
best IoU with any ground truth **0.326**.

**What happened.** The highest-confidence false positive in the entire run. The box covers
part of a ground-floor glazed unit that was already correctly detected by a higher-ranked
prediction; this second box overlaps it but falls below the 0.50 match threshold, so it is
counted as a hallucination.

**Hypothesis.** Fragmentation at a class boundary. Ground-floor units in this dataset are
tall and glazed, and the `door` / `window` decision depends on position and framing rather
than appearance. With only 96 `door` training instances the classifier head has not learned
a confident spatial prior, so it emits overlapping candidates at different scales and
NMS — which suppresses by IoU, not by semantics — keeps both. The 0.98 confidence is the
worrying part: the model is not hesitating.

**Why it matters here.** A duplicated ground-floor opening double-counts the most expensive
per-m² element in the rate table. This is the error class that inflates a cost index.

### FP-2 · Mirror-glass spandrel panel read as glazing
`fp_04_facade_valid_0117.jpg` — predicted `window`, conf 0.754, IoU **0.000** (no ground
truth anywhere near it).

**What happened.** The model boxed an opaque spandrel panel — one of the decoys planted at
a 13 % rate by the generator, carrying a sky-reflection gradient but no frame and no glass.

**Hypothesis.** The model has learned *reflection gradient* as a sufficient cue for
glazing. That cue is cheap, present in almost every true positive, and wrong exactly here.
This is the failure predicted in [`class_definitions.md`](class_definitions.md) boundary
case 1 and in the Session 2 Q&A, where a vest model latched onto reflective tape and then
failed when reflectivity changed.

**Why it matters here.** This is the project's most expensive single error. A spandrel
counted as glazing raises the glazed numerator *and* leaves the opaque denominator
unchanged, so WWR moves twice as fast as the area error alone. It is also the hardest to
catch by eye, because the box looks perfectly reasonable.

### FP-3 · Second hallucination with no ground truth
`fp_06_facade_valid_0098.jpg` — predicted `window`, conf 0.531, IoU 0.000.

**What happened.** The same decoy mechanism at roughly half the confidence.

**Hypothesis.** Same root cause as FP-2. Worth listing separately because the confidence
split matters operationally: raising the threshold from 0.35 to 0.60 would remove this one
and keep FP-2. **Thresholding cannot fix this failure** — the model is confidently wrong,
not uncertain. Only negative examples in the training data can fix it.

---

## 3 · Three false negatives

### FN-1 · Small windows below the detection floor
`fn_01_facade_valid_0119.jpg` and five more — missed `window` instances of
**304, 328, 505, 538, 574, 601 px²**, i.e. roughly 17×17 px down to 24×24 px in a 640×640
frame, each **under 0.15 % of image area**.

**What happened.** 16 of the 23 false negatives are `window`, and the smallest instances
dominate the ranking. The generator plants clerestory strips as a deliberate hard case.

**Hypothesis.** Scale, exactly as Session 3 describes it: after five stride-2
downsamples a 17 px object occupies about one cell of the P3 feature map. There is not
enough spatial support left for the head to localise it. *"Software cannot invent pixels
that aren't there."*

**Fix direction.** Not more epochs — more pixels. `imgsz=1280` or tiled inference. Both
are measurable and both are in the plan below.

### FN-2 · Doors missed at four times the base rate
4 of 24 `door` instances missed — recall **0.830**, against 0.951 for `window` and 1.000
for `curtain_wall`.

**Hypothesis.** Class imbalance, at **13.8 : 1** between the most and least frequent class
(96 `door` training instances against 1341 `window`). The classification loss is dominated
by windows; the cheapest way for the optimiser to reduce it is to become excellent at
windows and indifferent to doors. Session 2's Q&A on class imbalance describes precisely
this, and the linked arXiv study quantifies it for YOLO.

**Why it matters here.** `door` is the second-highest unit rate in the table. Missing one
in six understates entrance cost systematically — a **bias**, not noise, so it does not
average out across a portfolio of images.

### FN-3 · Occluded and glare-affected instances
Several missed instances sit behind the generator's foreground trees or inside its glare
blowouts.

**Hypothesis.** Two distinct mechanisms sharing a symptom. Occlusion removes the
rectangular gestalt the model relies on, so a window behind foliage presents as two
disconnected fragments. Glare destroys the frame-to-glass contrast the model uses as its
edge cue — LS3's "glare trap", where the camera clips to white and the signal is gone
before the model sees it.

**Fix direction.** Occlusion is trainable (label partial instances, augment with random
erasing). Glare is partly not — clipped pixels carry no information. The honest response
to glare is to detect the condition and abstain rather than to guess.

---

## 3b · The failure the headline metric hides

Not required by the brief, but it is this project's most important finding.

**`louvre_screen`: mAP50 0.971, mAP50-95 0.764.** Worst drift case
`drift_06_facade_valid_0108.jpg` — correct class, IoU 0.747, predicted box **+31 % larger
in area** than ground truth. Also `drift_01` (window, IoU 0.630, **−36 % area**) and
`drift_03` (balcony, IoU 0.732, **−22 % area**).

**Hypothesis.** Louvre screens are thin, high-aspect-ratio elements. The regression head
predicts width and height with roughly constant *absolute* error, so on an element 12 px
tall a 3 px error is 25 % of the dimension. Aspect ratios far from the anchor distribution
compound it.

**Why this is the finding.** Every one of these boxes is a **true positive** at IoU 0.50.
A report quoting mAP50 records them as successes. In a Value Engineering read-out computed
from box area, a +31 % box is a +31 % quantity and a +31 % cost. The error is invisible to
the metric most projects headline, which is the entire reason this project headlines
mAP50-95 instead — see [`problem_framing.md`](problem_framing.md) §3.

There is a third class-confusion case that fits here too:
`confusion_02_facade_valid_0108.jpg`, a `window` predicted as `louvre_screen` at IoU 0.551.
A thin horizontal glazed strip and a slatted screen are close to indistinguishable at that
scale — the same thin-element geometry causing a different symptom.

---

## 4 · Three prioritised data improvements

Ordered by expected mAP50-95 gain per hour of annotation. Each names a specific dataset
gap, a specific action, and how we will know it worked.

### Priority 1 · 150 hard negatives for reflective opaque surfaces
**Gap.** The model has learned "reflection gradient ⇒ glazing". There is not one negative
example teaching it otherwise. Root cause of FP-2 and FP-3, and of the project's most
expensive error mode.

**Action.** Collect 150 images rich in mirror-glass spandrel panels, polished stone,
anodised aluminium and wet surfaces, and add them **with no labels on those elements**.
Unlabelled regions are trained as background, which is exactly the lesson needed. Include
~30 images of neighbouring-building reflections (standing rule 1).

**Measure.** `window` false positives at IoU 0.00 fall from 2 to ≤ 1 per 24 images, with
no loss of `window` recall. Re-run notebook 03; the tally regenerates.

**Why first.** It is the only fix here that thresholding cannot substitute for, it targets
the error that moves WWR twice, and negatives are cheap — no boxes to draw.

### Priority 2 · Rebalance `door` from 96 to ~300 instances
**Gap.** 13.8 : 1 imbalance; `door` recall 0.830 and mAP50 0.821, both worst in class.
Root cause of FN-2 and of both `door` → `window` confusions (IoU 0.976 and 0.970 — the
boxes were *right*, only the name was wrong, which is a classifier problem, not a
localisation one).

**Action.** Targeted collection of ~200 additional ground-floor entrance instances across
revolving, paired, recessed and glazed-shopfront types. Do **not** rely on oversampling
the existing 96 — that amplifies whatever is unrepresentative about them. Simultaneously
sharpen the `door` / `window` rule in the class contract: the current "ground-level"
wording is what an annotator reaches for and it is ambiguous on a split-level entrance.

**Measure.** `door` recall ≥ 0.92, imbalance ratio below 6 : 1, `door`→`window` confusions
to zero.

### Priority 3 · Small-instance coverage plus a resolution decision
**Gap.** 16 `window` false negatives concentrated below ~600 px². The dataset contains
clerestory strips but too few for the model to learn them, and 640 px may simply be the
wrong resolution for this class.

**Action, in two parts.**
1. Add ~100 images containing clerestory strips, high-level vents and small punched
   windows at distance — instances between 8 and 30 px, annotated to the 8 px floor.
2. Run the same dataset at `imgsz=1280` and compare. Session 3 is explicit that doubling
   resolution quadruples training time, so this is a decision to *evidence*, not to
   assume. If 1280 does not lift small-instance recall materially, tiled inference at 640
   is the cheaper answer.

**Measure.** Recall on instances under 900 px² — a slice worth adding to
`error_analysis.py` — plus total training time, so the cost of the resolution change is
recorded alongside its benefit.

---

## 5 · What is deliberately not on this list

- **More epochs.** Validation loss had flattened, not turned up; the model is not
  underfitting. More epochs would buy nothing and risk the memorisation trap.
- **A bigger model (`yolov8s`/`m`).** Tempting and wrong as the next move. Every failure
  above is a *data* failure — missing negatives, missing instances, missing pixels. A
  larger model trained on the same gaps learns the same wrong cue with more capacity.
  Revisit after Priority 1–3, not before.
- **Lowering the confidence threshold to recover the false negatives.** FN-1 instances are
  not low-confidence detections waiting to be let through; they produce no detection at
  all. Lowering the threshold would admit more false positives and recover almost none of
  them.

## 6 · The iteration cycle

Session 3's software mindset: **annotate → train → analyse → fix the data → repeat.**
Each cycle changes *one* variable. Priority 1 is a data-only change with the model held
fixed, so any movement in the FP tally is attributable to it. Priority 3 explicitly
separates its data change from its resolution change for the same reason — two variables
moved at once produce a result nobody can act on.
