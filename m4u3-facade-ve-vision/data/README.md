# Data

**No images are committed to this repository.** `data/dataset/` is gitignored and
populated at run time by `src/dataset.py` from whichever source `src/config.py` names.

That is a deliberate choice with three reasons: the repository stays clonable in seconds;
third-party imagery keeps its own licence at its own source rather than being silently
relicensed by being copied here; and there is exactly one authoritative version of the
dataset — the Roboflow version number — instead of a copy that drifts.

## Contents

| Path | What it is | Committed? |
|---|---|---|
| `data.yaml` | The class contract in YOLO form. Authoritative class order. | yes |
| `dataset/` | Downloaded or generated images and labels. | no |
| `new_images/` | Unseen images for the honest demo (LS3: *"never show a client a training image"*). | no, except this README |

## Sources and licences

Every image used for a real training run must appear here with its source and licence
**in the same commit that introduces it**. An unrecorded image is a licensing liability.

| Tier | Source | Licence | Notes |
|---|---|---|---|
| Verification | `src/synthetic_facades.py` | Apache-2.0 (this project) | Generated, deterministic from `seed=42`. Proves the pipeline. Not a result. |
| Public | Roboflow Universe façade datasets | *record per dataset* | Fork into your workspace and paste the licence its page declares. |
| Public | Unsplash / Pexels building exteriors | Unsplash / Pexels licence | Free for commercial use, no attribution required — but record the photo URL anyway. |
| Own | Author's photographs of publicly visible exteriors | Apache-2.0 (this project) | No client or employer project imagery. Ever. |

> **Excluded by policy:** imagery from any commissioned project, employer's site or client
> deliverable. Such images carry confidentiality obligations a public repository cannot
> honour. See [`../docs/governance_checklist.md`](../docs/governance_checklist.md) §1.

## The 80/20 split

The brief specifies 80 / 20 train / validation. Session 2's homework mentions
70 / 20 / 10 with a test split; this project follows the brief and holds out no separate
test set. The honest consequence, stated rather than hidden: **the validation set is used
both for early stopping and for the reported metrics**, so the reported figures are
mildly optimistic. The mitigation is the new-image pack in
`results/evidence/new_images/` — images the model has never seen in any capacity, which
is the demo that actually tests generalisation.

Split the dataset in Roboflow, not in code. Roboflow's split is recorded against the
dataset version, so it is reproducible; a split done in a notebook is not.

## Adding new images for the demo

Drop unseen photographs into `data/new_images/` and re-run notebook 03. Requirements:
not in the training or validation split, not a render of a building already in the
dataset, and licence-clear.
