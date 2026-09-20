# Façade Element Detection for Continuous Value Engineering

**ZIGURAT AI-AECO Master · MAICEN 0526 · Module 4, Unit 3 — Computer Vision**
Omar Elsayed · Group 02

A YOLOv8 detector that reads building-envelope elements from photographs and rendered
elevations, so a Value Engineering assistant can estimate envelope composition for a
building it has no BIM model of.

[![Open 01 Baseline in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/OmarEAbdelaal/ZIGURAT-AI-AECO-Masters_Group-2/blob/main/m4u3-facade-ve-vision/notebooks/01_baseline_inference.ipynb)
[![Open 02 Train in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/OmarEAbdelaal/ZIGURAT-AI-AECO-Masters_Group-2/blob/main/m4u3-facade-ve-vision/notebooks/02_train_and_evaluate.ipynb)
[![Open 03 Evidence in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/OmarEAbdelaal/ZIGURAT-AI-AECO-Masters_Group-2/blob/main/m4u3-facade-ve-vision/notebooks/03_inference_and_evidence.ipynb)
[![Licence](https://img.shields.io/badge/licence-Apache--2.0-blue.svg)](LICENSE)

> ### ⚠️ Read this before using any number in this repository
> **This model is an assistive tool for preliminary screening only. It produces False
> Negatives. It must NOT be used as the sole verifier for life-safety decisions.**
>
> The metrics currently published are from a **verification run on procedurally generated
> façades**, which exists to prove the pipeline executes end-to-end for a stranger with no
> account. They demonstrate that the machinery works. They are **not** evidence of
> real-world façade detection performance. See
> [Reproducibility Proof](docs/reproducibility.md).

---

## 1 · The problem

Group 02's Final Master's Project is an **AI-Powered BIM Decision Support System for
Continuous Value Engineering** — a system that tells a design team where cost is
accumulating while the design is still moving, rather than at a gate review.

That system reads the BIM model. But three situations put the truth outside the model:
there is no modelled façade yet at concept stage; there is no model at all of a precedent
or competitor building you want to benchmark against; and the as-built façade may have
diverged from the model on site.

**This unit supplies the perception component.** Given a photograph or rendered elevation,
return the façade elements present, their class and their extent — so the VE engine can
compute envelope indicators without a model.

The envelope is the right target because it is where the money is: typically **15–25 % of
construction cost**, and consistently the first package opened in a VE exercise.

### Success criteria

Recover Window-to-Wall Ratio to within **±10 %** of a human's reading of the same image,
on frontal-to-30°-oblique daylight elevations of 3–10 storey buildings, in **under 2
seconds** per image.

### The headline metric is mAP50-95, not mAP50

The one non-obvious decision in this project, and the reason is worth a sentence. The VE
read-out is computed from **box area**. A box that covers the right window but is 20 % too
large scores as a clean hit at IoU 0.50 — and produces a 20 % cost error. `mAP50` is blind
to precisely the failure that costs this project money. Session 3's own error taxonomy
names it: *Localization Error — "the box around the window is 20 % too large… Cost:
Inaccurate quantity takeoff."*
Full reasoning: [`docs/problem_framing.md`](docs/problem_framing.md) §3.

---

## 2 · Classes and label rules

Five classes. **Order is load-bearing** — class ids are positional in every label file,
and `src/dataset.py` refuses to train if a dataset's order disagrees with the config.

| id | class | definition | the discriminating test |
|---|---|---|---|
| 0 | `window` | discrete glazed opening within an opaque wall | bounded by opaque material on all four sides |
| 1 | `curtain_wall` | continuous glazed zone, no opaque interruption | *can I trace unbroken glass across it?* |
| 2 | `door` | ground-level pedestrian entrance / egress | at grade and enterable |
| 3 | `balcony` | projecting or recessed occupiable slab with balustrade | occupiable depth, not a guard rail |
| 4 | `louvre_screen` | fixed slatted solar-shading or plant screening | permanent, not scaffold netting |

**The three standing rules** (Session 2's homework — the tie-breakers when the contract is
silent):

1. **No reflections.** A window mirrored in a neighbouring façade is not a window on this
   building. Labelling it double-counts the envelope.
2. **No neighbouring buildings.** One subject per image. Ambiguous → crop or discard.
3. **Partial and occluded elements ARE labelled**, boxing only the visible extent, down to
   an 8 px floor. A street-level façade is occluded; a model trained only on clean
   instances fails on every real photograph.

Boxes are drawn to the **outer frame edge**, because the frame is part of the purchased
unit and therefore part of the cost.

Full inclusion/exclusion rules and the seven-case boundary gallery:
[`docs/class_definitions.md`](docs/class_definitions.md).

---

## 3 · Dataset

| | |
|---|---|
| **Split** | **80 / 20** train / validation, split in Roboflow so it is recorded against the dataset version |
| **Format** | YOLOv8 (`data.yaml` + one `.txt` per image) |
| **Roboflow project** | set `ROBOFLOW_WORKSPACE` / `ROBOFLOW_PROJECT` / `ROBOFLOW_VERSION` in [`src/config.py`](src/config.py) |
| **Verification dataset** | 96 train / 24 val, 2 578 instances, generated by [`src/synthetic_facades.py`](src/synthetic_facades.py), deterministic from `seed=42` |
| **Rights** | public / licensed; per-source table in [`data/README.md`](data/README.md). No client or employer imagery. |

**Images are not committed.** `data/` is gitignored and populated at run time. That keeps
the clone fast, keeps third-party imagery under its own licence at its own source, and
leaves exactly one authoritative dataset version instead of a copy that drifts.

### Three dataset sources, one notebook

Set `DATASET_SOURCE` in `src/config.py`:

| Value | Behaviour | Requires |
|---|---|---|
| `synthetic` *(default)* | generates a procedural façade dataset locally | **nothing** |
| `roboflow` | downloads your own Roboflow project | API key + project in config |
| `universe` | downloads a forked Roboflow Universe project | same |

The default is `synthetic` so the notebooks **run end to end for a reader with no account,
no API key and no GPU**. That is the reproducibility requirement taken literally rather
than aspirationally.

---

## 4 · How to reproduce

Cloud only. Nothing to install locally.

### The three-minute version

1. Click **[Open 02 Train & Evaluate in Colab](https://colab.research.google.com/github/OmarEAbdelaal/ZIGURAT-AI-AECO-Masters_Group-2/blob/main/m4u3-facade-ve-vision/notebooks/02_train_and_evaluate.ipynb)**.
2. **Runtime → Change runtime type → T4 GPU.** (CPU also works — 8–12 min.)
3. **Runtime → Restart session and run all.** Change nothing.
4. Wait 2–4 min on GPU.

**Expected output, in order:** a dataset health report showing the 80/20 split and the
13.8 : 1 class imbalance → a 6-image grid of labelled training data → a 30-epoch training
log with `box_loss` falling → a metrics table → `results.png`, the normalised confusion
matrix and the PR curve → `best.pt` on disk.

Then open **[03 Inference & Evidence](https://colab.research.google.com/github/OmarEAbdelaal/ZIGURAT-AI-AECO-Masters_Group-2/blob/main/m4u3-facade-ve-vision/notebooks/03_inference_and_evidence.ipynb)** and run all: predictions on validation and on unseen
images, the VE read-out table, and the automatically mined error taxonomy with cropped
failure cases.

> **Verified, not asserted.** `02_train_and_evaluate.ipynb` was executed restart-and-run-all
> and reproduced the committed metrics **exactly to four decimal places**, with every
> generated curve byte-identical to the original run. Details:
> [`docs/reproducibility.md`](docs/reproducibility.md).

> **The notebooks ship with their outputs committed.** You can read the whole run —
> metrics, curves, predictions, error crops — on GitHub without executing anything. The
> outputs you see are from the run recorded in
> [`docs/reproducibility.md`](docs/reproducibility.md).

Start with **[01 Baseline Inference](https://colab.research.google.com/github/OmarEAbdelaal/ZIGURAT-AI-AECO-Masters_Group-2/blob/main/m4u3-facade-ve-vision/notebooks/01_baseline_inference.ipynb)** (~2 min) if you want to see *why* a custom model
is needed: stock COCO YOLOv8 on a façade finds no windows, no curtain wall and no
balconies, because it has never been given a word for them.

### To run on your own Roboflow dataset

In `src/config.py`:

```python
DATASET_SOURCE     = "roboflow"
ROBOFLOW_WORKSPACE = "your-workspace"   # from app.roboflow.com/<WORKSPACE>/<PROJECT>/<VERSION>
ROBOFLOW_PROJECT   = "your-project"
ROBOFLOW_VERSION   = 1
```

Then add your API key as a **Colab secret** named `ROBOFLOW_API_KEY` (sidebar → 🔑 → enable
for this notebook). It is never typed into a cell and never committed.

### To run inference without training

Notebook `03` downloads `best.pt` from the URL in `WEIGHTS_URL` if no local weights exist.
Publish yours as a **GitHub Release** asset and paste the direct link there.

---

## 5 · Results

> **VERIFICATION RUN** — procedural dataset, not a performance claim. Re-run against a
> Roboflow dataset before quoting any figure. The banner is generated from
> `DATASET_SOURCE`, so it cannot be left on by accident or taken off by hand.

**yolov8n · 30 epochs · batch 16 · imgsz 640 · seed 42 · validation split, IoU 0.50**

| Precision | Recall | mAP50 | **mAP50-95** |
|---:|---:|---:|---:|
| 0.975 | 0.946 | 0.948 | **0.879** |

| Class | Val instances | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|---:|
| `window` | 316 | 0.980 | 0.951 | 0.985 | 0.951 |
| `curtain_wall` | 37 | 0.980 | 1.000 | 0.995 | 0.976 |
| `door` | 24 | 0.952 | **0.830** | **0.821** | 0.809 |
| `balcony` | 66 | 0.994 | 0.970 | 0.965 | 0.897 |
| `louvre_screen` | 48 | 0.971 | 0.979 | 0.971 | **0.764** |

Generated by `src/train.py` → [`results/metrics/metrics.md`](results/metrics/metrics.md).
Nothing in this table was typed by hand.

### Three takeaways

**1 · The metric you report decides what you think you built.**
`louvre_screen` scores mAP50 **0.971** and mAP50-95 **0.764** — a 21-point collapse. At
mAP50 it looks like the second-best class; measured strictly it is the worst. The model
finds almost every louvre screen and boxes almost none of them tightly, because thin
high-aspect-ratio elements suffer roughly constant *absolute* regression error, which on a
12 px-tall element is 25 % of the dimension. Worst observed case: **+31 % box area**.
Since the VE read-out is computed from area, that is a +31 % cost error that `mAP50`
records as a success.

**2 · Class imbalance shows up as a systematic cost bias, not as noise.**
At **13.8 : 1** between the most and least frequent class, `door` — with 96 training
instances against 1 341 windows — is the worst class on every measure (recall 0.830,
mAP50 0.821). Both `door`→`window` confusions had near-perfect boxes (IoU 0.976 and 0.970):
the model localised correctly and *named* wrongly, which is a classifier problem caused by
imbalance, not a localisation problem. Because `door` carries the second-highest unit rate,
missing one in six understates entrance cost **systematically**, so it does not average out
across a portfolio.

**3 · The dangerous error is the quiet one.**
False negatives outnumber false positives 23 to 9. A false positive gets challenged the
moment a human looks at the annotated image; a false negative produces a plausible number
nobody questions. That inverts the PPE logic from the slides, where recall dominates
because a miss is a safety event. Here both directions distort a *ratio*, and the miss is
invisible — which is why every evidence render shows the boxes, not only the numbers. The
human check is the mitigation.

### Curves

| | |
|---|---|
| [`results/curves/results.png`](results/curves/results.png) | loss curves and metric progression — the vitals check |
| [`results/curves/confusion_matrix_normalized.png`](results/curves/confusion_matrix_normalized.png) | where classes are mixed up |
| [`results/curves/PR_curve.png`](results/curves/PR_curve.png) | precision–recall by class |
| [`results/curves/results.csv`](results/curves/results.csv) | per-epoch raw numbers |

### Evidence pack

| Folder | Contents |
|---|---|
| [`results/evidence/annotations/`](results/evidence/annotations/) | 5 ground-truth examples — the label contract as applied |
| [`results/evidence/validation/`](results/evidence/validation/) | 10 validation predictions |
| [`results/evidence/new_images/`](results/evidence/new_images/) | 5 predictions on **unseen** images — the honest test |
| [`results/evidence/errors/`](results/evidence/errors/) | worst FP / FN / class-confusion / localization-drift crops |
| [`results/metrics/error_analysis.json`](results/metrics/error_analysis.json) | machine-readable error tally |

All produced by code from the committed weights, not screenshotted — so `Run all`
refreshes the whole pack and a reviewer can tell which run produced which image.

---

## 6 · Error analysis

Errors are mined automatically by [`src/error_analysis.py`](src/error_analysis.py), which
classifies **every** prediction in the validation split against Session 3's four-way
taxonomy and ranks the failures — false positives by confidence, false negatives by size.
Nothing was chosen by scrolling until something looked bad.

| Error type | Count | % of errors |
|---|---:|---:|
| False negative | 23 | 56.1 % |
| False positive | 9 | 22.0 % |
| Localization error | 6 | 14.6 % |
| Class confusion | 3 | 7.3 % |

Three false positives, three false negatives, a hypothesis for each, and three prioritised
data improvements with success measures: **[`docs/error_analysis.md`](docs/error_analysis.md)**.

The short version of the iteration plan — every failure above is a *data* failure, so the
next move is data, not a bigger model:

1. **150 hard negatives** of reflective opaque surfaces. The model has learned
   "reflection gradient ⇒ glazing" and has never seen a counterexample.
2. **Rebalance `door` from 96 to ~300 instances.** Targeted collection, not oversampling.
3. **Small-instance coverage plus an evidenced resolution decision** (640 vs 1280 vs
   tiling), measured rather than assumed.

---

## 7 · Governance and licensing

| | |
|---|---|
| **Governance checklist** | [`docs/governance_checklist.md`](docs/governance_checklist.md) — provenance, PII, risk, human-in-the-loop, licence |
| **Model card** | [`docs/model_card.md`](docs/model_card.md) |
| **Code licence** | **Apache-2.0** ([`LICENSE`](LICENSE)) — chosen over MIT for the explicit patent grant |
| **Dataset rights** | public / licensed, per-source table in [`data/README.md`](data/README.md) |
| **⚠️ Upstream** | Ultralytics YOLOv8 is **AGPL-3.0**. Fine-tuned weights inherit it. Commercial deployment needs AGPL compliance or an Ultralytics Enterprise Licence — see [`NOTICE`](NOTICE) |

**Privacy by design:** there is no `person` class and no `vehicle` class. Data minimisation
is applied *at the class contract*, so the model is structurally incapable of identifying
anyone — not filtered afterwards. No biometric processing. No client or employer imagery.

**When not to use this:** quantity take-off, cost certification, code compliance,
BIM-vs-reality verification, heritage or non-European typologies, night/fog/extreme
obliquity, anything below ~8 px, anything involving people.
Full statement: [`docs/governance_checklist.md`](docs/governance_checklist.md) §5.

---

## 8 · Repository map

```
m4u3-facade-ve-vision/
├── notebooks/
│   ├── 01_baseline_inference.ipynb      COCO YOLOv8 fails on façades — the motivation
│   ├── 02_train_and_evaluate.ipynb      train, metrics, curves
│   └── 03_inference_and_evidence.ipynb  inference, evidence pack, error mining
├── src/
│   ├── config.py               ← THE only file to edit. Every parameter, one place.
│   ├── dataset.py              roboflow / universe / synthetic resolver + health check
│   ├── synthetic_facades.py    procedural fallback dataset with planted decoys
│   ├── train.py                training + metrics extraction
│   ├── evidence.py             evidence pack + Value Engineering read-out
│   └── error_analysis.py       AECO error taxonomy miner
├── docs/
│   ├── problem_framing.md      AECO problem, success criteria, anti-use case
│   ├── class_definitions.md    the labelling contract + boundary cases
│   ├── sam_exploration.md      SAM: what helped, what failed
│   ├── error_analysis.md       3 FP + 3 FN + 3 prioritised improvements
│   ├── governance_checklist.md privacy, risk, limitations, licence
│   ├── reproducibility.md      proof of last run + reproducibility checklist
│   ├── standalone_repo.md      how to lift this out into its own repository
│   └── model_card.md
├── results/
│   ├── metrics/                metrics.md · metrics.json · per-class CSV · error tally
│   ├── curves/                 results.png · confusion matrix · PR curve · results.csv
│   ├── evidence/               annotations · validation · new_images · errors
│   └── weights/best.pt
├── reports/                    6-slide PDF + 2-page mini report
├── data/                       data.yaml + provenance (images gitignored)
├── LICENSE · NOTICE · requirements.txt
```

---

## 9 · PDF pack

| Document | |
|---|---|
| **Slides** (6 pages) | [`reports/M4U3_Slides_FacadeVE_OmarElsayed.pdf`](reports/M4U3_Slides_FacadeVE_OmarElsayed.pdf) |
| **Mini report** (2 pages) | [`reports/M4U3_MiniReport_FacadeVE_OmarElsayed.pdf`](reports/M4U3_MiniReport_FacadeVE_OmarElsayed.pdf) |

## 10 · Weights

`best.pt` — 6.2 MB, yolov8n fine-tuned, 5 classes. In-repo at
[`results/weights/best.pt`](results/weights/best.pt); publish as a GitHub Release and set
`WEIGHTS_URL` in `src/config.py` so notebook 03 can fetch it without a clone.

`best.pt`, never `last.pt` — `last.pt` is wherever training happened to stop, possibly
while getting worse.

---

## 11 · Where this lives

This deliverable is **self-contained** — its own README, licence, notebooks, source and
results, with every path resolving from `src/config.py`. It currently sits as a subfolder
of the Group 02 repository. To lift it into a standalone repository with its commit
history intact, see [`docs/standalone_repo.md`](docs/standalone_repo.md) — three commands,
plus one `sed` to re-point the Colab badges.

---

## Acknowledgements

Module 4 Unit 3 taught by **Pablo Aumente Gallego** (Brave Studio GmbH), ZIGURAT Global
Institute of Technology. The error taxonomy, the class-definition contract, the handover
standard and the governance checklist template are all from those four sessions.

Built on [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) (AGPL-3.0).
