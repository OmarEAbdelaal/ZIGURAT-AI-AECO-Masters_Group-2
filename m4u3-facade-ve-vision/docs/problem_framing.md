# Problem Framing

## 1. Where this sits in the FMP

Group 02's Final Master's Project is an **AI-Powered BIM Decision Support System for
Continuous Value Engineering** — a system that watches a design as it develops and tells
the team, continuously rather than at a gate review, where cost is accumulating and which
substitutions would hold performance while releasing budget.

That system needs to know what is actually *on* the façade. Inside Revit it can read the
model. But three situations in a real project put the truth outside the model:

| Situation | Why the model cannot answer |
|---|---|
| Concept and early SD | There is no modelled façade yet — there are renders, sketch elevations and reference images. |
| Benchmarking | The team wants to compare against a precedent building or a competitor's scheme. There is no BIM model of someone else's building. |
| As-built divergence | The façade got value-engineered on site. The model says one thing; the site photograph says another. |

**This unit's contribution is the perception component**: given a photograph or a rendered
elevation, return the façade elements present, their class and their extent — so that the
VE engine can compute envelope indicators for a building it has no model of.

The façade is the right place to start because it is where the money is. On typical
commercial and residential projects the building envelope runs at roughly **15–25 % of
construction cost** and is consistently the first package opened in a value-engineering
exercise. Getting an early, cheap, repeatable read on envelope composition is worth more
than a more accurate read on almost anything else.

## 2. The problem framing template (LS1, Section 4)

| Component | This project |
|---|---|
| **Object(s) of interest** | `window`, `curtain_wall`, `door`, `balcony`, `louvre_screen` — the five façade elements that carry envelope cost and drive the glazing ratio |
| **Environment** | Exterior building elevations: daylight photographs taken from street level or drone, plus rendered elevations and elevation drawings exported from BIM. Mixed weather, oblique angles, partial occlusion by trees, vehicles and scaffold |
| **Critical metric** | **mAP50-95**, not mAP50. See §3 — this is the one non-obvious decision in the project |
| **Success criteria** | Recover Window-to-Wall Ratio to within ±10 % of the ratio a human derives from the same image, on frontal-to-30°-oblique daylight elevations of 3–10 storey buildings, in under 2 seconds per image |
| **Failure mode** | A mirror-glass spandrel panel — opaque, but reflecting sky exactly like a window — counted as glazing, inflating WWR and the cost index |

## 3. Why mAP50-95 and not mAP50

Session 3 gives the rule of thumb on mAP50: below 0.5 failing, 0.5–0.7 prototype,
above 0.7 solid. That rule is about *detection*. This project does not stop at detection.

The VE read-out is computed from **box area**:

```
WWR  =  Σ area(window, curtain_wall boxes)  /  façade area
cost ≈  Σ area(element) × rate(element class)
```

A box that covers the right window but is 20 % too large scores as a clean hit at
IoU 0.50. It also produces a 20 % cost error. `mAP50` is blind to precisely the failure
that costs this project money; `mAP50-95` averages across IoU 0.50→0.95 and so penalises
a loose box directly. Session 3's own error taxonomy names this **Localization Error —
"the box around the window is 20 % too large, including part of the wall.
(Cost: Inaccurate quantity takeoff.)"** That is this project's headline risk, so it is
measured by this project's headline metric.

`src/error_analysis.py` therefore reports localization drift as a **separate error
category**, not folded into the true positives, with a threshold at IoU 0.75.

## 4. Precision or recall?

Neither dominates here, which is itself worth stating rather than defaulting to the PPE
answer from the slides.

- This is **not** a life-safety system. A missed window is not a missed unvested worker.
  There is no recall imperative of the kind that justifies a paranoid threshold.
- It **is** a cost-estimation input feeding a recommendation a human then acts on. A
  false positive inflates a cost index and could send a team to value-engineer a package
  that was never over budget — wasted design effort and a damaged relationship with the
  client.

So the operating point is set at **conf = 0.35**, modestly above the Ultralytics default
of 0.25: lean slightly towards precision, because a hallucinated curtain wall is a more
expensive mistake than a missed one, and because in a *ratio* both the numerator and the
denominator are estimated — an error in either direction distorts the answer.

The one asymmetry worth protecting: `curtain_wall` instances are individually large. One
false `curtain_wall` moves the WWR far more than one false `window`. Per-class thresholds
are the first tuning lever in the iteration plan (`docs/error_analysis.md`, §4).

## 5. The anti-use case (LS1, Section 1)

Stating what this must never be used for is part of the deliverable, not a disclaimer
bolted on at the end.

- **Not a quantity take-off.** Pixel areas from a single uncalibrated photograph are not
  square metres. LS1's Q&A is explicit that dimensional inference from raw pixels with no
  scale or calibration is an unsolved problem. Every number this produces is a *relative*
  signal for comparing options, and every output carries that basis string.
- **Not a compliance check.** It cannot tell you whether the glazing ratio satisfies a
  thermal regulation, because it cannot measure the ratio in real units.
- **Not a BIM-vs-reality verifier.** That needs camera pose, registration and a reference
  model. LS1's Q&A sets this out as an advanced extension; detecting elements in site
  images is the one component of it in scope here.
- **Not a people-watching system.** No person class, by design. See
  `docs/governance_checklist.md`.

## 6. Operational tempo (LS4, Section 2)

**Mode 1 — batch.** A designer drops a folder of precedent images or rendered elevations
into the VE assistant and gets envelope indicators back. Latency is irrelevant; box
tightness is everything. This is the mode the project is built for, and it is why a nano
model at 640 px is a sensible starting point rather than a compromise.

Mode 2 (near-real-time site monitoring) and Mode 3 (field inspection on a tablet) are
plausible later homes for the same weights but are explicitly out of scope: neither has
been tested, and Mode 3 in particular would need a latency budget this project has not
measured.
